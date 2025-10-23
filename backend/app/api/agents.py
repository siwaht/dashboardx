"""
Agent API Endpoints

Provides REST API for interacting with LangGraph agents.
Supports chat, session management, and agent introspection.
"""

import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from app.agents.graph import run_agent, run_agent_streaming
from app.agents.checkpointer import get_checkpointer, get_session_history
from app.agents.tools import list_available_tools

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================

class AgentChatRequest(BaseModel):
    """Request model for agent chat"""
    query: str = Field(..., description="User query", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    stream: bool = Field(False, description="Enable streaming responses")


class AgentChatResponse(BaseModel):
    """Response model for agent chat"""
    answer: str = Field(..., description="Agent's answer")
    citations: list = Field(default_factory=list, description="Source citations")
    thoughts: list = Field(default_factory=list, description="Agent's reasoning steps")
    visualization: Optional[dict] = Field(None, description="Visualization data if applicable")
    session_id: str = Field(..., description="Session ID")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    tenant_id: str
    user_id: str
    created_at: str
    message_count: int
    last_activity: str


class ToolInfo(BaseModel):
    """Tool information"""
    name: str
    description: str


# ==================== API Endpoints ====================

@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat with the AI agent
    
    The agent will:
    1. Analyze the query intent
    2. Retrieve relevant information if needed
    3. Generate a response with citations
    4. Track reasoning steps
    
    Supports multi-turn conversations via session_id.
    """
    start_time = time.time()
    
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{current_user['user_id']}_{int(time.time())}"
        
        logger.info(f"Agent chat request: '{request.query}' (session: {session_id})")
        
        # Run agent
        final_state = await run_agent(
            user_query=request.query,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            session_id=session_id
        )
        
        # Check for errors
        if final_state.get("error"):
            logger.error(f"Agent error: {final_state['error']}")
            # Still return response, but with error info
        
        processing_time = time.time() - start_time
        
        response = AgentChatResponse(
            answer=final_state.get("final_response", "I apologize, but I couldn't generate a response."),
            citations=final_state.get("citations", []),
            thoughts=final_state.get("agent_thoughts", []),
            visualization=final_state.get("visualization_data"),
            session_id=session_id,
            processing_time=processing_time,
            metadata={
                "query_intent": final_state.get("query_intent"),
                "documents_retrieved": len(final_state.get("retrieved_documents", [])),
                "tools_used": final_state.get("tools_used", []),
                "confidence_score": final_state.get("confidence_score"),
                "current_step": final_state.get("current_step"),
                "error": final_state.get("error")
            }
        )
        
        logger.info(f"Agent response generated in {processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in agent chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent chat failed: {str(e)}"
        )


@router.post("/chat/stream")
async def agent_chat_stream(
    request: AgentChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat with the AI agent using streaming
    
    Returns Server-Sent Events (SSE) with incremental updates.
    """
    try:
        from fastapi.responses import StreamingResponse
        import json
        
        session_id = request.session_id or f"session_{current_user['user_id']}_{int(time.time())}"
        
        logger.info(f"Agent streaming chat: '{request.query}' (session: {session_id})")
        
        async def event_generator():
            try:
                async for state in run_agent_streaming(
                    user_query=request.query,
                    tenant_id=current_user["tenant_id"],
                    user_id=current_user["user_id"],
                    session_id=session_id
                ):
                    # Format as SSE
                    data = {
                        "current_step": state.get("current_step"),
                        "ui_state": state.get("ui_state", {}),
                        "thoughts": state.get("agent_thoughts", []),
                        "partial_response": state.get("draft_response") or state.get("final_response")
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                
                # Send completion event
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Streaming chat failed: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get information about a specific session
    """
    try:
        # Get session history
        history = await get_session_history(session_id=session_id, limit=1)
        
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Build session info
        latest = history[0] if history else {}
        
        return SessionInfo(
            session_id=session_id,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            created_at=latest.get("created_at", ""),
            message_count=len(history),
            last_activity=latest.get("timestamp", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/sessions/{session_id}/history")
async def get_session_history_endpoint(
    session_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get conversation history for a session
    """
    try:
        history = await get_session_history(
            session_id=session_id,
            limit=limit
        )
        
        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting session history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )


@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Resume an agent session from checkpoint
    
    Useful for:
    - Recovering from failures
    - Human-in-the-loop workflows
    - Debugging
    """
    try:
        from app.agents.checkpointer import resume_from_checkpoint
        
        logger.info(f"Resuming session: {session_id}")
        
        checkpoint = await resume_from_checkpoint(session_id=session_id)
        
        return {
            "status": "resumed",
            "session_id": session_id,
            "checkpoint": checkpoint
        }
        
    except Exception as e:
        logger.error(f"Error resuming session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume session: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a session and its checkpoints
    """
    try:
        checkpointer = get_checkpointer()
        
        deleted_count = await checkpointer.delete_checkpoints(session_id=session_id)
        
        return {
            "status": "deleted",
            "session_id": session_id,
            "checkpoints_deleted": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools(
    current_user: dict = Depends(get_current_user)
):
    """
    List all available tools the agent can use
    """
    try:
        tools = list_available_tools()
        return [ToolInfo(**tool) for tool in tools]
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/health")
async def agent_health_check():
    """
    Health check endpoint for agent system
    """
    try:
        from app.agents.graph import agent_graph
        
        return {
            "status": "healthy",
            "service": "Agent System",
            "graph_initialized": agent_graph is not None,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }


@router.get("/stats")
async def get_agent_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics about agent usage
    """
    try:
        # This is a placeholder for agent statistics
        # In production, track metrics like:
        # - Total queries processed
        # - Average response time
        # - Success rate
        # - Tool usage frequency
        
        return {
            "tenant_id": current_user["tenant_id"],
            "stats": {
                "total_queries": 0,
                "avg_response_time": 0.0,
                "success_rate": 0.0,
                "tools_used": {}
            },
            "message": "Statistics tracking to be implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
