# 🚀 Phase 1, 2, 3 Implementation Plan

**Target Phases:**
- Phase 1: Foundation & Core Dependencies (Complete remaining 10%)
- Phase 2: RAG Pipeline with LlamaIndex (Complete remaining 20%)
- Phase 3: LangGraph Agent Orchestration (Complete 100%)

**Total Estimated Time:** 6-8 days
**Recommended Order:** Phase 1 → Phase 2 → Phase 3

---

## 📋 PHASE 1: Foundation & Core Dependencies (Remaining Tasks)

**Status:** 90% Complete ✅  
**Remaining Time:** 1-2 hours  
**Priority:** CRITICAL (Blocks all other work)

### 1.1 Environment Configuration ⚠️ CRITICAL

#### Frontend Environment Setup

**Create `.env` file:**

```bash
# .env (project root)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
VITE_BACKEND_URL=http://localhost:8000
```

**Create `.env.example` template:**

```bash
# .env.example
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_BACKEND_URL=http://localhost:8000
```

#### Backend Environment Setup

**Create `backend/.env` file:**

```bash
# backend/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
SUPABASE_ANON_KEY=your-anon-key-here
JWT_SECRET_KEY=generate-with-openssl-rand-hex-32
OPENAI_API_KEY=sk-your-openai-key-here
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
LOG_LEVEL=INFO

# Optional: LangSmith for tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=agentic-rag-platform
```

**Create `backend/.env.example` template:**

```bash
# backend/.env.example
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_ANON_KEY=
JWT_SECRET_KEY=
OPENAI_API_KEY=
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=agentic-rag-platform
```

**Generate JWT Secret:**

```bash
# Generate a secure JWT secret
openssl rand -hex 32
```

### 1.2 Install Backend Dependencies ⚠️ CRITICAL

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- langchain==0.1.0
- langgraph==0.0.40
- llama-index==0.10.0
- supabase==2.3.0
- pydantic==2.5.0
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4
- python-multipart==0.0.6
- openai==1.10.0
- tiktoken==0.5.2
- tenacity==8.2.3

### 1.3 Database Extensions Setup

**Enable pgvector in Supabase:**

1. Go to Supabase Dashboard → Database → Extensions
2. Search for "vector"
3. Enable "pgvector" extension
4. Verify with SQL:

```sql
-- Check if pgvector is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Test vector operations
SELECT '[1,2,3]'::vector;
```

### 1.4 Create Storage Bucket

**In Supabase Dashboard:**

1. Go to Storage → Create bucket
2. Name: `documents`
3. Public: No (private)
4. File size limit: 50MB
5. Allowed MIME types: 
   - application/pdf
   - application/vnd.openxmlformats-officedocument.wordprocessingml.document
   - text/plain
   - text/markdown
   - text/html

**Set Storage Policies:**

```sql
-- Policy: Users can upload to their tenant folder
CREATE POLICY "Users can upload documents to their tenant"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'documents' AND
  (storage.foldername(name))[1] = auth.jwt() ->> 'tenant_id'
);

-- Policy: Users can read from their tenant folder
CREATE POLICY "Users can read documents from their tenant"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'documents' AND
  (storage.foldername(name))[1] = auth.jwt() ->> 'tenant_id'
);

-- Policy: Users can delete from their tenant folder
CREATE POLICY "Users can delete documents from their tenant"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'documents' AND
  (storage.foldername(name))[1] = auth.jwt() ->> 'tenant_id'
);
```

### 1.5 Verification Checklist

- [ ] Frontend `.env` file created with valid credentials
- [ ] Backend `.env` file created with valid credentials
- [ ] JWT secret generated and added
- [ ] Python virtual environment created
- [ ] All backend dependencies installed successfully
- [ ] pgvector extension enabled in Supabase
- [ ] `documents` storage bucket created
- [ ] Storage policies configured
- [ ] Can start frontend: `npm run dev`
- [ ] Can start backend: `cd backend && python -m app.main`

---

