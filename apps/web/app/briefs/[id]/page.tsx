"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, FileText, Clock, User, Tag, CheckCircle } from "lucide-react";
import Link from "next/link";
import apiClient from "@/lib/api";
import { GeneratePRDButton } from "@/app/components/GeneratePRDButton";
import { StreamingOutput } from "@/app/components/StreamingOutput";
import { useAIGenerationStore } from "@/lib/store/ai-store";

interface Brief {
  brief_id: string;
  project_id: string;
  title: string;
  background: string | null;
  problem_statement: string | null;
  target_users: string | null;
  goals: string[];
  non_goals: string[];
  scope: string | null;
  user_stories: string[];
  acceptance_criteria: string[];
  constraints: string | null;
  status: string;
  owner_id: string;
  reviewer_ids: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export default function BriefDetailPage() {
  const params = useParams();
  const briefId = params.id as string;
  const [showStream, setShowStream] = useState(false);
  const streamContent = useAIGenerationStore((s) => s.streamContent);
  const isStreaming = useAIGenerationStore((s) => s.isStreaming);
  const streamError = useAIGenerationStore((s) => s.streamError);

  const { data: brief, isLoading } = useQuery({
    queryKey: ["brief", briefId],
    queryFn: async () => {
      const res = await apiClient.get<Brief>(`/briefs/${briefId}`);
      return res.data;
    },
    enabled: !!briefId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 rounded-full border-2 border-slate-200 border-t-slate-600 animate-spin" />
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Brief not found</p>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    draft: "bg-slate-100 text-slate-700",
    reviewing: "bg-amber-100 text-amber-700",
    approved: "bg-emerald-100 text-emerald-700",
    rejected: "bg-red-100 text-red-700",
    archived: "bg-slate-100 text-slate-500",
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
            <h1 className="text-2xl font-bold text-slate-900">{brief.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", statusColors[brief.status])}>
                {brief.status}
              </span>
              <span className="text-xs text-slate-400">v{brief.version}</span>
            </div>
          </div>
        </div>
        <GeneratePRDButton
          briefId={briefId}
          briefStatus={brief.status}
          onSuccess={() => setShowStream(true)}
        />
      </div>

      {/* Streaming Output */}
      {showStream && (
        <StreamingOutput
          content={streamContent}
          isLoading={isStreaming}
          error={streamError}
          title="Generated PRD Preview"
          onClose={() => setShowStream(false)}
        />
      )}

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {brief.background && (
            <Section title="Background" icon={FileText}>
              <p className="text-sm text-slate-600 leading-relaxed">{brief.background}</p>
            </Section>
          )}

          {brief.problem_statement && (
            <Section title="Problem Statement" icon={FileText}>
              <p className="text-sm text-slate-600 leading-relaxed">{brief.problem_statement}</p>
            </Section>
          )}

          {brief.target_users && (
            <Section title="Target Users" icon={User}>
              <p className="text-sm text-slate-600 leading-relaxed">{brief.target_users}</p>
            </Section>
          )}

          {brief.goals.length > 0 && (
            <Section title="Goals" icon={CheckCircle}>
              <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                {brief.goals.map((goal, i) => (
                  <li key={i}>{goal}</li>
                ))}
              </ul>
            </Section>
          )}

          {brief.non_goals.length > 0 && (
            <Section title="Non-Goals" icon={Tag}>
              <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                {brief.non_goals.map((goal, i) => (
                  <li key={i}>{goal}</li>
                ))}
              </ul>
            </Section>
          )}

          {brief.scope && (
            <Section title="Scope" icon={FileText}>
              <p className="text-sm text-slate-600 leading-relaxed">{brief.scope}</p>
            </Section>
          )}

          {brief.user_stories.length > 0 && (
            <Section title="User Stories" icon={User}>
              <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                {brief.user_stories.map((story, i) => (
                  <li key={i}>{story}</li>
                ))}
              </ul>
            </Section>
          )}

          {brief.acceptance_criteria.length > 0 && (
            <Section title="Acceptance Criteria" icon={CheckCircle}>
              <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                {brief.acceptance_criteria.map((criteria, i) => (
                  <li key={i}>{criteria}</li>
                ))}
              </ul>
            </Section>
          )}

          {brief.constraints && (
            <Section title="Constraints" icon={Tag}>
              <p className="text-sm text-slate-600 leading-relaxed">{brief.constraints}</p>
            </Section>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Status</span>
                <span className={cn("px-2 py-0.5 rounded text-xs font-medium", statusColors[brief.status])}>
                  {brief.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Version</span>
                <span className="text-slate-700">{brief.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span className="text-slate-700">{new Date(brief.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Updated</span>
                <span className="text-slate-700">{new Date(brief.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          {brief.status === "approved" && (
            <div className="bg-emerald-50 rounded-lg border border-emerald-200 p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle size={16} className="text-emerald-600" />
                <h3 className="text-sm font-semibold text-emerald-800">Ready for PRD</h3>
              </div>
              <p className="text-xs text-emerald-600 mb-3">
                This brief is approved. You can generate a PRD using AI.
              </p>
              <GeneratePRDButton
                briefId={briefId}
                briefStatus={brief.status}
                variant="outline"
                size="sm"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={16} className="text-slate-400" />
        <h2 className="text-sm font-semibold text-slate-700">{title}</h2>
      </div>
      {children}
    </div>
  );
}

import { cn } from "@/lib/utils";
