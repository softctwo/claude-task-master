"use client";

import { useState } from "react";
import { Sparkles, Loader2, Wand2, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useGeneratePRD, useStreamGeneratePRD } from "@/lib/hooks/use-ai-generation";
import { StreamingOutput } from "./StreamingOutput";

interface GeneratePRDButtonProps {
  briefId: string;
  briefStatus: string;
  variant?: "default" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  onSuccess?: () => void;
  className?: string;
}

export function GeneratePRDButton({
  briefId,
  briefStatus,
  variant = "default",
  size = "md",
  onSuccess,
  className,
}: GeneratePRDButtonProps) {
  const [showStream, setShowStream] = useState(false);
  const [generatedPRD, setGeneratedPRD] = useState<string | null>(null);
  
  const generatePRD = useGeneratePRD();
  const streamPRD = useStreamGeneratePRD();

  const isApproved = briefStatus === "approved";
  const isLoading = generatePRD.isPending || streamPRD.isStreaming;

  const handleGenerate = async () => {
    if (!isApproved) return;
    
    setShowStream(true);
    setGeneratedPRD(null);
    
    try {
      // Use streaming for better UX
      const content = await streamPRD.startStream(briefId);
      setGeneratedPRD(content);
      onSuccess?.();
    } catch (error) {
      console.error("Failed to generate PRD:", error);
      // Fallback to non-streaming
      try {
        const result = await generatePRD.mutateAsync({ briefId });
        setGeneratedPRD(result.content_markdown);
        onSuccess?.();
      } catch (fallbackError) {
        console.error("Fallback generation also failed:", fallbackError);
      }
    }
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  const variantClasses = {
    default: "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm",
    outline: "border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50",
    ghost: "text-indigo-600 hover:bg-indigo-50",
  };

  return (
    <div className="space-y-4">
      <button
        onClick={handleGenerate}
        disabled={!isApproved || isLoading}
        className={cn(
          "inline-flex items-center gap-2 rounded-lg font-medium transition-all",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none",
          "active:scale-[0.98]",
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
        title={
          !isApproved
            ? "Brief must be approved before generating PRD"
            : isLoading
            ? "Generating..."
            : "Generate PRD with AI"
        }
      >
        {isLoading ? (
          <Loader2 size={size === "sm" ? 14 : size === "lg" ? 20 : 16} className="animate-spin" />
        ) : generatedPRD ? (
          <CheckCircle size={size === "sm" ? 14 : size === "lg" ? 20 : 16} />
        ) : (
          <Sparkles size={size === "sm" ? 14 : size === "lg" ? 20 : 16} />
        )}
        {isLoading
          ? "Generating..."
          : generatedPRD
          ? "PRD Generated"
          : "Generate PRD"}
      </button>

      {showStream && (
        <StreamingOutput
          content={streamPRD.streamContent}
          isLoading={streamPRD.isStreaming}
          error={streamPRD.streamError}
          title="AI PRD Generation"
          onClose={() => setShowStream(false)}
        />
      )}
    </div>
  );
}

// ── Compact inline variant ──

export function GeneratePRDInlineButton({
  briefId,
  briefStatus,
  onSuccess,
  className,
}: Omit<GeneratePRDButtonProps, "variant" | "size">) {
  const generatePRD = useGeneratePRD();
  const isApproved = briefStatus === "approved";
  const isLoading = generatePRD.isPending;

  return (
    <button
      onClick={() => {
        if (!isApproved) return;
        generatePRD.mutate({ briefId }, { onSuccess });
      }}
      disabled={!isApproved || isLoading}
      className={cn(
        "inline-flex items-center gap-1.5 text-sm",
        "text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50",
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
      {isLoading ? "Generating..." : "AI Generate"}
    </button>
  );
}
