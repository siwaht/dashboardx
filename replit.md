# Agentic RAG Platform

## Overview

An enterprise-grade SaaS platform combining Retrieval-Augmented Generation (RAG) with intelligent agent orchestration. Built to handle multi-modal data analysis, real-time collaboration, and advanced analytics workflows.

**Core Purpose:** Enable organizations to interact with their proprietary data through natural language, generating insights via AI agents that can retrieve, analyze, and visualize information from multiple sources.

**Tech Stack:**
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI (Python) with async/await patterns
- Database: Supabase (PostgreSQL + pgvector for vector embeddings)
- AI/ML: LangChain, LangGraph, LlamaIndex, OpenAI
- Security: JWT authentication, Row-Level Security (RLS), multi-tenancy

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Multi-Tenant Architecture
The platform is built from the ground up as a multi-tenant SaaS application. Every user belongs to a tenant (organization), and all data is isolated at the database level using Row-Level Security (RLS) policies. The `tenant_id` column appears throughout the schema, enforcing data separation without application-layer filtering.

### Authentication & Authorization
- Supabase Auth provides JWT-based authentication
- Custom `auth.users` table metadata stores roles (admin, user, viewer) and tenant associations
- Backend validates JWTs and extracts user/tenant context for every request
- Fine-Grained Access Control (FGAC) policies enforce permissions at the database row level
- User management includes account status tracking (active, suspended, disabled)

### RAG Pipeline Architecture
The platform implements a sophisticated RAG system for document understanding:

1. **Document Ingestion:** 
   - Supports PDF, DOCX, TXT, MD, HTML, images, audio, and video
   - Multi-modal processing extracts text via OCR (Tesseract, EasyOCR), tables (Camelot, Tabula), and visual understanding (CLIP, BLIP)
   - Documents are chunked using configurable strategies (recursive, semantic, fixed-size)

2. **Embeddings & Storage:**
   - OpenAI embeddings (text-embedding-3-small by default) convert chunks to vectors
   - pgvector extension stores embeddings in PostgreSQL with HNSW indexing
   - Hybrid search combines vector similarity with BM25 keyword matching

3. **Retrieval:**
   - LlamaIndex manages vector store connections and query orchestration
   - Supports reranking with cross-encoder models for relevance optimization
   - Query rewriting and HyDE (Hypothetical Document Embeddings) enhance retrieval quality
   - MMR (Maximal Marginal Relevance) provides diversity in results

### Agent System (LangGraph)
Intelligent agents orchestrate multi-step reasoning workflows:

- **State Management:** LangGraph maintains conversation state across agent interactions
- **Agent Types:** Data Explorer, Insight Generator, Visualization Agent, Predictive Analytics Agent, Report Generator
- **Tool Integration:** Agents can query databases, perform calculations, generate visualizations, and invoke ML models
- **Plugin Architecture:** Framework-agnostic design supports LangChain, LangGraph, n8n, CrewAI, AutoGen, and custom agents via adapters
- **Agent Registry:** Centralized discovery and capability-based routing

### Analytics Engine
Comprehensive analytics capabilities for data analysis:

- **Data Connectors:** PostgreSQL, MySQL, CSV, Excel, REST APIs, Kafka streaming, WebSocket
- **Analysis Types:** Exploratory, descriptive, diagnostic, predictive, prescriptive, real-time streaming
- **ML Models:** AutoML with hyperparameter tuning, time series forecasting (ARIMA, LSTM), anomaly detection (Isolation Forest, statistical methods)
- **Statistical RAG:** Natural language to SQL conversion with schema understanding
- **Visualization:** Automatic chart type recommendations and Plotly-based rendering

### Frontend Architecture
React-based SPA with component-driven design:

- **State Management:** React Context API for global state (auth, theme)
- **Routing:** File-based routing with protected routes for role-based access
- **UI Components:** Custom component library built on Tailwind CSS with Lucide icons
- **Real-time Updates:** WebSocket integration for live collaboration
- **Chat Interface:** CopilotKit integration for generative UI with streaming responses
- **Visualizations:** Recharts and Plotly for interactive data displays

