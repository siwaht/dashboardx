# 🚀 Agentic RAG Platform - Complete Integration Plan

## Executive Summary

This document outlines the comprehensive plan to transform the existing dashboard into a production-ready Agentic RAG Platform with:
- **CopilotKit** for Generative UI
- **LangGraph** for stateful agent orchestration  
- **LlamaIndex** for optimized RAG retrieval
- **Multi-tenant FGAC** security
- **Real-time streaming** via SSE

---

## 📊 Current State Analysis

### ✅ Existing Infrastructure
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Supabase (PostgreSQL with pgvector)
- **Database**: Multi-tenant schema with RLS policies
- **Auth**: Supabase Auth with tenant isolation
- **Features**: Basic chat, document upload, mock responses

### ❌ Missing Components
1. CopilotKit integration for Generative UI
2. Backend agent orchestration (LangGraph)
3. RAG retrieval pipeline (LlamaIndex)
4. Real-time streaming (SSE/WebSocket)
5. Actual vector similarity search
6. Enterprise data connectors
7. LLM integration (currently mock responses)

---

## 🎯 Implementation Phases

### **PHASE 1: Foundation & Core Dependencies** ⏱️ 2-3 days

#### 1.1 Frontend Dependencies Installation

**Package Additions:**
```json
{
  "@copilotkit/react-core": "^1.0.0",
  "@copilotkit/react-ui": "^1.0.0",
  "@copilotkit/react-textarea": "^1.0.0",
  "eventsource-parser": "^1.1.0",
  "recharts": "^2.10.0",
  "plotly.js": "^2.27.0",
  "react-plotly.js": "^2.6.0"
}
```

**Files to Create:**
- `src/lib/copilotkit-config.ts` - CopilotKit configuration
- `src/hooks/useAgentState.ts` - Agent state management hook
- `src/hooks/useStreamingResponse.ts` - SSE streaming hook
- `src/types/agent.types.ts` - Agent state TypeScript types

#### 1.2 Backend Service Setup

**Technology Stack:**
- **Framework**: FastAPI (Python 3.11+)
- **Agent**: LangGraph + LangChain
- **RAG**: LlamaIndex
- **LLM**: OpenAI GPT-4 / Anthropic Claude
- **Vector Store**: Supabase pgvector

**Directory Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Environment config
│   ├── dependencies.py         # Dependency injection
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat endpoints
│   │   ├── documents.py       # Document ingestion
│   │   └── streaming.py       # SSE streaming
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── graph.py           # LangGraph definition
│   │   ├── nodes.py           # Agent nodes
│   │   ├── state.py           # State schema
│   │   └── tools.py           # Agent tools
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestion.py       # Document processing
│   │   ├── retrieval.py       # Vector search
│   │   ├── chunking.py        # Chunking strategies
│   │   └── embeddings.py      # Embedding generation
│   ├── security/
│   │   ├── __init__.py
│   │   ├── auth.py            # JWT validation
│   │   └── fgac.py            # Tenant filtering
│   └── connectors/
│       ├── __init__.py
│       ├── s3.py              # S3 connector
│       ├── sharepoint.py      # SharePoint connector
│       └── base.py            # Base connector class
├── requirements.txt
├── .env.example
└── README.md
```

**Python Dependencies:**
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# LangChain & LangGraph
langgraph==0.0.40
langchain==0.1.0
langchain-openai==0.0.5
langchain-anthropic==0.1.0

# LlamaIndex
llama-index==0.10.0
llama-index-vector-stores-postgres==0.1.0
llama-index-embeddings-openai==0.1.0

# Database
psycopg2-binary==2.9.9
pgvector==0.2.4
supabase==2.3.0

# Utilities
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.26.0
sse-starlette==1.8.2
```

#### 1.3 Environment Configuration

