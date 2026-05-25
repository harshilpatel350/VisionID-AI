"""
Request-scoped context using *contextvars*.

This lets any layer (service, repository, logger) access the current
request's ID, authenticated user, and client IP without explicit arg-passing.
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequestContext:
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    client_ip: str = ""
    user_id: int | None = None
    user_role: str | None = None


_request_ctx: ContextVar[RequestContext] = ContextVar("request_ctx", default=RequestContext())


def get_request_context() -> RequestContext:
    return _request_ctx.get()


def set_request_context(ctx: RequestContext) -> None:
    _request_ctx.set(ctx)


def current_request_id() -> str:
    return _request_ctx.get().request_id


def current_client_ip() -> str:
    return _request_ctx.get().client_ip
