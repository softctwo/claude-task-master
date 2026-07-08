"""Audit router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import AuditLog
from app.schemas import AuditLogOut, PaginationParams, PaginatedResponse
from app.services import audit_service
from app.utils.pagination import paginate

router = APIRouter()


@router.get("/logs", response_model=PaginatedResponse)
async def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """List audit logs (admin only)."""
    stmt = select(AuditLog)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    stmt = stmt.order_by(desc(AuditLog.created_at))

    params = PaginationParams(page=page, page_size=page_size)
    return await paginate(
        db, stmt, params,
        transform=lambda a: AuditLogOut.model_validate(a).model_dump(),
    )


@router.post("/logs", response_model=AuditLogOut, status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create an audit log entry."""
    log_data = {
        "user_id": current_user.user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
    }
    log = await audit_service.create(db, log_data)
    return AuditLogOut.model_validate(log)
