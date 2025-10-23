# 🚀 Phase 4, 5, 6, 7 Implementation Plan

**Target Phases:**
- Phase 4: CopilotKit Integration (Generative UI)
- Phase 5: Security Hardening
- Phase 6: Streaming Responses
- Phase 7: Data Connectors

**Total Estimated Time:** 8-12 days
**Implementation Order:** Phase 4 → 5 → 6 → 7

---

## 📋 PHASE 4: CopilotKit Integration

**Status:** Starting Now 🚀
**Estimated Time:** 2-3 days
**Priority:** HIGH (Enhances UX significantly)

### 4.1 Install CopilotKit Dependencies

```bash
# Frontend dependencies
npm install @copilotkit/react-core @copilotkit/react-ui @copilotkit/react-textarea
```

### 4.2 Backend CopilotKit Runtime

**Create `backend/app/api/copilotkit.py`:**

```python
"""
CopilotKit Runtime Integration

Provides real-time agent state synchronization and action execution.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import asyncio

from app.agents.graph import run_agent_streaming
from app.security.auth import verify_websocket_token

router = APIRouter()


@router.websocket("/copilotkit/ws")
async def copilotkit_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for CopilotKit real-time communication
    """
    await websocket.accept()
    
    try:
        # Authenticate
        auth_message = await websocket.receive_json()
        token = auth_message.get("token")
        
        user = await verify_websocket_token(token)
        if not user:
            await websocket.send_json({"error": "Authentication failed"})
            await websocket.close()
            return
        
        # Handle messages
        while True:
            message = await websocket.receive_json()
            
            if message.get("type") == "agent_query":
                # Stream agent execution
                async for state_update in run_agent_streaming(
                    user_query=message["query"],
                    tenant_id=user["tenant_id"],
                    user_id=user["user_id"],
                    session_id=message.get("session_id", "default")
                ):
                    await websocket.send_json({
                        "type": "agent_state",
                        "data": state_update
                    })
            
            elif message.get("type") == "action":
                # Execute CopilotKit action
                result = await execute_copilotkit_action(
                    action=message["action"],
                    params=message.get("params", {}),
                    user=user
                )
                await websocket.send_json({
                    "type": "action_result",
                    "data": result
                })
    
    except WebSocketDisconnect:
        print(f"Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


async def execute_copilotkit_action(
    action: str,
    params: Dict[str, Any],
    user: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a CopilotKit action"""
    
    actions = {
        "search_documents": search_documents_action,
        "upload_document": upload_document_action,
        "create_visualization": create_visualization_action,
    }
    
    handler = actions.get(action)
    if not handler:
        return {"error": f"Unknown action: {action}"}
    
    return await handler(params, user)


async def search_documents_action(params: Dict, user: Dict) -> Dict:
    """Search documents action"""
    from app.rag.llama_index import get_llama_rag
    
    llama_rag = get_llama_rag()
    result = await llama_rag.query(
        query_text=params["query"],
        tenant_id=user["tenant_id"],
        top_k=params.get("top_k", 5)
    )
    
    return {"success": True, "results": result}


async def upload_document_action(params: Dict, user: Dict) -> Dict:
    """Upload document action"""
    # Implementation for document upload
    return {"success": True, "message": "Document uploaded"}


async def create_visualization_action(params: Dict, user: Dict) -> Dict:
    """Create visualization action"""
    from app.agents.tools import get_tool
    
    viz_tool = get_tool("data_visualization")
    result = await viz_tool.run(
        data=params["data"],
        chart_type=params.get("chart_type", "bar")
    )
    
    return result
```

### 4.3 Frontend CopilotKit Provider

**Update `src/App.tsx`:**

```typescript
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

function App() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="agentic-rag-agent"
    >
      <CopilotSidebar>
        {/* Your existing app */}
        <YourAppContent />
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

### 4.4 CopilotKit Chat Component

**Create `src/components/copilot/CopilotChat.tsx`:**

```typescript
import { useCopilotChat, useCopilotAction } from "@copilotkit/react-core";
import { CopilotTextarea } from "@copilotkit/react-textarea";

export function CopilotChat() {
  const { messages, sendMessage, isLoading } = useCopilotChat();
  
  // Define actions
  useCopilotAction({
    name: "search_documents",
    description: "Search through uploaded documents",
    parameters: [
      {
        name: "query",
        type: "string",
        description: "Search query",
        required: true,
      },
    ],
    handler: async ({ query }) => {
      // Action will be executed via WebSocket
      return { query };
    },
  });
  
  return (
    <div className="copilot-chat">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      
      <CopilotTextarea
        placeholder="Ask me anything..."
        onSubmit={sendMessage}
        disabled={isLoading}
      />
    </div>
  );
}
```

### 4.5 Agent State Rendering

**Create `src/components/copilot/AgentStateRenderer.tsx`:**

```typescript
import { useCopilotReadable } from "@copilotkit/react-core";
import { useAgentState } from "@/hooks/useAgentState";

