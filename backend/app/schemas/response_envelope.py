from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetails(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: list[Any] | dict[str, Any] | None = None


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    success: bool = True
    data: T | None = None
    meta: dict[str, Any] | None = None
    error: ErrorDetails | None = None
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedMeta(BaseModel):
    total: int
    page: int
    page_size: int
    has_more: bool


class PaginatedResponse(ResponseEnvelope[list[T]], Generic[T]):
    """Standardized paginated response."""
    meta: PaginatedMeta
