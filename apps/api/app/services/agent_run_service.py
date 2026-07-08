"""Agent Run Service - Agent 执行记录与日志管理"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRun, Task


# ────────────────────────────────
# Pydantic Schemas
# ────────────────────────────────

class AgentRunCreate(BaseModel):
    project_id: str
    task_id: Optional[str] = None
    executor_type: Literal["manual", "auto", "scheduled", "webhook"] = "manual"
    model: Optional[str] = None
    branch_name: Optional[str] = None
    command: Optional[str] = None
    status: Literal["pending", "running", "success", "failed", "cancelled"] = "pending"


class AgentRunUpdate(BaseModel):
    status: Optional[Literal["pending", "running", "success", "failed", "cancelled"]] = None
    logs: Optional[str] = None
    result_summary: Optional[str] = None
    pr_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class AgentRunOut(BaseModel):
    run_id: str
    project_id: str
    task_id: Optional[str] = None
    executor_type: Literal["manual", "auto", "scheduled", "webhook"]
    model: Optional[str] = None
    branch_name: Optional[str] = None
    command: Optional[str] = None
    status: Literal["pending", "running", "success", "failed", "cancelled"]
    logs: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result_summary: Optional[str] = None
    pr_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunListResponse(BaseModel):
    items: List[AgentRunOut]
    total: int
    page: int
    page_size: int


class LogAppendRequest(BaseModel):
    log_entry: str = Field(..., min_length=1)


class RunStatistics(BaseModel):
    total_runs: int
    success_count: int
    failed_count: int
    pending_count: int
    running_count: int
    cancelled_count: int
    success_rate: float
    average_duration_seconds: Optional[float] = None


# ────────────────────────────────
# Service Functions
# ────────────────────────────────

async def create_agent_run(db: AsyncSession, data: AgentRunCreate) -> AgentRunOut:
    """创建 Agent 执行记录"""
    run = AgentRun(
        project_id=UUID(data.project_id),
        task_id=UUID(data.task_id) if data.task_id else None,
        executor_type=data.executor_type,
        model=data.model,
        branch_name=data.branch_name,
        command=data.command,
        status=data.status,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return AgentRunOut.model_validate(run)


async def get_agent_run(db: AsyncSession, run_id: str) -> Optional[AgentRunOut]:
    """根据 ID 获取 Agent 执行记录"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None
    return AgentRunOut.model_validate(run)


async def list_agent_runs(
    db: AsyncSession,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    executor_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> AgentRunListResponse:
    """列出 Agent 执行记录，支持过滤和分页"""
    query = select(AgentRun)
    filters = []

    if project_id:
        filters.append(AgentRun.project_id == UUID(project_id))
    if task_id:
        filters.append(AgentRun.task_id == UUID(task_id))
    if status:
        filters.append(AgentRun.status == status)
    if executor_type:
        filters.append(AgentRun.executor_type == executor_type)

    if filters:
        query = query.where(and_(*filters))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.order_by(AgentRun.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    runs = result.scalars().all()

    return AgentRunListResponse(
        items=[AgentRunOut.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_agent_run(
    db: AsyncSession, run_id: str, data: AgentRunUpdate
) -> Optional[AgentRunOut]:
    """更新 Agent 执行记录"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(run, field, value)

    await db.commit()
    await db.refresh(run)
    return AgentRunOut.model_validate(run)


async def delete_agent_run(db: AsyncSession, run_id: str) -> bool:
    """删除 Agent 执行记录"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return False

    await db.delete(run)
    await db.commit()
    return True


async def append_logs(db: AsyncSession, run_id: str, log_entry: str) -> Optional[AgentRunOut]:
    """追加日志到 Agent 执行记录"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    formatted_entry = f"[{timestamp}] {log_entry}\n"

    if run.logs:
        run.logs += formatted_entry
    else:
        run.logs = formatted_entry

    await db.commit()
    await db.refresh(run)
    return AgentRunOut.model_validate(run)


async def get_run_logs(db: AsyncSession, run_id: str) -> Optional[str]:
    """获取 Agent 执行日志"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None
    return run.logs or ""


async def start_run(db: AsyncSession, run_id: str) -> Optional[AgentRunOut]:
    """标记 Agent 执行为开始状态"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None

    run.status = "running"
    run.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(run)
    return AgentRunOut.model_validate(run)


async def finish_run(
    db: AsyncSession,
    run_id: str,
    status: Literal["success", "failed", "cancelled"],
    result_summary: Optional[str] = None,
    pr_url: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Optional[AgentRunOut]:
    """标记 Agent 执行为完成状态"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None

    run.status = status
    run.finished_at = datetime.utcnow()
    if result_summary:
        run.result_summary = result_summary
    if pr_url:
        run.pr_url = pr_url
    if error_message:
        run.error_message = error_message

    await db.commit()
    await db.refresh(run)
    return AgentRunOut.model_validate(run)


async def get_run_statistics(
    db: AsyncSession, project_id: Optional[str] = None
) -> RunStatistics:
    """获取 Agent 执行统计信息"""
    query = select(AgentRun)
    if project_id:
        query = query.where(AgentRun.project_id == UUID(project_id))

    result = await db.execute(query)
    runs = result.scalars().all()

    total = len(runs)
    success_count = sum(1 for r in runs if r.status == "success")
    failed_count = sum(1 for r in runs if r.status == "failed")
    pending_count = sum(1 for r in runs if r.status == "pending")
    running_count = sum(1 for r in runs if r.status == "running")
    cancelled_count = sum(1 for r in runs if r.status == "cancelled")

    success_rate = (success_count / total * 100) if total > 0 else 0.0

    # Calculate average duration for completed runs
    durations = []
    for r in runs:
        if r.started_at and r.finished_at:
            duration = (r.finished_at - r.started_at).total_seconds()
            durations.append(duration)

    avg_duration = sum(durations) / len(durations) if durations else None

    return RunStatistics(
        total_runs=total,
        success_count=success_count,
        failed_count=failed_count,
        pending_count=pending_count,
        running_count=running_count,
        cancelled_count=cancelled_count,
        success_rate=round(success_rate, 2),
        average_duration_seconds=round(avg_duration, 2) if avg_duration else None,
    )


async def get_recent_runs(
    db: AsyncSession,
    project_id: Optional[str] = None,
    limit: int = 10,
) -> List[AgentRunOut]:
    """获取最近的 Agent 执行记录"""
    query = select(AgentRun).order_by(AgentRun.created_at.desc())
    if project_id:
        query = query.where(AgentRun.project_id == UUID(project_id))
    query = query.limit(limit)

    result = await db.execute(query)
    runs = result.scalars().all()
    return [AgentRunOut.model_validate(r) for r in runs]


async def cancel_run(db: AsyncSession, run_id: str) -> Optional[AgentRunOut]:
    """取消正在执行的 Agent 任务"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None

    if run.status not in ("pending", "running"):
        return None

    run.status = "cancelled"
    run.finished_at = datetime.utcnow()
    await db.commit()
    await db.refresh(run)
    return AgentRunOut.model_validate(run)
