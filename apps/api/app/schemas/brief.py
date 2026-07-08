"""Pydantic schemas for Brief model."""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


BriefStatus = Literal["draft", "in_review", "approved", "rejected", "superseded"]


class BriefBase(BaseModel):
    """Shared base fields for Brief schemas."""

    project_id: str = Field(description="Parent project ID (UUID as string)")
    title: str = Field(min_length=1, max_length=500, description="Brief title")
    background: Optional[str] = Field(default=None, description="Background context")
    problem_statement: Optional[str] = Field(default=None, description="Problem being solved")
    target_users: Optional[str] = Field(default=None, description="Target user personas")
    goals: List[str] = Field(default_factory=list, description="List of goals")
    non_goals: List[str] = Field(default_factory=list, description="List of non-goals")
    scope: Optional[str] = Field(default=None, description="Scope of work")
    user_stories: List[str] = Field(default_factory=list, description="List of user stories")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Acceptance criteria")
    constraints: Optional[str] = Field(default=None, description="Constraints and limitations")
    related_docs: List[str] = Field(default_factory=list, description="Related document URLs")
    related_code: List[str] = Field(default_factory=list, description="Related code references")
    status: BriefStatus = Field(default="draft", description="Brief status")
    reviewer_ids: List[str] = Field(default_factory=list, description="Reviewer user IDs")


class BriefCreate(BriefBase):
    """Schema for creating a new brief."""

    owner_id: str = Field(description="Brief owner user ID (UUID as string)")

    model_config = ConfigDict(from_attributes=True)


class BriefUpdate(BaseModel):
    """Schema for updating an existing brief."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Brief title")
    background: Optional[str] = Field(default=None, description="Background context")
    problem_statement: Optional[str] = Field(default=None, description="Problem being solved")
    target_users: Optional[str] = Field(default=None, description="Target user personas")
    goals: Optional[List[str]] = Field(default=None, description="List of goals")
    non_goals: Optional[List[str]] = Field(default=None, description="List of non-goals")
    scope: Optional[str] = Field(default=None, description="Scope of work")
    user_stories: Optional[List[str]] = Field(default=None, description="List of user stories")
    acceptance_criteria: Optional[List[str]] = Field(default=None, description="Acceptance criteria")
    constraints: Optional[str] = Field(default=None, description="Constraints and limitations")
    related_docs: Optional[List[str]] = Field(default=None, description="Related document URLs")
    related_code: Optional[List[str]] = Field(default=None, description="Related code references")
    status: Optional[BriefStatus] = Field(default=None, description="Brief status")
    owner_id: Optional[str] = Field(default=None, description="Brief owner user ID")
    reviewer_ids: Optional[List[str]] = Field(default=None, description="Reviewer user IDs")
    version: Optional[int] = Field(default=None, ge=1, description="Brief version number")

    model_config = ConfigDict(from_attributes=True)


class BriefResponse(BriefBase):
    """Schema for brief response."""

    brief_id: str = Field(description="Unique brief identifier (UUID as string)")
    owner_id: str = Field(description="Brief owner user ID (UUID as string)")
    version: int = Field(ge=1, description="Brief version number")
    created_at: datetime = Field(description="Brief creation timestamp")
    updated_at: datetime = Field(description="Brief last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class BriefList(BriefResponse):
    """Schema for brief list items (same as response)."""

    pass
