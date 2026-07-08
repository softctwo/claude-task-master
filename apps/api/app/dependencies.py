"""FastAPI dependency injection for Resoft AI Delivery Studio."""
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.utils.security import decode_access_token
from app.schemas import UserOut

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Dependency to extract and validate the current user from JWT Bearer token."""
    # Allow fallback to query param for WebSocket / special cases
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.query_params.get("token")
        if not token:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserOut.model_validate(user)


async def get_current_active_user(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    """Ensure the user is active (placeholder for future ban/suspend checks)."""
    return current_user


class RoleChecker:
    """Dependency factory to enforce role-based access control."""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: UserOut = Depends(get_current_user)) -> UserOut:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user


require_admin = RoleChecker(["admin"])
require_manager_or_admin = RoleChecker(["admin", "manager"])
require_developer_or_above = RoleChecker(["admin", "manager", "developer"])