**Frontend (.env):**
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_BACKEND_API_URL=http://localhost:8000
VITE_COPILOTKIT_PUBLIC_KEY=your_copilotkit_key
```

**Backend (.env):**
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# OpenAI
OPENAI_API_KEY=your_openai_key

# LangSmith (Optional - for observability)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=agentic-rag-platform

# CopilotKit
COPILOTKIT_API_KEY=your_copilotkit_key

# Server
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

---

### **PHASE 2: RAG Pipeline with LlamaIndex** ⏱️ 3-4 days

#### 2.1 Document Ingestion Pipeline

**Implementation Files:**

**`backend/app/rag/ingestion.py`**
- Document upload handler
- File type detection (PDF, DOCX, TXT, MD)
- Async processing with status updates
- Metadata extraction (filename, size, type, upload date)

**`backend/app/rag/chunking.py`**
- Semantic chunking (preserves context)
- Recursive text splitting (hierarchical separators)
- Sentence-based chunking
- Configurable chunk size (default: 512 tokens, overlap: 50)

**`backend/app/rag/embeddings.py`**
- OpenAI text-embedding-3-small (1536 dimensions)
- Batch processing for efficiency
- Error handling and retry logic
- Cost tracking

**Key Features:**
```python
# Chunking Strategy
- Chunk Size: 512 tokens
- Overlap: 50 tokens
- Method: Recursive with semantic boundaries
- Metadata: {tenant_id, document_id, chunk_index, source_url}

# Embedding Model
- Model: text-embedding-3-small
- Dimensions: 1536
- Batch Size: 100 chunks
- Rate Limiting: 3000 RPM
```

#### 2.2 Vector Store Integration

**`backend/app/rag/retrieval.py`**

**Core Functionality:**
1. **Similarity Search with FGAC**
   ```python
   async def similarity_search(
       query: str,
       tenant_id: str,
       top_k: int = 5,
       similarity_threshold: float = 0.7
   ) -> List[Document]:
       # 1. Generate query embedding
       # 2. Execute hybrid search (vector + metadata filter)
       # 3. Apply tenant_id filter (MANDATORY)
       # 4. Rerank results
       # 5. Return top_k documents
   ```

2. **Hybrid Search Pattern**
   ```sql
   SELECT 
       dc.id,
       dc.content,
       dc.metadata,
       1 - (dc.embedding <=> query_embedding) as similarity
   FROM document_chunks dc
   WHERE dc.tenant_id = $1  -- FGAC enforcement
   AND 1 - (dc.embedding <=> query_embedding) > $2
   ORDER BY dc.embedding <=> query_embedding
   LIMIT $3;
   ```

3. **LlamaIndex VectorStoreIndex**
   - Custom Supabase vector store adapter
   - Automatic metadata filtering
   - Query transformation for better retrieval

#### 2.3 Advanced RAG Features

**Retrieval Optimization:**
- **Query Transformation**: Rewrite user queries for better matching
- **Hypothetical Document Embeddings (HyDE)**: Generate hypothetical answers
- **Reranking**: Use cross-encoder for result refinement
- **Contextual Compression**: Remove irrelevant information

**Metadata Enrichment:**
```python
chunk_metadata = {
    "tenant_id": tenant_id,           # CRITICAL for FGAC
    "document_id": document_id,
    "chunk_index": index,
    "source_url": file_url,
    "file_type": file_type,
    "uploaded_by": user_id,
    "upload_date": timestamp,
    "page_number": page_num,          # For PDFs
    "section_title": section           # For structured docs
}
```

---

### **PHASE 3: LangGraph Agent Orchestration** ⏱️ 4-5 days

#### 3.1 Agent State Schema

**`backend/app/agents/state.py`**

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from operator import add

class AgentState(TypedDict):
    """State schema for the RAG agent workflow"""
    
    # Core conversation
    messages: Annotated[Sequence[BaseMessage], add]
    
    # User context
    tenant_id: str
    user_id: str
    session_id: str
    
    # RAG context
    retrieved_documents: list[dict]
    query_rewrite: str | None
    
    # Agent state
    current_step: str
    agent_thoughts: list[str]
    tool_calls: list[dict]
    
    # UI synchronization
    ui_state: dict
    progress: float
    
    # Final output
    final_response: str | None
    citations: list[dict]
```

