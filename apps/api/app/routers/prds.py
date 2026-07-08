"""PRD router with AI task generation."""
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
from app.services import prd_service, task_service, ai_service
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
    prd = await prd_service.create_prd(db, prd_service.PRDCreateRequest(**prd_in.model_dump()))
    return PRDOut.model_validate(prd)


@router.get("/{prd_id}", response_model=PRDOut)
async def get_prd(prd_id: str, db: AsyncSession = Depends(get_db)):
    """Get PRD by ID."""
    prd = await prd_service.get_prd(db, prd_id)
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
    prd = await prd_service.get_prd(db, prd_id)
    if not prd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PRD not found")
    updated = await prd_service.update_prd(db, prd_id, prd_service.PRDUpdateRequest(**prd_in.model_dump(exclude_unset=True)), current_user.user_id)
    return PRDOut.model_validate(updated)


@router.delete("/{prd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prd(
    prd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Delete PRD (admin/manager only)."""
    prd = await prd_service.get_prd(db, prd_id)
    if not prd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PRD not found")
    await prd_service.delete_prd(db, prd_id, current_user.user_id)
    return None


@router.post("/{prd_id}/generate-tasks", response_model=list[TaskOut])
async def generate_tasks_from_prd(
    prd_id: str,
    req: PRDGenerateTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate tasks from a PRD using AI."""
    prd = await prd_service.get_prd(db, prd_id)
    if not prd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PRD not found")

    if not prd.content_markdown:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PRD has no content to generate tasks from")

    try:
        result = await ai_service.generate_tasks_from_prd(
            prd_content=prd.content_markdown,
            model=getattr(req, "model", None) or "gpt-4o",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI task generation failed: {str(e)}")

    # Create tasks from generated results
    created_tasks = []
    for task_data in result.tasks:
        task_dict = task_data.model_dump()
        task_dict["project_id"] = str(prd.project_id)
        task_dict["source_prd_id"] = prd_id
        task_dict["status"] = "pending"
        
        # Resolve dependencies by title to task IDs (simplified: store as text for now)
        if task_dict.get("dependencies"):
            task_dict["dependencies"] = []  # Will be resolved after all tasks created
        
        t = await task_service.create_task(db, task_dict)
        created_tasks.append(TaskOut.model_validate(t))

    return created_tasks


@router.post("/{prd_id}/approve", response_model=PRDOut)
async def approve_prd(
    prd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Approve a PRD."""
    prd = await prd_service.approve_prd(db, prd_id, current_user.user_id)
    return PRDOut.model_validate(prd)
