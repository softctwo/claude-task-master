export interface Workspace {
  workspace_id: string;
  name: string;
  owner_id: string;
  default_model_config?: ModelConfig;
  security_policy?: SecurityPolicy;
  created_at: string;
}

export interface Project {
  project_id: string;
  workspace_id: string;
  name: string;
  description?: string;
  repo_url?: string;
  default_branch?: string;
  taskmaster_path?: string;
  status: ProjectStatus;
  owner_id: string;
  created_at: string;
}

export type ProjectStatus = "active" | "archived" | "paused";

export interface Brief {
  brief_id: string;
  project_id: string;
  title: string;
  background?: string;
  problem_statement?: string;
  target_users?: string;
  goals?: string[];
  non_goals?: string[];
  scope?: string;
  user_stories?: string[];
  acceptance_criteria?: string[];
  constraints?: string;
  related_docs?: string[];
  related_code?: string[];
  status: BriefStatus;
  owner_id: string;
  reviewer_ids?: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export type BriefStatus = "draft" | "reviewing" | "approved" | "rejected" | "archived";

export interface PRD {
  prd_id: string;
  brief_id?: string;
  project_id: string;
  content_markdown: string;
  source?: string;
  version: number;
  generated_by?: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  task_id: string;
  project_id: string;
  taskmaster_task_id?: string;
  parent_task_id?: string;
  title: string;
  description?: string;
  details?: string;
  test_strategy?: string;
  priority: TaskPriority;
  complexity_score?: number;
  dependencies?: string[];
  status: TaskStatus;
  assignee_id?: string;
  source_prd_id?: string;
  source_brief_id?: string;
  updated_from_taskmaster_at?: string;
  created_at: string;
  updated_at: string;
}

export type TaskPriority = "critical" | "high" | "medium" | "low";
export type TaskStatus = "pending" | "in_progress" | "done" | "blocked" | "deferred" | "cancelled";

export interface AgentRun {
  run_id: string;
  project_id: string;
  task_id?: string;
  executor_type: ExecutorType;
  model?: string;
  branch_name?: string;
  command?: string;
  status: RunStatus;
  logs?: string;
  started_at?: string;
  finished_at?: string;
  result_summary?: string;
  pr_url?: string;
  error_message?: string;
  created_at: string;
}

export type ExecutorType = "local" | "remote" | "manual";
export type RunStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface KnowledgeItem {
  knowledge_id: string;
  project_id?: string;
  type: KnowledgeType;
  title: string;
  source_url?: string;
  file_path?: string;
  content_hash?: string;
  parsed_text?: string;
  embedding_status?: EmbeddingStatus;
  visibility: Visibility;
  created_at: string;
}

export type KnowledgeType = "document" | "meeting" | "code" | "sop" | "template" | "other";
export type EmbeddingStatus = "pending" | "processing" | "completed" | "failed";
export type Visibility = "private" | "project" | "workspace" | "public";

export interface ContextEdge {
  edge_id: string;
  source_type: string;
  source_id: string;
  relation_type: RelationType;
  target_type: string;
  target_id: string;
  confidence?: number;
  created_by?: string;
  created_at: string;
}

export type RelationType =
  | "derived_from"
  | "implements"
  | "blocks"
  | "depends_on"
  | "references"
  | "owns"
  | "reviews"
  | "approved_by"
  | "generated_by"
  | "related_to";

export interface ModelConfig {
  provider: string;
  model: string;
  api_key?: string;
  base_url?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface SecurityPolicy {
  allowed_upload_types?: string[];
  blocked_paths?: string[];
  allow_external_models?: boolean;
  require_approval?: boolean;
}

export interface AuditLog {
  log_id: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}

export interface User {
  user_id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar_url?: string;
  created_at: string;
}

export type UserRole =
  | "admin"
  | "workspace_owner"
  | "project_owner"
  | "product_manager"
  | "tech_lead"
  | "developer"
  | "tester"
  | "viewer";

export interface TaskmasterTask {
  id: string;
  title: string;
  description: string;
  details?: string;
  status: string;
  priority: string;
  complexity_score?: number;
  dependencies: string[];
  subtasks?: TaskmasterTask[];
}

export interface TaskmasterProject {
  tasks: TaskmasterTask[];
  dependencies: Record<string, string[]>;
}
