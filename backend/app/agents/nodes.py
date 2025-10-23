"""
Agent Nodes for LangGraph Workflow

Each node represents a step in the agent's reasoning process.
Nodes receive the current state and return updates to merge into the state.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.agents.state import AgentState, update_ui_state
from app.agents.tools import get_tool
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=settings.openai_temperature,
    api_key=settings.openai_api_key
)


async def query_analysis_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyze the user query to determine intent and required actions
    
    Classifies query into:
    - retrieval: Needs document search
    - sql: Needs database query
    - visualization: Needs data visualization
    - calculation: Needs mathematical computation
    - general: General conversation
    """
    try:
        logger.info(f"Analyzing query: {state['user_query']}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a query analyzer. Analyze the user's query and respond with JSON.

Classify the query intent:
- "retrieval": User wants information from documents
- "sql": User wants to query structured data
- "visualization": User wants charts/graphs
- "calculation": User needs math calculations
- "general": General conversation

Also determine if query rewriting would improve retrieval.

Respond ONLY with valid JSON in this exact format:
{{
    "intent": "retrieval|sql|visualization|calculation|general",
    "needs_rewrite": true|false,
    "reasoning": "brief explanation",
    "confidence": 0.0-1.0
}}"""),
            ("user", "{query}")
        ])
        
        response = await llm.ainvoke(
            prompt.format_messages(query=state["user_query"])
        )
        
        # Parse JSON response
        try:
            analysis = json.loads(response.content)
            intent = analysis.get("intent", "retrieval")
            needs_rewrite = analysis.get("needs_rewrite", False)
            reasoning = analysis.get("reasoning", "")
            confidence = analysis.get("confidence", 0.8)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning("Failed to parse query analysis JSON, using defaults")
            intent = "retrieval"
            needs_rewrite = True
            reasoning = "Default classification"
            confidence = 0.5
        
        logger.info(f"Query intent: {intent} (confidence: {confidence})")
        
        return {
            "query_intent": intent,
            "needs_rewrite": needs_rewrite,
            "confidence_score": confidence,
            "agent_thoughts": [f"Analyzed query intent: {intent}. {reasoning}"],
            "current_step": "query_analyzed",
            "ui_state": update_ui_state(
                state,
                step="Analyzing your question...",
                progress=10,
                intent=intent
            )
        }
        
    except Exception as e:
        logger.error(f"Error in query analysis: {e}")
        return {
            "query_intent": "retrieval",
            "needs_rewrite": True,
            "agent_thoughts": [f"Error in analysis: {str(e)}. Defaulting to retrieval."],
            "current_step": "query_analyzed",
            "ui_state": update_ui_state(state, step="Analysis complete", progress=10)
        }


async def query_rewrite_node(state: AgentState) -> Dict[str, Any]:
    """
    Rewrite the query for better retrieval if needed
    """
    try:
        # Skip rewriting if not needed or not a retrieval query
        if not state.get("needs_rewrite") or state.get("query_intent") not in ["retrieval", "sql"]:
            logger.info("Skipping query rewrite")
            return {
                "rewritten_query": state["user_query"],
                "agent_thoughts": ["Query rewrite not needed"],
                "current_step": "query_ready",
                "ui_state": update_ui_state(state, step="Query ready", progress=20)
            }
        
        logger.info("Rewriting query for better retrieval")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Rewrite the user query to be more specific and retrieval-friendly.

Guidelines:
- Expand abbreviations
- Add context if needed
- Focus on key terms and concepts
- Keep it concise (1-2 sentences)
- Maintain the original intent

Respond with ONLY the rewritten query, no explanation."""),
            ("user", "{query}")
        ])
        
        response = await llm.ainvoke(
            prompt.format_messages(query=state["user_query"])
        )
        
        rewritten = response.content.strip()
        
        logger.info(f"Rewritten query: {rewritten}")
        
        return {
            "rewritten_query": rewritten,
            "agent_thoughts": [f"Rewrote query: '{rewritten}'"],
            "current_step": "query_rewritten",
            "ui_state": update_ui_state(
                state,
                step="Optimizing search...",
                progress=25,
                rewritten_query=rewritten
            )
        }
        
    except Exception as e:
        logger.error(f"Error in query rewrite: {e}")
        return {
            "rewritten_query": state["user_query"],
            "agent_thoughts": [f"Error rewriting query: {str(e)}"],
            "current_step": "query_rewritten"
        }


async def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """
    Retrieve relevant documents using vector search
    """
    try:
        query = state.get("rewritten_query") or state["user_query"]
        
        logger.info(f"Retrieving documents for: {query}")
        
        # Get vector search tool
        vector_search = get_tool("vector_search")
        
        # Execute search
        result = await vector_search.run(
            query=query,
            tenant_id=state["tenant_id"],
            top_k=settings.top_k_documents
        )
        
        if not result["success"]:
            logger.error(f"Vector search failed: {result.get('error')}")
            return {
                "retrieved_documents": [],
                "relevance_scores": [],
                "agent_thoughts": [f"Document retrieval failed: {result.get('error')}"],
                "current_step": "retrieval_failed",
                "error": result.get("error")
            }
        
        sources = result["sources"]
        scores = [s.get("score", 0.0) for s in sources]
        
        logger.info(f"Retrieved {len(sources)} documents")
        
        return {
            "retrieved_documents": sources,
            "relevance_scores": scores,
            "agent_thoughts": [f"Retrieved {len(sources)} relevant documents"],
            "current_step": "documents_retrieved",
            "tools_used": ["vector_search"],
            "ui_state": update_ui_state(
                state,
                step=f"Found {len(sources)} relevant documents...",
                progress=50,
                documents_count=len(sources)
            )
        }
        
    except Exception as e:
        logger.error(f"Error in retrieval: {e}")
        return {
            "retrieved_documents": [],
            "relevance_scores": [],
            "agent_thoughts": [f"Error retrieving documents: {str(e)}"],
            "current_step": "retrieval_failed",
            "error": str(e)
        }


