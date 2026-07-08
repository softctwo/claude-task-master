"""Brief router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.dependencies import get_current_user, require_manager_or_admin
from app.models import Brief, PRD
from app.schemas import (
    BriefCreate, BriefUpdate, BriefOut, BriefApprove, BriefGeneratePRD,
    PRDOut, PaginationParams, PaginatedResponse,
)
from app.services import brief_service, prd_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_briefs(
    page: int = 1,
    page_size: int = 20,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List briefs with optional filtering."""
    stmt = select(Brief)
    if project_id:
        stmt = stmt.where(Brief.project_id == project_id)
    if status:
        stmt = stmt.where(Brief.status == status)
    stmt = stmt.order_by(desc(Brief.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda b: BriefOut.model_validate(b).model_dump(),
    )


@router.post("", response_model=BriefOut, status_code=status.HTTP_201_CREATED)
async def create_brief(
    brief_in: BriefCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new brief."""
    brief_data = brief_in.model_dump()
    brief_data["owner_id"] = current_user.user_id
    brief = await brief_service.create(db, brief_data)
    return BriefOut.model_validate(brief)


@router.get("/{brief_id}", response_model=BriefOut)
async def get_brief(brief_id: str, db: AsyncSession = Depends(get_db)):
    """Get brief by ID."""
    brief = await brief_service.get(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    return BriefOut.model_validate(brief)


@router.put("/{brief_id}", response_model=BriefOut)
async def update_brief(
    brief_id: str,
    brief_in: BriefUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update brief."""
    brief = await brief_service.get(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    if str(brief.owner_id) != current_user.user_id and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this brief")
    updated = await brief_service.update(db, brief, brief_in.model_dump(exclude_unset=True))
    return BriefOut.model_validate(updated)


@router.delete("/{brief_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brief(
    brief_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Delete brief (admin/manager only)."""
    brief = await brief_service.get(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    await brief_service.delete(db, brief)
    return None


@router.post("/{brief_id}/generate-prd", response_model=PRDOut)
async def generate_prd_from_brief(
    brief_id: str,
    req: BriefGeneratePRD,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a PRD from an approved brief."""
    brief = await brief_service.get(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    if brief.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brief must be approved before generating PRD")

    # Create a placeholder PRD (real generation would be async / AI-driven)
    prd_data = {
        "brief_id": brief_id,
        "project_id": str(brief.project_id),
        "content_markdown": f"# PRD for {brief.title}\n\n_Generated from brief {brief_id}_\n\n## Background\n{brief.background or ''}\n\n## Problem Statement\n{brief.problem_statement or ''}",
        "source": "brief",
        "version": 1,
        "generated_by": req.generated_by or current_user.name,
    }
    prd = await prd_service.create(db, prd_data)
    return PRDOut.model_validate(prd)


@router.post("/{brief_id}/approve", response_model=BriefOut)
async def approve_brief(
    brief_id: str,
    req: BriefApprove,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Approve or reject a brief."""
    brief = await brief_service.get(db, brief_id)
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    updated = await brief_service.update(db, brief, {"status": req.status})
    return BriefOut.model_validate(updated)
