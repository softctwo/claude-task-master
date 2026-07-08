"""Pydantic schemas for Task model."""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


TaskPriority = Literal["low", "medium", "high", "critical"]
TaskStatus = Literal["pending", "in_progress", "blocked", "review", "completed", "cancelled"]


class TaskBase(BaseModel):
    """Shared base fields for Task schemas."""

    project_id: str = Field(description="Parent project ID (UUID as string)")
    taskmaster_task_id: Optional[str] = Field(default=None, description="External taskmaster task ID")
    parent_task_id: Optional[str] = Field(default=None, description="Parent task ID for subtasks")
    title: str = Field(min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    details: Optional[str] = Field(default=None, description="Detailed implementation notes")
    test_strategy: Optional[str] = Field(default=None, description="Testing approach for this task")
    priority: TaskPriority = Field(default="medium", description="Task priority")
    complexity_score: Optional[int] = Field(default=None, ge=1, le=10, description="Complexity score (1-10)")
    dependencies: List[str] = Field(default_factory=list, description="Dependent task IDs")
    status: TaskStatus = Field(default="pending", description="Task status")
    assignee_id: Optional[str] = Field(default=None, description="Assigned user ID")
    source_prd_id: Optional[str] = Field(default=None, description="Source PRD ID")
    source_brief_id: Optional[str] = Field(default=None, description="Source brief ID")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    taskmaster_task_id: Optional[str] = Field(default=None, description="External taskmaster task ID")
    parent_task_id: Optional[str] = Field(default=None, description="Parent task ID for subtasks")
    title: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    details: Optional[str] = Field(default=None, description="Detailed implementation notes")
    test_strategy: Optional[str] = Field(default=None, description="Testing approach")
    priority: Optional[TaskPriority] = Field(default=None, description="Task priority")
    complexity_score: Optional[int] = Field(default=None, ge=1, le=10, description="Complexity score (1-10)")
    dependencies: Optional[List[str]] = Field(default=None, description="Dependent task IDs")
    status: Optional[TaskStatus] = Field(default=None, description="Task status")
    assignee_id: Optional[str] = Field(default=None, description="Assigned user ID")
    source_prd_id: Optional[str] = Field(default=None, description="Source PRD ID")
    source_brief_id: Optional[str] = Field(default=None, description="Source brief ID")
    updated_from_taskmaster_at: Optional[datetime] = Field(default=None, description="Last sync timestamp from taskmaster")

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(TaskBase):
    """Schema for task response."""

    task_id: str = Field(description="Unique task identifier (UUID as string)")
    updated_from_taskmaster_at: Optional[datetime] = Field(default=None, description="Last sync timestamp from taskmaster")
    created_at: datetime = Field(description="Task creation timestamp")
    updated_at: datetime = Field(description="Task last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class TaskList(TaskResponse):
    """Schema for task list items (same as response)."""

    pass
