/**
 * Custom hook for CopilotKit agent integration
 * 
 * Provides WebSocket connection to backend agent system with
 * real-time state updates and action execution.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface AgentState {
  step: string;
  message?: string;
  thoughts?: string;
  all_thoughts?: string[];
  tools_used?: string[];
  progress?: number;
  ui_state?: Record<string, any>;
  response?: string;
  citations?: Array<{
    text: string;
    metadata: Record<string, any>;
  }>;
  visualization?: Record<string, any>;
}

interface UseCopilotAgentReturn {
  isConnected: boolean;
  isProcessing: boolean;
  agentState: AgentState | null;
  response: string;
  error: string | null;
  sendQuery: (query: string) => Promise<void>;
  executeAction: (action: string, params: Record<string, any>) => Promise<any>;
  disconnect: () => void;
}

export function useCopilotAgent(): UseCopilotAgentReturn {
  const { user } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [agentState, setAgentState] = useState<AgentState | null>(null);
  const [response, setResponse] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string>('');

  // Initialize WebSocket connection
  useEffect(() => {
    if (!user) return;

    const connectWebSocket = () => {
      try {
        // Determine WebSocket URL
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = import.meta.env.VITE_BACKEND_URL?.replace('http://', '').replace('https://', '') || 'localhost:8000';
        const wsUrl = `${wsProtocol}//${wsHost}/api/copilotkit/ws`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('WebSocket connected');
          
          // Send authentication
          ws.send(JSON.stringify({
            type: 'auth',
            token: (user as any).access_token || 'demo-token',
            user_id: user.id,
            tenant_id: user.user_metadata?.tenant_id || 'demo-tenant',
            email: user.email,
            session_id: sessionIdRef.current || `session_${user.id}_${Date.now()}`
          }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
          } catch (err) {
            console.error('Error parsing WebSocket message:', err);
          }
        };

        ws.onerror = (event) => {
          console.error('WebSocket error:', event);
          setError('WebSocket connection error');
          setIsConnected(false);
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setIsConnected(false);
          
          // Attempt to reconnect after 3 seconds
          setTimeout(() => {
            if (user) {
              connectWebSocket();
            }
          }, 3000);
        };
      } catch (err) {
        console.error('Error connecting WebSocket:', err);
        setError('Failed to connect to agent service');
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'auth_success':
        setIsConnected(true);
        sessionIdRef.current = data.session_id;
        setError(null);
        console.log('Authentication successful:', data.session_id);
        break;

      case 'state_update':
        setAgentState(data);
        setIsProcessing(true);
        break;

      case 'final_response':
        setAgentState(data);
        setResponse(data.response || '');
        setIsProcessing(false);
        break;

      case 'error':
        setError(data.message || 'An error occurred');
        setIsProcessing(false);
        break;

      case 'action_result':
        // Handle action results
        console.log('Action result:', data);
        break;

      case 'pong':
        // Heartbeat response
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }, []);

  // Send query to agent
  const sendQuery = useCallback(async (query: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected to agent service');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);
      setResponse('');
      setAgentState(null);

      wsRef.current.send(JSON.stringify({
        type: 'agent_query',
        query,
        session_id: sessionIdRef.current
      }));
    } catch (err) {
      console.error('Error sending query:', err);
      setError('Failed to send query');
      setIsProcessing(false);
    }
  }, []);

  // Execute CopilotKit action
  const executeAction = useCallback(async (action: string, params: Record<string, any>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      throw new Error('Not connected to agent service');
    }

    return new Promise((resolve, reject) => {
      const messageHandler = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'action_result' && data.action === action) {
            wsRef.current?.removeEventListener('message', messageHandler);
            if (data.result.success) {
              resolve(data.result.data);
            } else {
              reject(new Error(data.result.error));
            }
          }
        } catch (err) {
          reject(err);
        }
      };

      wsRef.current?.addEventListener('message', messageHandler);

      wsRef.current?.send(JSON.stringify({
        type: 'action',
        action,
        params
      }));

      // Timeout after 30 seconds
      setTimeout(() => {
        wsRef.current?.removeEventListener('message', messageHandler);
        reject(new Error('Action timeout'));
      }, 30000);
    });
  }, []);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Send heartbeat every 30 seconds
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected]);

  return {
    isConnected,
    isProcessing,
    agentState,
    response,
    error,
    sendQuery,
    executeAction,
    disconnect
  };
}
