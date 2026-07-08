"""Project router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.dependencies import get_current_user, require_manager_or_admin
from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate, ProjectOut, PaginationParams, PaginatedResponse
from app.services import project_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    workspace_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List projects with optional filtering."""
    stmt = select(Project)
    if status:
        stmt = stmt.where(Project.status == status)
    if workspace_id:
        stmt = stmt.where(Project.workspace_id == workspace_id)
    stmt = stmt.order_by(desc(Project.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda p: ProjectOut.model_validate(p).model_dump(),
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new project."""
    project_data = project_in.model_dump()
    project_data["owner_id"] = current_user.user_id
    project = await project_service.create(db, project_data)
    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get project by ID."""
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectOut.model_validate(project)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update project."""
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # Only owner or admin/manager can update
    if str(project.owner_id) != current_user.user_id and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this project")
    updated = await project_service.update(db, project, project_in.model_dump(exclude_unset=True))
    return ProjectOut.model_validate(updated)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Delete project (admin/manager only)."""
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await project_service.delete(db, project)
    return None
