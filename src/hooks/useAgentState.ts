/**
 * useAgentState Hook
 * 
 * Manages agent state synchronization with CopilotKit.
 * Provides real-time updates of agent thinking process, progress, and retrieved documents.
 */

import { useState, useCallback, useEffect } from 'react';
import type { AgentState, AgentStep } from '../types/agent.types';

interface UseAgentStateOptions {
  sessionId: string;
  onStepChange?: (step: AgentStep) => void;
  onProgressUpdate?: (progress: number) => void;
  onThoughtAdded?: (thought: string) => void;
}

const initialAgentState: AgentState = {
  messages: [],
  tenant_id: '',
  user_id: '',
  session_id: '',
  retrieved_documents: [],
  current_step: 'initializing',
  agent_thoughts: [],
  tool_calls: [],
  ui_state: {
    is_thinking: false,
    is_retrieving: false,
    is_generating: false,
    show_documents: false,
    show_citations: false,
  },
  progress: 0,
  citations: [],
};

export function useAgentState(options: UseAgentStateOptions) {
  const { sessionId, onStepChange, onProgressUpdate, onThoughtAdded } = options;

  const [agentState, setAgentState] = useState<AgentState>({
    ...initialAgentState,
    session_id: sessionId,
  });

  /**
   * Update agent step
   */
  const updateStep = useCallback((step: AgentStep) => {
    setAgentState((prev) => ({
      ...prev,
      current_step: step,
    }));
    onStepChange?.(step);
  }, [onStepChange]);

  /**
   * Update progress
   */
  const updateProgress = useCallback((progress: number) => {
    setAgentState((prev) => ({
      ...prev,
      progress: Math.min(100, Math.max(0, progress)),
    }));
    onProgressUpdate?.(progress);
  }, [onProgressUpdate]);

  /**
   * Add agent thought
   */
  const addThought = useCallback((thought: string) => {
    setAgentState((prev) => ({
      ...prev,
      agent_thoughts: [...prev.agent_thoughts, thought],
    }));
    onThoughtAdded?.(thought);
  }, [onThoughtAdded]);

  /**
   * Update UI state
   */
  const updateUIState = useCallback((updates: Partial<AgentState['ui_state']>) => {
    setAgentState((prev) => ({
      ...prev,
      ui_state: {
        ...prev.ui_state,
        ...updates,
      },
    }));
  }, []);

  /**
   * Set retrieved documents
   */
  const setRetrievedDocuments = useCallback((documents: AgentState['retrieved_documents']) => {
    setAgentState((prev) => ({
      ...prev,
      retrieved_documents: documents,
      ui_state: {
        ...prev.ui_state,
        show_documents: documents.length > 0,
      },
    }));
  }, []);

  /**
   * Set citations
   */
  const setCitations = useCallback((citations: AgentState['citations']) => {
    setAgentState((prev) => ({
      ...prev,
      citations,
      ui_state: {
        ...prev.ui_state,
        show_citations: citations.length > 0,
      },
    }));
  }, []);

  /**
   * Set final response
   */
  const setFinalResponse = useCallback((response: string) => {
    setAgentState((prev) => ({
      ...prev,
      final_response: response,
      current_step: 'completed',
      progress: 100,
      ui_state: {
        ...prev.ui_state,
        is_thinking: false,
        is_retrieving: false,
        is_generating: false,
      },
    }));
  }, []);

  /**
   * Set error
   */
  const setError = useCallback((error: { message: string; code: string }) => {
    setAgentState((prev) => ({
      ...prev,
      error: {
        ...error,
        timestamp: new Date().toISOString(),
      },
      current_step: 'error',
      ui_state: {
        ...prev.ui_state,
        is_thinking: false,
        is_retrieving: false,
        is_generating: false,
      },
    }));
  }, []);

  /**
   * Reset agent state
   */
  const reset = useCallback(() => {
    setAgentState({
      ...initialAgentState,
      session_id: sessionId,
    });
  }, [sessionId]);

  /**
   * Update entire state (for SSE updates)
   */
  const updateState = useCallback((updates: Partial<AgentState>) => {
    setAgentState((prev) => ({
      ...prev,
      ...updates,
    }));
  }, []);

  /**
   * Get step label for display
   */
  const getStepLabel = useCallback((step: AgentStep): string => {
    const labels: Record<AgentStep, string> = {
      initializing: 'Initializing...',
      analyzing_query: 'Analyzing your question...',
      rewriting_query: 'Optimizing search query...',
      searching_knowledge_base: 'Searching knowledge base...',
      reranking_results: 'Ranking results...',
      generating_response: 'Generating response...',
      validating_response: 'Validating answer...',
      completed: 'Complete',
      error: 'Error occurred',
    };
    return labels[step] || step;
  }, []);

  /**
   * Check if agent is active
   */
  const isActive = useCallback(() => {
    return agentState.ui_state.is_thinking ||
           agentState.ui_state.is_retrieving ||
           agentState.ui_state.is_generating;
  }, [agentState.ui_state]);

  // Update session ID when it changes
  useEffect(() => {
    setAgentState((prev) => ({
      ...prev,
      session_id: sessionId,
    }));
  }, [sessionId]);

  return {
    // State
    agentState,
    currentStep: agentState.current_step,
    progress: agentState.progress,
    thoughts: agentState.agent_thoughts,
    documents: agentState.retrieved_documents,
    citations: agentState.citations,
    uiState: agentState.ui_state,
    error: agentState.error,
    finalResponse: agentState.final_response,

    // Actions
    updateStep,
    updateProgress,
    addThought,
    updateUIState,
    setRetrievedDocuments,
    setCitations,
    setFinalResponse,
    setError,
    reset,
    updateState,

    // Utilities
    getStepLabel,
    isActive: isActive(),
  };
}
