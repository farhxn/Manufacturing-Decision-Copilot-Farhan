"""Shared API envelope schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = 1
    limit: int = 20
    total: int = 0
    total_pages: int = 0


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[str] = Field(default_factory=list)


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None
    meta: PaginationMeta | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
