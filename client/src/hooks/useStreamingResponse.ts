/**
 * useStreamingResponse Hook
 * 
 * Manages Server-Sent Events (SSE) streaming for real-time agent responses.
 * Handles token streaming, state updates, and error recovery.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type {
  StreamEvent,
  StateUpdateEvent,
  TokenEvent,
  ThoughtEvent,
  DocumentEvent,
  CitationEvent,
  DoneEvent,
  ErrorEvent,
  AgentState,
} from '../types/agent.types';

interface UseStreamingResponseOptions {
  onStateUpdate?: (state: Partial<AgentState>) => void;
  onToken?: (token: string) => void;
  onThought?: (thought: string) => void;
  onDocuments?: (documents: any[]) => void;
  onCitations?: (citations: any[]) => void;
  onComplete?: (response: string, citations: any[]) => void;
  onError?: (error: Error) => void;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
}

interface StreamingState {
  isStreaming: boolean;
  response: string;
  currentState: Partial<AgentState>;
  error: Error | null;
  reconnectAttempts: number;
}

export function useStreamingResponse(options: UseStreamingResponseOptions = {}) {
  const {
    onStateUpdate,
    onToken,
    onThought,
    onDocuments,
    onCitations,
    onComplete,
    onError,
    maxReconnectAttempts = 3,
    reconnectDelay = 1000,
  } = options;

  const [state, setState] = useState<StreamingState>({
    isStreaming: false,
    response: '',
    currentState: {},
    error: null,
    reconnectAttempts: 0,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Clean up event source and timeouts
   */
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  /**
   * Handle incoming stream events
   */
  const handleStreamEvent = useCallback((event: MessageEvent) => {
    try {
      const streamEvent: StreamEvent = JSON.parse(event.data);

      switch (streamEvent.type) {
        case 'state': {
          const stateEvent = streamEvent as StateUpdateEvent;
          setState(prev => ({
            ...prev,
            currentState: {
              ...prev.currentState,
              ...stateEvent.data,
            },
          }));
          onStateUpdate?.(stateEvent.data);
          break;
        }

        case 'token': {
          const tokenEvent = streamEvent as TokenEvent;
          setState(prev => ({
            ...prev,
            response: prev.response + tokenEvent.data.content,
          }));
          onToken?.(tokenEvent.data.content);
          break;
        }

        case 'thought': {
          const thoughtEvent = streamEvent as ThoughtEvent;
          onThought?.(thoughtEvent.data.thought);
          break;
        }

        case 'document': {
          const docEvent = streamEvent as DocumentEvent;
          onDocuments?.(docEvent.data.documents);
          break;
        }

        case 'citation': {
          const citationEvent = streamEvent as CitationEvent;
          onCitations?.(citationEvent.data.citations);
          break;
        }

        case 'done': {
          const doneEvent = streamEvent as DoneEvent;
          setState(prev => ({
            ...prev,
            isStreaming: false,
            response: doneEvent.data.final_response,
          }));
          onComplete?.(doneEvent.data.final_response, doneEvent.data.citations);
          cleanup();
          break;
        }

        case 'error': {
          const errorEvent = streamEvent as ErrorEvent;
          const error = new Error(errorEvent.data.message);
          setState(prev => ({
            ...prev,
            isStreaming: false,
            error,
          }));
          onError?.(error);
          cleanup();
          break;
        }
      }
    } catch (error) {
      console.error('Error parsing stream event:', error);
    }
  }, [onStateUpdate, onToken, onThought, onDocuments, onCitations, onComplete, onError, cleanup]);

  /**
   * Handle stream errors with reconnection logic
   */
  const handleStreamError = useCallback((error: Event) => {
    console.error('Stream error:', error);

    setState(prev => {
      const newAttempts = prev.reconnectAttempts + 1;

      if (newAttempts < maxReconnectAttempts) {
        // Attempt reconnection
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Reconnecting... (attempt ${newAttempts + 1}/${maxReconnectAttempts})`);
          // The reconnection will be handled by the caller
        }, reconnectDelay);

        return {
          ...prev,
          reconnectAttempts: newAttempts,
        };
      } else {
        // Max attempts reached
        const maxAttemptsError = new Error('Max reconnection attempts reached');
        onError?.(maxAttemptsError);
        cleanup();

        return {
          ...prev,
          isStreaming: false,
          error: maxAttemptsError,
        };
      }
    });
  }, [maxReconnectAttempts, reconnectDelay, onError, cleanup]);

  /**
   * Start streaming a response
   */
  const streamResponse = useCallback(async (
    message: string,
    sessionId: string,
    additionalParams?: Record<string, any>
  ) => {
    // Clean up any existing connection
    cleanup();

    // Reset state
    setState({
      isStreaming: true,
      response: '',
      currentState: {},
      error: null,
      reconnectAttempts: 0,
    });

    try {
      // Get authentication token (for future use)
      // const token = localStorage.getItem('supabase.auth.token');

      // Build URL with query parameters
      const baseUrl = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';
      const params = new URLSearchParams({
        session_id: sessionId,
        message: message,
        ...additionalParams,
      });

      const url = `${baseUrl}/chat/stream?${params.toString()}`;

      // Create EventSource connection
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      // Set up event listeners
      eventSource.onmessage = handleStreamEvent;
      eventSource.onerror = handleStreamError;

      // Handle connection open
      eventSource.onopen = () => {
        console.log('Stream connection opened');
        setState(prev => ({ ...prev, reconnectAttempts: 0 }));
      };

    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to start stream');
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: err,
      }));
      onError?.(err);
    }
  }, [cleanup, handleStreamEvent, handleStreamError, onError]);

  /**
   * Stop streaming
   */
  const stopStreaming = useCallback(() => {
    cleanup();
    setState(prev => ({
      ...prev,
      isStreaming: false,
    }));
  }, [cleanup]);

  /**
   * Reset state
   */
  const reset = useCallback(() => {
    cleanup();
    setState({
      isStreaming: false,
      response: '',
      currentState: {},
      error: null,
      reconnectAttempts: 0,
    });
  }, [cleanup]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    // State
    isStreaming: state.isStreaming,
    response: state.response,
    currentState: state.currentState,
    error: state.error,
    reconnectAttempts: state.reconnectAttempts,

    // Actions
    streamResponse,
    stopStreaming,
    reset,
  };
}
