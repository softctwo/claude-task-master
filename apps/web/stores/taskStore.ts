import { create } from "zustand";
import { taskApi } from "@/lib/api";
import type {
  TaskOut,
  TaskCreate,
  TaskUpdate,
  TaskTreeOut,
  TaskNext,
  TaskComplexity,
  ApiError,
  PaginatedResponse,
} from "@/lib/types";

interface TaskState {
  tasks: TaskOut[];
  taskTree: TaskTreeOut[];
  currentTask: TaskOut | null;
  nextTask: TaskNext | null;
  complexity: TaskComplexity | null;
  total: number;
  page: number;
  pageSize: number;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isExpanding: boolean;
  error: string | null;

  // Actions
  fetchTasks: (params?: { page?: number; page_size?: number; project_id?: string; status?: string; assignee_id?: string }) => Promise<void>;
  fetchTaskTree: (projectId?: string) => Promise<void>;
  fetchNextTask: () => Promise<void>;
  fetchComplexity: () => Promise<void>;
  getTask: (id: string) => Promise<void>;
  createTask: (data: TaskCreate) => Promise<TaskOut>;
  updateTask: (id: string, data: TaskUpdate) => Promise<TaskOut>;
  deleteTask: (id: string) => Promise<void>;
  expandTask: (id: string, count?: number) => Promise<TaskOut[]>;
  setCurrentTask: (task: TaskOut | null) => void;
  clearError: () => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  taskTree: [],
  currentTask: null,
  nextTask: null,
  complexity: null,
  total: 0,
  page: 1,
  pageSize: 20,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isExpanding: false,
  error: null,

  fetchTasks: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const data: PaginatedResponse<TaskOut> = await taskApi.list(params);
      set({
        tasks: data.items,
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        isLoading: false,
      });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取任务列表失败", isLoading: false });
      throw err;
    }
  },

  fetchTaskTree: async (projectId?: string) => {
    set({ isLoading: true, error: null });
    try {
      const tree = await taskApi.tree(projectId);
      set({ taskTree: tree, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取任务树失败", isLoading: false });
      throw err;
    }
  },

  fetchNextTask: async () => {
    set({ isLoading: true, error: null });
    try {
      const next = await taskApi.next();
      set({ nextTask: next, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取下一个任务失败", isLoading: false });
      throw err;
    }
  },

  fetchComplexity: async () => {
    set({ isLoading: true, error: null });
    try {
      const complexity = await taskApi.complexity();
      set({ complexity, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取复杂度分析失败", isLoading: false });
      throw err;
    }
  },

  getTask: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const task = await taskApi.get(id);
      set({ currentTask: task, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取任务详情失败", isLoading: false });
      throw err;
    }
  },

  createTask: async (data: TaskCreate) => {
    set({ isCreating: true, error: null });
    try {
      const task = await taskApi.create(data);
      set((state) => ({
        tasks: [task, ...state.tasks],
        isCreating: false,
      }));
      return task;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "创建任务失败", isCreating: false });
      throw err;
    }
  },

  updateTask: async (id: string, data: TaskUpdate) => {
    set({ isUpdating: true, error: null });
    try {
      const task = await taskApi.update(id, data);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.task_id === id ? task : t)),
        currentTask: state.currentTask?.task_id === id ? task : state.currentTask,
        isUpdating: false,
      }));
      return task;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "更新任务失败", isUpdating: false });
      throw err;
    }
  },

  deleteTask: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await taskApi.remove(id);
      set((state) => ({
        tasks: state.tasks.filter((t) => t.task_id !== id),
        currentTask: state.currentTask?.task_id === id ? null : state.currentTask,
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "删除任务失败", isLoading: false });
      throw err;
    }
  },

  expandTask: async (id: string, count = 3) => {
    set({ isExpanding: true, error: null });
    try {
      const subtasks = await taskApi.expand(id, count);
      set({ isExpanding: false });
      return subtasks;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "展开任务失败", isExpanding: false });
      throw err;
    }
  },

  setCurrentTask: (task: TaskOut | null) => set({ currentTask: task }),
  clearError: () => set({ error: null }),
}));
