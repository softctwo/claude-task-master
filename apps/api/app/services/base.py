"""Generic CRUD Service layer for SQLAlchemy async models."""
from typing import Generic, TypeVar, Optional, List, Any
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.database import Base

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class CRUDService(Generic[ModelType]):
    """Generic async CRUD service."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: str) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.__table__.primary_key.columns.values()[0] == id))
        return result.scalar_one_or_none()

    async def get_by(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        stmt = select(self.model)
        for key, value in kwargs.items():
            if not hasattr(self.model, key):
                continue
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, db: AsyncSession, *, order_by: Optional[str] = None, desc_order: bool = True) -> List[ModelType]:
        stmt = select(self.model)
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            stmt = stmt.order_by(desc(col) if desc_order else col)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            if value is not None and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, db_obj: ModelType) -> None:
        await db.delete(db_obj)
        await db.commit()

    async def filter_by(self, db: AsyncSession, **kwargs) -> List[ModelType]:
        stmt = select(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await db.execute(stmt)
        return list(result.scalars().all())