## 📋 PHASE 2: RAG Pipeline with LlamaIndex (Remaining Tasks)

**Status:** 80% Complete 🟡  
**Remaining Time:** 2-3 hours  
**Dependencies:** Phase 1 must be complete

### 2.1 Complete LlamaIndex Integration

**Create `backend/app/rag/llama_index.py`:**

```python
"""
LlamaIndex integration for RAG pipeline
"""
from typing import List, Optional
from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext,
    Settings
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.supabase import SupabaseVectorStore

from app.config import get_settings
from app.rag.embeddings import EmbeddingGenerator

settings = get_settings()


class LlamaIndexRAG:
    """LlamaIndex RAG pipeline"""
    
    def __init__(self):
        # Configure LlamaIndex settings
        Settings.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY
        )
        Settings.llm = OpenAI(
            model="gpt-4-turbo-preview",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize vector store
        self.vector_store = SupabaseVectorStore(
            postgres_connection_string=self._get_connection_string(),
            collection_name="document_chunks",
            dimension=1536  # OpenAI embedding dimension
        )
        
        # Initialize storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
    
    def _get_connection_string(self) -> str:
        """Get PostgreSQL connection string from Supabase URL"""
        # Convert Supabase URL to PostgreSQL connection string
        # Example: https://xxx.supabase.co -> postgresql://postgres:password@xxx.supabase.co:5432/postgres
        supabase_url = settings.SUPABASE_URL.replace("https://", "")
        return f"postgresql://postgres:{settings.SUPABASE_SERVICE_KEY}@{supabase_url}:5432/postgres"
    
    async def create_index(
        self,
        documents: List[Document],
        tenant_id: str
    ) -> VectorStoreIndex:
        """
        Create vector index from documents
        
        Args:
            documents: List of LlamaIndex Document objects
            tenant_id: Tenant ID for multi-tenancy
            
        Returns:
            VectorStoreIndex
        """
        # Add tenant_id to document metadata
        for doc in documents:
            doc.metadata["tenant_id"] = tenant_id
        
        # Create index
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            show_progress=True
        )
        
        return index
    
    async def query(
        self,
        query_text: str,
        tenant_id: str,
        top_k: int = 5
    ) -> dict:
        """
        Query the RAG system
        
        Args:
            query_text: User query
            tenant_id: Tenant ID for filtering
            top_k: Number of results to return
            
        Returns:
            Query response with sources
        """
        # Load index from vector store
        index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context
        )
        
        # Create query engine with metadata filtering
        query_engine = index.as_query_engine(
            similarity_top_k=top_k,
            filters={"tenant_id": tenant_id}
        )
        
        # Execute query
        response = query_engine.query(query_text)
        
        # Format response
        return {
            "answer": str(response),
            "sources": [
                {
                    "text": node.text,
                    "score": node.score,
                    "metadata": node.metadata
                }
                for node in response.source_nodes
            ]
        }
    
    async def add_documents(
        self,
        documents: List[Document],
        tenant_id: str
    ) -> None:
        """
        Add documents to existing index
        
        Args:
            documents: List of documents to add
            tenant_id: Tenant ID
        """
        # Add tenant_id to metadata
        for doc in documents:
            doc.metadata["tenant_id"] = tenant_id
        
        # Load existing index
        index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context
        )
        
        # Insert documents
        for doc in documents:
            index.insert(doc)


# Singleton instance
llama_rag = LlamaIndexRAG()
```

### 2.2 Create RAG API Endpoints

**Create `backend/app/api/rag.py`:**

