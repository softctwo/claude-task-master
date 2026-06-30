from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, ARRAY, Float, UUID as SAUUID, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="developer")
    avatar_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    workspace_id = Column(SAUUID, ForeignKey("workspaces.workspace_id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    repo_url = Column(Text)
    default_branch = Column(String(255), default="main")
    taskmaster_path = Column(Text)
    status = Column(String(50), nullable=False, default="active")
    owner_id = Column(SAUUID, ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")


class Brief(Base):
    __tablename__ = "briefs"

    brief_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(SAUUID, ForeignKey("projects.project_id", ondelete="CASCADE"))
    title = Column(String(500), nullable=False)
    background = Column(Text)
    problem_statement = Column(Text)
    target_users = Column(Text)
    goals = Column(ARRAY(Text))
    non_goals = Column(ARRAY(Text))
    scope = Column(Text)
    user_stories = Column(ARRAY(Text))
    acceptance_criteria = Column(ARRAY(Text))
    constraints = Column(Text)
    related_docs = Column(ARRAY(Text))
    related_code = Column(ARRAY(Text))
    status = Column(String(50), nullable=False, default="draft")
    owner_id = Column(SAUUID, ForeignKey("users.user_id"))
    reviewer_ids = Column(ARRAY(SAUUID))
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PRD(Base):
    __tablename__ = "prds"

    prd_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    brief_id = Column(SAUUID, ForeignKey("briefs.brief_id"))
    project_id = Column(SAUUID, ForeignKey("projects.project_id", ondelete="CASCADE"))
    content_markdown = Column(Text, nullable=False)
    source = Column(String(255))
    version = Column(Integer, nullable=False, default=1)
    generated_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(SAUUID, ForeignKey("projects.project_id", ondelete="CASCADE"))
    taskmaster_task_id = Column(String(255))
    parent_task_id = Column(SAUUID, ForeignKey("tasks.task_id"))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    details = Column(Text)
    test_strategy = Column(Text)
    priority = Column(String(50), nullable=False, default="medium")
    complexity_score = Column(Integer)
    dependencies = Column(ARRAY(SAUUID))
    status = Column(String(50), nullable=False, default="pending")
    assignee_id = Column(SAUUID, ForeignKey("users.user_id"))
    source_prd_id = Column(SAUUID, ForeignKey("prds.prd_id"))
    source_brief_id = Column(SAUUID, ForeignKey("briefs.brief_id"))
    updated_from_taskmaster_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(SAUUID, ForeignKey("projects.project_id", ondelete="CASCADE"))
    task_id = Column(SAUUID, ForeignKey("tasks.task_id"))
    executor_type = Column(String(50), nullable=False, default="manual")
    model = Column(String(255))
    branch_name = Column(String(255))
    command = Column(Text)
    status = Column(String(50), nullable=False, default="pending")
    logs = Column(Text)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    result_summary = Column(Text)
    pr_url = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    knowledge_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(SAUUID, ForeignKey("projects.project_id", ondelete="SET NULL"))
    type = Column(String(50), nullable=False, default="document")
    title = Column(String(500), nullable=False)
    source_url = Column(Text)
    file_path = Column(Text)
    content_hash = Column(String(64))
    parsed_text = Column(Text)
    embedding_status = Column(String(50), default="pending")
    visibility = Column(String(50), nullable=False, default="project")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(SAUUID, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(SAUUID, ForeignKey("users.user_id"))
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(SAUUID)
    details = Column(JSON)
    ip_address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
