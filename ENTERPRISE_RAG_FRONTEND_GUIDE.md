# Enterprise RAG Frontend - Complete Guide

## 🎯 Overview

This platform is now a **universal enterprise-level RAG (Retrieval-Augmented Generation) frontend** that can connect to **ANY AI agent backend**. Whether you're using LangChain, LangGraph, OpenAI, Anthropic, custom LLMs, or your own AI services, this frontend provides a unified interface for all of them.

## 🌟 Key Features

### Universal Agent Connectivity
- **Pre-built Adapters**: OpenAI, Anthropic Claude, LangChain, LangGraph, n8n
- **HTTP Adapter**: Connect to ANY REST API endpoint
- **Custom Adapters**: Easy to create your own adapters
- **Multi-Agent Support**: Run multiple AI backends simultaneously

### Enterprise Features
- **Multi-tenancy**: Complete data isolation between organizations
- **Configuration Management**: Web-based UI for managing agent connections
- **Health Monitoring**: Real-time health checks for all connected agents
- **Streaming Support**: Real-time streaming responses
- **Session Management**: Persistent conversation history
- **Authentication & Authorization**: JWT-based security with RBAC

### Developer-Friendly
- **Plugin Architecture**: Add new agent types without modifying core code
- **Type-Safe**: Full TypeScript support on frontend
- **API-First**: RESTful API for all operations
- **Auto-Discovery**: Agents are automatically registered on startup

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)             │
│  ┌──────────────┬──────────────┬─────────────────────────┐  │
│  │  Chat UI     │   Document   │   Agent Config UI       │  │
│  │              │   Management │   (Connect AI Backends) │  │
│  └──────────────┴──────────────┴─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Python)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Agent Configuration API                     │   │
│  │    (Manage connections to AI backends)               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Agent Registry & Factory                 │   │
│  │      (Dynamic agent creation & management)           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Agent Adapters                       │   │
│  │  ┌────────┬─────────┬──────────┬──────────────────┐  │   │
│  │  │OpenAI  │Anthropic│LangChain │  HTTP (Universal)│  │   │
│  │  ├────────┼─────────┼──────────┼──────────────────┤  │   │
│  │  │LangGraph│  n8n   │  Custom  │    Your Agent    │  │   │
│  │  └────────┴─────────┴──────────┴──────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │  OpenAI  │  │ Anthropic│  │  Custom  │
         │   API    │  │   API    │  │  Backend │
         └──────────┘  └──────────┘  └──────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
npm install
```

### 2. Configure Your First Agent

You can configure agents through the API or directly in configuration:

#### Option A: Via API (Recommended)

```bash
# Create OpenAI agent configuration
curl -X POST http://localhost:8000/api/agent-configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "GPT-4 Production",
    "agent_type": "openai",
    "description": "Production GPT-4 instance",
    "enabled": true,
    "priority": 1,
    "config": {
      "api_key": "sk-...",
      "model": "gpt-4-turbo-preview",
      "temperature": 0.7
    }
  }'
```

#### Option B: Environment Variables

```bash
# backend/.env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Start the Services

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Agent Config UI**: http://localhost:5173/agents

## 🔌 Connecting Different AI Backends

### OpenAI (GPT-4, GPT-3.5)

```python
{
  "name": "GPT-4 Turbo",
  "agent_type": "openai",
  "config": {
    "api_key": "sk-...",
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

### Anthropic Claude

```python
{
  "name": "Claude 3 Opus",
  "agent_type": "anthropic",
  "config": {
    "api_key": "sk-ant-...",
    "model": "claude-3-opus-20240229",
    "temperature": 1.0
  }
}
```

### LangChain Agent

```python
{
  "name": "LangChain RAG",
  "agent_type": "langchain",
  "config": {
    "model": "gpt-3.5-turbo",
    "tools": ["search", "calculator"],
    "temperature": 0.7
  }
}
```

### LangGraph Workflow

```python
{
  "name": "LangGraph Advanced RAG",
  "agent_type": "langgraph",
  "config": {
    "model": "gpt-4",
    "enable_rag": true,
    "enable_tools": true
  }
}
```

### Custom HTTP Endpoint (Universal)

This is the most powerful option - connect to **ANY** AI service:

```python
{
  "name": "My Custom LLM",
  "agent_type": "http",
  "config": {
    "endpoint_url": "https://my-llm.example.com/v1/chat",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json"
    },
    "auth_type": "bearer",
    "auth_token": "your-api-key",
    "request_template": {
      "model": "llama-70b",
      "messages": "{{messages}}",
      "temperature": "{{temperature}}",
      "max_tokens": "{{max_tokens}}"
    },
    "response_path": "choices.0.message.content"
  }
}
```

**Examples of services you can connect to:**
- Hugging Face Inference API
- Together AI
- Replicate
- Ollama (local)
- vLLM deployments
- Your own AI services
- AI21 Labs
- Cohere
- Groq
- Mistral AI
- Any custom LLM backend

## 📝 Creating Custom Adapters

Want to create your own adapter? It's easy!

```python
# backend/app/agents/adapters/my_adapter.py

from app.agents.base import BaseAgent, AgentResponse, AgentContext
import time

class MyCustomAdapter(BaseAgent):
    """Your custom AI agent adapter"""

    def __init__(self, config):
        super().__init__(config)
        # Initialize your custom client
        self.my_api_key = config.get("api_key")

    async def execute(self, query: str, context: AgentContext) -> AgentResponse:
        """Execute your agent"""
        start_time = time.time()

        # Call your AI service
        answer = await self.my_custom_ai_call(query)

        return AgentResponse(
            answer=answer,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            execution_time=time.time() - start_time
        )

    async def execute_streaming(self, query: str, context: AgentContext):
        """Optional: implement streaming"""
        yield AgentStreamChunk(chunk_type="text", content=answer)

    def get_capabilities(self):
        """Declare your agent's capabilities"""
        return AgentCapabilities(
            supports_streaming=True,
            supports_tools=False,
            supports_memory=True
        )

    async def health_check(self):
        """Health check for your service"""
        return HealthStatus(healthy=True)
