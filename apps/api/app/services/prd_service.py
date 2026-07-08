"""PRD Service — PRD CRUD + 生成任务调用."""
from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PRD, Brief, Task

# ────────────────────────────────
# Schemas
# ────────────────────────────────
PRDSource = Literal["ai_generated", "manual", "imported"]


class PRDCreateRequest(BaseModel):
    brief_id: Optional[str] = None
    project_id: str
    content_markdown: str = Field(..., min_length=1)
    source: Optional[PRDSource] = "manual"
    generated_by: Optional[str] = None


class PRDUpdateRequest(BaseModel):
    content_markdown: Optional[str] = None
    source: Optional[PRDSource] = None
    generated_by: Optional[str] = None


class PRDApproveRequest(BaseModel):
    approver_id: str


class PRDResponse(BaseModel):
    prd_id: str
    brief_id: Optional[str] = None
    project_id: str
    content_markdown: str
    source: str
    version: int
    generated_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PRDListResponse(BaseModel):
    total: int
    items: List[PRDResponse]


class PRDGenerateRequest(BaseModel):
    brief_id: str
    model: Optional[str] = "claude-3-5-sonnet-20241022"
    extra_context: Optional[str] = None


class GenerateTasksRequest(BaseModel):
    model: Optional[str] = "claude-3-5-sonnet-20241022"
    executor_type: Optional[str] = "ai"


class TaskPreviewResponse(BaseModel):
    task_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    parent_task_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ────────────────────────────────
# Service functions
# ────────────────────────────────

async def create_prd(
    db: AsyncSession,
    payload: PRDCreateRequest,
) -> PRDResponse:
    # Validate brief if provided
    if payload.brief_id:
        brief_result = await db.execute(
            select(Brief).where(Brief.brief_id == UUID(payload.brief_id))
        )
        if not brief_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief not found",
            )

    # Validate project
    from app.models import Project
    project_result = await db.execute(
        select(Project).where(Project.project_id == UUID(payload.project_id))
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Determine version: increment from existing PRDs for same brief
    version = 1
    if payload.brief_id:
        existing = await db.execute(
            select(PRD)
            .where(PRD.brief_id == UUID(payload.brief_id))
            .order_by(PRD.version.desc())
        )
        latest = existing.scalar_one_or_none()
        if latest:
            version = latest.version + 1

    prd = PRD(
        brief_id=UUID(payload.brief_id) if payload.brief_id else None,
        project_id=UUID(payload.project_id),
        content_markdown=payload.content_markdown,
        source=payload.source or "manual",
        version=version,
        generated_by=payload.generated_by,
    )
    db.add(prd)
    await db.commit()
    await db.refresh(prd)
    return PRDResponse.model_validate(prd)


async def get_prd(db: AsyncSession, prd_id: str) -> PRD:
    result = await db.execute(
        select(PRD).where(PRD.prd_id == UUID(prd_id))
    )
    prd = result.scalar_one_or_none()
    if not prd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PRD not found",
        )
    return prd


async def get_prd_response(db: AsyncSession, prd_id: str) -> PRDResponse:
    prd = await get_prd(db, prd_id)
    return PRDResponse.model_validate(prd)


async def list_prds(
    db: AsyncSession,
    project_id: Optional[str] = None,
    brief_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> PRDListResponse:
    query = select(PRD)
    if project_id:
        query = query.where(PRD.project_id == UUID(project_id))
    if brief_id:
        query = query.where(PRD.brief_id == UUID(brief_id))

    count_result = await db.execute(query.with_only_columns(PRD.prd_id))
    total = len(count_result.all())

    query = query.order_by(PRD.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    prds = result.scalars().all()

    return PRDListResponse(
        total=total,
        items=[PRDResponse.model_validate(p) for p in prds],
    )


async def update_prd(
    db: AsyncSession,
    prd_id: str,
    payload: PRDUpdateRequest,
    current_user_id: str,
) -> PRDResponse:
    prd = await get_prd(db, prd_id)

    # Check if already approved — approved PRDs should not be edited directly
    if prd.approved_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approved PRD cannot be edited. Create a new version.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(prd, field) and value is not None:
            setattr(prd, field, value)

    prd.updated_at = datetime.now()
    await db.commit()
    await db.refresh(prd)
    return PRDResponse.model_validate(prd)


async def delete_prd(db: AsyncSession, prd_id: str, current_user_id: str) -> None:
    prd = await get_prd(db, prd_id)
    # Only allow deletion if not approved
    if prd.approved_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approved PRD cannot be deleted",
        )
    await db.delete(prd)
    await db.commit()


async def approve_prd(
    db: AsyncSession,
    prd_id: str,
    approver_id: str,
) -> PRDResponse:
    """Approve a PRD — sets approved_at timestamp."""
    prd = await get_prd(db, prd_id)

    if prd.approved_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PRD is already approved",
        )

    prd.approved_at = datetime.now()
    prd.updated_at = datetime.now()
    await db.commit()
    await db.refresh(prd)
    return PRDResponse.model_validate(prd)


