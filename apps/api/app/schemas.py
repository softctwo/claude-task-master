"""Pydantic v2 Schemas for Resoft AI Delivery Studio API."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


# ------------------------------------------------------------------
# User
# ------------------------------------------------------------------
class UserBase(BaseModel):
    email: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    role: Literal["admin", "manager", "developer", "viewer"] = "developer"
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=255)


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    role: Optional[Literal["admin", "manager", "developer", "viewer"]] = None
    avatar_url: Optional[str] = None


class UserOut(UserBase):
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------------------------------------------------------
# Project
# ------------------------------------------------------------------
class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    repo_url: Optional[str] = None
    default_branch: str = "main"
    taskmaster_path: Optional[str] = None
    status: Literal["active", "archived", "paused"] = "active"
    workspace_id: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    repo_url: Optional[str] = None
    default_branch: Optional[str] = None
    taskmaster_path: Optional[str] = None
    status: Optional[Literal["active", "archived", "paused"]] = None
    workspace_id: Optional[str] = None


class ProjectOut(ProjectBase):
    project_id: str
    owner_id: str
    created_at: datetime
    owner: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------
# Brief
# ------------------------------------------------------------------
class BriefBase(BaseModel):
    title: str = Field(..., max_length=500)
    background: Optional[str] = None
    problem_statement: Optional[str] = None
    target_users: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    non_goals: List[str] = Field(default_factory=list)
    scope: Optional[str] = None
    user_stories: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    constraints: Optional[str] = None
    related_docs: List[str] = Field(default_factory=list)
    related_code: List[str] = Field(default_factory=list)
    status: Literal["draft", "reviewing", "approved", "rejected", "archived"] = "draft"
    reviewer_ids: List[str] = Field(default_factory=list)
    version: int = 1


class BriefCreate(BriefBase):
    project_id: str


class BriefUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    background: Optional[str] = None
    problem_statement: Optional[str] = None
    target_users: Optional[str] = None
    goals: Optional[List[str]] = None
    non_goals: Optional[List[str]] = None
    scope: Optional[str] = None
    user_stories: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    constraints: Optional[str] = None
    related_docs: Optional[List[str]] = None
    related_code: Optional[List[str]] = None
    status: Optional[Literal["draft", "reviewing", "approved", "rejected", "archived"]] = None
    reviewer_ids: Optional[List[str]] = None
    version: Optional[int] = None


class BriefOut(BriefBase):
    brief_id: str
    project_id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BriefApprove(BaseModel):
    status: Literal["approved", "rejected"] = "approved"


class BriefGeneratePRD(BaseModel):
    generated_by: Optional[str] = "system"


# ------------------------------------------------------------------
# PRD
# ------------------------------------------------------------------
class PRDBase(BaseModel):
    content_markdown: str
    source: Optional[str] = None
    version: int = 1
    generated_by: Optional[str] = None


class PRDCreate(PRDBase):
    brief_id: str
    project_id: str


class PRDUpdate(BaseModel):
    content_markdown: Optional[str] = None
    source: Optional[str] = None
    version: Optional[int] = None
    generated_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class PRDOut(PRDBase):
    prd_id: str
    brief_id: str
    project_id: str
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PRDGenerateTasks(BaseModel):
    pass


# ------------------------------------------------------------------
# Task
# ------------------------------------------------------------------
class TaskBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    details: Optional[str] = None
    test_strategy: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    complexity_score: Optional[int] = None
    dependencies: List[str] = Field(default_factory=list)
    status: Literal["pending", "in_progress", "completed", "blocked", "cancelled"] = "pending"
    taskmaster_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    assignee_id: Optional[str] = None
    source_prd_id: Optional[str] = None
    source_brief_id: Optional[str] = None


class TaskCreate(TaskBase):
    project_id: str


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    details: Optional[str] = None
    test_strategy: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    complexity_score: Optional[int] = None
    dependencies: Optional[List[str]] = None
    status: Optional[Literal["pending", "in_progress", "completed", "blocked", "cancelled"]] = None
    taskmaster_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    assignee_id: Optional[str] = None
    source_prd_id: Optional[str] = None
    source_brief_id: Optional[str] = None
    updated_from_taskmaster_at: Optional[datetime] = None


class TaskOut(TaskBase):
    task_id: str
    project_id: str
    updated_from_taskmaster_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TaskTreeOut(TaskOut):
    children: List["TaskTreeOut"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class TaskExpand(BaseModel):
    count: int = 3


class TaskNext(BaseModel):
    next_task: Optional[TaskOut] = None
    reason: Optional[str] = None


class TaskComplexity(BaseModel):
    average: float
    max: int
    min: int
    distribution: Dict[str, int]


# ------------------------------------------------------------------
# AgentRun
# ------------------------------------------------------------------
class AgentRunBase(BaseModel):
    executor_type: Literal["manual", "auto", "scheduled"] = "manual"
    model: Optional[str] = None
    branch_name: Optional[str] = None
    command: Optional[str] = None
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"
    logs: Optional[str] = None
    result_summary: Optional[str] = None
    pr_url: Optional[str] = None
    error_message: Optional[str] = None


class AgentRunCreate(AgentRunBase):
    project_id: str
    task_id: Optional[str] = None


class AgentRunUpdate(BaseModel):
    executor_type: Optional[Literal["manual", "auto", "scheduled"]] = None
    model: Optional[str] = None
    branch_name: Optional[str] = None
    command: Optional[str] = None
    status: Optional[Literal["pending", "running", "completed", "failed", "cancelled"]] = None
    logs: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result_summary: Optional[str] = None
    pr_url: Optional[str] = None
    error_message: Optional[str] = None


class AgentRunOut(AgentRunBase):
    run_id: str
    project_id: str
    task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentRunLogs(BaseModel):
    run_id: str
    logs: str


# ------------------------------------------------------------------
# KnowledgeItem
# ------------------------------------------------------------------
class KnowledgeItemBase(BaseModel):
    type: Literal["document", "code", "link", "note", "image"] = "document"
    title: str = Field(..., max_length=500)
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    parsed_text: Optional[str] = None
    embedding_status: Literal["pending", "processing", "completed", "failed"] = "pending"
    visibility: Literal["project", "workspace", "private"] = "project"


class KnowledgeItemCreate(KnowledgeItemBase):
    project_id: str


class KnowledgeItemUpdate(BaseModel):
    type: Optional[Literal["document", "code", "link", "note", "image"]] = None
    title: Optional[str] = Field(None, max_length=500)
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    parsed_text: Optional[str] = None
    embedding_status: Optional[Literal["pending", "processing", "completed", "failed"]] = None
    visibility: Optional[Literal["project", "workspace", "private"]] = None


class KnowledgeItemOut(KnowledgeItemBase):
    knowledge_id: str
    project_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class KnowledgeSearchResult(BaseModel):
    query: str
    results: List[KnowledgeItemOut]


# ------------------------------------------------------------------
# AuditLog
# ------------------------------------------------------------------
class AuditLogBase(BaseModel):
    action: str = Field(..., max_length=255)
    resource_type: str = Field(..., max_length=100)
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: Optional[str] = None


class AuditLogOut(AuditLogBase):
    log_id: str
    user_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------
# Pagination / Common
# ------------------------------------------------------------------
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: List[Any]


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# Resolve forward refs
TaskTreeOut.model_rebuild()