#### 3.2 LangGraph Workflow Design

**`backend/app/agents/graph.py`**

**Workflow Nodes:**

1. **Query Analysis Node**
   - Classify query intent (factual, analytical, conversational)
   - Determine if RAG retrieval is needed
   - Extract key entities and topics

2. **Query Rewrite Node**
   - Transform query for better retrieval
   - Generate multiple query variations
   - Apply HyDE if beneficial

3. **Retrieval Node** (LlamaIndex Tool)
   - Execute vector similarity search
   - Apply FGAC filtering (tenant_id)
   - Retrieve top-k relevant chunks
   - Emit state: "Searching knowledge base..."

4. **Reranking Node**
   - Cross-encoder reranking
   - Relevance scoring
   - Filter low-quality results

5. **Response Generation Node**
   - Construct prompt with retrieved context
   - Stream LLM response
   - Extract citations
   - Emit state: "Generating response..."

6. **Validation Node**
   - Check response quality
   - Verify citations
   - Detect hallucinations

**Conditional Edges:**
```python
# Routing logic
def should_retrieve(state: AgentState) -> str:
    """Decide if retrieval is needed"""
    if requires_knowledge(state["messages"][-1]):
        return "retrieve"
    return "respond_directly"

def should_rerank(state: AgentState) -> str:
    """Decide if reranking is beneficial"""
    if len(state["retrieved_documents"]) > 10:
        return "rerank"
    return "generate"
```

**Graph Structure:**
```
START → Query Analysis → [Needs RAG?]
                           ├─ Yes → Query Rewrite → Retrieval → Rerank → Generate → Validate → END
                           └─ No  → Direct Response → END
```

#### 3.3 Agent Tools

**`backend/app/agents/tools.py`**

**Tool 1: Vector Search Tool**
```python
@tool
async def search_knowledge_base(
    query: str,
    tenant_id: str,
    top_k: int = 5
) -> list[dict]:
    """Search the vector database for relevant documents"""
    # Calls LlamaIndex retrieval pipeline
    # Enforces FGAC filtering
    # Returns structured results
```

**Tool 2: SQL Query Tool** (for structured data)
```python
@tool
async def query_database(
    natural_language_query: str,
    tenant_id: str
) -> dict:
    """Convert natural language to SQL and execute"""
    # Text-to-SQL with LlamaIndex
    # Read-only execution
    # Tenant-scoped queries
```

**Tool 3: Data Visualization Tool**
```python
@tool
async def create_visualization(
    data: dict,
    chart_type: str
) -> dict:
    """Generate chart configuration for frontend rendering"""
    # Returns JSON schema for Chart.js/Plotly
    # Frontend renders the actual chart
```

#### 3.4 Durable Execution & Checkpointing

**Features:**
- **Persistence**: Save agent state to Supabase
- **Resume**: Continue from last checkpoint on failure
- **Human-in-the-Loop**: Pause for approval before sensitive actions
- **Time-Travel Debugging**: Replay agent execution

**Implementation:**
```python
from langgraph.checkpoint.postgres import PostgresSaver

# Configure checkpointer
checkpointer = PostgresSaver(
    connection_string=SUPABASE_CONNECTION_STRING
)

# Create graph with persistence
graph = StateGraph(AgentState)
# ... add nodes and edges ...
app = graph.compile(checkpointer=checkpointer)

# Execute with checkpointing
result = await app.ainvoke(
    initial_state,
    config={"configurable": {"thread_id": session_id}}
)
```

---

### **PHASE 4: CopilotKit Frontend Integration** ⏱️ 3-4 days

#### 4.1 CopilotKit Setup

**`src/lib/copilotkit-config.ts`**

