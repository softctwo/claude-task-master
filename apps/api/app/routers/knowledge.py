"""Knowledge router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_

from app.database import get_db
from app.dependencies import get_current_user, require_developer_or_above
from app.models import KnowledgeItem
from app.schemas import (
    KnowledgeItemCreate, KnowledgeItemUpdate, KnowledgeItemOut,
    KnowledgeSearchResult, PaginationParams, PaginatedResponse,
)
from app.services import knowledge_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_knowledge_items(
    page: int = 1,
    page_size: int = 20,
    project_id: Optional[str] = None,
    type: Optional[str] = None,
    visibility: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List knowledge items with optional filtering."""
    stmt = select(KnowledgeItem)
    if project_id:
        stmt = stmt.where(KnowledgeItem.project_id == project_id)
    if type:
        stmt = stmt.where(KnowledgeItem.type == type)
    if visibility:
        stmt = stmt.where(KnowledgeItem.visibility == visibility)
    stmt = stmt.order_by(desc(KnowledgeItem.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda k: KnowledgeItemOut.model_validate(k).model_dump(),
    )


@router.post("", response_model=KnowledgeItemOut, status_code=status.HTTP_201_CREATED)
async def upload_knowledge(
    item_in: KnowledgeItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a knowledge item."""
    item = await knowledge_service.create(db, item_in.model_dump())
    return KnowledgeItemOut.model_validate(item)


@router.get("/search", response_model=KnowledgeSearchResult)
async def search_knowledge(
    q: str,
    project_id: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Full-text search over knowledge items (placeholder for semantic search)."""
    stmt = select(KnowledgeItem).where(
        or_(
            KnowledgeItem.title.ilike(f"%{q}%"),
            KnowledgeItem.parsed_text.ilike(f"%{q}%"),
        )
    )
    if project_id:
        stmt = stmt.where(KnowledgeItem.project_id == project_id)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    items = [KnowledgeItemOut.model_validate(k) for k in result.scalars().all()]
    return KnowledgeSearchResult(query=q, results=items)


@router.get("/{item_id}", response_model=KnowledgeItemOut)
async def get_knowledge_item(item_id: str, db: AsyncSession = Depends(get_db)):
    """Get knowledge item by ID."""
    item = await knowledge_service.get(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    return KnowledgeItemOut.model_validate(item)


@router.put("/{item_id}", response_model=KnowledgeItemOut)
async def update_knowledge_item(
    item_id: str,
    item_in: KnowledgeItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update knowledge item."""
    item = await knowledge_service.get(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    updated = await knowledge_service.update(db, item, item_in.model_dump(exclude_unset=True))
    return KnowledgeItemOut.model_validate(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_developer_or_above),
):
    """Delete knowledge item."""
    item = await knowledge_service.get(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    await knowledge_service.delete(db, item)
    return None
