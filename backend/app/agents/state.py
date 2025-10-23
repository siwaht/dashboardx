"""
Agent State Schema for LangGraph

Defines the state structure that flows through the agent workflow.
Uses TypedDict with Annotated for proper state management.
"""

from typing import TypedDict, List, Optional, Annotated, Any
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    State schema for the agent workflow
    
    This state is passed between nodes in the LangGraph workflow.
    Fields with Annotated[List, operator.add] will accumulate values.
    """
    
    # ==================== User Context ====================
    tenant_id: str
    user_id: str
    session_id: str
    
    # ==================== Conversation ====================
    messages: Annotated[List[dict], operator.add]  # Accumulate messages
    user_query: str
    
    # ==================== Query Processing ====================
    query_intent: Optional[str]  # retrieval, sql, visualization, general
    rewritten_query: Optional[str]
    needs_rewrite: bool
    
    # ==================== RAG Context ====================
    retrieved_documents: List[dict]
    relevance_scores: List[float]
    reranked_documents: Optional[List[dict]]
    
    # ==================== Agent Reasoning ====================
    agent_thoughts: Annotated[List[str], operator.add]  # Accumulate thoughts
    current_step: str
    tools_used: Annotated[List[str], operator.add]  # Track tool usage
    
    # ==================== Response Generation ====================
    draft_response: Optional[str]
    final_response: Optional[str]
    citations: List[dict]
    confidence_score: Optional[float]
    
    # ==================== Visualization ====================
    visualization_data: Optional[dict]
    chart_type: Optional[str]
    
    # ==================== Metadata ====================
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]
    retry_count: int
    
    # ==================== UI Synchronization ====================
    ui_state: dict  # For CopilotKit state rendering


def create_initial_state(
    tenant_id: str,
    user_id: str,
    session_id: str,
    user_query: str
) -> AgentState:
    """
    Create initial agent state
    
    Args:
        tenant_id: Tenant ID for multi-tenancy
        user_id: User ID
        session_id: Session ID for conversation tracking
        user_query: User's question/query
        
    Returns:
        Initial AgentState
    """
    return AgentState(
        # User context
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        
        # Conversation
        messages=[],
        user_query=user_query,
        
        # Query processing
        query_intent=None,
        rewritten_query=None,
        needs_rewrite=False,
        
        # RAG context
        retrieved_documents=[],
        relevance_scores=[],
        reranked_documents=None,
        
        # Agent reasoning
        agent_thoughts=[],
        current_step="initialized",
        tools_used=[],
        
        # Response generation
        draft_response=None,
        final_response=None,
        citations=[],
        confidence_score=None,
        
        # Visualization
        visualization_data=None,
        chart_type=None,
        
        # Metadata
        started_at=datetime.utcnow(),
        completed_at=None,
        error=None,
        retry_count=0,
        
        # UI state
        ui_state={
            "step": "Initializing...",
            "progress": 0,
            "status": "processing"
        }
    )


def update_ui_state(
    state: AgentState,
    step: str,
    progress: int,
    status: str = "processing",
    **kwargs
) -> dict:
    """
    Helper to update UI state
    
    Args:
        state: Current agent state
        step: Current step description
        progress: Progress percentage (0-100)
        status: Status (processing, complete, error)
        **kwargs: Additional UI state fields
        
    Returns:
        Updated ui_state dict
    """
    ui_state = {
        "step": step,
        "progress": progress,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add any additional fields
    ui_state.update(kwargs)
    
    return ui_state
