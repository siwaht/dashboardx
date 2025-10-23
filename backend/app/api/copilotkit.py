"""
CopilotKit Runtime Integration

Provides real-time agent state synchronization and action execution
through WebSocket connections for seamless UI updates.
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.agents.graph import agent_graph
from app.agents.state import create_initial_state, AgentState
from app.rag.llama_index import llama_rag
from app.rag.ingestion import DocumentIngestionPipeline
from app.agents.tools import get_tool
from app.security.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/copilotkit", tags=["CopilotKit"])


# ==================== WebSocket Connection Manager ====================

class ConnectionManager:
    """Manage WebSocket connections for CopilotKit"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)


manager = ConnectionManager()


# ==================== Agent Streaming ====================

async def run_agent_streaming(
    user_query: str,
    tenant_id: str,
    user_id: str,
    session_id: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run agent with streaming state updates
    
    Yields state updates at each step of the workflow for real-time UI rendering.
    """
    try:
        # Create initial state
        initial_state = create_initial_state(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            user_query=user_query
        )
        
        # Yield initial state
        yield {
            "type": "state_update",
            "step": "initialized",
            "message": "Starting agent workflow...",
            "progress": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Run agent graph with streaming
        step_count = 0
        total_steps = 7  # Approximate number of workflow steps
        
        async for state_update in agent_graph.astream(initial_state):
            step_count += 1
            progress = min(int((step_count / total_steps) * 100), 95)
            
            # Extract relevant state information
            current_step = state_update.get("current_step", "processing")
            thoughts = state_update.get("agent_thoughts", [])
            tools_used = state_update.get("tools_used", [])
            ui_state = state_update.get("ui_state", {})
            
            # Yield state update
            yield {
                "type": "state_update",
                "step": current_step,
                "thoughts": thoughts[-1] if thoughts else None,
                "all_thoughts": thoughts,
                "tools_used": tools_used,
                "progress": progress,
                "ui_state": ui_state,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Small delay for UI rendering
            await asyncio.sleep(0.1)
        
        # Get final state
        final_state = state_update
        
        # Yield final response
        yield {
            "type": "final_response",
            "step": "completed",
            "response": final_state.get("final_response", ""),
            "citations": final_state.get("citations", []),
            "thoughts": final_state.get("agent_thoughts", []),
            "tools_used": final_state.get("tools_used", []),
            "visualization": final_state.get("visualization_data"),
            "progress": 100,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in agent streaming: {e}")
        yield {
            "type": "error",
            "step": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# ==================== WebSocket Endpoint ====================

@router.websocket("/ws")
async def copilotkit_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for CopilotKit real-time communication
    
    Handles:
    - Authentication
    - Agent query streaming
    - Action execution
    - State synchronization
    """
    session_id = None
    
    try:
        # Accept connection
        await websocket.accept()
        
        # Wait for authentication message
        auth_message = await websocket.receive_json()
        
        if auth_message.get("type") != "auth":
            await websocket.send_json({
                "type": "error",
                "message": "First message must be authentication"
            })
            await websocket.close()
            return
        
        # Verify token (simplified - enhance with proper JWT verification)
        token = auth_message.get("token")
        if not token:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication token required"
            })
            await websocket.close()
            return
        
        # Mock user for now (replace with actual token verification)
        user = {
            "user_id": auth_message.get("user_id", "demo-user"),
            "tenant_id": auth_message.get("tenant_id", "demo-tenant"),
            "email": auth_message.get("email", "demo@example.com")
        }
        
        session_id = auth_message.get("session_id", f"session_{user['user_id']}_{int(datetime.utcnow().timestamp())}")
        
        # Register connection
        await manager.connect(session_id, websocket)
        
        # Send authentication success
        await websocket.send_json({
            "type": "auth_success",
            "session_id": session_id,
            "user": user
        })
        
        # Message handling loop
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            
            if message_type == "agent_query":
                # Stream agent execution
                query = message.get("query")
                
                if not query:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Query is required"
                    })
                    continue
                
                # Stream agent responses
                async for state_update in run_agent_streaming(
                    user_query=query,
                    tenant_id=user["tenant_id"],
                    user_id=user["user_id"],
                    session_id=session_id
                ):
                    await websocket.send_json(state_update)
            
            elif message_type == "action":
                # Execute CopilotKit action
                action_name = message.get("action")
                params = message.get("params", {})
                
                result = await execute_copilotkit_action(
                    action=action_name,
                    params=params,
                    user=user
                )
                
                await websocket.send_json({
                    "type": "action_result",
                    "action": action_name,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if session_id:
            manager.disconnect(session_id)


# ==================== CopilotKit Actions ====================

async def execute_copilotkit_action(
    action: str,
    params: Dict[str, Any],
    user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a CopilotKit action
    
    Available actions:
    - search_documents: Search through uploaded documents
    - upload_document: Upload a new document
    - create_visualization: Generate data visualization
    - get_document_stats: Get document statistics
    - list_tools: List available agent tools
    """
    try:
        actions = {
            "search_documents": search_documents_action,
            "upload_document": upload_document_action,
            "create_visualization": create_visualization_action,
            "get_document_stats": get_document_stats_action,
            "list_tools": list_tools_action,
        }
        
        handler = actions.get(action)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
        result = await handler(params, user)
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error executing action {action}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def search_documents_action(params: Dict, user: Dict) -> Dict:
    """Search documents using RAG"""
    query = params.get("query")
    top_k = params.get("top_k", 5)
    
    if not query:
        raise ValueError("Query parameter is required")
    
    result = await llama_rag.query(
        query_text=query,
        tenant_id=user["tenant_id"],
        top_k=top_k
    )
    
    return {
        "query": query,
        "results": result["sources"],
        "count": len(result["sources"])
    }


async def upload_document_action(params: Dict, user: Dict) -> Dict:
    """Upload and process a document"""
    filename = params.get("filename")
    content = params.get("content")  # Base64 encoded
    
    if not filename or not content:
        raise ValueError("Filename and content are required")
    
    # Decode base64 content
    import base64
    file_content = base64.b64decode(content)
    
    # Process document
    pipeline = DocumentIngestionPipeline()
    result = await pipeline.process_document(
        file_content=file_content,
        filename=filename,
        tenant_id=user["tenant_id"],
        user_id=user["user_id"]
    )
    
    return {
        "document_id": result["document_id"],
        "chunks_created": result["chunks_created"],
        "filename": filename
    }


async def create_visualization_action(params: Dict, user: Dict) -> Dict:
    """Create a data visualization"""
    data = params.get("data", [])
    chart_type = params.get("chart_type", "bar")
    
    if not data:
        raise ValueError("Data is required for visualization")
    
    viz_tool = get_tool("data_visualization")
    result = await viz_tool.run(data=data, chart_type=chart_type)
    
    return result


async def get_document_stats_action(params: Dict, user: Dict) -> Dict:
    """Get document statistics for the tenant"""
    # This would query the database for document stats
    # Simplified implementation
    return {
        "total_documents": 0,  # TODO: Query from database
        "total_chunks": 0,
        "total_size_bytes": 0,
        "tenant_id": user["tenant_id"]
    }


async def list_tools_action(params: Dict, user: Dict) -> Dict:
    """List available agent tools"""
    from app.agents.tools import TOOLS
    
    tools_info = []
    for tool_name, tool in TOOLS.items():
        tools_info.append({
            "name": tool.name,
            "description": tool.description
        })
    
    return {
        "tools": tools_info,
        "count": len(tools_info)
    }


# ==================== HTTP Endpoints ====================

@router.post("/actions/{action_name}")
async def execute_action_http(
    action_name: str,
    params: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    HTTP endpoint for executing CopilotKit actions
    (Alternative to WebSocket for simpler integrations)
    """
    result = await execute_copilotkit_action(
        action=action_name,
        params=params,
        user=current_user
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/health")
async def copilotkit_health():
    """Health check for CopilotKit integration"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """List active CopilotKit sessions for the user"""
    user_sessions = [
        session_id for session_id in manager.active_connections.keys()
        if current_user["user_id"] in session_id
    ]
    
    return {
        "sessions": user_sessions,
        "count": len(user_sessions)
    }
