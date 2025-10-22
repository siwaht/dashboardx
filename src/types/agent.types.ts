/**
 * Agent State Types for Agentic RAG Platform
 * 
 * These types define the structure of agent state, messages, and UI synchronization
 * for the LangGraph-powered agent system with CopilotKit integration.
 */

export type MessageRole = 'user' | 'assistant' | 'system';

export interface AgentMessage {
  id: string;
  role: MessageRole;
  content: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface RetrievedDocument {
  id: string;
  content: string;
  metadata: {
    tenant_id: string;
    document_id: string;
    chunk_index: number;
    source_url?: string;
    file_type?: string;
    similarity_score?: number;
  };
}

export interface Citation {
  document_id: string;
  document_title: string;
  chunk_content: string;
  source_url?: string;
  relevance_score: number;
}

export interface ToolCall {
  tool_name: string;
  arguments: Record<string, any>;
  result?: any;
  timestamp: string;
}

export type AgentStep = 
  | 'initializing'
  | 'analyzing_query'
  | 'rewriting_query'
  | 'searching_knowledge_base'
  | 'reranking_results'
  | 'generating_response'
  | 'validating_response'
  | 'completed'
  | 'error';

export interface AgentState {
  // Core conversation
  messages: AgentMessage[];
  
  // User context
  tenant_id: string;
  user_id: string;
  session_id: string;
  
  // RAG context
  retrieved_documents: RetrievedDocument[];
  query_rewrite?: string;
  
  // Agent state
  current_step: AgentStep;
  agent_thoughts: string[];
  tool_calls: ToolCall[];
  
  // UI synchronization
  ui_state: {
    is_thinking: boolean;
    is_retrieving: boolean;
    is_generating: boolean;
    show_documents: boolean;
    show_citations: boolean;
  };
  progress: number; // 0-100
  
  // Final output
  final_response?: string;
  citations: Citation[];
  
  // Error handling
  error?: {
    message: string;
    code: string;
    timestamp: string;
  };
}

export interface StreamEvent {
  type: 'state' | 'token' | 'thought' | 'document' | 'citation' | 'done' | 'error';
  data: any;
  timestamp: string;
}

export interface StateUpdateEvent extends StreamEvent {
  type: 'state';
  data: {
    current_step: AgentStep;
    progress: number;
    ui_state: AgentState['ui_state'];
  };
}

export interface TokenEvent extends StreamEvent {
  type: 'token';
  data: {
    content: string;
    is_final: boolean;
  };
}

export interface ThoughtEvent extends StreamEvent {
  type: 'thought';
  data: {
    thought: string;
  };
}

export interface DocumentEvent extends StreamEvent {
  type: 'document';
  data: {
    documents: RetrievedDocument[];
    count: number;
  };
}

export interface CitationEvent extends StreamEvent {
  type: 'citation';
  data: {
    citations: Citation[];
  };
}

export interface DoneEvent extends StreamEvent {
  type: 'done';
  data: {
    final_response: string;
    citations: Citation[];
    total_tokens?: number;
    duration_ms?: number;
  };
}

export interface ErrorEvent extends StreamEvent {
  type: 'error';
  data: {
    message: string;
    code: string;
    details?: any;
  };
}

// Chart/Visualization types for data visualization agent
export type ChartType = 'line' | 'bar' | 'pie' | 'scatter' | 'area';

export interface ChartData {
  type: ChartType;
  title: string;
  data: any[];
  config?: {
    xAxis?: string;
    yAxis?: string;
    colors?: string[];
    legend?: boolean;
  };
}

export interface VisualizationAction {
  action: 'render_chart';
  data: ChartData;
}

// CopilotKit action types
export interface CopilotAction {
  name: string;
  description: string;
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required?: boolean;
  }>;
  handler: (args: any) => Promise<any>;
}

// API Request/Response types
export interface ChatRequest {
  message: string;
  session_id?: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  citations: Citation[];
  session_id: string;
  agent_state: Partial<AgentState>;
}

export interface StreamingChatRequest extends ChatRequest {
  stream: true;
}

// Configuration types
export interface AgentConfig {
  temperature: number;
  max_tokens: number;
  top_k_documents: number;
  similarity_threshold: number;
  enable_reranking: boolean;
  enable_query_rewrite: boolean;
  streaming: boolean;
}

export interface RAGConfig {
  chunk_size: number;
  chunk_overlap: number;
  embedding_model: string;
  retrieval_strategy: 'similarity' | 'mmr' | 'hybrid';
  reranking_model?: string;
}
