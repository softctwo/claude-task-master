"use client";

import { create } from "zustand";

interface AIGenerationState {
  // Generation status
  isGeneratingPRD: boolean;
  isGeneratingTasks: boolean;
  isStreaming: boolean;
  
  // Streaming content
  streamContent: string;
  streamError: string | null;
  
  // Actions
  setGeneratingPRD: (value: boolean) => void;
  setGeneratingTasks: (value: boolean) => void;
  setStreaming: (value: boolean) => void;
  appendStreamContent: (chunk: string) => void;
  setStreamError: (error: string | null) => void;
  resetStream: () => void;
}

export const useAIGenerationStore = create<AIGenerationState>((set) => ({
  isGeneratingPRD: false,
  isGeneratingTasks: false,
  isStreaming: false,
  streamContent: "",
  streamError: null,

  setGeneratingPRD: (value) => set({ isGeneratingPRD: value }),
  setGeneratingTasks: (value) => set({ isGeneratingTasks: value }),
  setStreaming: (value) => set({ isStreaming: value }),
  appendStreamContent: (chunk) =>
    set((state) => ({ streamContent: state.streamContent + chunk })),
  setStreamError: (error) => set({ streamError: error }),
  resetStream: () =>
    set({ streamContent: "", streamError: null, isStreaming: false }),
}));
