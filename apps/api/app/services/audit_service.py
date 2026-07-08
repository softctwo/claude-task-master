"""Audit Service - 审计日志记录"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


# ────────────────────────────────
# Pydantic Schemas
# ────────────────────────────────

class AuditLogCreate(BaseModel):
    user_id: Optional[str] = None
    action: str = Field(..., min_length=1, max_length=255)
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None


class AuditLogOut(BaseModel):
    log_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogOut]
    total: int
    page: int
    page_size: int


class AuditLogFilter(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ActionSummary(BaseModel):
    action: str
    count: int
    last_occurred: datetime


class ResourceActivitySummary(BaseModel):
    resource_type: str
    resource_id: str
    action_count: int
    last_action: str
    last_action_at: datetime


# ────────────────────────────────
# Service Functions
# ────────────────────────────────

async def create_audit_log(db: AsyncSession, data: AuditLogCreate) -> AuditLogOut:
    """创建审计日志记录"""
    log = AuditLog(
        user_id=UUID(data.user_id) if data.user_id else None,
        action=data.action,
        resource_type=data.resource_type,
        resource_id=UUID(data.resource_id) if data.resource_id else None,
        details=data.details,
        ip_address=data.ip_address,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return AuditLogOut.model_validate(log)


async def get_audit_log(db: AsyncSession, log_id: str) -> Optional[AuditLogOut]:
    """根据 ID 获取审计日志"""
    result = await db.execute(
        select(AuditLog).where(AuditLog.log_id == UUID(log_id))
    )
    log = result.scalar_one_or_none()
    if log is None:
        return None
    return AuditLogOut.model_validate(log)


async def list_audit_logs(
    db: AsyncSession,
    filters: Optional[AuditLogFilter] = None,
    page: int = 1,
    page_size: int = 50,
) -> AuditLogListResponse:
    """列出审计日志，支持过滤和分页"""
    query = select(AuditLog)
    conditions = []

    if filters:
        if filters.user_id:
            conditions.append(AuditLog.user_id == UUID(filters.user_id))
        if filters.action:
            conditions.append(AuditLog.action == filters.action)
        if filters.resource_type:
            conditions.append(AuditLog.resource_type == filters.resource_type)
        if filters.resource_id:
            conditions.append(AuditLog.resource_id == UUID(filters.resource_id))
        if filters.start_date:
            conditions.append(AuditLog.created_at >= filters.start_date)
        if filters.end_date:
            conditions.append(AuditLog.created_at <= filters.end_date)

    if conditions:
        query = query.where(and_(*conditions))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditLogListResponse(
        items=[AuditLogOut.model_validate(l) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_user_activity(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
) -> List[AuditLogOut]:
    """获取用户的活动日志"""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == UUID(user_id))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [AuditLogOut.model_validate(l) for l in logs]


async def get_resource_activity(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
    limit: int = 50,
) -> List[AuditLogOut]:
    """获取特定资源的审计日志"""
    result = await db.execute(
        select(AuditLog)
        .where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == UUID(resource_id),
            )
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [AuditLogOut.model_validate(l) for l in logs]


async def get_action_summary(
    db: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[ActionSummary]:
    """获取操作类型汇总统计"""
    query = select(
        AuditLog.action,
        func.count().label("count"),
        func.max(AuditLog.created_at).label("last_occurred"),
    )

    conditions = []
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.group_by(AuditLog.action).order_by(func.count().desc())

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        ActionSummary(
            action=row.action,
            count=row.count,
            last_occurred=row.last_occurred,
        )
        for row in rows
    ]


async def get_resource_activity_summary(
    db: AsyncSession,
    resource_type: Optional[str] = None,
    limit: int = 20,
) -> List[ResourceActivitySummary]:
    """获取资源活动汇总"""
    query = select(
        AuditLog.resource_type,
        AuditLog.resource_id,
        func.count().label("action_count"),
        func.max(AuditLog.action).label("last_action"),
        func.max(AuditLog.created_at).label("last_action_at"),
    ).where(AuditLog.resource_id.isnot(None))

    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    query = (
        query.group_by(AuditLog.resource_type, AuditLog.resource_id)
        .order_by(func.count().desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        ResourceActivitySummary(
            resource_type=row.resource_type,
            resource_id=str(row.resource_id),
            action_count=row.action_count,
            last_action=row.last_action,
            last_action_at=row.last_action_at,
        )
        for row in rows
    ]


async def log_user_action(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLogOut:
    """便捷方法：记录用户操作"""
    return await create_audit_log(
        db,
        AuditLogCreate(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        ),
    )


async def get_recent_audit_logs(
    db: AsyncSession,
    limit: int = 20,
) -> List[AuditLogOut]:
    """获取最近的审计日志"""
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [AuditLogOut.model_validate(l) for l in logs]


async def get_audit_logs_by_action(
    db: AsyncSession,
    action: str,
    page: int = 1,
    page_size: int = 50,
) -> AuditLogListResponse:
    """按操作类型获取审计日志"""
    return await list_audit_logs(
        db,
        filters=AuditLogFilter(action=action),
        page=page,
        page_size=page_size,
    )


async def delete_old_audit_logs(
    db: AsyncSession,
    before_date: datetime,
) -> int:
    """删除指定日期之前的审计日志，返回删除数量"""
    result = await db.execute(
        select(AuditLog).where(AuditLog.created_at < before_date)
    )
    logs = result.scalars().all()
    count = len(logs)

    for log in logs:
        await db.delete(log)

    await db.commit()
    return count
