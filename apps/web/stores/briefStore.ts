import { create } from "zustand";
import { briefApi } from "@/lib/api";
import type { BriefOut, BriefCreate, BriefUpdate, ApiError, PaginatedResponse } from "@/lib/types";

interface BriefState {
  briefs: BriefOut[];
  currentBrief: BriefOut | null;
  total: number;
  page: number;
  pageSize: number;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isGenerating: boolean;
  error: string | null;

  // Actions
  fetchBriefs: (params?: { page?: number; page_size?: number; project_id?: string; status?: string }) => Promise<void>;
  getBrief: (id: string) => Promise<void>;
  createBrief: (data: BriefCreate) => Promise<BriefOut>;
  updateBrief: (id: string, data: BriefUpdate) => Promise<BriefOut>;
  deleteBrief: (id: string) => Promise<void>;
  generatePRD: (id: string, generatedBy?: string) => Promise<unknown>;
  approveBrief: (id: string, status: "approved" | "rejected") => Promise<BriefOut>;
  setCurrentBrief: (brief: BriefOut | null) => void;
  clearError: () => void;
}

export const useBriefStore = create<BriefState>((set) => ({
  briefs: [],
  currentBrief: null,
  total: 0,
  page: 1,
  pageSize: 20,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isGenerating: false,
  error: null,

  fetchBriefs: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const data: PaginatedResponse<BriefOut> = await briefApi.list(params);
      set({
        briefs: data.items,
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        isLoading: false,
      });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取 Brief 列表失败", isLoading: false });
      throw err;
    }
  },

  getBrief: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const brief = await briefApi.get(id);
      set({ currentBrief: brief, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "获取 Brief 详情失败", isLoading: false });
      throw err;
    }
  },

  createBrief: async (data: BriefCreate) => {
    set({ isCreating: true, error: null });
    try {
      const brief = await briefApi.create(data);
      set((state) => ({
        briefs: [brief, ...state.briefs],
        isCreating: false,
      }));
      return brief;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "创建 Brief 失败", isCreating: false });
      throw err;
    }
  },

  updateBrief: async (id: string, data: BriefUpdate) => {
    set({ isUpdating: true, error: null });
    try {
      const brief = await briefApi.update(id, data);
      set((state) => ({
        briefs: state.briefs.map((b) => (b.brief_id === id ? brief : b)),
        currentBrief: state.currentBrief?.brief_id === id ? brief : state.currentBrief,
        isUpdating: false,
      }));
      return brief;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "更新 Brief 失败", isUpdating: false });
      throw err;
    }
  },

  deleteBrief: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await briefApi.remove(id);
      set((state) => ({
        briefs: state.briefs.filter((b) => b.brief_id !== id),
        currentBrief: state.currentBrief?.brief_id === id ? null : state.currentBrief,
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "删除 Brief 失败", isLoading: false });
      throw err;
    }
  },

  generatePRD: async (id: string, generatedBy?: string) => {
    set({ isGenerating: true, error: null });
    try {
      const result = await briefApi.generatePRD(id, { generated_by: generatedBy });
      set({ isGenerating: false });
      return result;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "生成 PRD 失败", isGenerating: false });
      throw err;
    }
  },

  approveBrief: async (id: string, status: "approved" | "rejected") => {
    set({ isUpdating: true, error: null });
    try {
      const brief = await briefApi.approve(id, { status });
      set((state) => ({
        briefs: state.briefs.map((b) => (b.brief_id === id ? brief : b)),
        currentBrief: state.currentBrief?.brief_id === id ? brief : state.currentBrief,
        isUpdating: false,
      }));
      return brief;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || "审批 Brief 失败", isUpdating: false });
      throw err;
    }
  },

  setCurrentBrief: (brief: BriefOut | null) => set({ currentBrief: brief }),
  clearError: () => set({ error: null }),
}));
