"""PRD router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.dependencies import get_current_user, require_manager_or_admin
from app.models import PRD, Task
from app.schemas import (
    PRDCreate, PRDUpdate, PRDOut, PRDGenerateTasks,
    TaskOut, PaginationParams, PaginatedResponse,
)
from app.services import prd_service, task_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_prds(
    page: int = 1,
    page_size: int = 20,
    project_id: Optional[str] = None,
    brief_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List PRDs with optional filtering."""
    stmt = select(PRD)
    if project_id:
        stmt = stmt.where(PRD.project_id == project_id)
    if brief_id:
        stmt = stmt.where(PRD.brief_id == brief_id)
    stmt = stmt.order_by(desc(PRD.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda p: PRDOut.model_validate(p).model_dump(),
    )


@router.post("", response_model=PRDOut, status_code=status.HTTP_201_CREATED)
async def create_prd(
    prd_in: PRDCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a PRD manually."""
    prd = await prd_service.create(db, prd_in.model_dump())
    return PRDOut.model_validate(prd)


@router.get("/{prd_id}", response_model=PRDOut)
async def get_prd(prd_id: str, db: AsyncSession = Depends(get_db)):
    """Get PRD by ID."""
    prd = await prd_service.get(db, prd_id)
    if not prd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PRD not found")
    return PRDOut.model_validate(prd)


@router.put("/{prd_id}", response_model=PRDOut)
async def update_prd(
    prd_id: str,
    prd_in: PRDUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update PRD."""
    prd = await prd_service.get(db, prd_id)
    if not prd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PRD not found")
    updated = await prd_service.update(db, prd, prd_in.model_dump(exclude_unset=True))
    return PRDOut.model_validate(updated)


@router.delete("/{prd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prd(
    prd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Delete PRD (admin/manager only)."""
    prd = await prd_service.get(db, prd_id)
    if not prd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PRD not found")
    await prd_service.delete(db, prd)
    return None


@router.post("/{prd_id}/generate-tasks", response_model=list[TaskOut])
async def generate_tasks_from_prd(
    prd_id: str,
    req: PRDGenerateTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate placeholder tasks from a PRD."""
    prd = await prd_service.get(db, prd_id)
    if not prd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PRD not found")

    # Placeholder: create 3 sample tasks (real implementation would parse PRD content)
    tasks = []
    for i in range(1, 4):
        task_data = {
            "project_id": str(prd.project_id),
            "title": f"Task {i} from PRD {prd_id}",
            "description": f"Auto-generated task placeholder {i}",
            "priority": "medium",
            "status": "pending",
            "source_prd_id": prd_id,
        }
        t = await task_service.create(db, task_data)
        tasks.append(TaskOut.model_validate(t))
    return tasks