```python
"""
RAG API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

from app.security.auth import get_current_user
from app.rag.ingestion import DocumentIngestionPipeline
from app.rag.llama_index import llama_rag
from llama_index.core import Document

router = APIRouter(prefix="/api/rag", tags=["RAG"])


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Ingest a document into the RAG system
    """
    try:
        # Initialize ingestion pipeline
        pipeline = DocumentIngestionPipeline()
        
        # Read file content
        content = await file.read()
        
        # Process document
        result = await pipeline.process_document(
            file_content=content,
            filename=file.filename,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"]
        )
        
        return {
            "status": "success",
            "document_id": result["document_id"],
            "chunks_created": result["chunks_created"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Query the RAG system
    """
    try:
        result = await llama_rag.query(
            query_text=request.query,
            tenant_id=current_user["tenant_id"],
            top_k=request.top_k
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    List all documents for the current tenant
    """
    # TODO: Implement document listing from database
    pass


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a document and its chunks
    """
    # TODO: Implement document deletion
    pass
```

### 2.3 Update Main App to Include RAG Routes

**Update `backend/app/main.py`:**

```python
# Add this import
from app.api import rag

# Add this line after other router includes
app.include_router(rag.router)
```

### 2.4 Testing the RAG Pipeline

**Create `backend/tests/test_rag.py`:**

```python
"""
Tests for RAG pipeline
"""
import pytest
from app.rag.chunking import ChunkingStrategyFactory
from app.rag.embeddings import EmbeddingGenerator
from app.rag.retrieval import VectorRetriever

@pytest.mark.asyncio
async def test_chunking():
    """Test document chunking"""
    text = "This is a test document. " * 100
    
    chunker = ChunkingStrategyFactory.create_strategy("semantic")
    chunks = await chunker.chunk(text)
    
    assert len(chunks) > 0
    assert all(len(chunk) > 0 for chunk in chunks)


@pytest.mark.asyncio
async def test_embedding_generation():
    """Test embedding generation"""
    generator = EmbeddingGenerator()
    
    texts = ["Hello world", "Test document"]
    embeddings = await generator.generate_embeddings(texts)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1536  # OpenAI embedding dimension


@pytest.mark.asyncio
async def test_retrieval():
    """Test vector retrieval"""
    retriever = VectorRetriever()
    
    # This requires a populated database
    # Skip if not in test environment
    pass
```

### 2.5 Phase 2 Verification Checklist

- [ ] `backend/app/rag/llama_index.py` created
- [ ] `backend/app/api/rag.py` created
- [ ] RAG routes added to main app
- [ ] Test file created
- [ ] Can upload a document via API
- [ ] Document is chunked correctly
- [ ] Embeddings are generated
- [ ] Can query the RAG system
- [ ] Results include relevant sources
- [ ] Multi-tenant filtering works

---

## 📋 PHASE 3: LangGraph Agent Orchestration (Complete Implementation)

**Status:** 0% Complete ⬜  
**Estimated Time:** 4-5 days  
**Dependencies:** Phases 1 & 2 must be complete

### 3.1 Agent State Schema

**Create `backend/app/agents/__init__.py`:**

```python
"""
LangGraph agents module
"""
```

**Create `backend/app/agents/state.py`:**

```python
"""
Agent state schema for LangGraph
"""
from typing import TypedDict, List, Optional, Annotated
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    State schema for the agent workflow
    
    This state is passed between nodes in the LangGraph workflow
    """
    # User context
    tenant_id: str
    user_id: str
    session_id: str
    
    # Conversation
    messages: Annotated[List[dict], operator.add]  # Accumulate messages
    user_query: str
    
    # Query processing
    query_intent: Optional[str]  # classified, retrieval, sql, visualization
    rewritten_query: Optional[str]
    
    # RAG context
    retrieved_documents: List[dict]
    relevance_scores: List[float]
    reranked_documents: Optional[List[dict]]
    
    # Agent reasoning
    agent_thoughts: Annotated[List[str], operator.add]  # Accumulate thoughts
    current_step: str
    tools_used: Annotated[List[str], operator.add]  # Track tool usage
    
    # Response generation
    draft_response: Optional[str]
    final_response: Optional[str]
    citations: List[dict]
    
    # Visualization
    visualization_data: Optional[dict]
    chart_type: Optional[str]
    
    # Metadata
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]
    
    # UI synchronization
    ui_state: dict  # For CopilotKit state rendering


def create_initial_state(
    tenant_id: str,
    user_id: str,
    session_id: str,
    user_query: str
) -> AgentState:
    """Create initial agent state"""
    return AgentState(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        messages=[],
        user_query=user_query,
        query_intent=None,
        rewritten_query=None,
        retrieved_documents=[],
        relevance_scores=[],
        reranked_documents=None,
        agent_thoughts=[],
        current_step="initialized",
        tools_used=[],
        draft_response=None,
        final_response=None,
        citations=[],
        visualization_data=None,
        chart_type=None,
        started_at=datetime.utcnow(),
        completed_at=None,
        error=None,
        ui_state={}
    )
```

