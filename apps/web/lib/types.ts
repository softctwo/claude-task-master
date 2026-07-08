// ==================================================================
// Resoft AI Delivery Studio — TypeScript Types
// 1:1 mapping with backend Pydantic schemas (apps/api/app/schemas.py)
// ==================================================================

// ------------------------------------------------------------------
// Common
// ------------------------------------------------------------------
export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  pages: number;
  items: T[];
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// ------------------------------------------------------------------
// User
// ------------------------------------------------------------------
export type UserRole = "admin" | "manager" | "developer" | "viewer";

export interface UserBase {
  email: string;
  name: string;
  role: UserRole;
  avatar_url?: string | null;
}

export interface UserCreate extends UserBase {
  password: string;
}

export interface UserUpdate {
  email?: string;
  name?: string;
  role?: UserRole;
  avatar_url?: string | null;
}

export interface UserOut extends UserBase {
  user_id: string;
  created_at: string; // ISO datetime
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  user: UserOut;
}

// ------------------------------------------------------------------
// Project
// ------------------------------------------------------------------
export type ProjectStatus = "active" | "archived" | "paused";

export interface ProjectBase {
  name: string;
  description?: string | null;
  repo_url?: string | null;
  default_branch: string;
  taskmaster_path?: string | null;
  status: ProjectStatus;
  workspace_id?: string | null;
}

export interface ProjectCreate extends ProjectBase {}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
  repo_url?: string | null;
  default_branch?: string;
  taskmaster_path?: string | null;
  status?: ProjectStatus;
  workspace_id?: string | null;
}

export interface ProjectOut extends ProjectBase {
  project_id: string;
  owner_id: string;
  created_at: string;
  owner?: UserOut | null;
}

// ------------------------------------------------------------------
// Brief
// ------------------------------------------------------------------
export type BriefStatus = "draft" | "reviewing" | "approved" | "rejected" | "archived";

export interface BriefBase {
  title: string;
  background?: string | null;
  problem_statement?: string | null;
  target_users?: string | null;
  goals: string[];
  non_goals: string[];
  scope?: string | null;
  user_stories: string[];
  acceptance_criteria: string[];
  constraints?: string | null;
  related_docs: string[];
  related_code: string[];
  status: BriefStatus;
  reviewer_ids: string[];
  version: number;
}

export interface BriefCreate extends BriefBase {
  project_id: string;
}

export interface BriefUpdate {
  title?: string;
  background?: string | null;
  problem_statement?: string | null;
  target_users?: string | null;
  goals?: string[];
  non_goals?: string[];
  scope?: string | null;
  user_stories?: string[];
  acceptance_criteria?: string[];
  constraints?: string | null;
  related_docs?: string[];
  related_code?: string[];
  status?: BriefStatus;
  reviewer_ids?: string[];
  version?: number;
}

