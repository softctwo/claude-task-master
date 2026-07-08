import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authApi } from "@/lib/api";
import type { UserOut, TokenOut, ApiError } from "@/lib/types";

interface AuthState {
  user: UserOut | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string, role?: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const data: TokenOut = await authApi.login({ email, password });
          if (typeof window !== "undefined") {
            localStorage.setItem("access_token", data.access_token);
          }
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const error = err as ApiError;
          set({
            error: error.message || "登录失败，请检查邮箱和密码",
            isLoading: false,
            isAuthenticated: false,
          });
          throw err;
        }
      },

      register: async (email: string, name: string, password: string, role = "developer") => {
        set({ isLoading: true, error: null });
        try {
          const data: TokenOut = await authApi.register({ email, name, password, role });
          if (typeof window !== "undefined") {
            localStorage.setItem("access_token", data.access_token);
          }
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const error = err as ApiError;
          set({
            error: error.message || "注册失败",
            isLoading: false,
          });
          throw err;
        }
      },

      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
        }
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      fetchMe: async () => {
        const token = get().token;
        if (!token) return;
        set({ isLoading: true });
        try {
          const user = await authApi.me();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (err) {
          const error = err as ApiError;
          if (error.status === 401) {
            get().logout();
          }
          set({ isLoading: false });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ token: state.token }),
    }
  )
);
