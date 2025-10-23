"""
LangGraph Workflow Definition

Defines the agent workflow using LangGraph's StateGraph.
The workflow orchestrates the agent's reasoning process through multiple nodes.
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState, create_initial_state
from app.agents.nodes import (
    query_analysis_node,
    query_rewrite_node,
    retrieval_node,
    reranking_node,
    response_generation_node,
    validation_node,
    error_handling_node
)

logger = logging.getLogger(__name__)


# ==================== Conditional Edge Functions ====================

def should_retrieve(state: AgentState) -> Literal["retrieve", "respond", "error"]:
    """
    Determine if we should retrieve documents
    
    Returns:
        - "retrieve": Query needs document retrieval
        - "respond": Can respond without retrieval
        - "error": Error occurred
    """
    if state.get("error"):
        return "error"
    
    intent = state.get("query_intent", "retrieval")
    
    if intent in ["retrieval", "sql"]:
        return "retrieve"
    
    return "respond"


def should_rerank(state: AgentState) -> Literal["rerank", "respond", "error"]:
    """
    Determine if we should rerank documents
    
    Returns:
        - "rerank": Many documents, reranking would help
        - "respond": Few documents, proceed to response
        - "error": Error occurred
    """
    if state.get("error"):
        return "error"
    
    docs = state.get("retrieved_documents", [])
    
    if len(docs) > 3:
        return "rerank"
    
    return "respond"


def should_retry(state: AgentState) -> Literal["rewrite", "end", "error"]:
    """
    Determine if we should retry response generation
    
    Returns:
        - "rewrite": Retry with query rewrite
        - "end": Response is good, finish
        - "error": Error occurred
    """
    if state.get("error"):
        return "error"
    
    # Check validation status
    current_step = state.get("current_step", "")
    retry_count = state.get("retry_count", 0)
    
    if current_step == "validation_failed" and retry_count < 2:
        return "rewrite"
    
    return "end"


def route_after_analysis(state: AgentState) -> Literal["rewrite", "error"]:
    """
    Route after query analysis
    
    Returns:
        - "rewrite": Proceed to query rewrite
        - "error": Error occurred
    """
    if state.get("error"):
        return "error"
    
    return "rewrite"


# ==================== Graph Creation ====================

def create_agent_graph() -> StateGraph:
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
    
    Returns:
        Compiled StateGraph
    """
    logger.info("Creating agent graph")
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", query_analysis_node)
    workflow.add_node("rewrite", query_rewrite_node)
    workflow.add_node("retrieve", retrieval_node)
    workflow.add_node("rerank", reranking_node)
    workflow.add_node("respond", response_generation_node)
    workflow.add_node("validate", validation_node)
    workflow.add_node("error", error_handling_node)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    # Add edges
    # After analysis, go to rewrite or error
    workflow.add_conditional_edges(
        "analyze",
        route_after_analysis,
        {
            "rewrite": "rewrite",
            "error": "error"
        }
    )
    
    # After rewrite, decide: retrieve or respond directly
    workflow.add_conditional_edges(
        "rewrite",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "respond": "respond",
            "error": "error"
        }
    )
    
    # After retrieval, decide: rerank or respond
    workflow.add_conditional_edges(
        "retrieve",
        should_rerank,
        {
            "rerank": "rerank",
            "respond": "respond",
            "error": "error"
        }
    )
    
    # After reranking, go to response
    workflow.add_edge("rerank", "respond")
    
    # After response, validate
    workflow.add_edge("respond", "validate")
    
    # After validation, decide: retry or end
    workflow.add_conditional_edges(
        "validate",
        should_retry,
        {
            "rewrite": "rewrite",  # Retry from rewrite
            "end": END,
            "error": "error"
        }
    )
    
    # Error handling leads to end
    workflow.add_edge("error", END)
    
    # Compile graph
    graph = workflow.compile()
    
    logger.info("Agent graph created successfully")
    
    return graph


# Create graph instance
agent_graph = create_agent_graph()


# ==================== Agent Execution ====================

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
        tenant_id: Tenant ID for multi-tenancy
        user_id: User ID
        session_id: Session ID for conversation tracking
        
    Returns:
        Final agent state with response
    """
    try:
        logger.info(f"Running agent for query: '{user_query}' (tenant: {tenant_id})")
        
        # Create initial state
        initial_state = create_initial_state(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            user_query=user_query
        )
        
        # Run graph
        final_state = await agent_graph.ainvoke(initial_state)
        
        logger.info(f"Agent completed: {final_state.get('current_step')}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        
        # Return error state
        from datetime import datetime
        return {
            **create_initial_state(tenant_id, user_id, session_id, user_query),
            "error": str(e),
            "final_response": f"I apologize, but I encountered an error: {str(e)}",
            "current_step": "error",
            "completed_at": datetime.utcnow()
        }


async def run_agent_streaming(
    user_query: str,
    tenant_id: str,
    user_id: str,
    session_id: str
):
    """
    Run the agent workflow with streaming updates
    
    This is a placeholder for streaming implementation.
    In production, use LangGraph's streaming capabilities.
    
    Args:
        user_query: User's question
        tenant_id: Tenant ID
        user_id: User ID
        session_id: Session ID
        
    Yields:
        State updates as they occur
    """
    try:
        logger.info(f"Running agent with streaming for: '{user_query}'")
        
        # Create initial state
        initial_state = create_initial_state(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            user_query=user_query
        )
        
        # Stream graph execution
        async for state in agent_graph.astream(initial_state):
            yield state
        
    except Exception as e:
        logger.error(f"Error in streaming agent: {e}", exc_info=True)
        yield {
            "error": str(e),
            "final_response": f"Error: {str(e)}",
            "current_step": "error"
        }


def visualize_graph(output_path: str = "agent_graph.png"):
    """
    Visualize the agent graph
    
    Args:
        output_path: Path to save the visualization
    """
    try:
        from IPython.display import Image, display
        
        # Get graph visualization
        graph_image = agent_graph.get_graph().draw_mermaid_png()
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(graph_image)
        
        logger.info(f"Graph visualization saved to {output_path}")
        
        # Display if in notebook
        try:
            display(Image(graph_image))
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error visualizing graph: {e}")
