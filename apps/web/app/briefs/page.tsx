"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashboardLayout from "../dashboard/layout";
import { useBriefStore } from "@/stores/briefStore";
import { useUIStore } from "@/stores/uiStore";
import type { BriefStatus } from "@/lib/types";

const statusColorMap: Record<BriefStatus, string> = {
  draft: "bg-slate-50 text-slate-600 border-slate-100",
  reviewing: "bg-amber-50 text-amber-700 border-amber-100",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-100",
  rejected: "bg-red-50 text-red-700 border-red-100",
  archived: "bg-slate-50 text-slate-400 border-slate-100",
};

const statusLabelMap: Record<BriefStatus, string> = {
  draft: "草稿",
  reviewing: "评审中",
  approved: "已审批",
  rejected: "已拒绝",
  archived: "已归档",
};

const columns: { status: BriefStatus; label: string }[] = [
  { status: "draft", label: "草稿" },
  { status: "reviewing", label: "评审中" },
  { status: "approved", label: "已审批" },
];

export default function BriefsPage() {
  const { briefs, isLoading, fetchBriefs, approveBrief, generatePRD } = useBriefStore();
  const addToast = useUIStore((s) => s.addToast);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  useEffect(() => {
    fetchBriefs().catch(() => addToast("获取 Brief 列表失败", "error"));
  }, [fetchBriefs, addToast]);

  const handleApprove = async (id: string, status: "approved" | "rejected") => {
    setApprovingId(id);
    try {
      await approveBrief(id, status);
      addToast(`Brief 已${status === "approved" ? "审批通过" : "拒绝"}`, "success");
    } catch {
      addToast("审批操作失败", "error");
    } finally {
      setApprovingId(null);
    }
  };

  const handleGeneratePRD = async (id: string) => {
    setGeneratingId(id);
    try {
      await generatePRD(id);
      addToast("PRD 生成已触发", "success");
    } catch {
      addToast("生成 PRD 失败", "error");
    } finally {
      setGeneratingId(null);
    }
  };

  const briefsByStatus = (status: BriefStatus) =>
    briefs.filter((b) => b.status === status);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Briefs</h1>
            <p className="text-slate-500 mt-1">需求澄清和产品意图</p>
          </div>
          <Link
            href="/briefs/new"
            className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            创建 Brief
          </Link>
        </div>

        {/* Kanban Board */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
                <div className="h-5 w-20 bg-slate-200 rounded animate-pulse" />
                {[1, 2].map((j) => (
                  <div key={j} className="h-24 bg-slate-100 rounded-lg animate-pulse" />
                ))}
              </div>
            ))}
          </div>
        ) : briefs.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-500">
            <p>暂无 Brief</p>
            <p className="text-sm mt-1">点击「创建 Brief」开始记录需求</p>
            <Link
              href="/briefs/new"
              className="inline-block mt-4 px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800"
            >
              创建 Brief
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {columns.map((col) => (
              <div key={col.status} className="bg-white rounded-lg border border-slate-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-900">{col.label}</h3>
                  <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                    {briefsByStatus(col.status).length}
                  </span>
                </div>
                <div className="space-y-2 min-h-[120px]">
                  {briefsByStatus(col.status).length === 0 ? (
                    <p className="text-sm text-slate-400 text-center py-4">暂无</p>
                  ) : (
                    briefsByStatus(col.status).map((brief) => (
                      <div
                        key={brief.brief_id}
                        className="p-3 rounded-lg border border-slate-100 hover:border-slate-200 hover:shadow-sm transition-all group"
                      >
                        <Link href={`/briefs/${brief.brief_id}`}>
                          <p className="font-medium text-slate-900 text-sm line-clamp-2 hover:text-slate-700">
                            {brief.title}
                          </p>
                        </Link>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <span className={`text-xs px-1.5 py-0.5 rounded border ${statusColorMap[brief.status]}`}>
                            v{brief.version}
                          </span>
                          {brief.goals.length > 0 && (
                            <span className="text-xs text-slate-400">{brief.goals.length} 个目标</span>
                          )}
                        </div>
                        {/* Actions */}
                        <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          {brief.status === "reviewing" && (
                            <>
                              <button
                                onClick={() => handleApprove(brief.brief_id, "approved")}
                                disabled={approvingId === brief.brief_id}
                                className="text-xs px-2 py-1 bg-emerald-50 text-emerald-700 rounded hover:bg-emerald-100 disabled:opacity-50"
                              >
                                通过
                              </button>
                              <button
                                onClick={() => handleApprove(brief.brief_id, "rejected")}
                                disabled={approvingId === brief.brief_id}
                                className="text-xs px-2 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100 disabled:opacity-50"
                              >
                                拒绝
                              </button>
                            </>
                          )}
                          {brief.status === "approved" && (
                            <button
                              onClick={() => handleGeneratePRD(brief.brief_id)}
                              disabled={generatingId === brief.brief_id}
                              className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 disabled:opacity-50"
                            >
                              {generatingId === brief.brief_id ? "生成中..." : "生成 PRD"}
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
