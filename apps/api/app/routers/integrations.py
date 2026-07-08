"""Integrations router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.dependencies import get_current_user, require_manager_or_admin
from app.models import Project
from app.schemas import ProjectOut, PaginationParams, PaginatedResponse
from app.services import project_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("/git", response_model=PaginatedResponse)
async def list_git_integrations(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List projects with Git repository integrations."""
    stmt = select(Project).where(Project.repo_url.isnot(None)).order_by(desc(Project.created_at))
    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda p: ProjectOut.model_validate(p).model_dump(),
    )


@router.post("/git", response_model=ProjectOut)
async def create_git_integration(
    project_id: str,
    repo_url: str,
    default_branch: str = "main",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Link a Git repository to a project."""
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    updated = await project_service.update(
        db, project,
        {"repo_url": repo_url, "default_branch": default_branch},
    )
    return ProjectOut.model_validate(updated)
