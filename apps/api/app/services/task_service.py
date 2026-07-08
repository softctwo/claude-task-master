"""Task Service - 任务管理、依赖分析、复杂度评估与推荐"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Task, Project, User, PRD, Brief


# ────────────────────────────────
# Pydantic Schemas
# ────────────────────────────────

class TaskCreate(BaseModel):
    project_id: str
    taskmaster_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    details: Optional[str] = None
    test_strategy: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    dependencies: Optional[List[str]] = Field(default_factory=list)
    status: Literal["pending", "in_progress", "review", "done", "blocked"] = "pending"
    assignee_id: Optional[str] = None
    source_prd_id: Optional[str] = None
    source_brief_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    details: Optional[str] = None
    test_strategy: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    dependencies: Optional[List[str]] = None
    status: Optional[Literal["pending", "in_progress", "review", "done", "blocked"]] = None
    assignee_id: Optional[str] = None
    taskmaster_task_id: Optional[str] = None


class TaskOut(BaseModel):
    task_id: str
    project_id: str
    taskmaster_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    details: Optional[str] = None
    test_strategy: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"]
    complexity_score: Optional[int] = None
    dependencies: Optional[List[str]] = None
    status: Literal["pending", "in_progress", "review", "done", "blocked"]
    assignee_id: Optional[str] = None
    source_prd_id: Optional[str] = None
    source_brief_id: Optional[str] = None
    updated_from_taskmaster_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskTreeNode(BaseModel):
    task_id: str
    title: str
    status: str
    priority: str
    complexity_score: Optional[int] = None
    assignee_id: Optional[str] = None
    children: List["TaskTreeNode"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: List[TaskOut]
    total: int
    page: int
    page_size: int


class ComplexityAnalysis(BaseModel):
    task_id: str
    title: str
    complexity_score: int
    factors: Dict[str, Any]
    recommendation: str


class NextTaskRecommendation(BaseModel):
    task_id: str
    title: str
    priority: str
    complexity_score: Optional[int] = None
    reason: str
    blocked_by: Optional[List[str]] = None


class TaskExpandResult(BaseModel):
    parent_task_id: str
    subtasks: List[TaskOut]
    count: int


# ────────────────────────────────
# Service Functions
# ────────────────────────────────

async def create_task(db: AsyncSession, data: TaskCreate) -> TaskOut:
    """创建新任务"""
    task = Task(
        project_id=UUID(data.project_id) if data.project_id else None,
        taskmaster_task_id=data.taskmaster_task_id,
        parent_task_id=UUID(data.parent_task_id) if data.parent_task_id else None,
        title=data.title,
        description=data.description,
        details=data.details,
        test_strategy=data.test_strategy,
        priority=data.priority,
        complexity_score=data.complexity_score,
        dependencies=[UUID(d) for d in data.dependencies] if data.dependencies else [],
        status=data.status,
        assignee_id=UUID(data.assignee_id) if data.assignee_id else None,
        source_prd_id=UUID(data.source_prd_id) if data.source_prd_id else None,
        source_brief_id=UUID(data.source_brief_id) if data.source_brief_id else None,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return TaskOut.model_validate(task)


async def get_task(db: AsyncSession, task_id: str) -> Optional[TaskOut]:
    """根据 ID 获取任务"""
    result = await db.execute(
        select(Task).where(Task.task_id == UUID(task_id))
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None
    return TaskOut.model_validate(task)


async def list_tasks(
    db: AsyncSession,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> TaskListResponse:
    """列出任务，支持过滤和分页"""
    query = select(Task)
    filters = []

    if project_id:
        filters.append(Task.project_id == UUID(project_id))
    if status:
        filters.append(Task.status == status)
    if priority:
        filters.append(Task.priority == priority)
    if assignee_id:
        filters.append(Task.assignee_id == UUID(assignee_id))

    if filters:
        query = query.where(and_(*filters))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.order_by(Task.priority.desc(), Task.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return TaskListResponse(
        items=[TaskOut.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_task(db: AsyncSession, task_id: str, data: TaskUpdate) -> Optional[TaskOut]:
    """更新任务"""
    result = await db.execute(
        select(Task).where(Task.task_id == UUID(task_id))
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "dependencies" and value is not None:
            value = [UUID(d) for d in value]
        elif field in ("assignee_id", "parent_task_id", "source_prd_id", "source_brief_id") and value is not None:
            value = UUID(value)
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return TaskOut.model_validate(task)


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    """删除任务（同时删除子任务）"""
    result = await db.execute(
        select(Task).where(Task.task_id == UUID(task_id))
    )
    task = result.scalar_one_or_none()
    if task is None:
        return False

    # Delete subtasks recursively
    await _delete_subtasks(db, UUID(task_id))
    await db.delete(task)
    await db.commit()
    return True


async def _delete_subtasks(db: AsyncSession, parent_id: UUID) -> None:
    """递归删除子任务"""
    result = await db.execute(
        select(Task).where(Task.parent_task_id == parent_id)
    )
    subtasks = result.scalars().all()
    for sub in subtasks:
        await _delete_subtasks(db, sub.task_id)
        await db.delete(sub)


async def get_task_tree(db: AsyncSession, project_id: str) -> List[TaskTreeNode]:
    """获取项目任务树"""
    result = await db.execute(
        select(Task)
        .where(Task.project_id == UUID(project_id))
        .order_by(Task.created_at)
    )
    tasks = result.scalars().all()

    task_map: Dict[str, TaskTreeNode] = {}
    roots: List[TaskTreeNode] = []

    for task in tasks:
        node = TaskTreeNode(
            task_id=str(task.task_id),
            title=task.title,
            status=task.status,
            priority=task.priority,
            complexity_score=task.complexity_score,
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            children=[],
        )
        task_map[str(task.task_id)] = node

    for task in tasks:
        node = task_map[str(task.task_id)]
        if task.parent_task_id and str(task.parent_task_id) in task_map:
            task_map[str(task.parent_task_id)].children.append(node)
        else:
            roots.append(node)

    return roots


async def analyze_task_complexity(db: AsyncSession, task_id: str) -> Optional[ComplexityAnalysis]:
    """分析任务复杂度"""
    result = await db.execute(
        select(Task).where(Task.task_id == UUID(task_id))
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None

    # Calculate complexity based on multiple factors
    factors = {
        "description_length": len(task.description or ""),
        "details_length": len(task.details or ""),
        "dependency_count": len(task.dependencies or []),
        "has_test_strategy": bool(task.test_strategy),
        "has_subtasks": False,  # Will be checked below
    }

    # Check for subtasks
    sub_result = await db.execute(
        select(func.count()).where(Task.parent_task_id == UUID(task_id))
    )
    factors["has_subtasks"] = sub_result.scalar_one() > 0

    # Calculate score (1-10)
    score = 3  # Base score
    if factors["description_length"] > 500:
        score += 1
    if factors["details_length"] > 1000:
        score += 1
    if factors["dependency_count"] > 2:
        score += 1
    if factors["has_subtasks"]:
        score += 2
    if task.priority == "critical":
        score += 1
    if not factors["has_test_strategy"]:
        score += 1

    score = min(10, max(1, score))

    recommendation = _generate_complexity_recommendation(score, factors)

    # Update task complexity_score
    task.complexity_score = score
    task.updated_at = datetime.utcnow()
    await db.commit()

    return ComplexityAnalysis(
        task_id=str(task.task_id),
        title=task.title,
        complexity_score=score,
        factors=factors,
        recommendation=recommendation,
    )


def _generate_complexity_recommendation(score: int, factors: Dict[str, Any]) -> str:
    """根据复杂度分数生成建议"""
    if score <= 3:
        return "复杂度较低，建议直接分配给初级开发者，预计 1-2 天完成。"
    elif score <= 5:
        return "中等复杂度，建议分配给中级开发者，预计 3-5 天完成，需要编写测试策略。"
    elif score <= 7:
        return "较高复杂度，建议分配给高级开发者，预计 1-2 周完成，需要详细的技术方案评审。"
    else:
        return "高复杂度任务，建议拆分为子任务，需要架构师参与评审，预计 2 周以上。"


async def get_next_task(
    db: AsyncSession,
    project_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
) -> Optional[NextTaskRecommendation]:
    """推荐下一个应该执行的任务

    优先级：
    1. 未阻塞的 pending 高优先级任务
    2. 依赖已完成的 pending 任务
    3. 按优先级和创建时间排序
    """
    query = select(Task).where(Task.status == "pending")

    if project_id:
        query = query.where(Task.project_id == UUID(project_id))
    if assignee_id:
        query = query.where(
            or_(
                Task.assignee_id == UUID(assignee_id),
                Task.assignee_id.is_(None),
            )
        )

    query = query.order_by(
        func.case(
            (Task.priority == "critical", 4),
            (Task.priority == "high", 3),
            (Task.priority == "medium", 2),
            else_=1,
        ).desc(),
        Task.created_at.asc(),
    )

    result = await db.execute(query)
    tasks = result.scalars().all()

    for task in tasks:
        # Check if all dependencies are done
        blocked_by = []
        if task.dependencies:
            dep_result = await db.execute(
                select(Task).where(Task.task_id.in_(task.dependencies))
            )
            deps = dep_result.scalars().all()
            for dep in deps:
                if dep.status != "done":
                    blocked_by.append(str(dep.task_id))

        if not blocked_by:
            reason = (
                f"优先级为 {task.priority} 的未阻塞任务，"
                f"复杂度评分 {task.complexity_score or '未评估'}，"
                f"建议立即开始处理。"
            )
            return NextTaskRecommendation(
                task_id=str(task.task_id),
                title=task.title,
                priority=task.priority,
                complexity_score=task.complexity_score,
                reason=reason,
                blocked_by=None,
            )

    # If all tasks are blocked, return the highest priority blocked task
    if tasks:
        task = tasks[0]
        blocked_by = []
        if task.dependencies:
            dep_result = await db.execute(
                select(Task).where(Task.task_id.in_(task.dependencies))
            )
            deps = dep_result.scalars().all()
            for dep in deps:
                if dep.status != "done":
                    blocked_by.append(str(dep.task_id))

        return NextTaskRecommendation(
            task_id=str(task.task_id),
            title=task.title,
            priority=task.priority,
            complexity_score=task.complexity_score,
            reason="该任务被阻塞，请先完成依赖任务。",
            blocked_by=blocked_by or None,
        )

    return None


async def expand_task(
    db: AsyncSession,
    task_id: str,
    subtask_titles: List[str],
) -> Optional[TaskExpandResult]:
    """将任务拆解为子任务"""
    result = await db.execute(
        select(Task).where(Task.task_id == UUID(task_id))
    )
    parent = result.scalar_one_or_none()
    if parent is None:
        return None

    subtasks: List[TaskOut] = []
    for idx, title in enumerate(subtask_titles, 1):
        sub = Task(
            project_id=parent.project_id,
            parent_task_id=parent.task_id,
            title=f"{parent.title} - {title}",
            priority=parent.priority,
            status="pending",
            assignee_id=parent.assignee_id,
            source_prd_id=parent.source_prd_id,
            source_brief_id=parent.source_brief_id,
        )
        db.add(sub)
        await db.flush()
        subtasks.append(TaskOut.model_validate(sub))

    # Update parent status
    parent.status = "in_progress"
    parent.updated_at = datetime.utcnow()
    await db.commit()

    return TaskExpandResult(
        parent_task_id=str(parent.task_id),
        subtasks=subtasks,
        count=len(subtasks),
    )


async def validate_dependencies(db: AsyncSession, task_id: str) -> Dict[str, Any]:
    """验证任务依赖是否形成循环"""
    result = await db.execute(
        select(Task).where(Task.task_id == UUID(task_id))
    )
    task = result.scalar_one_or_none()
    if task is None:
        return {"valid": False, "error": "Task not found"}

    if not task.dependencies:
        return {"valid": True, "cycle": None}

    visited = set()
    stack = set()

    async def has_cycle(current_id: UUID) -> Optional[List[str]]:
        visited.add(str(current_id))
        stack.add(str(current_id))

        current_result = await db.execute(
            select(Task).where(Task.task_id == current_id)
        )
        current = current_result.scalar_one_or_none()
        if current is None or not current.dependencies:
            stack.remove(str(current_id))
            return None

        for dep_id in current.dependencies:
            dep_str = str(dep_id)
            if dep_str in stack:
                return list(stack) + [dep_str]
            if dep_str not in visited:
                cycle = await has_cycle(dep_id)
                if cycle:
                    return cycle

        stack.remove(str(current_id))
        return None

    for dep_id in task.dependencies:
        cycle = await has_cycle(dep_id)
        if cycle:
            return {"valid": False, "cycle": cycle}

    return {"valid": True, "cycle": None}


async def get_task_dependencies_chain(
    db: AsyncSession, task_id: str
) -> List[TaskOut]:
    """获取任务的完整依赖链"""
    result = await db.execute(
        select(Task).where(Task.task_id == UUID(task_id))
    )
    task = result.scalar_one_or_none()
    if task is None or not task.dependencies:
        return []

    chain = []
    to_process = list(task.dependencies)
    visited = set()

    while to_process:
        dep_id = to_process.pop(0)
        dep_str = str(dep_id)
        if dep_str in visited:
            continue
        visited.add(dep_str)

        dep_result = await db.execute(
            select(Task).where(Task.task_id == dep_id)
        )
        dep = dep_result.scalar_one_or_none()
        if dep:
            chain.append(TaskOut.model_validate(dep))
            if dep.dependencies:
                to_process.extend(dep.dependencies)

    return chain
