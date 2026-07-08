"""Pagination utilities for SQLAlchemy async queries."""
from math import ceil
from typing import TypeVar, Generic, List, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.schemas import PaginatedResponse, PaginationParams

T = TypeVar("T", bound=DeclarativeBase)


async def paginate(
    session: AsyncSession,
    stmt,
    params: PaginationParams,
    transform: Any = None,
) -> PaginatedResponse:
    """Execute a paginated query and return a PaginatedResponse.

    Args:
        session: Async SQLAlchemy session.
        stmt: SQLAlchemy select statement.
        params: PaginationParams with page and page_size.
        transform: Optional callable to transform each ORM instance into a dict/Pydantic model.
    """
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Fetch page
    offset = (params.page - 1) * params.page_size
    page_stmt = stmt.offset(offset).limit(params.page_size)
    result = await session.execute(page_stmt)
    rows = result.scalars().all()

    items = rows
    if transform is not None:
        items = [transform(r) for r in rows]

    pages = ceil(total / params.page_size) if params.page_size > 0 else 0

    return PaginatedResponse(
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=pages,
        items=items,
    )
