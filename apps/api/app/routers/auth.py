"""Authentication router."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserCreate, UserLogin, TokenOut, UserOut
from app.utils.security import hash_password, verify_password, create_access_token
from app.services.base import CRUDService

router = APIRouter()
user_service = CRUDService(User)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check duplicate email
    existing = await user_service.get_by(db, email=user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_data = user_in.model_dump()
    user_data["hashed_password"] = hash_password(user_data.pop("password"))
    user = await user_service.create(db, user_data)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenOut)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT token."""
    user = await user_service.get_by(db, email=credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=timedelta(minutes=60 * 24),
    )
    return TokenOut(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user
