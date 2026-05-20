from __future__ import annotations
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

@dataclass
class RateLimitState:
    hits: deque


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int = 180):
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self._state: dict[str, RateLimitState] = defaultdict(lambda: RateLimitState(deque()))

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
            return await call_next(request)
        key = request.client.host if request.client else "unknown"
        now = time.time()
        state = self._state[key]
        window = 60.0
        while state.hits and now - state.hits[0] > window:
            state.hits.popleft()
        if len(state.hits) >= self.limit_per_minute:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        state.hits.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit_per_minute - len(state.hits)))
        return response