export interface BriefOut extends BriefBase {
  brief_id: string;
  project_id: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface BriefApprove {
  status?: "approved" | "rejected";
}

export interface BriefGeneratePRD {
  generated_by?: string;
}

// ------------------------------------------------------------------
// PRD
// ------------------------------------------------------------------
export interface PRDBase {
  content_markdown: string;
  source?: string | null;
  version: number;
  generated_by?: string | null;
}

export interface PRDCreate extends PRDBase {
  brief_id: string;
  project_id: string;
}

export interface PRDUpdate {
  content_markdown?: string;
  source?: string | null;
  version?: number;
  generated_by?: string | null;
  approved_at?: string | null;
}

export interface PRDOut extends PRDBase {
  prd_id: string;
  brief_id: string;
  project_id: string;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PRDGenerateTasks {
  // empty body
}

// ------------------------------------------------------------------
// Task
// ------------------------------------------------------------------
export type TaskPriority = "low" | "medium" | "high" | "critical";
export type TaskStatus = "pending" | "in_progress" | "completed" | "blocked" | "cancelled";

export interface TaskBase {
  title: string;
  description?: string | null;
  details?: string | null;
  test_strategy?: string | null;
  priority: TaskPriority;
  complexity_score?: number | null;
  dependencies: string[];
  status: TaskStatus;
  taskmaster_task_id?: string | null;
  parent_task_id?: string | null;
  assignee_id?: string | null;
  source_prd_id?: string | null;
  source_brief_id?: string | null;
}

export interface TaskCreate extends TaskBase {
  project_id: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string | null;
  details?: string | null;
  test_strategy?: string | null;
  priority?: TaskPriority;
  complexity_score?: number | null;
  dependencies?: string[];
  status?: TaskStatus;
  taskmaster_task_id?: string | null;
  parent_task_id?: string | null;
  assignee_id?: string | null;
  source_prd_id?: string | null;
  source_brief_id?: string | null;
  updated_from_taskmaster_at?: string | null;
}

export interface TaskOut extends TaskBase {
  task_id: string;
  project_id: string;
  updated_from_taskmaster_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskTreeOut extends TaskOut {
  children: TaskTreeOut[];
}

export interface TaskExpand {
  count?: number;
}

export interface TaskNext {
  next_task?: TaskOut | null;
  reason?: string | null;
}

export interface TaskComplexity {
  average: number;
  max: number;
  min: number;
  distribution: Record<string, number>;
}

// ------------------------------------------------------------------
// Agent Run
// ------------------------------------------------------------------
export type AgentRunExecutorType = "manual" | "auto" | "scheduled";
export type AgentRunStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface AgentRunBase {
  executor_type: AgentRunExecutorType;
  model?: string | null;
  branch_name?: string | null;
  command?: string | null;
  status: AgentRunStatus;
  logs?: string | null;
  result_summary?: string | null;
  pr_url?: string | null;
  error_message?: string | null;
}

export interface AgentRunCreate extends AgentRunBase {
  project_id: string;
  task_id?: string | null;
}

export interface AgentRunUpdate {
  executor_type?: AgentRunExecutorType;
  model?: string | null;
  branch_name?: string | null;
  command?: string | null;
  status?: AgentRunStatus;
  logs?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  result_summary?: string | null;
  pr_url?: string | null;
  error_message?: string | null;
}

export interface AgentRunOut extends AgentRunBase {
  run_id: string;
  project_id: string;
  task_id?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
}

export interface AgentRunLogs {
  run_id: string;
  logs: string;
}

// ------------------------------------------------------------------
// Knowledge Item
// ------------------------------------------------------------------
export type KnowledgeItemType = "document" | "code" | "link" | "note" | "image";
export type KnowledgeItemEmbeddingStatus = "pending" | "processing" | "completed" | "failed";
export type KnowledgeItemVisibility = "project" | "workspace" | "private";

export interface KnowledgeItemBase {
  type: KnowledgeItemType;
  title: string;
  source_url?: string | null;
  file_path?: string | null;
  content_hash?: string | null;
  parsed_text?: string | null;
  embedding_status: KnowledgeItemEmbeddingStatus;
  visibility: KnowledgeItemVisibility;
}

export interface KnowledgeItemCreate extends KnowledgeItemBase {
  project_id: string;
}

export interface KnowledgeItemUpdate {
  type?: KnowledgeItemType;
  title?: string;
  source_url?: string | null;
  file_path?: string | null;
  content_hash?: string | null;
  parsed_text?: string | null;
  embedding_status?: KnowledgeItemEmbeddingStatus;
  visibility?: KnowledgeItemVisibility;
}

export interface KnowledgeItemOut extends KnowledgeItemBase {
  knowledge_id: string;
  project_id: string;
  created_at: string;
}

export interface KnowledgeSearchResult {
  query: string;
  results: KnowledgeItemOut[];
}

// ------------------------------------------------------------------
// Audit Log
// ------------------------------------------------------------------
export interface AuditLogBase {
  action: string;
  resource_type: string;
  resource_id?: string | null;
  details?: Record<string, unknown> | null;
  ip_address?: string | null;
}

export interface AuditLogCreate extends AuditLogBase {
  user_id?: string | null;
}

export interface AuditLogOut extends AuditLogBase {
  log_id: string;
  user_id?: string | null;
  created_at: string;
}

// ------------------------------------------------------------------
// Git Integration
// ------------------------------------------------------------------
export interface GitIntegration {
  integration_id: string;
  project_id: string;
  provider: string;
  repo_url: string;
  default_branch: string;
  webhook_secret?: string | null;
  created_at: string;
}

export interface GitIntegrationCreate {
  project_id: string;
  provider: string;
  repo_url: string;
  default_branch?: string;
  webhook_secret?: string;
}

// ------------------------------------------------------------------
// Dashboard / UI
// ------------------------------------------------------------------
export interface DashboardStats {
  activeProjects: number;
  pendingTasks: number;
  inProgressTasks: number;
  completedTasks: number;
  totalBriefs: number;
  totalPRDs: number;
  totalAgentRuns: number;
}

export interface RecentActivity {
  id: string;
  type: "project" | "brief" | "task" | "agent_run" | "prd";
  title: string;
  action: string;
  timestamp: string;
  user?: string;
}