```

Then register it:

```python
# backend/app/agents/adapters/__init__.py

from app.agents.adapters.my_adapter import MyCustomAdapter
from app.agents.registry import AgentRegistry

AgentRegistry.register(
    agent_id="my-custom",
    agent_class=MyCustomAdapter,
    metadata={
        "name": "My Custom AI",
        "description": "My custom AI agent",
        "enabled": True
    }
)
```

## 🔧 API Reference

### Agent Configuration Endpoints

#### List Available Agent Types
```http
GET /api/agent-configs/types
```

Returns all available agent adapter types with configuration schemas.

#### Create Agent Configuration
```http
POST /api/agent-configs
Content-Type: application/json

{
  "name": "My Agent",
  "agent_type": "openai",
  "config": { ... }
}
```

#### List Configurations
```http
GET /api/agent-configs?enabled_only=true
```

#### Get Configuration
```http
GET /api/agent-configs/{config_id}
```

#### Update Configuration
```http
PUT /api/agent-configs/{config_id}
Content-Type: application/json

{
  "enabled": false,
  "priority": 5
}
```

#### Delete Configuration
```http
DELETE /api/agent-configs/{config_id}
```

#### Test Configuration
```http
POST /api/agent-configs/{config_id}/test
```

Performs a health check on the agent.

### Agent Execution Endpoints

#### Chat with Agent
```http
POST /api/agents/chat
Content-Type: application/json

{
  "query": "Hello, how are you?",
  "session_id": "optional-session-id"
}
```

#### Streaming Chat
```http
POST /api/agents/chat/stream
Content-Type: application/json

{
  "query": "Tell me a story",
  "session_id": "session-123"
}
```

Returns Server-Sent Events (SSE) with streaming response.

## 🎨 Frontend Integration

### React Component Example

```typescript
import { useState } from 'react';

function AgentChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    const response = await fetch('/api/agents/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: input })
    });

    const data = await response.json();
    setMessages([...messages,
      { role: 'user', content: input },
      { role: 'assistant', content: data.answer }
    ]);
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>{msg.content}</div>
        ))}
      </div>
      <input
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && sendMessage()}
      />
    </div>
  );
}
```

## 🔐 Security Best Practices

1. **API Keys**: Store API keys securely (use environment variables or secret managers)
2. **Rate Limiting**: Implement rate limiting on agent endpoints
3. **Authentication**: Always require authentication for agent configuration
4. **Secret Masking**: API keys are automatically masked in API responses
5. **Tenant Isolation**: All configurations are isolated per tenant

## 📊 Monitoring & Observability

### Health Checks

```bash
# Check overall health
curl http://localhost:8000/health

# Check specific agent configuration
curl -X POST http://localhost:8000/api/agent-configs/{config_id}/test
```

### Metrics (Coming Soon)

- Request latency
- Token usage
- Error rates
- Agent availability

### Logging

All agent interactions are logged with:
- Tenant ID
- User ID
- Query
- Response time
- Errors

## 🌍 Use Cases

### 1. Multi-Model Comparison
Run the same query against multiple AI models and compare results:
```python
# Configure GPT-4, Claude, and your custom model
# Users can switch between them in the UI
```

### 2. Specialized Agents
Different agents for different tasks:
```python
# Agent 1: Code generation (GPT-4)
# Agent 2: Document analysis (Claude Opus)
# Agent 3: Customer support (Your fine-tuned model)
```

### 3. Fallback & Load Balancing
Primary and backup agents:
```python
# Priority 1: Custom model (cost-effective)
# Priority 2: GPT-3.5 (fallback)
# Priority 3: GPT-4 (high-quality fallback)
```

### 4. RAG Pipeline Integration
Connect different RAG implementations:
```python
# LangGraph for complex workflows
# LlamaIndex for document processing
# Custom RAG with your vector database
```

## 🚦 Deployment

### Docker

```bash
# Build
docker-compose build

# Run
docker-compose up -d
```

### Environment Variables

```bash
# backend/.env
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Optional: Pre-configure agents
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Production Checklist

- [ ] Set up secret management (AWS Secrets Manager, Azure Key Vault)
- [ ] Configure rate limiting
- [ ] Enable monitoring (Sentry, LangSmith)
- [ ] Set up backups for configuration database
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS
- [ ] Set up CI/CD pipeline

## 📚 Additional Resources

- **LangChain**: https://langchain.com/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **OpenAI API**: https://platform.openai.com/docs
- **Anthropic API**: https://docs.anthropic.com/
- **FastAPI**: https://fastapi.tiangolo.com/

## 🤝 Contributing

### Adding a New Adapter

1. Create adapter file in `backend/app/agents/adapters/`
2. Implement `BaseAgent` interface
3. Register in `backend/app/agents/adapters/__init__.py`
4. Add configuration schema in `agent_config.py`
5. Test with health check endpoint

### Reporting Issues

Open an issue with:
- Agent type
- Configuration (with secrets removed)
- Error message
- Expected behavior

## 📄 License

[Your License Here]

---

**Built with ❤️ for the AI community**

This is now a truly universal, enterprise-ready RAG frontend that can connect to any AI backend. Start building amazing AI applications today!