### 3.2 Agent Nodes

**Create `backend/app/agents/nodes.py`:**

```python
"""
Agent nodes for LangGraph workflow
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.agents.state import AgentState
from app.rag.llama_index import llama_rag
from app.config import get_settings

settings = get_settings()
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.1)


async def query_analysis_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyze the user query to determine intent and required actions
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a query analyzer. Classify the user's query into one of these intents:
        - retrieval: User wants information from documents
        - sql: User wants to query structured data
        - visualization: User wants to see charts/graphs
        - general: General conversation
        
        Also identify if query rewriting would help improve retrieval.
        
        Respond in JSON format:
        {{
            "intent": "retrieval|sql|visualization|general",
            "needs_rewrite": true|false,
            "reasoning": "explanation"
        }}"""),
        ("user", "{query}")
    ])
    
    response = await llm.ainvoke(
        prompt.format_messages(query=state["user_query"])
    )
    
    # Parse response (simplified - add proper JSON parsing)
    intent = "retrieval"  # Default
    
    return {
        "query_intent": intent,
        "agent_thoughts": [f"Analyzed query intent: {intent}"],
        "current_step": "query_analyzed",
        "ui_state": {"step": "Analyzing your question..."}
    }


async def query_rewrite_node(state: AgentState) -> Dict[str, Any]:
    """
    Rewrite the query for better retrieval
    """
    if state["query_intent"] != "retrieval":
        return {"rewritten_query": state["user_query"]}
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Rewrite the user query to be more specific and retrieval-friendly.
        Focus on key terms and concepts. Keep it concise."""),
        ("user", "{query}")
    ])
    
    response = await llm.ainvoke(
        prompt.format_messages(query=state["user_query"])
    )
    
    rewritten = response.content
    
    return {
        "rewritten_query": rewritten,
        "agent_thoughts": [f"Rewrote query: {rewritten}"],
        "current_step": "query_rewritten",
        "ui_state": {"step": "Optimizing search..."}
    }


async def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """
    Retrieve relevant documents using RAG
    """
    query = state.get("rewritten_query") or state["user_query"]
    
    # Use LlamaIndex RAG
    result = await llama_rag.query(
        query_text=query,
        tenant_id=state["tenant_id"],
        top_k=5
    )
    
    return {
        "retrieved_documents": result["sources"],
        "relevance_scores": [doc["score"] for doc in result["sources"]],
        "agent_thoughts": [f"Retrieved {len(result['sources'])} documents"],
        "current_step": "documents_retrieved",
        "tools_used": ["vector_search"],
        "ui_state": {
            "step": "Found relevant information...",
            "documents_count": len(result["sources"])
        }
    }


async def reranking_node(state: AgentState) -> Dict[str, Any]:
    """
    Rerank retrieved documents for relevance
    """
    docs = state["retrieved_documents"]
    
    # Simple reranking based on scores (can be enhanced with cross-encoder)
    sorted_docs = sorted(
        docs,
        key=lambda x: x.get("score", 0),
        reverse=True
    )
    
    return {
        "reranked_documents": sorted_docs[:3],  # Top 3
        "agent_thoughts": ["Reranked documents by relevance"],
        "current_step": "documents_reranked",
        "ui_state": {"step": "Analyzing information..."}
    }


async def response_generation_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate response using retrieved context
    """
    docs = state.get("reranked_documents") or state["retrieved_documents"]
    
    # Build context from documents
    context = "\n\n".join([
        f"Document {i+1}:\n{doc['text']}"
        for i, doc in enumerate(docs[:3])
    ])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant. Answer the user's question based on the provided context.
        Be accurate, concise, and cite your sources.
        
        Context:
        {context}"""),
        ("user", "{query}")
    ])
    
    response = await llm.ainvoke(
        prompt.format_messages(
            context=context,
            query=state["user_query"]
        )
    )
    
    # Extract citations
    citations = [
        {
            "text": doc["text"][:200] + "...",
            "metadata": doc.get("metadata", {})
        }
        for doc in docs[:3]
    ]
    
    return {
        "final_response": response.content,
        "citations": citations,
        "agent_thoughts": ["Generated response with citations"],
        "current_step": "response_generated",
        "completed_at": datetime.utcnow(),
        "ui_state": {"step": "Complete", "done": True}
    }


async def validation_node(state: AgentState) -> Dict[str, Any]:
    """
    Validate the generated response
    """
    response = state.get("final_response", "")
    
    # Simple validation (can be enhanced)
    is_valid = len(response) > 10 and not response.startswith("I don't know")
    
    if not is_valid:
        return {
            "error": "Response validation failed",
            "agent_thoughts": ["Response needs improvement"],
            "current_step": "validation_failed"
        }
    
    return {
        "agent_thoughts": ["Response validated successfully"],
        "current_step": "validated"
    }
```

