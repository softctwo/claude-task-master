"""Project Service — 项目 CRUD + 成员管理."""
from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User

# ────────────────────────────────
# Schemas
# ────────────────────────────────
ProjectStatus = Literal["active", "archived", "paused"]


class ProjectCreateRequest(BaseModel):
    workspace_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    repo_url: Optional[str] = None
    default_branch: Optional[str] = "main"
    taskmaster_path: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    repo_url: Optional[str] = None
    default_branch: Optional[str] = None
    taskmaster_path: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectMemberRequest(BaseModel):
    user_id: str
    role: Optional[str] = "member"


class ProjectResponse(BaseModel):
    project_id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    default_branch: str
    taskmaster_path: Optional[str] = None
    status: str
    owner_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    total: int
    items: List[ProjectResponse]


class ProjectMemberResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ────────────────────────────────
# Service functions
# ────────────────────────────────

async def create_project(
    db: AsyncSession,
    payload: ProjectCreateRequest,
    owner_id: str,
) -> ProjectResponse:
    project = Project(
        workspace_id=UUID(payload.workspace_id) if payload.workspace_id else None,
        name=payload.name,
        description=payload.description,
        repo_url=payload.repo_url,
        default_branch=payload.default_branch or "main",
        taskmaster_path=payload.taskmaster_path,
        status="active",
        owner_id=UUID(owner_id),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


async def get_project(db: AsyncSession, project_id: str) -> Project:
    result = await db.execute(
        select(Project).where(Project.project_id == UUID(project_id))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


async def get_project_response(db: AsyncSession, project_id: str) -> ProjectResponse:
    project = await get_project(db, project_id)
    return ProjectResponse.model_validate(project)


async def list_projects(
    db: AsyncSession,
    workspace_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    status_filter: Optional[ProjectStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> ProjectListResponse:
    query = select(Project)
    if workspace_id:
        query = query.where(Project.workspace_id == UUID(workspace_id))
    if owner_id:
        query = query.where(Project.owner_id == UUID(owner_id))
    if status_filter:
        query = query.where(Project.status == status_filter)

    count_result = await db.execute(query.with_only_columns(Project.project_id))
    total = len(count_result.all())

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectListResponse(
        total=total,
        items=[ProjectResponse.model_validate(p) for p in projects],
    )


async def update_project(
    db: AsyncSession,
    project_id: str,
    payload: ProjectUpdateRequest,
) -> ProjectResponse:
    project = await get_project(db, project_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        project.status = update_data["status"]
    if "name" in update_data and update_data["name"] is not None:
        project.name = update_data["name"]
    if "description" in update_data:
        project.description = update_data["description"]
    if "repo_url" in update_data:
        project.repo_url = update_data["repo_url"]
    if "default_branch" in update_data and update_data["default_branch"] is not None:
        project.default_branch = update_data["default_branch"]
    if "taskmaster_path" in update_data:
        project.taskmaster_path = update_data["taskmaster_path"]

    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


async def delete_project(db: AsyncSession, project_id: str) -> None:
    project = await get_project(db, project_id)
    await db.delete(project)
    await db.commit()


async def is_project_owner(db: AsyncSession, project_id: str, user_id: str) -> bool:
    project = await get_project(db, project_id)
    return str(project.owner_id) == user_id


# ────────────────────────────────
# Project members (placeholder — pending members table)
# ────────────────────────────────

async def list_project_members(db: AsyncSession, project_id: str) -> List[ProjectMemberResponse]:
    """List project members. Returns owner as first member."""
    project = await get_project(db, project_id)
    owner_result = await db.execute(
        select(User).where(User.user_id == project.owner_id)
    )
    owner = owner_result.scalar_one_or_none()
    members = []
    if owner:
        members.append(
            ProjectMemberResponse(
                user_id=str(owner.user_id),
                name=owner.name,
                email=owner.email,
                role="owner",
                avatar_url=owner.avatar_url,
            )
        )
    return members


async def add_project_member(
    db: AsyncSession,
    project_id: str,
    payload: ProjectMemberRequest,
) -> ProjectMemberResponse:
    """Add a member to project. (Placeholder — requires project_members junction table)."""
    user_result = await db.execute(select(User).where(User.user_id == UUID(payload.user_id)))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return ProjectMemberResponse(
        user_id=str(user.user_id),
        name=user.name,
        email=user.email,
        role=payload.role or "member",
        avatar_url=user.avatar_url,
    )


async def remove_project_member(db: AsyncSession, project_id: str, user_id: str) -> None:
    """Remove a member from project. (Placeholder — requires project_members junction table)."""
    pass