```typescript
import { CopilotKitConfig } from '@copilotkit/react-core';

export const copilotConfig: CopilotKitConfig = {
  publicApiKey: import.meta.env.VITE_COPILOTKIT_PUBLIC_KEY,
  runtimeUrl: `${import.meta.env.VITE_BACKEND_API_URL}/copilotkit`,
  transcribeAudioUrl: '/api/transcribe',
  textToSpeechUrl: '/api/tts',
};
```

**`src/App.tsx` - Wrap with CopilotKit Provider**

```typescript
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';

function App() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </CopilotKit>
  );
}
```

#### 4.2 Generative UI Components

**`src/components/chat/AgentStateDisplay.tsx`**

```typescript
import { useCoAgentStateRender } from '@copilotkit/react-core';

export function AgentStateDisplay() {
  const { state } = useCoAgentStateRender({
    name: "rag_agent",
    render: ({ state }) => {
      return (
        <div className="agent-state">
          {/* Current Step */}
          <div className="step-indicator">
            <Loader2 className="animate-spin" />
            <span>{state.current_step}</span>
          </div>
          
          {/* Progress Bar */}
          <div className="progress-bar">
            <div style={{ width: `${state.progress}%` }} />
          </div>
          
          {/* Agent Thoughts */}
          {state.agent_thoughts.map((thought, i) => (
            <div key={i} className="thought">
              <Brain size={16} />
              <span>{thought}</span>
            </div>
          ))}
          
          {/* Retrieved Documents Preview */}
          {state.retrieved_documents.length > 0 && (
            <div className="documents-preview">
              <FileText size={16} />
              <span>Found {state.retrieved_documents.length} relevant documents</span>
            </div>
          )}
        </div>
      );
    }
  });
  
  return state;
}
```

**`src/components/chat/DataVisualization.tsx`**

```typescript
import { useCopilotAction } from '@copilotkit/react-core';
import { Line, Bar, Pie } from 'recharts';

export function DataVisualization() {
  const [chartData, setChartData] = useState(null);
  
  useCopilotAction({
    name: "render_chart",
    description: "Render a data visualization",
    parameters: [
      {
        name: "data",
        type: "object",
        description: "Chart data and configuration"
      }
    ],
    handler: async ({ data }) => {
      setChartData(data);
    }
  });
  
  if (!chartData) return null;
  
  return (
    <div className="chart-container">
      {chartData.type === 'line' && <Line data={chartData.data} />}
      {chartData.type === 'bar' && <Bar data={chartData.data} />}
      {chartData.type === 'pie' && <Pie data={chartData.data} />}
    </div>
  );
}
```

#### 4.3 Streaming Integration

**`src/hooks/useStreamingResponse.ts`**

```typescript
import { useEffect, useState } from 'react';

export function useStreamingResponse(sessionId: string) {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  const streamResponse = async (message: string) => {
    setIsStreaming(true);
    setResponse('');
    
    const eventSource = new EventSource(
      `${API_URL}/chat/stream?session_id=${sessionId}&message=${encodeURIComponent(message)}`
    );
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'token') {
        setResponse(prev => prev + data.content);
      } else if (data.type === 'state') {
        // Update agent state in UI
        updateAgentState(data.state);
      } else if (data.type === 'done') {
        setIsStreaming(false);
        eventSource.close();
      }
    };
    
    eventSource.onerror = () => {
      setIsStreaming(false);
      eventSource.close();
    };
  };
  
  return { response, isStreaming, streamResponse };
}
```

#### 4.4 Enhanced Chat Interface

**`src/components/chat/EnhancedChatInterface.tsx`**