### 3.3 Agent Tools

**Create `backend/app/agents/tools.py`:**

```python
"""
Tools for LangGraph agents
"""
from typing import List, Dict, Any
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

from app.rag.llama_index import llama_rag


class VectorSearchTool:
    """Tool for vector similarity search"""
    
    def __init__(self):
        self.name = "vector_search"
        self.description = "Search for relevant documents using vector similarity"
    
    async def run(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Execute vector search"""
        result = await llama_rag.query(
            query_text=query,
            tenant_id=tenant_id,
            top_k=top_k
        )
        return result["sources"]


class SQLQueryTool:
    """Tool for text-to-SQL queries"""
    
    def __init__(self):
        self.name = "sql_query"
        self.description = "Convert natural language to SQL and execute queries"
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview")
    
    async def run(
        self,
        query: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Convert query to SQL and execute
        
        NOTE: This is a simplified version. In production:
        - Use proper SQL injection prevention
        - Validate queries before execution
        - Limit query complexity
        - Add query timeout
        """
        # TODO: Implement text-to-SQL conversion
        # TODO: Execute query safely
        # TODO: Return results
        
        return {
            "error": "SQL tool not yet implemented",
            "results": []
        }


class DataVisualizationTool:
    """Tool for creating data visualizations"""
    
    def __init__(self):
        self.name = "data_visualization"
        self.description = "Create charts and visualizations from data"
    
    async def run(
        self,
        data: List[Dict[str, Any]],
        chart_type: str = "bar"
    ) -> Dict[str, Any]:
        """
        Generate visualization configuration
        
        Args:
            data: Data to visualize
            chart_type: Type of chart (bar, line, pie, scatter)
            
        Returns:
            Visualization configuration for frontend
        """
        return {
            "type": chart_type,
            "data": data,
            "config": {
                "responsive": True,
                "maintainAspectRatio": False
            }
        }


# Tool registry
TOOLS = {
    "vector_search": VectorSearchTool(),
    "sql_query": SQLQueryTool(),
    "data_visualization": DataVisualizationTool()
}


def get_tool(tool_name: str):
    """Get tool by name"""
    return TOOLS.get(tool_name)
```

### 3.4 LangGraph Workflow

**Create `backend/app/agents/graph.py`:**

