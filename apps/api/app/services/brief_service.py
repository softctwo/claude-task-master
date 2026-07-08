"""Brief Service — Brief CRUD + 状态流转 + 审批 + 版本快照."""
from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Brief, PRD

# ────────────────────────────────
# Schemas
# ────────────────────────────────
BriefStatus = Literal["draft", "review", "approved", "rejected", "archived"]


class BriefCreateRequest(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=500)
    background: Optional[str] = None
    problem_statement: Optional[str] = None
    target_users: Optional[str] = None
    goals: Optional[List[str]] = None
    non_goals: Optional[List[str]] = None
    scope: Optional[str] = None
    user_stories: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    constraints: Optional[str] = None
    related_docs: Optional[List[str]] = None
    related_code: Optional[List[str]] = None


class BriefUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    background: Optional[str] = None
    problem_statement: Optional[str] = None
    target_users: Optional[str] = None
    goals: Optional[List[str]] = None
    non_goals: Optional[List[str]] = None
    scope: Optional[str] = None
    user_stories: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    constraints: Optional[str] = None
    related_docs: Optional[List[str]] = None
    related_code: Optional[List[str]] = None
    reviewer_ids: Optional[List[str]] = None


class BriefApproveRequest(BaseModel):
    reviewer_id: str
    decision: Literal["approve", "reject"]
    comment: Optional[str] = None


class BriefResponse(BaseModel):
    brief_id: str
    project_id: str
    title: str
    background: Optional[str] = None
    problem_statement: Optional[str] = None
    target_users: Optional[str] = None
    goals: Optional[List[str]] = None
    non_goals: Optional[List[str]] = None
    scope: Optional[str] = None
    user_stories: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    constraints: Optional[str] = None
    related_docs: Optional[List[str]] = None
    related_code: Optional[List[str]] = None
    status: str
    owner_id: str
    reviewer_ids: Optional[List[str]] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BriefListResponse(BaseModel):
    total: int
    items: List[BriefResponse]


class BriefVersionSnapshot(BaseModel):
    """版本快照 — 用于历史记录对比."""
    version: int
    title: str
    goals: Optional[List[str]] = None
    scope: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ────────────────────────────────
# Service functions
# ────────────────────────────────

async def create_brief(
    db: AsyncSession,
    payload: BriefCreateRequest,
    owner_id: str,
) -> BriefResponse:
    brief = Brief(
        project_id=UUID(payload.project_id),
        title=payload.title,
        background=payload.background,
        problem_statement=payload.problem_statement,
        target_users=payload.target_users,
        goals=payload.goals or [],
        non_goals=payload.non_goals or [],
        scope=payload.scope,
        user_stories=payload.user_stories or [],
        acceptance_criteria=payload.acceptance_criteria or [],
        constraints=payload.constraints,
        related_docs=payload.related_docs or [],
        related_code=payload.related_code or [],
        status="draft",
        owner_id=UUID(owner_id),
        reviewer_ids=[],
        version=1,
    )
    db.add(brief)
    await db.commit()
    await db.refresh(brief)
    return BriefResponse.model_validate(brief)


async def get_brief(db: AsyncSession, brief_id: str) -> Brief:
    result = await db.execute(
        select(Brief).where(Brief.brief_id == UUID(brief_id))
    )
    brief = result.scalar_one_or_none()
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brief not found",
        )
    return brief


async def get_brief_response(db: AsyncSession, brief_id: str) -> BriefResponse:
    brief = await get_brief(db, brief_id)
    return BriefResponse.model_validate(brief)