export function AgentStateRenderer() {
  const agentState = useAgentState();
  
  // Make agent state readable by CopilotKit
  useCopilotReadable({
    description: "Current agent reasoning state",
    value: agentState,
  });
  
  return (
    <div className="agent-state">
      <h3>Agent Status</h3>
      
      {/* Current Step */}
      <div className="step">
        <span className="label">Current Step:</span>
        <span className="value">{agentState.current_step}</span>
      </div>
      
      {/* Progress */}
      <div className="progress">
        <div 
          className="progress-bar" 
          style={{ width: `${agentState.ui_state?.progress || 0}%` }}
        />
      </div>
      
      {/* Agent Thoughts */}
      <div className="thoughts">
        <h4>Reasoning:</h4>
        {agentState.agent_thoughts?.map((thought, idx) => (
          <div key={idx} className="thought">
            {thought}
          </div>
        ))}
      </div>
      
      {/* Tools Used */}
      {agentState.tools_used?.length > 0 && (
        <div className="tools">
          <h4>Tools Used:</h4>
          {agentState.tools_used.map((tool, idx) => (
            <span key={idx} className="tool-badge">{tool}</span>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 4.6 Generative UI Components

**Create `src/components/copilot/GenerativeUI.tsx`:**

```typescript
import { useMakeCopilotReadable, useMakeCopilotActionable } from "@copilotkit/react-core";

export function DocumentCard({ document }) {
  // Make document data readable
  useMakeCopilotReadable(
    `Document: ${document.title}`,
    document
  );
  
  // Make actions available
  useMakeCopilotActionable({
    name: "view_document",
    description: `View the document "${document.title}"`,
    handler: () => {
      // Handle document view
    },
  });
  
  return (
    <div className="document-card">
      <h3>{document.title}</h3>
      <p>{document.summary}</p>
      <button>View</button>
    </div>
  );
}

export function VisualizationCard({ data, type }) {
  useMakeCopilotReadable(
    `Visualization: ${type} chart`,
    { data, type }
  );
  
  return (
    <div className="visualization-card">
      {/* Render chart based on type */}
    </div>
  );
}
```

### 4.7 Phase 4 Verification

- [ ] CopilotKit dependencies installed
- [ ] WebSocket endpoint created
- [ ] CopilotKit provider configured
- [ ] Chat component working
- [ ] Agent state rendering
- [ ] Actions defined and working
- [ ] Generative UI components created
- [ ] Real-time updates working

---

## 📋 PHASE 5: Security Hardening

**Status:** Pending Phase 4 ⏳
**Estimated Time:** 2-3 days
**Priority:** CRITICAL (Production readiness)

### 5.1 Rate Limiting

**Create `backend/app/middleware/rate_limit.py`:**

```python
"""
Rate limiting middleware
"""
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)


@limiter.limit("60/minute")
async def rate_limited_endpoint(request: Request):
    """Example rate-limited endpoint"""
    pass
```

### 5.2 Input Validation

**Create `backend/app/middleware/validation.py`:**

```python
"""
Input validation and sanitization
"""
import re
from typing import Any
from fastapi import HTTPException


class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if len(value) > max_length:
            raise HTTPException(400, "Input too long")
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>\"\'&]', '', value)
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: list) -> bool:
        """Validate file type"""
        ext = filename.split('.')[-1].lower()
        return ext in allowed_types
```

### 5.3 SQL Injection Prevention

**Update database queries to use parameterized statements:**

```python
# Bad (vulnerable)
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good (safe)
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

### 5.4 XSS Protection

**Add security headers:**

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])
app.add_middleware(HTTPSRedirectMiddleware)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### 5.5 CSRF Protection

**Create `backend/app/middleware/csrf.py`:**

```python
"""
CSRF protection
"""
import secrets
from fastapi import Request, HTTPException


class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    async def validate_token(request: Request, token: str) -> bool:
        """Validate CSRF token"""
        session_token = request.session.get("csrf_token")
        return secrets.compare_digest(session_token, token)
```

### 5.6 Audit Logging

**Create `backend/app/middleware/audit.py`:**

```python
"""
Audit logging for security events
"""
import logging
from datetime import datetime
from typing import Dict, Any

audit_logger = logging.getLogger("audit")


class AuditLogger:
    """Log security-relevant events"""
    
    @staticmethod
    async def log_event(
        event_type: str,
        user_id: str,
        tenant_id: str,
        details: Dict[str, Any]
    ):
        """Log audit event"""
        audit_logger.info({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "details": details
        })
```

### 5.7 Phase 5 Verification

- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS protection headers added
- [ ] CSRF tokens implemented
- [ ] Audit logging working
- [ ] Security scan passed
- [ ] Penetration testing completed

---

## 📋 PHASE 6: Streaming Responses

**Status:** Pending Phases 4 & 5 ⏳
**Estimated Time:** 1-2 days
**Priority:** MEDIUM (UX enhancement)

### 6.1 Server-Sent Events (SSE)

**Create `backend/app/api/streaming.py`:**

```python
"""
Streaming responses using SSE
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio

router = APIRouter()


@router.get("/stream/agent")
async def stream_agent_response(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """Stream agent response in real-time"""
    
    async def event_stream() -> AsyncGenerator[str, None]:
        async for state in run_agent_streaming(
            user_query=query,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            session_id="stream"
        ):
            # Format as SSE
            data = json.dumps({
                "step": state.get("current_step"),
                "thoughts": state.get("agent_thoughts", []),
                "response": state.get("final_response")
            })
            
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.1)
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

### 6.2 Token Streaming

**Update agent nodes for streaming:**

```python
async def response_generation_node_streaming(state: AgentState):
    """Generate response with token streaming"""
    
    async for token in llm.astream(prompt):
        yield {
            "partial_response": token,
            "current_step": "generating"
        }
```

### 6.3 Frontend SSE Client

**Create `src/hooks/useStreamingAgent.ts`:**

```typescript
import { useState, useEffect } from 'react';

export function useStreamingAgent() {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  const streamQuery = async (query: string) => {
    setIsStreaming(true);
    setResponse('');
    
    const eventSource = new EventSource(
      `/api/stream/agent?query=${encodeURIComponent(query)}`
    );
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        setIsStreaming(false);
        return;
      }
      
      const data = JSON.parse(event.data);
      setResponse(prev => prev + data.response);
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setIsStreaming(false);
    };
  };
  
  return { response, isStreaming, streamQuery };
}
```

### 6.4 Phase 6 Verification

- [ ] SSE endpoint created
- [ ] Token streaming implemented
- [ ] Frontend SSE client working
- [ ] Real-time updates visible
- [ ] Error handling for disconnects
- [ ] Performance tested

---

## 📋 PHASE 7: Data Connectors

**Status:** Pending Phases 4, 5 & 6 ⏳
**Estimated Time:** 3-4 days
**Priority:** MEDIUM (Enterprise features)

### 7.1 AWS S3 Connector

**Create `backend/app/connectors/s3.py`:**

```python
"""
AWS S3 connector for document ingestion
"""
import boto3
from typing import List, Dict
from app.config import settings


class S3Connector:
    """Connect to AWS S3 for document storage"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
    
    async def list_documents(self, bucket: str, prefix: str = '') -> List[Dict]:
        """List documents in S3 bucket"""
        response = self.s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        return [
            {
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            }
            for obj in response.get('Contents', [])
        ]
    
    async def download_document(self, bucket: str, key: str) -> bytes:
        """Download document from S3"""
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    
    async def sync_documents(
        self,
        bucket: str,
        tenant_id: str,
        user_id: str
    ) -> Dict:
        """Sync all documents from S3 bucket"""
        from app.rag.ingestion import DocumentIngestionPipeline
        
        pipeline = DocumentIngestionPipeline()
        documents = await self.list_documents(bucket)
        
        results = []
        for doc in documents:
            content = await self.download_document(bucket, doc['key'])
            result = await pipeline.ingest_document(
                file_content=content,
                filename=doc['key'],
                tenant_id=tenant_id,
                user_id=user_id
            )
            results.append(result)
        
        return {
            'synced': len(results),
            'results': results
        }
```

### 7.2 Google Drive Connector

**Create `backend/app/connectors/google_drive.py`:**

```python
"""
Google Drive connector
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GoogleDriveConnector:
    """Connect to Google Drive"""
    
    def __init__(self, credentials: dict):
        self.creds = Credentials.from_authorized_user_info(credentials)
        self.service = build('drive', 'v3', credentials=self.creds)
    
    async def list_files(self, folder_id: str = None) -> List[Dict]:
        """List files in Google Drive"""
        query = f"'{folder_id}' in parents" if folder_id else None
        
        results = self.service.files().list(
            q=query,
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        
        return results.get('files', [])
    
    async def download_file(self, file_id: str) -> bytes:
        """Download file from Google Drive"""
        request = self.service.files().get_media(fileId=file_id)
        return request.execute()
```

### 7.3 SharePoint Connector

**Create `backend/app/connectors/sharepoint.py`:**

```python
"""
SharePoint connector
"""
from office365.sharepoint.client_context import ClientContext


class SharePointConnector:
    """Connect to SharePoint"""
    
    def __init__(self, site_url: str, client_id: str, client_secret: str):
        self.ctx = ClientContext(site_url).with_credentials(
            ClientCredential(client_id, client_secret)
        )
    
    async def list_documents(self, library: str) -> List[Dict]:
        """List documents in SharePoint library"""
        # Implementation
        pass
    
    async def download_document(self, file_url: str) -> bytes:
        """Download document from SharePoint"""
        # Implementation
        pass
```

### 7.4 Confluence Connector

**Create `backend/app/connectors/confluence.py`:**

```python
"""
Confluence connector
"""
from atlassian import Confluence


class ConfluenceConnector:
    """Connect to Confluence"""
    
    def __init__(self, url: str, username: str, api_token: str):
        self.confluence = Confluence(
            url=url,
            username=username,
            password=api_token
        )
    
    async def get_pages(self, space_key: str) -> List[Dict]:
        """Get all pages from Confluence space"""
        return self.confluence.get_all_pages_from_space(
            space_key,
            expand='body.storage'
        )
    
    async def sync_space(
        self,
        space_key: str,
        tenant_id: str,
        user_id: str
    ) -> Dict:
        """Sync entire Confluence space"""
        # Implementation
        pass
```

### 7.5 Connector API Endpoints

**Create `backend/app/api/connectors.py`:**

```python
"""
Data connector API endpoints
"""
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/connectors")


@router.post("/s3/sync")
async def sync_s3(
    bucket: str,
    current_user: dict = Depends(get_current_user)
):
    """Sync documents from S3"""
    from app.connectors.s3 import S3Connector
    
    connector = S3Connector()
    result = await connector.sync_documents(
        bucket=bucket,
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"]
    )
    
    return result


@router.post("/google-drive/sync")
async def sync_google_drive(
    folder_id: str,
    credentials: dict,
    current_user: dict = Depends(get_current_user)
):
    """Sync documents from Google Drive"""
    # Implementation
    pass


@router.post("/sharepoint/sync")
async def sync_sharepoint(
    library: str,
    current_user: dict = Depends(get_current_user)
):
    """Sync documents from SharePoint"""
    # Implementation
    pass


@router.post("/confluence/sync")
async def sync_confluence(
    space_key: str,
    current_user: dict = Depends(get_current_user)
):
    """Sync pages from Confluence"""
    # Implementation
    pass
```

### 7.6 Phase 7 Verification

- [ ] S3 connector working
- [ ] Google Drive connector working
- [ ] SharePoint connector working
- [ ] Confluence connector working
- [ ] Sync endpoints created
- [ ] OAuth flows implemented
- [ ] Error handling for API failures
- [ ] Scheduled sync working

---

## 🎯 COMPLETE IMPLEMENTATION ROADMAP

### Week 1: CopilotKit (Phase 4)
- Days 1-2: Backend WebSocket + Actions
- Day 3: Frontend integration + UI components

### Week 2: Security (Phase 5)
- Days 4-5: Rate limiting + Input validation
- Day 6: Security headers + CSRF + Audit logging

### Week 3: Streaming (Phase 6)
- Days 7-8: SSE implementation + Token streaming

### Week 4: Connectors (Phase 7)
- Days 9-10: S3 + Google Drive
- Days 11-12: SharePoint + Confluence

---

## 📊 SUCCESS METRICS

### Phase 4 Success
- ✅ Real-time agent state updates
- ✅ CopilotKit actions working
- ✅ Generative UI rendering
- ✅ WebSocket stable

### Phase 5 Success
- ✅ Rate limits enforced
- ✅ No security vulnerabilities
- ✅ Audit logs captured
- ✅ Security scan passed

### Phase 6 Success
- ✅ Streaming responses work
- ✅ No buffering delays
- ✅ Error recovery working
- ✅ Performance acceptable

### Phase 7 Success
- ✅ All connectors functional
- ✅ OAuth flows working
- ✅ Sync reliable
- ✅ Error handling robust

---

**Ready to implement Phase 4!** 🚀
