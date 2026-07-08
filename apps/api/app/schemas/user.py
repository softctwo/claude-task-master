"""Pydantic schemas for User model."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, EmailStr


UserRole = Literal["admin", "manager", "developer", "viewer"]
UserStatus = Literal["active", "inactive", "suspended"]


class UserBase(BaseModel):
    """Shared base fields for User schemas."""

    email: EmailStr = Field(description="User email address")
    name: str = Field(min_length=1, max_length=255, description="User display name")
    role: UserRole = Field(default="developer", description="User role")
    avatar_url: Optional[str] = Field(default=None, description="URL to user avatar image")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(min_length=8, max_length=255, description="Plaintext password")

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: Optional[EmailStr] = Field(default=None, description="User email address")
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="User display name")
    role: Optional[UserRole] = Field(default=None, description="User role")
    avatar_url: Optional[str] = Field(default=None, description="URL to user avatar image")
    password: Optional[str] = Field(default=None, min_length=8, max_length=255, description="New plaintext password")

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""

    user_id: str = Field(description="Unique user identifier (UUID as string)")
    created_at: datetime = Field(description="Account creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class UserList(UserResponse):
    """Schema for user list items (same as response)."""

    pass
