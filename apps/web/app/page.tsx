"use client";

import { useEffect } from "react";
import Link from "next/link";
import DashboardLayout from "./dashboard/layout";
import { useProjectStore } from "@/stores/projectStore";
import { useTaskStore } from "@/stores/taskStore";
import { useBriefStore } from "@/stores/briefStore";
import { useUIStore } from "@/stores/uiStore";
import type { ProjectStatus, TaskStatus } from "@/lib/types";

const statusColorMap: Record<ProjectStatus | TaskStatus, string> = {
  active: "bg-blue-50 text-blue-700 border-blue-100",
  archived: "bg-slate-50 text-slate-600 border-slate-100",
  paused: "bg-amber-50 text-amber-700 border-amber-100",
  pending: "bg-amber-50 text-amber-700 border-amber-100",
  in_progress: "bg-emerald-50 text-emerald-700 border-emerald-100",
  completed: "bg-slate-50 text-slate-600 border-slate-100",
  blocked: "bg-red-50 text-red-700 border-red-100",
  cancelled: "bg-slate-50 text-slate-400 border-slate-100",
};

const statusLabelMap: Record<string, string> = {
  active: "活跃",
  archived: "归档",
  paused: "暂停",
  pending: "待办",
  in_progress: "进行中",
  completed: "已完成",
  blocked: "阻塞",
  cancelled: "已取消",
};

export default function DashboardPage() {
  const { projects, isLoading: projectsLoading, fetchProjects } = useProjectStore();
  const { tasks, isLoading: tasksLoading, fetchTasks } = useTaskStore();
  const { briefs, isLoading: briefsLoading, fetchBriefs } = useBriefStore();
  const addToast = useUIStore((s) => s.addToast);

  useEffect(() => {
    fetchProjects({ page_size: 5 }).catch(() => addToast("获取项目数据失败", "error"));
    fetchTasks({ page_size: 100 }).catch(() => addToast("获取任务数据失败", "error"));
    fetchBriefs({ page_size: 5 }).catch(() => addToast("获取 Brief 数据失败", "error"));
  }, [fetchProjects, fetchTasks, fetchBriefs, addToast]);

  const activeProjects = projects.filter((p) => p.status === "active").length;
  const pendingTasks = tasks.filter((t) => t.status === "pending").length;
  const inProgressTasks = tasks.filter((t) => t.status === "in_progress").length;
  const completedTasks = tasks.filter((t) => t.status === "completed").length;

  const isLoading = projectsLoading || tasksLoading || briefsLoading;

  const stats = [
    { label: "活跃项目", value: activeProjects.toString(), color: "bg-blue-50 text-blue-700" },
    { label: "待办任务", value: pendingTasks.toString(), color: "bg-amber-50 text-amber-700" },
    { label: "进行中", value: inProgressTasks.toString(), color: "bg-emerald-50 text-emerald-700" },
    { label: "已完成", value: completedTasks.toString(), color: "bg-slate-50 text-slate-700" },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">仪表盘</h1>
          <p className="text-slate-500 mt-1">概览项目交付状态</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div key={stat.label} className={`p-4 rounded-lg border ${stat.color} border-opacity-10`}>
              {isLoading ? (
                <div className="animate-pulse">
                  <div className="h-8 w-12 bg-current opacity-10 rounded" />
                  <div className="h-4 w-20 bg-current opacity-10 rounded mt-2" />
                </div>
              ) : (
                <>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-sm mt-1 opacity-80">{stat.label}</p>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Recent Projects */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">最近项目</h2>
            <Link href="/projects" className="text-sm text-slate-600 hover:text-slate-900 font-medium">
              查看全部 →
            </Link>
          </div>

          {projectsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse flex items-center gap-3 p-3 rounded-lg border border-slate-100">
                  <div className="h-10 w-10 bg-slate-200 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-1/3 bg-slate-200 rounded" />
                    <div className="h-3 w-1/4 bg-slate-200 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <p>暂无项目</p>
              <p className="text-sm mt-1">请先创建一个项目开始工作</p>
              <Link
                href="/projects"
                className="inline-block mt-4 px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800"
              >
                创建项目
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {projects.slice(0, 5).map((project) => (
                <Link
                  key={project.project_id}
                  href={`/projects`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100"
                >
                  <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500 font-semibold text-sm">
                    {project.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900 truncate">{project.name}</p>
                    <p className="text-sm text-slate-500 truncate">{project.description || "暂无描述"}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full border ${statusColorMap[project.status]}`}>
                    {statusLabelMap[project.status]}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent Briefs */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">最近 Briefs</h2>
            <Link href="/briefs" className="text-sm text-slate-600 hover:text-slate-900 font-medium">
              查看全部 →
            </Link>
          </div>

          {briefsLoading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="animate-pulse h-16 bg-slate-100 rounded-lg" />
              ))}
            </div>
          ) : briefs.length === 0 ? (
            <p className="text-slate-500 text-sm text-center py-4">暂无 Brief</p>
          ) : (
            <div className="space-y-2">
              {briefs.slice(0, 5).map((brief) => (
                <div
                  key={brief.brief_id}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-slate-900 truncate">{brief.title}</p>
                    <p className="text-sm text-slate-500">版本 {brief.version}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full border ${statusColorMap[brief.status]}`}>
                    {statusLabelMap[brief.status] || brief.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
