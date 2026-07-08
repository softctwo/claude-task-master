-- 初始化数据库 schema
-- 创建 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'developer',
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 工作区表
CREATE TABLE IF NOT EXISTS workspaces (
    workspace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID REFERENCES users(user_id),
    default_model_config JSONB,
    security_policy JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(workspace_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repo_url TEXT,
    default_branch VARCHAR(255) DEFAULT 'main',
    taskmaster_path TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    owner_id UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 项目成员表
CREATE TABLE IF NOT EXISTS project_members (
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'developer',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

-- Brief 表
CREATE TABLE IF NOT EXISTS briefs (
    brief_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    background TEXT,
    problem_statement TEXT,
    target_users TEXT,
    goals TEXT[],
    non_goals TEXT[],
    scope TEXT,
    user_stories TEXT[],
    acceptance_criteria TEXT[],
    constraints TEXT,
    related_docs TEXT[],
    related_code TEXT[],
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    owner_id UUID REFERENCES users(user_id),
    reviewer_ids UUID[],
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Brief 版本快照表
CREATE TABLE IF NOT EXISTS brief_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID REFERENCES briefs(brief_id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PRD 表
CREATE TABLE IF NOT EXISTS prds (
    prd_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID REFERENCES briefs(brief_id),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    content_markdown TEXT NOT NULL,
    source VARCHAR(255),
    version INTEGER NOT NULL DEFAULT 1,
    generated_by VARCHAR(255),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    taskmaster_task_id VARCHAR(255),
    parent_task_id UUID REFERENCES tasks(task_id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    details TEXT,
    test_strategy TEXT,
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    complexity_score INTEGER,
    dependencies UUID[],
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    assignee_id UUID REFERENCES users(user_id),
    source_prd_id UUID REFERENCES prds(prd_id),
    source_brief_id UUID REFERENCES briefs(brief_id),
    updated_from_taskmaster_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 任务依赖表
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    depends_on_task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, depends_on_task_id)
);

-- Agent Run 表
CREATE TABLE IF NOT EXISTS agent_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(task_id),
    executor_type VARCHAR(50) NOT NULL DEFAULT 'manual',
    model VARCHAR(255),
    branch_name VARCHAR(255),
    command TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    logs TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    result_summary TEXT,
    pr_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 知识项表
CREATE TABLE IF NOT EXISTS knowledge_items (
    knowledge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'document',
    title VARCHAR(500) NOT NULL,
    source_url TEXT,
    file_path TEXT,
    content_hash VARCHAR(64),
    parsed_text TEXT,
    embedding_status VARCHAR(50) DEFAULT 'pending',
    embedding VECTOR(1536),
    visibility VARCHAR(50) NOT NULL DEFAULT 'project',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 知识切片表
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id UUID REFERENCES knowledge_items(knowledge_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 关系边表 (Context Graph)
CREATE TABLE IF NOT EXISTS context_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    source_id UUID NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 集成配置表
CREATE TABLE IF NOT EXISTS integrations (
    integration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 模型配置表
CREATE TABLE IF NOT EXISTS model_configs (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT,
    base_url TEXT,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    user_id UUID REFERENCES users(user_id),
    content TEXT NOT NULL,
    parent_comment_id UUID REFERENCES comments(comment_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_workspace ON projects(workspace_id);
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_briefs_project ON briefs(project_id);
CREATE INDEX IF NOT EXISTS idx_briefs_status ON briefs(status);
CREATE INDEX IF NOT EXISTS idx_prds_brief ON prds(brief_id);
CREATE INDEX IF NOT EXISTS idx_prds_project ON prds(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_project ON agent_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_project ON knowledge_items(project_id);
CREATE INDEX IF NOT EXISTS idx_context_edges_source ON context_edges(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_context_edges_target ON context_edges(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_comments_resource ON comments(resource_type, resource_id);

-- 插入默认工作区
INSERT INTO workspaces (name, owner_id, default_model_config)
VALUES ('Default Workspace', NULL, '{"provider": "openai", "model": "gpt-4"}'::jsonb)
ON CONFLICT DO NOTHING;