### Security Architecture
Defense-in-depth security model:

- **Authentication:** Supabase Auth with JWT tokens, refresh token rotation
- **Authorization:** Role-based access control (RBAC) + attribute-based access control (ABAC)
- **Data Isolation:** RLS policies ensure tenant-level data separation
- **Audit Logging:** All user actions tracked in `audit_logs` table with actor, action, resource, timestamp
- **Input Validation:** Pydantic models validate all API inputs
- **Rate Limiting:** Planned token bucket implementation to prevent abuse
- **Encryption:** Sensitive credentials encrypted at rest with AES-256

### Database Design Decisions
PostgreSQL chosen for its vector extension and ACID guarantees:

- **pgvector Extension:** Native vector storage and similarity search with HNSW indexing
- **JSON Support:** JSONB columns store flexible metadata, agent configurations, and execution logs
- **Indexes:** Strategic B-tree and vector indexes optimize common queries
- **Triggers:** Automatic `updated_at` timestamp management
- **Helper Functions:** SQL functions for setup tasks (e.g., `setup_admin_user_profile`)

### API Design
RESTful API with FastAPI conventions:

- **Versioning:** Implicit v1 via `/api/` prefix
- **Authentication:** Bearer token in Authorization header
- **Response Format:** Consistent JSON with `data`, `message`, `error` fields
- **Error Handling:** HTTP status codes with detailed error messages
- **Streaming:** Server-Sent Events (SSE) for real-time agent responses
- **File Uploads:** Multipart form data with Supabase Storage integration

### Scalability Considerations
Current architecture designed for ~10-20 concurrent users but planned enhancements:

- **Connection Pooling:** SQLAlchemy async engine with configurable pool sizes
- **Caching Layer:** Redis for user profiles, permissions, query results
- **Background Tasks:** Celery for long-running operations (document processing, model training)
- **Multi-Worker:** Gunicorn with worker count based on CPU cores
- **Load Balancing:** Horizontal scaling with stateless API servers

## External Dependencies

### Third-Party Services
- **Supabase:** PostgreSQL database, authentication, file storage (required)
- **OpenAI:** LLM API for chat completions and embeddings (required)
- **LangSmith:** Agent tracing and debugging (optional, configured via env)

### Python Libraries (Key Dependencies)
- **FastAPI 0.109+:** Web framework for API
- **Supabase-py:** Supabase client SDK
- **LangChain 0.1+:** LLM orchestration framework
- **LangGraph 0.0.20+:** Agent workflow state management
- **LlamaIndex 0.9+:** RAG indexing and retrieval
- **Pydantic 2.x:** Data validation and settings management
- **SQLAlchemy 2.x:** Database ORM (for future connection pooling)
- **Pandas, NumPy, Scikit-learn:** Analytics and ML
- **PyTesseract, EasyOCR:** OCR for document processing
- **Transformers, Torch:** Deep learning models for multi-modal processing

### Frontend Libraries
- **React 18.3:** UI framework
- **TypeScript 5.5:** Type safety
- **Vite 5.4:** Build tool and dev server
- **Supabase-js:** Supabase client for browser
- **CopilotKit:** Generative UI components for agent interactions
- **Tailwind CSS:** Utility-first CSS framework
- **Recharts, Plotly:** Data visualization libraries
- **Lucide React:** Icon library

### Environment Configuration
All external service credentials configured via environment variables:
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`
- `OPENAI_API_KEY`
- `JWT_SECRET_KEY` (for custom JWT signing if needed)
- `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` (optional tracing)
- Feature flags for toggling capabilities (e.g., `ENABLE_RERANKING`, `ENABLE_HYBRID_SEARCH`)

### Database Schema
- pgvector extension for vector similarity search
- Custom tables: `profiles`, `chat_sessions`, `chat_messages`, `documents`, `data_sources`, `custom_agents`, `agent_credentials`, `agent_executions`, `agent_metrics`, `audit_logs`
- RLS policies on all tables enforcing tenant isolation
- Indexes optimized for common query patterns