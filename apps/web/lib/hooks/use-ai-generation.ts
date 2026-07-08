"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import { useAIGenerationStore } from "@/lib/store/ai-store";

// ── Types ──

export interface GeneratePRDRequest {
  generated_by?: string;
  model?: string;
}

export interface GenerateTasksRequest {
  model?: string;
}

export interface PRD {
  prd_id: string;
  brief_id: string;
  project_id: string;
  content_markdown: string;
  source: string;
  version: number;
  generated_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  task_id: string;
  project_id: string;
  title: string;
  description: string | null;
  details: string | null;
  test_strategy: string | null;
  priority: "low" | "medium" | "high" | "critical";
  complexity_score: number | null;
  dependencies: string[];
  status: "pending" | "in_progress" | "completed" | "blocked" | "cancelled";
  taskmaster_task_id: string | null;
  parent_task_id: string | null;
  assignee_id: string | null;
  source_prd_id: string | null;
  source_brief_id: string | null;
  created_at: string;
  updated_at: string;
}

// ── Mutations ──

export function useGeneratePRD() {
  const queryClient = useQueryClient();
  const setGenerating = useAIGenerationStore((s) => s.setGeneratingPRD);

  return useMutation({
    mutationFn: async ({
      briefId,
      data,
    }: {
      briefId: string;
      data?: GeneratePRDRequest;
    }) => {
      setGenerating(true);
      try {
        const res = await apiClient.post<PRD>(
          `/briefs/${briefId}/generate-prd`,
          data || {}
        );
        return res.data;
      } finally {
        setGenerating(false);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prds"] });
      queryClient.invalidateQueries({ queryKey: ["briefs"] });
    },
  });
}

export function useGenerateTasks() {
  const queryClient = useQueryClient();
  const setGenerating = useAIGenerationStore((s) => s.setGeneratingTasks);

  return useMutation({
    mutationFn: async ({
      prdId,
      data,
    }: {
      prdId: string;
      data?: GenerateTasksRequest;
    }) => {
      setGenerating(true);
      try {
        const res = await apiClient.post<Task[]>(
          `/prds/${prdId}/generate-tasks`,
          data || {}
        );
        return res.data;
      } finally {
        setGenerating(false);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["prds"] });
    },
  });
}

// ── Streaming PRD Generation ──

export function useStreamGeneratePRD() {
  const store = useAIGenerationStore();

  const startStream = async (
    briefId: string,
    data?: GeneratePRDRequest
  ): Promise<string> => {
    store.resetStream();
    store.setStreaming(true);

    const token = localStorage.getItem("access_token");
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const url = `${API_BASE_URL}/api/v1/briefs/${briefId}/generate-prd-stream`;

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      let accumulated = "";

      xhr.open("POST", url, true);
      xhr.setRequestHeader("Content-Type", "application/json");
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }

      xhr.onprogress = () => {
        const responseText = xhr.responseText;
        // Parse SSE events from the accumulated response
        const newText = responseText.substring(accumulated.length);
        accumulated = responseText;

        // Parse SSE data lines
        const lines = newText.split("\n");
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            const data = trimmed.slice(6).trim();
            if (data === "[DONE]") {
              store.setStreaming(false);
              resolve(store.streamContent);
            } else if (data.startsWith("[ERROR]")) {
              store.setStreamError(data.slice(8).trim());
              store.setStreaming(false);
              reject(new Error(data.slice(8).trim()));
            } else {
              store.appendStreamContent(data);
            }
          }
        }
      };

      xhr.onerror = () => {
        store.setStreaming(false);
        store.setStreamError("Network error during streaming");
        reject(new Error("Network error during streaming"));
      };

      xhr.onabort = () => {
        store.setStreaming(false);
      };

      xhr.onload = () => {
        store.setStreaming(false);
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(store.streamContent);
        } else {
          const errorMsg = `HTTP ${xhr.status}: ${xhr.statusText}`;
          store.setStreamError(errorMsg);
          reject(new Error(errorMsg));
        }
      };

      xhr.send(JSON.stringify(data || {}));
    });
  };

  return { startStream, ...store };
}
