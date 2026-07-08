"use client";

import { useRef, useEffect } from "react";
import { X, AlertCircle, FileText, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

interface StreamingOutputProps {
  content: string;
  isLoading: boolean;
  error: string | null;
  title?: string;
  onClose?: () => void;
  className?: string;
}

export function StreamingOutput({
  content,
  isLoading,
  error,
  title = "AI Generation",
  onClose,
  className,
}: StreamingOutputProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when content updates
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [content]);

  // Blinking cursor effect when loading
  const showCursor = isLoading && content.length > 0;

  return (
    <div
      className={cn(
        "bg-white rounded-lg border border-slate-200 shadow-lg overflow-hidden",
        "flex flex-col",
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center">
            <Bot size={14} className="text-indigo-600" />
          </div>
          <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
          {isLoading && (
            <span className="flex items-center gap-1 text-xs text-indigo-500">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              Generating...
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {content.length > 0 && (
            <span className="text-xs text-slate-400">
              {content.length} chars
            </span>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-b border-red-100 flex items-center gap-2">
          <AlertCircle size={14} className="text-red-500 flex-shrink-0" />
          <p className="text-xs text-red-600">{error}</p>
        </div>
      )}

      {/* Content */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 max-h-[600px] min-h-[200px]"
      >
        {content.length === 0 && isLoading ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-400">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin mb-3" />
            <p className="text-sm">AI is thinking...</p>
          </div>
        ) : content.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-400">
            <FileText size={24} className="mb-2 opacity-50" />
            <p className="text-sm">Waiting to generate...</p>
          </div>
        ) : (
          <div ref={contentRef} className="prose prose-slate prose-sm max-w-none">
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <h1 className="text-xl font-bold text-slate-900 mt-6 mb-3">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-lg font-semibold text-slate-800 mt-5 mb-2">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-base font-semibold text-slate-700 mt-4 mb-2">{children}</h3>
                ),
                p: ({ children }) => (
                  <p className="text-sm text-slate-600 leading-relaxed mb-3">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside text-sm text-slate-600 mb-3 space-y-1">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside text-sm text-slate-600 mb-3 space-y-1">{children}</ol>
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
                  <pre className="bg-slate-900 text-slate-100 p-3 rounded-lg overflow-x-auto text-xs mb-3">
                    {children}
                  </pre>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-indigo-300 pl-3 italic text-slate-500 mb-3">
                    {children}
                  </blockquote>
                ),
                hr: () => <hr className="border-slate-200 my-4" />,
              }}
            >
              {content + (showCursor ? "▌" : "")}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              isLoading ? "bg-amber-400 animate-pulse" : "bg-emerald-500"
            )}
          />
          <span className="text-xs text-slate-500">
            {isLoading ? "Generating" : "Complete"}
          </span>
        </div>
        {content.length > 0 && (
          <span className="text-xs text-slate-400">
            {content.split(/\s+/).filter(Boolean).length} words
          </span>
        )}
      </div>
    </div>
  );
}