async def reranking_node(state: AgentState) -> Dict[str, Any]:
    """
    Rerank retrieved documents for better relevance
    """
    try:
        docs = state.get("retrieved_documents", [])
        
        if len(docs) <= 3:
            logger.info("Skipping reranking (too few documents)")
            return {
                "reranked_documents": docs,
                "agent_thoughts": ["Skipped reranking (sufficient documents)"],
                "current_step": "documents_ready"
            }
        
        logger.info(f"Reranking {len(docs)} documents")
        
        # Simple reranking based on scores
        # In production, use a cross-encoder model for better reranking
        sorted_docs = sorted(
            docs,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        
        # Take top 3
        top_docs = sorted_docs[:3]
        
        logger.info(f"Reranked to top {len(top_docs)} documents")
        
        return {
            "reranked_documents": top_docs,
            "agent_thoughts": [f"Reranked to top {len(top_docs)} most relevant documents"],
            "current_step": "documents_reranked",
            "ui_state": update_ui_state(
                state,
                step="Analyzing information...",
                progress=60
            )
        }
        
    except Exception as e:
        logger.error(f"Error in reranking: {e}")
        return {
            "reranked_documents": state.get("retrieved_documents", []),
            "agent_thoughts": [f"Error reranking: {str(e)}"],
            "current_step": "documents_ready"
        }


async def response_generation_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate response using retrieved context
    """
    try:
        logger.info("Generating response")
        
        # Get documents (reranked or original)
        docs = state.get("reranked_documents") or state.get("retrieved_documents", [])
        
        # Build context from documents
        if docs:
            context = "\n\n".join([
                f"Document {i+1} (relevance: {doc.get('score', 0):.2f}):\n{doc.get('text', '')}"
                for i, doc in enumerate(docs[:3])
            ])
        else:
            context = "No relevant documents found."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant. Answer the user's question based on the provided context.

Guidelines:
- Be accurate and concise
- Cite your sources using [1], [2], etc.
- If the context doesn't contain the answer, say so
- Provide specific details from the documents
- Be professional and clear

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
        
        answer = response.content
        
        # Extract citations
        citations = [
            {
                "text": doc.get("text", "")[:200] + "...",
                "score": doc.get("score"),
                "metadata": doc.get("metadata", {})
            }
            for doc in docs[:3]
        ]
        
        logger.info("Response generated successfully")
        
        return {
            "final_response": answer,
            "citations": citations,
            "agent_thoughts": ["Generated response with citations"],
            "current_step": "response_generated",
            "completed_at": datetime.utcnow(),
            "ui_state": update_ui_state(
                state,
                step="Complete",
                progress=100,
                status="complete",
                done=True
            )
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "final_response": f"I apologize, but I encountered an error: {str(e)}",
            "citations": [],
            "agent_thoughts": [f"Error generating response: {str(e)}"],
            "current_step": "response_failed",
            "error": str(e),
            "completed_at": datetime.utcnow()
        }


async def validation_node(state: AgentState) -> Dict[str, Any]:
    """
    Validate the generated response
    """
    try:
        response = state.get("final_response", "")
        
        # Simple validation checks
        is_valid = (
            len(response) > 10 and
            not response.startswith("I don't know") and
            not response.startswith("I apologize, but I encountered an error")
        )
        
        if not is_valid:
            logger.warning("Response validation failed")
            
            # Check if we should retry
            retry_count = state.get("retry_count", 0)
            if retry_count < 2:
                return {
                    "agent_thoughts": ["Response needs improvement, retrying..."],
                    "current_step": "validation_failed",
                    "retry_count": retry_count + 1,
                    "needs_rewrite": True  # Trigger rewrite on retry
                }
        
        logger.info("Response validated successfully")
        
        return {
            "agent_thoughts": ["Response validated successfully"],
            "current_step": "validated"
        }
        
    except Exception as e:
        logger.error(f"Error in validation: {e}")
        return {
            "agent_thoughts": [f"Validation error: {str(e)}"],
            "current_step": "validated"
        }


async def error_handling_node(state: AgentState) -> Dict[str, Any]:
    """
    Handle errors and provide fallback response
    """
    try:
        error = state.get("error", "Unknown error")
        
        logger.error(f"Handling error: {error}")
        
        fallback_response = (
            "I apologize, but I encountered an issue while processing your request. "
            "Please try rephrasing your question or contact support if the problem persists."
        )
        
        return {
            "final_response": fallback_response,
            "citations": [],
            "agent_thoughts": [f"Error handled: {error}"],
            "current_step": "error_handled",
            "completed_at": datetime.utcnow(),
            "ui_state": update_ui_state(
                state,
                step="Error occurred",
                progress=100,
                status="error",
                error=error
            )
        }
        
    except Exception as e:
        logger.error(f"Error in error handling: {e}")
        return {
            "final_response": "An unexpected error occurred.",
            "current_step": "error_handled",
            "completed_at": datetime.utcnow()
        }
