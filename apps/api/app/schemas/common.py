"""Common pagination schemas for API responses."""

from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""

    items: List[T] = Field(description="List of items for the current page")
    total: int = Field(ge=0, description="Total number of items across all pages")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")

    model_config = ConfigDict(from_attributes=True)
