"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, FileText, Clock, CheckCircle, Tag } from "lucide-react";
import Link from "next/link";
import apiClient from "@/lib/api";
import { GenerateTasksButton } from "@/app/components/GenerateTasksButton";
import ReactMarkdown from "react-markdown";

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

export default function PRDDetailPage() {
  const params = useParams();
  const prdId = params.id as string;

  const { data: prd, isLoading } = useQuery({
    queryKey: ["prd", prdId],
    queryFn: async () => {
      const res = await apiClient.get<PRD>(`/prds/${prdId}`);
      return res.data;
    },
    enabled: !!prdId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 rounded-full border-2 border-slate-200 border-t-slate-600 animate-spin" />
      </div>
    );
  }

  if (!prd) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">PRD not found</p>
      </div>
    );
  }

  const isApproved = !!prd.approved_at;
  const sourceColors: Record<string, string> = {
    ai_generated: "bg-indigo-100 text-indigo-700",
    manual: "bg-slate-100 text-slate-700",
    imported: "bg-amber-100 text-amber-700",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/briefs"
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
          >
            <ArrowLeft size={18} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">PRD</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", sourceColors[prd.source] || "bg-slate-100 text-slate-700")}>
                {prd.source}
              </span>
              <span className="text-xs text-slate-400">v{prd.version}</span>
              {isApproved && (
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-100 text-emerald-700">
                  Approved
                </span>
              )}
            </div>
          </div>
        </div>
        <GenerateTasksButton
          prdId={prdId}
          prdContent={prd.content_markdown}
        />
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - PRD Markdown */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="prose prose-slate max-w-none">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-2xl font-bold text-slate-900 mt-8 mb-4">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl font-semibold text-slate-800 mt-6 mb-3">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-semibold text-slate-700 mt-4 mb-2">{children}</h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-sm text-slate-600 leading-relaxed mb-4">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside text-sm text-slate-600 mb-4 space-y-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside text-sm text-slate-600 mb-4 space-y-1">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="text-sm text-slate-600">{children}</li>
                  ),
                  code: ({ children }) => (
                    <code className="bg-slate-100 text-slate-800 px-1 py-0.5 rounded text-xs font-mono">
                      {children}
                    </code>
                  ),
                  pre: ({ children }) => (
                    <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-sm mb-4">
                      {children}
                    </pre>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-indigo-300 pl-4 italic text-slate-500 mb-4">
                      {children}
                    </blockquote>
                  ),
                  hr: () => <hr className="border-slate-200 my-6" />,
                }}
              >
                {prd.content_markdown}
              </ReactMarkdown>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Source</span>
                <span className={cn("px-2 py-0.5 rounded text-xs font-medium", sourceColors[prd.source] || "bg-slate-100 text-slate-700")}>
                  {prd.source}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Version</span>
                <span className="text-slate-700">{prd.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Generated By</span>
                <span className="text-slate-700">{prd.generated_by || "Manual"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span className="text-slate-700">{new Date(prd.created_at).toLocaleDateString()}</span>
              </div>
              {prd.approved_at && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Approved</span>
                  <span className="text-slate-700">{new Date(prd.approved_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Actions</h3>
            <div className="space-y-2">
              <GenerateTasksButton
                prdId={prdId}
                prdContent={prd.content_markdown}
                variant="outline"
                size="sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import { cn } from "@/lib/utils";
