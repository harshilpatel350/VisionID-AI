from __future__ import annotations
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.context import RequestContext, set_request_context

logger = logging.getLogger("visionid")


# ── Request Context Middleware ──────────────────────────────────

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Generates a unique request ID, resolves client IP (including behind proxies),
    and populates the request-scoped context for logging & audit.
    Also adds X-Request-ID and X-Process-Time headers to every response.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        client_ip = self._resolve_client_ip(request)

        ctx = RequestContext(request_id=request_id, client_ip=client_ip)
        set_request_context(ctx)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms:.1f}ms"

        logger.info(
            "%s %s → %s (%.1fms) [ip=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_ip,
        )
        return response

    @staticmethod
    def _resolve_client_ip(request: Request) -> str:
        """Extract the real client IP, respecting reverse proxy headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"


# ── Rate Limiter ────────────────────────────────────────────────

@dataclass
class _RateBucket:
    hits: deque = field(default_factory=deque)
    last_accessed: float = 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP sliding-window rate limiter with:
    • Configurable default limit and per-path overrides
    • Auto-cleanup of stale entries to prevent memory leaks
    • Proper proxy IP resolution via RequestContext
    """

    _STALE_ENTRY_TTL = 300  # seconds before a bucket is cleaned up

    def __init__(
        self,
        app,
        default_limit: int = 240,
        path_limits: dict[str, int] | None = None,
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.path_limits = path_limits or {}
        self._buckets: dict[str, _RateBucket] = defaultdict(_RateBucket)
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip docs / health endpoints
        if any(path.startswith(p) for p in ("/docs", "/openapi", "/redoc", "/api/health")):
            return await call_next(request)

        # Determine limit for this path
        limit = self.default_limit
        for prefix, lim in self.path_limits.items():
            if path.startswith(prefix):
                limit = lim
                break

        # Resolve client IP from context or header
        try:
            from app.core.context import get_request_context
            key = get_request_context().client_ip
        except Exception:
            key = request.client.host if request.client else "unknown"

        now = time.time()
        bucket = self._buckets[key]
        bucket.last_accessed = now

        # Slide window: remove entries older than 60s
        while bucket.hits and now - bucket.hits[0] > 60.0:
            bucket.hits.popleft()

        if len(bucket.hits) >= limit:
            return JSONResponse(
                {"success": False, "error": {"code": "RATE_LIMIT", "message": "Rate limit exceeded. Please slow down."}},
                status_code=429,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        bucket.hits.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - len(bucket.hits)))
        self._periodic_cleanup(now)
        return response

    def _periodic_cleanup(self, now: float) -> None:
        """Remove stale entries to prevent unbounded memory growth."""
        if now - self._last_cleanup < self._STALE_ENTRY_TTL:
            return
        stale_keys = [k for k, v in self._buckets.items() if now - v.last_accessed > self._STALE_ENTRY_TTL]
        for k in stale_keys:
            del self._buckets[k]
        self._last_cleanup = now
