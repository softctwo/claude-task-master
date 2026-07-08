"""Pydantic schemas for AgentRun model."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


AgentRunExecutorType = Literal["manual", "auto", "scheduled", "webhook"]
AgentRunStatus = Literal["pending", "running", "success", "failed", "cancelled", "timeout"]


class AgentRunBase(BaseModel):
    """Shared base fields for AgentRun schemas."""

    project_id: str = Field(description="Parent project ID (UUID as string)")
    task_id: Optional[str] = Field(default=None, description="Associated task ID (UUID as string)")
    executor_type: AgentRunExecutorType = Field(default="manual", description="Execution trigger type")
    model: Optional[str] = Field(default=None, description="AI model used for execution")
    branch_name: Optional[str] = Field(default=None, description="Git branch name for the run")
    command: Optional[str] = Field(default=None, description="Command or prompt executed")
    status: AgentRunStatus = Field(default="pending", description="Run status")
    logs: Optional[str] = Field(default=None, description="Execution logs")
    result_summary: Optional[str] = Field(default=None, description="Summary of execution results")
    pr_url: Optional[str] = Field(default=None, description="Pull request URL if created")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class AgentRunCreate(AgentRunBase):
    """Schema for creating a new agent run."""

    model_config = ConfigDict(from_attributes=True)


class AgentRunUpdate(BaseModel):
    """Schema for updating an existing agent run."""

    executor_type: Optional[AgentRunExecutorType] = Field(default=None, description="Execution trigger type")
    model: Optional[str] = Field(default=None, description="AI model used for execution")
    branch_name: Optional[str] = Field(default=None, description="Git branch name for the run")
    command: Optional[str] = Field(default=None, description="Command or prompt executed")
    status: Optional[AgentRunStatus] = Field(default=None, description="Run status")
    logs: Optional[str] = Field(default=None, description="Execution logs")
    started_at: Optional[datetime] = Field(default=None, description="Run start timestamp")
    finished_at: Optional[datetime] = Field(default=None, description="Run finish timestamp")
    result_summary: Optional[str] = Field(default=None, description="Summary of execution results")
    pr_url: Optional[str] = Field(default=None, description="Pull request URL if created")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(from_attributes=True)


class AgentRunResponse(AgentRunBase):
    """Schema for agent run response."""

    run_id: str = Field(description="Unique run identifier (UUID as string)")
    started_at: Optional[datetime] = Field(default=None, description="Run start timestamp")
    finished_at: Optional[datetime] = Field(default=None, description="Run finish timestamp")
    created_at: datetime = Field(description="Run creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class AgentRunList(AgentRunResponse):
    """Schema for agent run list items (same as response)."""

    pass
