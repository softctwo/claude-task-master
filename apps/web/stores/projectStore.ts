import { create } from "zustand";
import { projectApi } from "@/lib/api";
import type { ProjectOut, ProjectCreate, ProjectUpdate, ApiError, PaginatedResponse } from "@/lib/types";

interface ProjectState {
  projects: ProjectOut[];
  currentProject: ProjectOut | null;
  total: number;
  page: number;
  pageSize: number;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  error: string | null;

  // Actions
  fetchProjects: (params?: { page?: number; page_size?: number; status?: string }) => Promise<void>;
  getProject: (id: string) => Promise<void>;
  createProject: (data: ProjectCreate) => Promise<ProjectOut>;
  updateProject: (id: string, data: ProjectUpdate) => Promise<ProjectOut>;
  deleteProject: (id: string) => Promise<void>;
  setCurrentProject: (project: ProjectOut | null) => void;
  clearError: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  total: 0,
  page: 1,
  pageSize: 20,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  error: null,

  fetchProjects: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const data: PaginatedResponse<ProjectOut> = await projectApi.list(params);
      set({
        projects: data.items,
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        isLoading: false,
      });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取项目列表失败", isLoading: false });
      throw err;
    }
  },

  getProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectApi.get(id);
      set({ currentProject: project, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取项目详情失败", isLoading: false });
      throw err;
    }
  },

  createProject: async (data: ProjectCreate) => {
    set({ isCreating: true, error: null });
    try {
      const project = await projectApi.create(data);
      set((state) => ({
        projects: [project, ...state.projects],
        isCreating: false,
      }));
      return project;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "创建项目失败", isCreating: false });
      throw err;
    }
  },

  updateProject: async (id: string, data: ProjectUpdate) => {
    set({ isUpdating: true, error: null });
    try {
      const project = await projectApi.update(id, data);
      set((state) => ({
        projects: state.projects.map((p) => (p.project_id === id ? project : p)),
        currentProject: state.currentProject?.project_id === id ? project : state.currentProject,
        isUpdating: false,
      }));
      return project;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "更新项目失败", isUpdating: false });
      throw err;
    }
  },

  deleteProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await projectApi.remove(id);
      set((state) => ({
        projects: state.projects.filter((p) => p.project_id !== id),
        currentProject: state.currentProject?.project_id === id ? null : state.currentProject,
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "删除项目失败", isLoading: false });
      throw err;
    }
  },

  setCurrentProject: (project: ProjectOut | null) => set({ currentProject: project }),
  clearError: () => set({ error: null }),
}));