```python
"""
LangGraph workflow definition
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from app.agents.state import AgentState, create_initial_state
from app.agents.nodes import (
    query_analysis_node,
    query_rewrite_node,
    retrieval_node,
    reranking_node,
    response_generation_node,
    validation_node
)
from app.config import get_settings

settings = get_settings()


def should_retrieve(state: AgentState) -> str:
    """Determine if we should retrieve documents"""
    intent = state.get("query_intent")
    if intent in ["retrieval", "sql"]:
        return "retrieve"
    return "respond"


def should_rerank(state: AgentState) -> str:
    """Determine if we should rerank documents"""
    docs = state.get("retrieved_documents", [])
    if len(docs) > 3:
        return "rerank"
    return "respond"


def should_retry(state: AgentState) -> str:
    """Determine if we should retry response generation"""
    error = state.get("error")
    if error:
        return "rewrite"
    return "end"


def create_agent_graph():
    """
    Create the LangGraph workflow
    
    Workflow:
    1. Analyze query intent
    2. Rewrite query if needed
    3. Retrieve documents (if needed)
    4. Rerank documents (if many results)
    5. Generate response
    6. Validate response
    7. Return or retry
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", query_analysis_node)
    workflow.add_node("rewrite", query_rewrite_node)
    workflow.add_node("retrieve", retrieval_node)
    workflow.add_node("rerank", reranking_node)
    workflow.add_node("respond", response_generation_node)
    workflow.add_node("validate", validation_node)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    # Add edges
    workflow.add_edge("analyze", "rewrite")
    
    # Conditional: retrieve or skip to response
    workflow.add_conditional_edges(
        "rewrite",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "respond": "respond"
        }
    )
    
    # Conditional: rerank or skip to response
    workflow.add_conditional_edges(
        "retrieve",
        should_rerank,
        {
            "rerank": "rerank",
            "respond": "respond"
        }
    )
    
    workflow.add_edge("rerank", "respond")
    workflow.add_edge("respond", "validate")
    
    # Conditional: retry or end
    workflow.add_conditional_edges(
        "validate",
        should_retry,
        {
            "rewrite": "rewrite",
            "end": END
        }
    )
    
    # Compile graph
    graph = workflow.compile()
    
    return graph


# Create graph instance
agent_graph = create_agent_graph()


async def run_agent(
    user_query: str,
    tenant_id: str,
    user_id: str,
    session_id: str
) -> AgentState:
    """
    Run the agent workflow
    
    Args:
        user_query: User's question
        tenant_id: Tenant ID
        user_id: User ID
        session_id: Session ID
        
    Returns:
        Final agent state
    """
    # Create initial state
    initial_state = create_initial_state(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        user_query=user_query
    )
    
    # Run graph
    final_state = await agent_graph.ainvoke(initial_state)
    
    return final_state
```

### 3.5 Durable Execution with Checkpointing

**Create `backend/app/agents/checkpointer.py`:**

```python
"""
Checkpointing for durable agent execution
"""
from langgraph.checkpoint.postgres import PostgresSaver
from app.config import get_settings

settings = get_settings()


def get_checkpointer() -> PostgresSaver:
    """
    Get PostgreSQL checkpointer for durable execution
    
    This allows:
    - Resuming from failures
    - Time-travel debugging
    - Human-in-the-loop workflows
    """
    connection_string = _get_connection_string()
    
    checkpointer = PostgresSaver(
        connection_string=connection_string,
        # Table will be created automatically
    )
    
    return checkpointer


def _get_connection_string() -> str:
    """Get PostgreSQL connection string"""
    # Convert Supabase URL to PostgreSQL connection string
    supabase_url = settings.SUPABASE_URL.replace("https://", "")
    return f"postgresql://postgres:{settings.SUPABASE_SERVICE_KEY}@{supabase_url}:5432/postgres"


# Usage in graph:
# graph = workflow.compile(checkpointer=get_checkpointer())
```

### 3.6 Agent API Endpoints

**Create `backend/app/api/agents.py`:**

