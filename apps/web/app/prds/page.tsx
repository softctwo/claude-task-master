"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, Plus, Search } from "lucide-react";
import Link from "next/link";
import apiClient from "@/lib/api";
import { GenerateTasksInlineButton } from "@/app/components/GenerateTasksButton";

interface PRD {
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

interface PRDListResponse {
  total: number;
  page: number;
  page_size: number;
  pages: number;
  items: PRD[];
}

export default function PRDsListPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["prds", page],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", "20");
      const res = await apiClient.get<PRDListResponse>(`/prds?${params}`);
      return res.data;
    },
  });

  const sourceColors: Record<string, string> = {
    ai_generated: "bg-indigo-100 text-indigo-700",
    manual: "bg-slate-100 text-slate-700",
    imported: "bg-amber-100 text-amber-700",
  };

  // Extract title from markdown
  const extractTitle = (markdown: string): string => {
    const match = markdown.match(/^#\s+(.+)$/m);
    return match ? match[1] : "Untitled PRD";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">PRDs</h1>
          <p className="text-slate-500 mt-1">Product Requirements Documents</p>
        </div>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 rounded-full border-2 border-slate-200 border-t-slate-600 animate-spin" />
        </div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <FileText size={32} className="mx-auto text-slate-300 mb-3" />
          <p className="text-slate-500">No PRDs found</p>
          <p className="text-slate-400 text-sm mt-1">
            Generate a PRD from an approved brief
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="divide-y divide-slate-100">
            {data?.items.map((prd) => (
              <div
                key={prd.prd_id}
                className="p-4 hover:bg-slate-50 transition-colors flex items-center justify-between"
              >
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/prds/${prd.prd_id}`}
                    className="text-sm font-medium text-slate-900 hover:text-indigo-600 transition-colors"
                  >
                    {extractTitle(prd.content_markdown)}
                  </Link>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={cn("text-xs px-1.5 py-0.5 rounded font-medium", sourceColors[prd.source] || "bg-slate-100 text-slate-700")}>
                      {prd.source}
                    </span>
                    <span className="text-xs text-slate-400">v{prd.version}</span>
                    {prd.approved_at && (
                      <span className="text-xs px-1.5 py-0.5 rounded font-medium bg-emerald-100 text-emerald-700">
                        Approved
                      </span>
                    )}
                    <span className="text-xs text-slate-400">
                      {new Date(prd.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <GenerateTasksInlineButton prdId={prd.prd_id} />
                  <Link
                    href={`/prds/${prd.prd_id}`}
                    className="text-xs text-indigo-600 hover:text-indigo-700 px-2 py-1 rounded hover:bg-indigo-50 transition-colors"
                  >
                    View
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Page {data.page} of {data.pages} ({data.total} total)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page >= data.pages}
                  className="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import { cn } from "@/lib/utils";