```typescript
import { CopilotChat } from '@copilotkit/react-ui';
import { AgentStateDisplay } from './AgentStateDisplay';
import { DataVisualization } from './DataVisualization';

export function EnhancedChatInterface() {
  return (
    <div className="chat-container">
      <CopilotChat
        labels={{
          title: "RAG Assistant",
          initial: "Ask me anything about your documents..."
        }}
        makeSystemMessage={(message) => ({
          role: "system",
          content: message
        })}
        showResponseButton={true}
      >
        {/* Agent State Visualization */}
        <AgentStateDisplay />
        
        {/* Data Visualizations */}
        <DataVisualization />
      </CopilotChat>
    </div>
  );
}
```

---

### **PHASE 5: Security & Multi-Tenancy** ⏱️ 2-3 days

#### 5.1 JWT Authentication

**`backend/app/security/auth.py`**

```python
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Verify JWT token and extract tenant_id"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        # Extract critical claims
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")  # Custom claim
        
        if not user_id or not tenant_id:
            raise HTTPException(401, "Invalid token claims")
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "email": payload.get("email")
        }
    except JWTError:
        raise HTTPException(401, "Invalid authentication token")
```

#### 5.2 Fine-Grained Access Control (FGAC)

**`backend/app/security/fgac.py`**

```python
from typing import List
from app.rag.retrieval import Document

class FGACEnforcer:
    """Enforce tenant isolation at every data access point"""
    
    @staticmethod
    def filter_documents(
        documents: List[Document],
        tenant_id: str
    ) -> List[Document]:
        """Filter documents by tenant_id"""
        return [
            doc for doc in documents
            if doc.metadata.get("tenant_id") == tenant_id
        ]
    
    @staticmethod
    def validate_access(
        resource_tenant_id: str,
        user_tenant_id: str
    ) -> bool:
        """Validate user has access to resource"""
        if resource_tenant_id != user_tenant_id:
            raise HTTPException(
                403,
                "Access denied: Resource belongs to different tenant"
            )
        return True
```

**Critical Implementation Points:**

1. **Mandatory Tenant Filter in ALL Queries**
   ```python
   # CORRECT ✅
   results = await vector_store.similarity_search(
       query_embedding,
       filter={"tenant_id": user_tenant_id},  # MANDATORY
       top_k=5
   )
   
   # WRONG ❌ - Security vulnerability!
   results = await vector_store.similarity_search(
       query_embedding,
       top_k=5
   )
   ```

2. **Validate at API Boundary**
   ```python
   @router.post("/chat")
   async def chat_endpoint(
       request: ChatRequest,
       auth: dict = Depends(verify_token)
   ):
       # Extract tenant_id from JWT
       tenant_id = auth["tenant_id"]
       
       # Pass to agent - NEVER trust client-provided tenant_id
       response = await agent.run(
           query=request.message,
           tenant_id=tenant_id  # From JWT, not request body
       )
   ```

3. **Audit Logging**
   ```python
   async def log_access(
       user_id: str,
       tenant_id: str,
       action: str,
       resource_id: str
   ):
       """Log all data access for compliance"""
       await supabase.table("access_logs").insert({
           "user_id": user_id,
           "tenant_id": tenant_id,
           "action": action,
           "resource_id": resource_id,
           "timestamp": datetime.utcnow()
       })
   ```

#### 5.3 Frontend Token Management

**`src/lib/api-client.ts`**

```typescript
import { supabase } from './supabase';

export class APIClient {
  private baseURL: string;
  
  constructor() {
    this.baseURL = import.meta.env.VITE_BACKEND_API_URL;
  }
  
  private async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.access_token) {
      throw new Error('No active session');
    }
    
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    };
  }
  
  async post<T>(endpoint: string, body: any): Promise<T> {
    const headers = await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const apiClient = new APIClient();
```

---

### **PHASE 6: Real-Time Streaming (SSE)** ⏱️ 2 days

#### 6.1 Backend SSE Implementation

**`backend/app/api/streaming.py`**