```python
"""
Agent API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.security.auth import get_current_user
from app.agents.graph import run_agent
from app.agents.state import AgentState

router = APIRouter(prefix="/api/agents", tags=["Agents"])


class AgentRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    answer: str
    citations: list
    thoughts: list
    visualization: Optional[dict] = None


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    request: AgentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat with the AI agent
    
    The agent will:
    1. Analyze the query
    2. Retrieve relevant information
    3. Generate a response with citations
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{current_user['user_id']}_{int(time.time())}"
        
        # Run agent
        final_state = await run_agent(
            user_query=request.query,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            session_id=session_id
        )
        
        # Check for errors
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
        
        return AgentResponse(
            answer=final_state.get("final_response", ""),
            citations=final_state.get("citations", []),
            thoughts=final_state.get("agent_thoughts", []),
            visualization=final_state.get("visualization_data")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get agent session history
    """
    # TODO: Implement session retrieval from checkpoints
    pass


@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Resume an agent session from checkpoint
    """
    # TODO: Implement session resumption
    pass
```

### 3.7 Update Main App

**Update `backend/app/main.py`:**

```python
# Add this import
from app.api import agents

# Add this line after other router includes
app.include_router(agents.router)
```

### 3.8 Testing the Agent System

**Create `backend/tests/test_agents.py`:**

```python
"""
Tests for agent system
"""
import pytest
from app.agents.state import create_initial_state
from app.agents.nodes import (
    query_analysis_node,
    query_rewrite_node,
    retrieval_node
)


@pytest.mark.asyncio
async def test_query_analysis():
    """Test query analysis node"""
    state = create_initial_state(
        tenant_id="test-tenant",
        user_id="test-user",
        session_id="test-session",
        user_query="What is machine learning?"
    )
    
    result = await query_analysis_node(state)
    
    assert "query_intent" in result
    assert result["query_intent"] in ["retrieval", "sql", "visualization", "general"]


@pytest.mark.asyncio
async def test_query_rewrite():
    """Test query rewrite node"""
    state = create_initial_state(
        tenant_id="test-tenant",
        user_id="test-user",
        session_id="test-session",
        user_query="What's ML?"
    )
    state["query_intent"] = "retrieval"
    
    result = await query_rewrite_node(state)
    
    assert "rewritten_query" in result
    assert len(result["rewritten_query"]) > 0


@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test complete agent workflow"""
    # This requires full setup
    # Skip if not in test environment
    pass
```

### 3.9 Phase 3 Verification Checklist

- [ ] All agent files created in `backend/app/agents/`
- [ ] Agent state schema defined
- [ ] All agent nodes implemented
- [ ] Agent tools created
- [ ] LangGraph workflow defined
- [ ] Checkpointing configured
- [ ] Agent API endpoints created
- [ ] Routes added to main app
- [ ] Tests created
- [ ] Can send query to agent endpoint
- [ ] Agent analyzes query correctly
- [ ] Agent retrieves relevant documents
- [ ] Agent generates response with citations
- [ ] Agent thoughts are tracked
- [ ] Checkpointing works (can resume)

---

## 🎯 IMPLEMENTATION ROADMAP

### Week 1: Foundation (Phase 1)

**Day 1: Environment Setup**
- [ ] Morning: Create all .env files
- [ ] Afternoon: Install backend dependencies
- [ ] Evening: Verify setup, test connections

**Day 2: Database Setup**
- [ ] Morning: Enable pgvector extension
- [ ] Afternoon: Create storage bucket and policies
- [ ] Evening: Test database operations

### Week 2: RAG Pipeline (Phase 2)

**Day 3: LlamaIndex Integration**
- [ ] Morning: Create `llama_index.py`
- [ ] Afternoon: Test document indexing
- [ ] Evening: Test querying

**Day 4: RAG API**
- [ ] Morning: Create RAG endpoints
- [ ] Afternoon: Test document ingestion
- [ ] Evening: Test query endpoint

**Day 5: Testing & Refinement**
- [ ] Morning: Write tests
- [ ] Afternoon: Fix bugs
- [ ] Evening: Performance testing