# ────────────────────────────────
# Generate PRD from Brief (AI call)
# ────────────────────────────────

async def generate_prd_from_brief(
    db: AsyncSession,
    brief_id: str,
    model: str = "claude-3-5-sonnet-20241022",
    extra_context: Optional[str] = None,
) -> PRDResponse:
    """Generate a PRD from a Brief using AI. (Placeholder — integrates with AI provider)."""
    brief = await db.execute(
        select(Brief).where(Brief.brief_id == UUID(brief_id))
    )
    brief_obj = brief.scalar_one_or_none()
    if not brief_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brief not found",
        )

    if brief_obj.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brief must be approved before generating PRD",
        )

    # TODO: Integrate with actual AI provider (OpenAI/Anthropic)
    # For now, generate a structured markdown from brief content
    generated_markdown = _build_prd_markdown(brief_obj, extra_context)

    prd = PRD(
        brief_id=UUID(brief_id),
        project_id=brief_obj.project_id,
        content_markdown=generated_markdown,
        source="ai_generated",
        version=1,
        generated_by=model,
    )
    db.add(prd)
    await db.commit()
    await db.refresh(prd)
    return PRDResponse.model_validate(prd)


def _build_prd_markdown(brief, extra_context: Optional[str] = None) -> str:
    """Build PRD markdown from brief content."""
    lines = [
        f"# {brief.title}",
        "",
        "## 背景",
        brief.background or "",
        "",
        "## 问题陈述",
        brief.problem_statement or "",
        "",
        "## 目标用户",
        brief.target_users or "",
        "",
        "## 目标",
    ]
    for goal in (brief.goals or []):
        lines.append(f"- {goal}")
    lines.extend(["", "## 非目标"])
    for non_goal in (brief.non_goals or []):
        lines.append(f"- {non_goal}")
    lines.extend(["", "## 范围", brief.scope or "", "", "## 用户故事"])
    for story in (brief.user_stories or []):
        lines.append(f"- {story}")
    lines.extend(["", "## 验收标准"])
    for criteria in (brief.acceptance_criteria or []):
        lines.append(f"- {criteria}")
    lines.extend(["", "## 约束", brief.constraints or ""])
    if extra_context:
        lines.extend(["", "## 额外上下文", extra_context])
    return "\n".join(lines)


# ────────────────────────────────
# Generate Tasks from PRD
# ────────────────────────────────

async def generate_tasks_from_prd(
    db: AsyncSession,
    prd_id: str,
    model: str = "claude-3-5-sonnet-20241022",
    executor_type: str = "ai",
) -> List[TaskPreviewResponse]:
    """Generate tasks from an approved PRD. (Placeholder — integrates with taskmaster)."""
    prd = await get_prd(db, prd_id)

    if prd.approved_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PRD must be approved before generating tasks",
        )

    # TODO: Integrate with actual taskmaster / AI task generation
    # For now, create placeholder tasks from PRD content
    placeholder_tasks = _extract_tasks_from_prd(prd)

    created_tasks = []
    for task_data in placeholder_tasks:
        task = Task(
            project_id=prd.project_id,
            title=task_data["title"],
            description=task_data.get("description"),
            priority=task_data.get("priority", "medium"),
            status="pending",
            source_prd_id=UUID(prd_id),
        )
        db.add(task)
        created_tasks.append(task)

    await db.commit()
    for task in created_tasks:
        await db.refresh(task)

    return [TaskPreviewResponse.model_validate(t) for t in created_tasks]


def _extract_tasks_from_prd(prd) -> List[dict]:
    """Extract task placeholders from PRD markdown. (Naive implementation)."""
    content = prd.content_markdown or ""
    tasks = []

    # Look for lines that look like tasks (bullet points with action verbs)
    import re
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith(("- ", "* ", "1. ", "2. ", "3. ")):
            text = re.sub(r"^[-*\d.\s]+", "", line).strip()
            if len(text) > 5:
                tasks.append({
                    "title": text[:100],
                    "description": text,
                    "priority": "medium",
                })

    # If no tasks found, create a default one
    if not tasks:
        tasks.append({
            "title": "Implement PRD requirements",
            "description": f"Implement the requirements specified in PRD {prd.prd_id}",
            "priority": "high",
        })

    return tasks[:20]  # Limit to 20 tasks


async def get_prd_tasks(db: AsyncSession, prd_id: str) -> List[TaskPreviewResponse]:
    """Get all tasks generated from a PRD."""
    result = await db.execute(
        select(Task).where(Task.source_prd_id == UUID(prd_id))
    )
    tasks = result.scalars().all()
    return [TaskPreviewResponse.model_validate(t) for t in tasks]