```python
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from app.agents.graph import agent_graph

router = APIRouter()

@router.get("/chat/stream")
async def stream_chat(
    session_id: str,
    message: str,
    auth: dict = Depends(verify_token)
):
    """Stream agent responses via SSE"""
    
    async def event_generator():
        tenant_id = auth["tenant_id"]
        user_id = auth["user_id"]
        
        # Initialize agent state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "tenant_id": tenant_id,
            "user_id": user_id,
            "session_id": session_id,
            "current_step": "initializing",
            "progress": 0.0
        }
        
        # Stream agent execution
        async for event in agent_graph.astream(
            initial_state,
            config={"configurable": {"thread_id": session_id}}
        ):
            # Emit state updates
            if "current_step" in event:
                yield {
                    "event": "state",
                    "data": json.dumps({
                        "type": "state",
                        "step": event["current_step"],
                        "progress": event.get("progress", 0)
                    })
                }
            
            # Emit token chunks
            if "token" in event:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "token",
                        "content": event["token"]
                    })
                }
            
            # Emit final response
            if "final_response" in event:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "done",
                        "response": event["final_response"],
                        "citations": event.get("citations", [])
                    })
                }
    
    return EventSourceResponse(event_generator())
```

#### 6.2 Frontend SSE Consumer

**Already covered in Phase 4.3** - `useStreamingResponse` hook

---

### **PHASE 7: Enterprise Data Connectors** ⏱️ 3-4 days

#### 7.1 Base Connector Interface

**`backend/app/connectors/base.py`**

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class BaseConnector(ABC):
    """Base class for all data source connectors"""
    
    def __init__(self, config: dict, tenant_id: str):
        self.config = config
        self.tenant_id = tenant_id
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the data source"""
        pass
    
    @abstractmethod
    async def list_documents(self) -> list[dict]:
        """List available documents"""
        pass
    
    @abstractmethod
    async def fetch_document(self, doc_id: str) -> bytes:
        """Fetch document content"""
        pass
    
    @abstractmethod
    async def sync(self) -> AsyncIterator[dict]:
        """Sync documents from source"""
        pass
```

#### 7.2 S3 Connector

**`backend/app/connectors/s3.py`**

```python
import boto3
from app.connectors.base import BaseConnector

class S3Connector(BaseConnector):
    """Amazon S3 connector"""
    
    async def authenticate(self) -> bool:
        self.client = boto3.client(
            's3',
            aws_access_key_id=self.config['access_key'],
            aws_secret_access_key=self.config['secret_key'],
            region_name=self.config.get('region', 'us-east-1')
        )
        return True
    
    async def list_documents(self) -> list[dict]:
        bucket = self.config['bucket']
        prefix = self.config.get('prefix', '')
        
        response = self.client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        return [
            {
                'id': obj['Key'],
                'name': obj['Key'].split('/')[-1],
                'size': obj['Size'],
                'modified': obj['LastModified']
            }
            for obj in response.get('Contents', [])
        ]
    
    async def fetch_document(self, doc_id: str) -> bytes:
        bucket = self.config['bucket']
        response = self.client.get_object(Bucket=bucket, Key=doc_id)
        return response['Body'].read()
    
    async def sync(self):
        """Sync all documents from S3"""
        documents = await self.list_documents()
        
        for doc in documents:
            content = await self.fetch_document(doc['id'])
            
            # Process and ingest
            yield {
                'status': 'processing',
                'document': doc['name'],
                'progress': documents.index(doc) / len(documents)
            }
            
            await ingest_document(
                content=content,
                metadata={
                    'tenant_id': self.tenant_id,
                    'source': 's3',
                    'source_id': doc['id'],
                    **doc
                }
            )
```

#### 7.3 SharePoint Connector

**`backend/app/connectors/sharepoint.py`**

```python
from office365.sharepoint.client_context import ClientContext
from app.connectors.base import BaseConnector

class SharePointConnector(BaseConnector):
    """Microsoft SharePoint connector"""
    
    async def authenticate(self) -> bool:
        self.ctx = ClientContext(self.config['site_url']).with_credentials(
            User