### Week 3-4: Agent System (Phase 3)

**Day 6-7: Agent State & Nodes**
- [ ] Create state schema
- [ ] Implement all nodes
- [ ] Test each node individually

**Day 8-9: Agent Tools & Workflow**
- [ ] Create agent tools
- [ ] Define LangGraph workflow
- [ ] Test workflow execution

**Day 10-11: Checkpointing & API**
- [ ] Setup checkpointing
- [ ] Create agent endpoints
- [ ] Test end-to-end

**Day 12: Testing & Documentation**
- [ ] Comprehensive testing
- [ ] Fix bugs
- [ ] Update documentation

---

## 🧪 TESTING STRATEGY

### Unit Tests
```bash
# Run all tests
cd backend
pytest

# Run specific test file
pytest tests/test_rag.py

# Run with coverage
pytest --cov=app tests/
```

### Integration Tests
```bash
# Test RAG pipeline
curl -X POST http://localhost:8000/api/rag/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'

# Test agent
curl -X POST http://localhost:8000/api/agents/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain neural networks"}'
```

### Manual Testing Checklist
- [ ] Upload a PDF document
- [ ] Verify document is chunked
- [ ] Verify embeddings are generated
- [ ] Query the RAG system
- [ ] Verify relevant results returned
- [ ] Test agent chat
- [ ] Verify agent thoughts are tracked
- [ ] Verify citations are included
- [ ] Test multi-tenant isolation
- [ ] Test error handling

---

## 🚨 COMMON ISSUES & SOLUTIONS

### Issue 1: OpenAI API Rate Limits
**Solution:** Implement exponential backoff (already in code)

### Issue 2: Vector Search Returns No Results
**Solution:** 
- Check if documents are indexed
- Verify tenant_id filtering
- Check embedding dimensions match

### Issue 3: Agent Workflow Hangs
**Solution:**
- Check for infinite loops in conditional edges
- Add timeout to LLM calls
- Check database connections

### Issue 4: Memory Issues with Large Documents
**Solution:**
- Implement streaming for large files
- Process documents in batches
- Increase chunk size limits

---

## 📊 SUCCESS METRICS

### Phase 1 Success Criteria
- ✅ All environment variables configured
- ✅ Backend starts without errors
- ✅ Frontend connects to backend
- ✅ Database operations work

### Phase 2 Success Criteria
- ✅ Documents can be uploaded
- ✅ Documents are chunked correctly
- ✅ Embeddings are generated
- ✅ Vector search returns relevant results
- ✅ Multi-tenant filtering works

### Phase 3 Success Criteria
- ✅ Agent analyzes queries correctly
- ✅ Agent retrieves relevant context
- ✅ Agent generates accurate responses
- ✅ Citations are included
- ✅ Agent thoughts are tracked
- ✅ Workflow completes successfully
- ✅ Checkpointing works

---

## 🎓 LEARNING RESOURCES

### LangGraph
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Tutorials](https://github.com/langchain-ai/langgraph/tree/main/examples)

### LlamaIndex
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [LlamaIndex Examples](https://github.com/run-llama/llama_index/tree/main/docs/examples)

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

---

## 📝 NEXT STEPS AFTER PHASE 3

Once Phases 1-3 are complete, you'll have:
- ✅ Fully functional RAG pipeline
- ✅ Intelligent agent system
- ✅ Multi-tenant architecture
- ✅ Durable execution

**Recommended Next Phases:**
1. **Phase 4: CopilotKit Integration** - Add generative UI
2. **Phase 6: Streaming** - Real-time responses
3. **Phase 5: Security Hardening** - Complete security audit
4. **Phase 7: Data Connectors** - Enterprise integrations

---

## 🤝 GETTING HELP

If you encounter issues:
1. Check the error logs
2. Review the verification checklists
3. Consult the documentation links
4. Ask for specific help with error messages

---

**Ready to start? Let's begin with Phase 1!** 🚀

