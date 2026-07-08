"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashboardLayout from "../dashboard/layout";
import { useTaskStore } from "@/stores/taskStore";
import { useUIStore } from "@/stores/uiStore";
import type { TaskStatus, TaskPriority } from "@/lib/types";

type ViewMode = "kanban" | "list" | "tree";

const statusColorMap: Record<TaskStatus, string> = {
  pending: "bg-amber-50 text-amber-700 border-amber-100",
  in_progress: "bg-blue-50 text-blue-700 border-blue-100",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-100",
  blocked: "bg-red-50 text-red-700 border-red-100",
  cancelled: "bg-slate-50 text-slate-400 border-slate-100",
};

const statusLabelMap: Record<TaskStatus, string> = {
  pending: "待办",
  in_progress: "进行中",
  completed: "已完成",
  blocked: "阻塞",
  cancelled: "已取消",
};

const priorityColorMap: Record<TaskPriority, string> = {
  low: "text-slate-400",
  medium: "text-amber-600",
  high: "text-orange-600",
  critical: "text-red-600",
};

const priorityLabelMap: Record<TaskPriority, string> = {
  low: "低",
  medium: "中",
  high: "高",
  critical: "紧急",
};

const kanbanColumns: { status: TaskStatus; label: string }[] = [
  { status: "pending", label: "待办" },
  { status: "in_progress", label: "进行中" },
  { status: "completed", label: "已完成" },
  { status: "blocked", label: "阻塞" },
];

export default function TasksPage() {
  const { tasks, isLoading, fetchTasks, updateTask, deleteTask } = useTaskStore();
  const addToast = useUIStore((s) => s.addToast);
  const [viewMode, setViewMode] = useState<ViewMode>("kanban");
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks().catch(() => addToast("获取任务列表失败", "error"));
  }, [fetchTasks, addToast]);

  const handleStatusChange = async (id: string, status: TaskStatus) => {
    setUpdatingId(id);
    try {
      await updateTask(id, { status });
      addToast(`任务状态已更新为「${statusLabelMap[status]}」`, "success");
    } catch {
      addToast("更新任务状态失败", "error");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除此任务吗？")) return;
    setDeletingId(id);
    try {
      await deleteTask(id);
      addToast("任务已删除", "success");
    } catch {
      addToast("删除任务失败", "error");
    } finally {
      setDeletingId(null);
    }
  };

  const tasksByStatus = (status: TaskStatus) => tasks.filter((t) => t.status === status);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">任务</h1>
            <p className="text-slate-500 mt-1">任务树、看板和依赖管理</p>
          </div>
          <Link
            href="/tasks/new"
            className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            创建任务
          </Link>
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 border-b border-slate-200 pb-2">
          {[
            { key: "kanban" as ViewMode, label: "看板" },
            { key: "list" as ViewMode, label: "列表" },
            { key: "tree" as ViewMode, label: "树形" },
          ].map((v) => (
            <button
              key={v.key}
              onClick={() => setViewMode(v.key)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                viewMode === v.key
                  ? "bg-slate-100 text-slate-900 font-medium"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              {v.label}
            </button>
          ))}
        </div>

        {/* Kanban View */}
        {viewMode === "kanban" && (
          <>
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
                    <div className="h-5 w-16 bg-slate-200 rounded animate-pulse" />
                    <div className="h-32 bg-slate-100 rounded-lg animate-pulse" />
                  </div>
                ))}
              </div>
            ) : tasks.length === 0 ? (
              <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-500">
                <p>暂无任务</p>
                <p className="text-sm mt-1">点击「创建任务」开始管理工作</p>
                <Link
                  href="/tasks/new"
                  className="inline-block mt-4 px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800"
                >
                  创建任务
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {kanbanColumns.map((col) => (
                  <div key={col.status} className="bg-white rounded-lg border border-slate-200 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-slate-900">{col.label}</h3>
                      <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                        {tasksByStatus(col.status).length}
                      </span>
                    </div>
                    <div className="space-y-2 min-h-[120px]">
                      {tasksByStatus(col.status).length === 0 ? (
                        <p className="text-sm text-slate-400 text-center py-4">暂无</p>
                      ) : (
                        tasksByStatus(col.status).map((task) => (
                          <div
                            key={task.task_id}
                            className="p-3 rounded-lg border border-slate-100 hover:border-slate-200 hover:shadow-sm transition-all group"
                          >
                            <Link href={`/tasks/${task.task_id}`}>
                              <p className="font-medium text-slate-900 text-sm line-clamp-2 hover:text-slate-700">
                                {task.title}
                              </p>
                            </Link>
                            {task.description && (
                              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{task.description}</p>
                            )}
                            <div className="flex items-center gap-2 mt-2 flex-wrap">
                              <span className={`text-xs font-medium ${priorityColorMap[task.priority]}`}>
                                {priorityLabelMap[task.priority]}
                              </span>
                              {task.complexity_score !== null && task.complexity_score !== undefined && (
                                <span className="text-xs text-slate-400">复杂度 {task.complexity_score}</span>
                              )}
                              {task.dependencies.length > 0 && (
                                <span className="text-xs text-slate-400">{task.dependencies.length} 个依赖</span>
                              )}
                            </div>
                            {/* Quick actions */}
                            <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              {col.status === "pending" && (
                                <button
                                  onClick={() => handleStatusChange(task.task_id, "in_progress")}
                                  disabled={updatingId === task.task_id}
                                  className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 disabled:opacity-50"
                                >
                                  开始
                                </button>
                              )}
                              {col.status === "in_progress" && (
                                <button
                                  onClick={() => handleStatusChange(task.task_id, "completed")}
                                  disabled={updatingId === task.task_id}
                                  className="text-xs px-2 py-1 bg-emerald-50 text-emerald-700 rounded hover:bg-emerald-100 disabled:opacity-50"
                                >
                                  完成
                                </button>
                              )}
                              <button
                                onClick={() => handleDelete(task.task_id)}
                                disabled={deletingId === task.task_id}
                                className="text-xs px-2 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100 disabled:opacity-50"
                              >
                                {deletingId === task.task_id ? "删除中..." : "删除"}
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* List View */}
        {viewMode === "list" && (
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            {isLoading ? (
              <div className="p-8 space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse h-16 bg-slate-100 rounded-lg" />
                ))}
              </div>
            ) : tasks.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <p>暂无任务</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {tasks.map((task) => (
                  <div key={task.task_id} className="flex items-center gap-4 p-4 hover:bg-slate-50 transition-colors">
                    <div className="flex-1 min-w-0">
                      <Link href={`/tasks/${task.task_id}`}>
                        <p className="font-medium text-slate-900 hover:text-slate-700 truncate">{task.title}</p>
                      </Link>
                      <p className="text-sm text-slate-500 truncate">{task.description || "暂无描述"}</p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className={`text-xs font-medium ${priorityColorMap[task.priority]}`}>
                        {priorityLabelMap[task.priority]}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full border ${statusColorMap[task.status]}`}>
                        {statusLabelMap[task.status]}
                      </span>
                      <span className="text-xs text-slate-400">
                        {new Date(task.created_at).toLocaleDateString("zh-CN")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tree View (placeholder) */}
        {viewMode === "tree" && (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-500">
            <p>树形视图开发中</p>
            <p className="text-sm mt-1">使用 /api/v1/tasks/tree 接口获取任务树数据</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
