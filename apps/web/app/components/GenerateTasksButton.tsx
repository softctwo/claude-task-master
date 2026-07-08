"use client";

import { useState } from "react";
import { ListChecks, Loader2, CheckCircle, Wand2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useGenerateTasks } from "@/lib/hooks/use-ai-generation";
import { StreamingOutput } from "./StreamingOutput";

interface GenerateTasksButtonProps {
  prdId: string;
  prdContent?: string;
  variant?: "default" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  onSuccess?: () => void;
  className?: string;
}

export function GenerateTasksButton({
  prdId,
  prdContent,
  variant = "default",
  size = "md",
  onSuccess,
  className,
}: GenerateTasksButtonProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [taskCount, setTaskCount] = useState(0);
  
  const generateTasks = useGenerateTasks();
  const isLoading = generateTasks.isPending;
  const isSuccess = generateTasks.isSuccess;

  const handleGenerate = async () => {
    try {
      const result = await generateTasks.mutateAsync({ prdId });
      setTaskCount(result.length);
      setShowPreview(true);
      onSuccess?.();
    } catch (error) {
      console.error("Failed to generate tasks:", error);
    }
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  const variantClasses = {
    default: "bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm",
    outline: "border-2 border-emerald-600 text-emerald-600 hover:bg-emerald-50",
    ghost: "text-emerald-600 hover:bg-emerald-50",
  };

  return (
    <div className="space-y-4">
      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className={cn(
          "inline-flex items-center gap-2 rounded-lg font-medium transition-all",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none",
          "active:scale-[0.98]",
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
      >
        {isLoading ? (
          <Loader2 size={size === "sm" ? 14 : size === "lg" ? 20 : 16} className="animate-spin" />
        ) : isSuccess ? (
          <CheckCircle size={size === "sm" ? 14 : size === "lg" ? 20 : 16} />
        ) : (
          <ListChecks size={size === "sm" ? 14 : size === "lg" ? 20 : 16} />
        )}
        {isLoading
          ? "Generating Tasks..."
          : isSuccess
          ? `${taskCount} Tasks Generated`
          : "Generate Tasks from PRD"}
      </button>

      {showPreview && generateTasks.data && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700">
              Generated Tasks ({generateTasks.data.length})
            </h3>
            <button
              onClick={() => setShowPreview(false)}
              className="text-xs text-slate-500 hover:text-slate-700"
            >
              Hide
            </button>
          </div>
          <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
            {generateTasks.data.map((task, index) => (
              <div key={task.task_id || index} className="px-4 py-3 hover:bg-slate-50">
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-medium">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900">{task.title}</p>
                    {task.description && (
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{task.description}</p>
                    )}
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className={cn(
                        "text-xs px-1.5 py-0.5 rounded font-medium",
                        task.priority === "critical" && "bg-red-100 text-red-700",
                        task.priority === "high" && "bg-orange-100 text-orange-700",
                        task.priority === "medium" && "bg-amber-100 text-amber-700",
                        task.priority === "low" && "bg-slate-100 text-slate-600",
                      )}>
                        {task.priority}
                      </span>
                      {task.complexity_score && (
                        <span className="text-xs text-slate-400">
                          Complexity: {task.complexity_score}/10
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Compact inline variant ──

export function GenerateTasksInlineButton({
  prdId,
  onSuccess,
  className,
}: Omit<GenerateTasksButtonProps, "variant" | "size" | "prdContent">) {
  const generateTasks = useGenerateTasks();
  const isLoading = generateTasks.isPending;

  return (
    <button
      onClick={() => generateTasks.mutate({ prdId }, { onSuccess })}
      disabled={isLoading}
      className={cn(
        "inline-flex items-center gap-1.5 text-sm",
        "text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50",
        "rounded-md px-2 py-1 transition-colors",
        "disabled:opacity-40 disabled:cursor-not-allowed",
        className
      )}
    >
      {isLoading ? (
        <Loader2 size={14} className="animate-spin" />
      ) : (
        <Wand2 size={14} />
      )}
      {isLoading ? "Generating..." : "AI Tasks"}
    </button>
  );
}
