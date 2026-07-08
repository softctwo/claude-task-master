import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ------------------------------------------------------------------
// Axios instance with interceptors
// ------------------------------------------------------------------
export const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor: attach JWT token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: unified error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    const status = error.response?.status;
    const data = error.response?.data;

    if (status === 401) {
      // Token expired or invalid — clear auth and redirect
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }

    // Normalize error for consumers
    const normalizedError: ApiError = {
      message: data?.detail || data?.message || error.message || "请求失败",
      status,
      code: data?.code,
      errors: data?.errors,
    };

    return Promise.reject(normalizedError);
  }
);

// ------------------------------------------------------------------
// Error types
// ------------------------------------------------------------------
export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  code?: string;
  errors?: Record<string, string[]>;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  errors?: Record<string, string[]>;
}

// ------------------------------------------------------------------
// Generic CRUD helpers
// ------------------------------------------------------------------
export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await api.get<T>(url, { params });
  return response.data;
}

export async function post<T>(url: string, data?: unknown): Promise<T> {
  const response = await api.post<T>(url, data);
  return response.data;
}

export async function put<T>(url: string, data?: unknown): Promise<T> {
  const response = await api.put<T>(url, data);
  return response.data;
}

export async function patch<T>(url: string, data?: unknown): Promise<T> {
  const response = await api.patch<T>(url, data);
  return response.data;
}

export async function del<T>(url: string): Promise<T> {
  const response = await api.delete<T>(url);
  return response.data;
}

// ------------------------------------------------------------------
// Auth API
// ------------------------------------------------------------------
export const authApi = {
  register: (data: { email: string; name: string; password: string; role?: string }) =>
    post<TokenOut>("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    post<TokenOut>("/auth/login", data),
  me: () => get<UserOut>("/auth/me"),
};

// ------------------------------------------------------------------
// Project API
// ------------------------------------------------------------------
export const projectApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    get<PaginatedResponse<ProjectOut>>("/projects", params),
  create: (data: ProjectCreate) => post<ProjectOut>("/projects", data),
  get: (id: string) => get<ProjectOut>(`/projects/${id}`),
  update: (id: string, data: ProjectUpdate) => put<ProjectOut>(`/projects/${id}`, data),
  remove: (id: string) => del<ProjectOut>(`/projects/${id}`),
};

// ------------------------------------------------------------------
// Brief API
// ------------------------------------------------------------------
export const briefApi = {
  list: (params?: { page?: number; page_size?: number; project_id?: string; status?: string }) =>
    get<PaginatedResponse<BriefOut>>("/briefs", params),
  create: (data: BriefCreate) => post<BriefOut>("/briefs", data),
  get: (id: string) => get<BriefOut>(`/briefs/${id}`),
  update: (id: string, data: BriefUpdate) => put<BriefOut>(`/briefs/${id}`, data),
  remove: (id: string) => del<BriefOut>(`/briefs/${id}`),
  generatePRD: (id: string, data?: { generated_by?: string }) =>
    post<PRDOut>(`/briefs/${id}/generate-prd`, data),
  approve: (id: string, data?: { status?: "approved" | "rejected" }) =>
    post<BriefOut>(`/briefs/${id}/approve`, data),
};

// ------------------------------------------------------------------
// PRD API
// ------------------------------------------------------------------
export const prdApi = {
  list: (params?: { page?: number; page_size?: number; project_id?: string }) =>
    get<PaginatedResponse<PRDOut>>("/prds", params),
  create: (data: PRDCreate) => post<PRDOut>("/prds", data),
  get: (id: string) => get<PRDOut>(`/prds/${id}`),
  update: (id: string, data: PRDUpdate) => put<PRDOut>(`/prds/${id}`, data),
  remove: (id: string) => del<PRDOut>(`/prds/${id}`),
  generateTasks: (id: string) => post<{ message: string; tasks_count: number }>(`/prds/${id}/generate-tasks`),
};

// ------------------------------------------------------------------
// Task API
// ------------------------------------------------------------------
export const taskApi = {
  list: (params?: { page?: number; page_size?: number; project_id?: string; status?: string; assignee_id?: string }) =>
    get<PaginatedResponse<TaskOut>>("/tasks", params),
  create: (data: TaskCreate) => post<TaskOut>("/tasks", data),
  get: (id: string) => get<TaskOut>(`/tasks/${id}`),
  update: (id: string, data: TaskUpdate) => put<TaskOut>(`/tasks/${id}`, data),
  remove: (id: string) => del<TaskOut>(`/tasks/${id}`),
  tree: (projectId?: string) =>
    get<TaskTreeOut[]>("/tasks/tree", projectId ? { project_id: projectId } : undefined),
  next: () => get<TaskNext>("/tasks/next"),
  complexity: () => get<TaskComplexity>("/tasks/complexity"),
  expand: (id: string, count?: number) =>
    post<TaskOut[]>(`/tasks/${id}/expand`, { count: count ?? 3 }),
};

// ------------------------------------------------------------------
// Agent Run API
// ------------------------------------------------------------------
export const agentRunApi = {
  list: (params?: { page?: number; page_size?: number; project_id?: string; status?: string }) =>
    get<PaginatedResponse<AgentRunOut>>("/agent-runs", params),
  create: (data: AgentRunCreate) => post<AgentRunOut>("/agent-runs", data),
  get: (id: string) => get<AgentRunOut>(`/agent-runs/${id}`),
  logs: (id: string) => get<AgentRunLogs>(`/agent-runs/${id}/logs`),
};

// ------------------------------------------------------------------
// Knowledge API
// ------------------------------------------------------------------
export const knowledgeApi = {
  list: (params?: { page?: number; page_size?: number; project_id?: string; type?: string }) =>
    get<PaginatedResponse<KnowledgeItemOut>>("/knowledge", params),
  create: (data: KnowledgeItemCreate) => post<KnowledgeItemOut>("/knowledge", data),
  get: (id: string) => get<KnowledgeItemOut>(`/knowledge/${id}`),
  remove: (id: string) => del<KnowledgeItemOut>(`/knowledge/${id}`),
  search: (query: string, project_id?: string) =>
    get<KnowledgeSearchResult>("/knowledge/search", { query, project_id }),
};

// ------------------------------------------------------------------
// Audit API
// ------------------------------------------------------------------
export const auditApi = {
  logs: (params?: { page?: number; page_size?: number; resource_type?: string }) =>
    get<PaginatedResponse<AuditLogOut>>("/audit/logs", params),
};

// ------------------------------------------------------------------
// Integration API
// ------------------------------------------------------------------
export const integrationApi = {
  gitList: () => get<GitIntegration[]>("/integrations/git"),
  gitCreate: (data: GitIntegrationCreate) => post<GitIntegration>("/integrations/git", data),
};

// ------------------------------------------------------------------
// Type imports (forward declarations — actual types in types.ts)
// ------------------------------------------------------------------
import type {
  UserOut,
  TokenOut,
  ProjectOut,
  ProjectCreate,
  ProjectUpdate,
  BriefOut,
  BriefCreate,
  BriefUpdate,
  PRDOut,
  PRDCreate,
  PRDUpdate,
  TaskOut,
  TaskCreate,
  TaskUpdate,
  TaskTreeOut,
  TaskNext,
  TaskComplexity,
  AgentRunOut,
  AgentRunCreate,
  AgentRunLogs,
  KnowledgeItemOut,
  KnowledgeItemCreate,
  KnowledgeSearchResult,
  AuditLogOut,
  GitIntegration,
  GitIntegrationCreate,
  PaginatedResponse,
} from "./types";
