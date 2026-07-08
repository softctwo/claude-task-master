"""Task router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.dependencies import get_current_user, require_developer_or_above
from app.models import Task
from app.schemas import (
    TaskCreate, TaskUpdate, TaskOut, TaskTreeOut, TaskExpand, TaskNext, TaskComplexity,
    PaginationParams, PaginatedResponse,
)
from app.services import task_service
from app.utils.pagination import paginate

router = APIRouter()


def _build_tree(tasks: list, parent_id: Optional[str] = None) -> list[TaskTreeOut]:
    """Recursively build task tree."""
    nodes = []
    for t in tasks:
        pid = str(t.parent_task_id) if t.parent_task_id else None
        if pid == parent_id:
            node = TaskTreeOut.model_validate(t)
            node.children = _build_tree(tasks, str(t.task_id))
            nodes.append(node)
    return nodes


@router.get("", response_model=PaginatedResponse)
async def list_tasks(
    page: int = 1,
    page_size: int = 20,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List tasks with optional filtering."""
    stmt = select(Task)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    if status:
        stmt = stmt.where(Task.status == status)
    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    stmt = stmt.order_by(desc(Task.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda t: TaskOut.model_validate(t).model_dump(),
    )


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new task."""
    task = await task_service.create(db, task_in.model_dump())
    return TaskOut.model_validate(task)


@router.get("/tree", response_model=list[TaskTreeOut])
async def get_task_tree(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get hierarchical task tree."""
    stmt = select(Task)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())
    return _build_tree(tasks)


@router.get("/next", response_model=TaskNext)
async def get_next_task(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Recommend the next task to work on."""
    stmt = select(Task).where(Task.status == "pending")
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    stmt = stmt.order_by(Task.priority, desc(Task.created_at)).limit(1)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        return TaskNext(next_task=None, reason="No pending tasks available")
    return TaskNext(
        next_task=TaskOut.model_validate(task),
        reason="Highest priority pending task",
    )


@router.get("/complexity", response_model=TaskComplexity)
async def analyze_complexity(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Analyze task complexity distribution."""
    stmt = select(Task)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())

    scores = [t.complexity_score for t in tasks if t.complexity_score is not None]
    if not scores:
        return TaskComplexity(average=0.0, max=0, min=0, distribution={})

    distribution: dict[str, int] = {}
    for s in scores:
        bucket = f"{s}"
        distribution[bucket] = distribution.get(bucket, 0) + 1

    return TaskComplexity(
        average=round(sum(scores) / len(scores), 2),
        max=max(scores),
        min=min(scores),
        distribution=distribution,
    )


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get task by ID."""
    task = await task_service.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskOut.model_validate(task)


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update task."""
    task = await task_service.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    updated = await task_service.update(db, task, task_in.model_dump(exclude_unset=True))
    return TaskOut.model_validate(updated)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_developer_or_above),
):
    """Delete task."""
    task = await task_service.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await task_service.delete(db, task)
    return None


@router.post("/{task_id}/expand", response_model=list[TaskOut])
async def expand_task(
    task_id: str,
    req: TaskExpand,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Break down a task into subtasks."""
    task = await task_service.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    subtasks = []
    for i in range(1, req.count + 1):
        subtask_data = {
            "project_id": str(task.project_id),
            "title": f"{task.title} - Subtask {i}",
            "description": f"Subtask {i} of {task.title}",
            "parent_task_id": task_id,
            "priority": task.priority,
            "status": "pending",
        }
        st = await task_service.create(db, subtask_data)
        subtasks.append(TaskOut.model_validate(st))
    return subtasks
