/**
 * CopilotKit Configuration
 * 
 * Configures CopilotKit for the Agentic RAG Platform with custom runtime URL,
 * agent state synchronization, and Generative UI settings.
 */

import type { CopilotAction } from '../types/agent.types';

export const COPILOTKIT_CONFIG = {
  // Runtime URL - points to our FastAPI backend
  runtimeUrl: import.meta.env.VITE_BACKEND_API_URL 
    ? `${import.meta.env.VITE_BACKEND_API_URL}/copilotkit`
    : 'http://localhost:8000/copilotkit',
  
  // Public API key (optional - for CopilotKit Cloud features)
  publicApiKey: import.meta.env.VITE_COPILOTKIT_PUBLIC_KEY,
  
  // Agent configuration
  agent: {
    name: 'rag_agent',
    description: 'Intelligent RAG agent with multi-step reasoning and document retrieval',
  },
  
  // UI customization
  ui: {
    // Chat window settings
    chatWindow: {
      title: 'RAG Assistant',
      placeholder: 'Ask me anything about your documents...',
      showResponseButton: true,
      showStopButton: true,
    },
    
    // Theme customization
    theme: {
      primaryColor: '#3B82F6', // blue-600
      backgroundColor: '#FFFFFF',
      textColor: '#111827', // gray-900
      borderRadius: '0.5rem',
    },
  },
  
  // Headers for authentication
  headers: async () => {
    // This will be populated with JWT token from Supabase
    const token = localStorage.getItem('supabase.auth.token');
    return {
      'Authorization': token ? `Bearer ${token}` : '',
    };
  },
};

/**
 * Default agent actions for CopilotKit
 * These actions allow the agent to interact with the UI
 */
export const DEFAULT_COPILOT_ACTIONS: CopilotAction[] = [
  {
    name: 'search_documents',
    description: 'Search the knowledge base for relevant documents',
    parameters: [
      {
        name: 'query',
        type: 'string',
        description: 'The search query',
        required: true,
      },
      {
        name: 'top_k',
        type: 'number',
        description: 'Number of documents to retrieve',
        required: false,
      },
    ],
    handler: async ({ query, top_k = 5 }) => {
      // This will be implemented to call the backend
      console.log('Searching documents:', query, top_k);
      return { success: true };
    },
  },
  {
    name: 'render_chart',
    description: 'Render a data visualization chart',
    parameters: [
      {
        name: 'chart_type',
        type: 'string',
        description: 'Type of chart (line, bar, pie, scatter)',
        required: true,
      },
      {
        name: 'data',
        type: 'object',
        description: 'Chart data and configuration',
        required: true,
      },
    ],
    handler: async ({ chart_type, data }) => {
      console.log('Rendering chart:', chart_type, data);
      return { success: true };
    },
  },
  {
    name: 'show_citations',
    description: 'Display source citations for the response',
    parameters: [
      {
        name: 'citations',
        type: 'array',
        description: 'Array of citation objects',
        required: true,
      },
    ],
    handler: async ({ citations }) => {
      console.log('Showing citations:', citations);
      return { success: true };
    },
  },
];

/**
 * Agent state render configuration
 * Defines how agent state should be visualized in the UI
 */
export const AGENT_STATE_RENDER_CONFIG = {
  // State update interval (ms)
  updateInterval: 100,
  
  // Show agent thoughts
  showThoughts: true,
  
  // Show retrieved documents
  showDocuments: true,
  
  // Show progress bar
  showProgress: true,
  
  // Animate state transitions
  animateTransitions: true,
  
  // Step labels for UI display
  stepLabels: {
    initializing: 'Initializing...',
    analyzing_query: 'Analyzing your question...',
    rewriting_query: 'Optimizing search query...',
    searching_knowledge_base: 'Searching knowledge base...',
    reranking_results: 'Ranking results...',
    generating_response: 'Generating response...',
    validating_response: 'Validating answer...',
    completed: 'Complete',
    error: 'Error occurred',
  },
  
  // Progress weights for each step
  stepProgress: {
    initializing: 5,
    analyzing_query: 15,
    rewriting_query: 25,
    searching_knowledge_base: 45,
    reranking_results: 60,
    generating_response: 85,
    validating_response: 95,
    completed: 100,
    error: 0,
  },
};

/**
 * Streaming configuration
 */
export const STREAMING_CONFIG = {
  // Enable streaming
  enabled: true,
  
  // Reconnect on error
  reconnect: true,
  
  // Max reconnection attempts
  maxReconnectAttempts: 3,
  
  // Reconnection delay (ms)
  reconnectDelay: 1000,
  
  // Timeout for connection (ms)
  connectionTimeout: 30000,
};

/**
 * Get CopilotKit runtime URL with authentication
 */
export function getCopilotKitRuntimeUrl(): string {
  return COPILOTKIT_CONFIG.runtimeUrl;
}

/**
 * Get authentication headers for CopilotKit requests
 */
export async function getCopilotKitHeaders(): Promise<Record<string, string>> {
  if (typeof COPILOTKIT_CONFIG.headers === 'function') {
    return await COPILOTKIT_CONFIG.headers();
  }
  return {};
}
