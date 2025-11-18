"""
Agent Adapters

This module contains adapters for different agent frameworks.
Adapters are automatically registered with the AgentRegistry on import.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Import all adapters to trigger registration
try:
    from app.agents.adapters.langgraph_adapter import LangGraphAdapter
    from app.agents.registry import AgentRegistry
    
    # Register LangGraph adapter
    AgentRegistry.register(
        agent_id="langgraph",
        agent_class=LangGraphAdapter,
        metadata={
            "name": "LangGraph RAG Agent",
            "description": "Advanced RAG agent using LangGraph workflows",
            "type": "langgraph",
            "enabled": True,
            "priority": 1,
            "version": "1.0.0"
        }
    )
    logger.info("Registered LangGraph adapter")
    
except ImportError as e:
    logger.warning(f"Could not import LangGraph adapter: {e}")

try:
    from app.agents.adapters.langchain_adapter import LangChainAdapter
    from app.agents.registry import AgentRegistry
    
    # Register LangChain adapter
    AgentRegistry.register(
        agent_id="langchain",
        agent_class=LangChainAdapter,
        metadata={
            "name": "LangChain Agent",
            "description": "Simple LangChain agent with tool support",
            "type": "langchain",
            "enabled": True,
            "priority": 2,
            "version": "1.0.0"
        }
    )
    logger.info("Registered LangChain adapter")
    
except ImportError as e:
    logger.warning(f"Could not import LangChain adapter: {e}")

try:
    from app.agents.adapters.n8n_adapter import N8NAdapter
    from app.agents.registry import AgentRegistry

    # Register n8n adapter
    AgentRegistry.register(
        agent_id="n8n",
        agent_class=N8NAdapter,
        metadata={
            "name": "n8n Workflow Agent",
            "description": "Execute n8n workflows as agents",
            "type": "n8n",
            "enabled": False,  # Disabled by default (requires configuration)
            "priority": 3,
            "version": "1.0.0"
        }
    )
    logger.info("Registered n8n adapter")

except ImportError as e:
    logger.warning(f"Could not import n8n adapter: {e}")

try:
    from app.agents.adapters.openai_adapter import OpenAIAdapter
    from app.agents.registry import AgentRegistry

    # Register OpenAI adapter
    AgentRegistry.register(
        agent_id="openai",
        agent_class=OpenAIAdapter,
        metadata={
            "name": "OpenAI Direct",
            "description": "Direct OpenAI API integration (GPT-4, GPT-3.5, etc.)",
            "type": "custom",
            "enabled": True,
            "priority": 4,
            "version": "1.0.0"
        }
    )
    logger.info("Registered OpenAI adapter")

except ImportError as e:
    logger.warning(f"Could not import OpenAI adapter: {e}")

try:
    from app.agents.adapters.anthropic_adapter import AnthropicAdapter
    from app.agents.registry import AgentRegistry

    # Register Anthropic adapter
    AgentRegistry.register(
        agent_id="anthropic",
        agent_class=AnthropicAdapter,
        metadata={
            "name": "Anthropic Claude",
            "description": "Direct Anthropic Claude API integration",
            "type": "custom",
            "enabled": True,
            "priority": 5,
            "version": "1.0.0"
        }
    )
    logger.info("Registered Anthropic adapter")

except ImportError as e:
    logger.warning(f"Could not import Anthropic adapter: {e}")

try:
    from app.agents.adapters.http_adapter import HTTPAdapter
    from app.agents.registry import AgentRegistry

    # Register HTTP adapter
    AgentRegistry.register(
        agent_id="http",
        agent_class=HTTPAdapter,
        metadata={
            "name": "Custom HTTP Endpoint",
            "description": "Universal adapter for any HTTP/REST AI endpoint",
            "type": "custom",
            "enabled": True,
            "priority": 6,
            "version": "1.0.0"
        }
    )
    logger.info("Registered HTTP adapter")

except ImportError as e:
    logger.warning(f"Could not import HTTP adapter: {e}")

try:
    from app.agents.adapters.webhook_adapter import WebhookAdapter
    from app.agents.registry import AgentRegistry

    # Register Webhook adapter
    AgentRegistry.register(
        agent_id="webhook",
        agent_class=WebhookAdapter,
        metadata={
            "name": "Webhook",
            "description": "Simple webhook-based agent integration",
            "type": "custom",
            "enabled": True,
            "priority": 7,
            "version": "1.0.0"
        }
    )
    logger.info("Registered Webhook adapter")

except ImportError as e:
    logger.warning(f"Could not import Webhook adapter: {e}")

try:
    from app.agents.adapters.websocket_adapter import WebSocketAdapter
    from app.agents.registry import AgentRegistry

    # Register WebSocket adapter
    AgentRegistry.register(
        agent_id="websocket",
        agent_class=WebSocketAdapter,
        metadata={
            "name": "WebSocket",
            "description": "Real-time WebSocket connection to agents",
            "type": "custom",
            "enabled": True,
            "priority": 8,
            "version": "1.0.0"
        }
    )
    logger.info("Registered WebSocket adapter")

except ImportError as e:
    logger.warning(f"Could not import WebSocket adapter: {e}")

try:
    from app.agents.adapters.mcp_adapter import MCPAdapter
    from app.agents.registry import AgentRegistry

    # Register MCP adapter
    AgentRegistry.register(
        agent_id="mcp",
        agent_class=MCPAdapter,
        metadata={
            "name": "MCP (Model Context Protocol)",
            "description": "Anthropic's Model Context Protocol for tool/resource integration",
            "type": "custom",
            "enabled": True,
            "priority": 9,
            "version": "1.0.0"
        }
    )
    logger.info("Registered MCP adapter")

except ImportError as e:
    logger.warning(f"Could not import MCP adapter: {e}")


# Export all adapters
__all__ = [
    "LangGraphAdapter",
    "LangChainAdapter",
    "N8NAdapter",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "HTTPAdapter",
    "WebhookAdapter",
    "WebSocketAdapter",
    "MCPAdapter"
]


def get_available_adapters() -> List[str]:
    """
    Get list of available adapter IDs
    
    Returns:
        List of registered adapter IDs
    """
    from app.agents.registry import AgentRegistry
    return AgentRegistry.list_agents()


def get_adapter_info(adapter_id: str) -> dict:
    """
    Get information about a specific adapter
    
    Args:
        adapter_id: ID of the adapter
        
    Returns:
        Dictionary with adapter information
    """
    from app.agents.registry import AgentRegistry
    
    adapter_class = AgentRegistry.get(adapter_id)
    metadata = AgentRegistry.get_metadata(adapter_id)
    
    if not adapter_class:
        return {}
    
    return {
        "id": adapter_id,
        "class_name": adapter_class.__name__,
        "metadata": metadata
    }


logger.info(f"Agent adapters module initialized. Available adapters: {get_available_adapters()}")