async def list_briefs(
    db: AsyncSession,
    project_id: Optional[str] = None,
    status_filter: Optional[BriefStatus] = None,
    owner_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> BriefListResponse:
    query = select(Brief)
    if project_id:
        query = query.where(Brief.project_id == UUID(project_id))
    if status_filter:
        query = query.where(Brief.status == status_filter)
    if owner_id:
        query = query.where(Brief.owner_id == UUID(owner_id))

    count_result = await db.execute(query.with_only_columns(Brief.brief_id))
    total = len(count_result.all())

    query = query.order_by(Brief.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    briefs = result.scalars().all()

    return BriefListResponse(
        total=total,
        items=[BriefResponse.model_validate(b) for b in briefs],
    )


async def update_brief(
    db: AsyncSession,
    brief_id: str,
    payload: BriefUpdateRequest,
    current_user_id: str,
) -> BriefResponse:
    brief = await get_brief(db, brief_id)

    # Only owner or reviewer can edit
    if str(brief.owner_id) != current_user_id and current_user_id not in (brief.reviewer_ids or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this brief",
        )

    # If brief is approved, editing requires creating a new version
    if brief.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approved brief cannot be edited directly. Create a new version.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "reviewer_ids" and value is not None:
            value = [UUID(v) for v in value]
        if hasattr(brief, field) and value is not None:
            setattr(brief, field, value)

    brief.updated_at = datetime.now()
    await db.commit()
    await db.refresh(brief)
    return BriefResponse.model_validate(brief)


async def delete_brief(db: AsyncSession, brief_id: str, current_user_id: str) -> None:
    brief = await get_brief(db, brief_id)
    if str(brief.owner_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete this brief",
        )
    await db.delete(brief)
    await db.commit()


# ────────────────────────────────
# Status workflow
# ────────────────────────────────

VALID_STATUS_TRANSITIONS: dict[BriefStatus, List[BriefStatus]] = {
    "draft": ["review", "archived"],
    "review": ["approved", "rejected", "draft"],
    "approved": ["archived"],
    "rejected": ["draft", "archived"],
    "archived": [],
}


async def transition_brief_status(
    db: AsyncSession,
    brief_id: str,
    new_status: BriefStatus,
    current_user_id: str,
) -> BriefResponse:
    brief = await get_brief(db, brief_id)

    current = brief.status  # type: ignore
    if new_status not in VALID_STATUS_TRANSITIONS.get(current, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{current}' to '{new_status}'",
        )

    # Only owner or reviewer can transition
    if str(brief.owner_id) != current_user_id and current_user_id not in (brief.reviewer_ids or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to change this brief's status",
        )

    brief.status = new_status
    brief.updated_at = datetime.now()
    await db.commit()
    await db.refresh(brief)
    return BriefResponse.model_validate(brief)


async def submit_brief_for_review(
    db: AsyncSession,
    brief_id: str,
    current_user_id: str,
) -> BriefResponse:
    """Submit brief from draft to review."""
    return await transition_brief_status(db, brief_id, "review", current_user_id)


async def approve_brief(
    db: AsyncSession,
    brief_id: str,
    reviewer_id: str,
) -> BriefResponse:
    """Approve a brief (reviewer action)."""
    brief = await get_brief(db, brief_id)

    if brief.status != "review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brief must be in 'review' status to be approved",
        )

    if reviewer_id not in (brief.reviewer_ids or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned reviewers can approve",
        )

    brief.status = "approved"
    brief.updated_at = datetime.now()
    await db.commit()
    await db.refresh(brief)
    return BriefResponse.model_validate(brief)


async def reject_brief(
    db: AsyncSession,
    brief_id: str,
    reviewer_id: str,
) -> BriefResponse:
    """Reject a brief (reviewer action)."""
    brief = await get_brief(db, brief_id)

    if brief.status != "review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brief must be in 'review' status to be rejected",
        )

    if reviewer_id not in (brief.reviewer_ids or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned reviewers can reject",
        )

    brief.status = "rejected"
    brief.updated_at = datetime.now()
    await db.commit()
    await db.refresh(brief)
    return BriefResponse.model_validate(brief)


# ────────────────────────────────
# Version snapshot
# ────────────────────────────────

async def create_new_version(
    db: AsyncSession,
    brief_id: str,
    current_user_id: str,
) -> BriefResponse:
    """Create a new version from an existing brief (fork)."""
    original = await get_brief(db, brief_id)

    if str(original.owner_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can create a new version",
        )

    # Create a new brief with incremented version
    new_brief = Brief(
        project_id=original.project_id,
        title=original.title,
        background=original.background,
        problem_statement=original.problem_statement,
        target_users=original.target_users,
        goals=original.goals or [],
        non_goals=original.non_goals or [],
        scope=original.scope,
        user_stories=original.user_stories or [],
        acceptance_criteria=original.acceptance_criteria or [],
        constraints=original.constraints,
        related_docs=original.related_docs or [],
        related_code=original.related_code or [],
        status="draft",
        owner_id=original.owner_id,
        reviewer_ids=original.reviewer_ids or [],
        version=original.version + 1,
    )
    db.add(new_brief)
    await db.commit()
    await db.refresh(new_brief)
    return BriefResponse.model_validate(new_brief)


async def list_brief_versions(
    db: AsyncSession,
    project_id: str,
    title: str,
) -> List[BriefVersionSnapshot]:
    """List all versions of briefs with the same title in a project."""
    result = await db.execute(
        select(Brief)
        .where(Brief.project_id == UUID(project_id))
        .where(Brief.title == title)
        .order_by(Brief.version.asc())
    )
    briefs = result.scalars().all()
    return [BriefVersionSnapshot.model_validate(b) for b in briefs]
