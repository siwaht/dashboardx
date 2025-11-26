import logging
from typing import Dict, Any, AsyncGenerator
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
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("analyze", query_analysis_node)
workflow.add_node("rewrite", query_rewrite_node)
workflow.add_node("retrieve", retrieval_node)
workflow.add_node("rerank", reranking_node)
workflow.add_node("respond", response_generation_node)
workflow.add_node("validate", validation_node)
workflow.add_node("error", error_handling_node)

# Define Edges
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "rewrite")
workflow.add_edge("rewrite", "retrieve")
workflow.add_edge("retrieve", "rerank")
workflow.add_edge("rerank", "respond")
workflow.add_edge("respond", "validate")
workflow.add_edge("validate", END)
workflow.add_edge("error", END)

agent_graph = workflow.compile()

async def run_agent(user_query: str, tenant_id: str, user_id: str, session_id: str) -> AgentState:
    initial_state = create_initial_state(tenant_id, user_id, session_id, user_query)
    try:
        result = await agent_graph.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        initial_state["error"] = str(e)
        return initial_state

async def run_agent_streaming(user_query: str, tenant_id: str, user_id: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    initial_state = create_initial_state(tenant_id, user_id, session_id, user_query)
    try:
        async for event in agent_graph.astream(initial_state):
            for key, value in event.items():
                yield value # Yield the state update from the node
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        yield {"error": str(e)}
