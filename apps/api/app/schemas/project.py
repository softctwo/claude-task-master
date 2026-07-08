"""Pydantic schemas for Project model."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


ProjectStatus = Literal["active", "archived", "paused", "deleted"]


class ProjectBase(BaseModel):
    """Shared base fields for Project schemas."""

    workspace_id: Optional[str] = Field(default=None, description="Parent workspace ID (UUID as string)")
    name: str = Field(min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    repo_url: Optional[str] = Field(default=None, description="Git repository URL")
    default_branch: str = Field(default="main", max_length=255, description="Default Git branch")
    taskmaster_path: Optional[str] = Field(default=None, description="Path to taskmaster configuration")
    status: ProjectStatus = Field(default="active", description="Project status")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    owner_id: str = Field(description="Project owner user ID (UUID as string)")

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    workspace_id: Optional[str] = Field(default=None, description="Parent workspace ID")
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    repo_url: Optional[str] = Field(default=None, description="Git repository URL")
    default_branch: Optional[str] = Field(default=None, max_length=255, description="Default Git branch")
    taskmaster_path: Optional[str] = Field(default=None, description="Path to taskmaster configuration")
    status: Optional[ProjectStatus] = Field(default=None, description="Project status")
    owner_id: Optional[str] = Field(default=None, description="Project owner user ID")

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    project_id: str = Field(description="Unique project identifier (UUID as string)")
    owner_id: str = Field(description="Project owner user ID (UUID as string)")
    created_at: datetime = Field(description="Project creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProjectList(ProjectResponse):
    """Schema for project list items (same as response)."""

    pass
