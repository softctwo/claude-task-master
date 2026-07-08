"""Pydantic schemas for PRD model."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


PRDSource = Literal["manual", "ai_generated", "imported"]
PRDStatus = Literal["draft", "in_review", "approved", "rejected"]


class PRDBase(BaseModel):
    """Shared base fields for PRD schemas."""

    brief_id: str = Field(description="Parent brief ID (UUID as string)")
    project_id: str = Field(description="Parent project ID (UUID as string)")
    content_markdown: str = Field(min_length=1, description="PRD content in Markdown format")
    source: PRDSource = Field(default="manual", description="PRD source type")
    generated_by: Optional[str] = Field(default=None, description="Model or user that generated the PRD")


class PRDCreate(PRDBase):
    """Schema for creating a new PRD."""

    model_config = ConfigDict(from_attributes=True)


class PRDUpdate(BaseModel):
    """Schema for updating an existing PRD."""

    content_markdown: Optional[str] = Field(default=None, min_length=1, description="PRD content in Markdown format")
    source: Optional[PRDSource] = Field(default=None, description="PRD source type")
    generated_by: Optional[str] = Field(default=None, description="Model or user that generated the PRD")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    version: Optional[int] = Field(default=None, ge=1, description="PRD version number")

    model_config = ConfigDict(from_attributes=True)


class PRDResponse(PRDBase):
    """Schema for PRD response."""

    prd_id: str = Field(description="Unique PRD identifier (UUID as string)")
    version: int = Field(ge=1, description="PRD version number")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    created_at: datetime = Field(description="PRD creation timestamp")
    updated_at: datetime = Field(description="PRD last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PRDList(PRDResponse):
    """Schema for PRD list items (same as response)."""

    pass
