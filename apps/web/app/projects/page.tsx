"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashboardLayout from "../dashboard/layout";
import { useProjectStore } from "@/stores/projectStore";
import { useUIStore } from "@/stores/uiStore";
import type { ProjectStatus } from "@/lib/types";

const statusColorMap: Record<ProjectStatus, string> = {
  active: "bg-blue-50 text-blue-700 border-blue-100",
  archived: "bg-slate-50 text-slate-600 border-slate-100",
  paused: "bg-amber-50 text-amber-700 border-amber-100",
};

const statusLabelMap: Record<ProjectStatus, string> = {
  active: "活跃",
  archived: "归档",
  paused: "暂停",
};

export default function ProjectsPage() {
  const { projects, total, isLoading, fetchProjects, deleteProject } = useProjectStore();
  const addToast = useUIStore((s) => s.addToast);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | "all">("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects().catch(() => addToast("获取项目列表失败", "error"));
  }, [fetchProjects, addToast]);

  const filteredProjects = projects.filter((p) => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.description?.toLowerCase() || "").includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除此项目吗？此操作不可撤销。")) return;
    setDeletingId(id);
    try {
      await deleteProject(id);
      addToast("项目已删除", "success");
    } catch {
      addToast("删除项目失败", "error");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">项目</h1>
            <p className="text-slate-500 mt-1">管理所有研发项目</p>
          </div>
          <Link
            href="/projects/new"
            className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            创建项目
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex gap-2 flex-wrap">
            <input
              type="text"
              placeholder="搜索项目..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1 min-w-[200px] px-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ProjectStatus | "all")}
              className="px-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
            >
              <option value="all">全部状态</option>
              <option value="active">活跃</option>
              <option value="paused">暂停</option>
              <option value="archived">归档</option>
            </select>
          </div>
        </div>

        {/* Project List */}
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          {isLoading ? (
            <div className="p-8 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse flex items-center gap-4 p-4 border-b border-slate-100 last:border-0">
                  <div className="h-12 w-12 bg-slate-200 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-1/3 bg-slate-200 rounded" />
                    <div className="h-3 w-1/2 bg-slate-200 rounded" />
                  </div>
                  <div className="h-8 w-20 bg-slate-200 rounded" />
                </div>
              ))}
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              {search || statusFilter !== "all" ? (
                <>
                  <p>没有匹配的项目</p>
                  <p className="text-sm mt-1">尝试调整搜索条件</p>
                </>
              ) : (
                <>
                  <p>暂无项目</p>
                  <p className="text-sm mt-1">点击「创建项目」开始</p>
                  <Link
                    href="/projects/new"
                    className="inline-block mt-4 px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800"
                  >
                    创建项目
                  </Link>
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filteredProjects.map((project) => (
                <div
                  key={project.project_id}
                  className="flex items-center gap-4 p-4 hover:bg-slate-50 transition-colors group"
                >
                  <div className="h-12 w-12 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500 font-semibold text-sm shrink-0">
                    {project.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <Link
                      href={`/projects/${project.project_id}`}
                      className="font-medium text-slate-900 hover:text-slate-700 truncate block"
                    >
                      {project.name}
                    </Link>
                    <p className="text-sm text-slate-500 truncate">
                      {project.description || "暂无描述"}
                      {project.repo_url && (
                        <span className="ml-2 text-slate-400">· {project.repo_url}</span>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`text-xs px-2.5 py-1 rounded-full border ${statusColorMap[project.status]}`}>
                      {statusLabelMap[project.status]}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(project.created_at).toLocaleDateString("zh-CN")}
                    </span>
                    <button
                      onClick={() => handleDelete(project.project_id)}
                      disabled={deletingId === project.project_id}
                      className="opacity-0 group-hover:opacity-100 px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded transition-all disabled:opacity-50"
                    >
                      {deletingId === project.project_id ? "删除中..." : "删除"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination info */}
        {!isLoading && filteredProjects.length > 0 && (
          <p className="text-sm text-slate-500 text-center">
            共 {total} 个项目
            {(search || statusFilter !== "all") && `，显示 ${filteredProjects.length} 个`}
          </p>
        )}
      </div>
    </DashboardLayout>
  );
}
