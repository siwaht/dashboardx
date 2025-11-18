"""
MCP (Model Context Protocol) Adapter

Connects to agents using Anthropic's Model Context Protocol.
MCP is a standard for connecting LLMs to external tools and data sources.

Learn more: https://modelcontextprotocol.io/
"""

import logging
from typing import Dict, Any, AsyncIterator, List, Optional
from datetime import datetime
import time
import json

import httpx

from app.agents.base import (
    BaseAgent,
    AgentResponse,
    AgentContext,
    AgentCapabilities,
    AgentType,
    AgentStatus,
    AgentStreamChunk,
    HealthStatus,
    Citation,
    AgentThought
)

logger = logging.getLogger(__name__)


class MCPAdapter(BaseAgent):
    """
    Model Context Protocol (MCP) Adapter

    Connects to agents using MCP - Anthropic's open standard for
    connecting LLMs to external tools and data sources.

    MCP Features:
    - Standardized tool/resource definitions
    - Prompt templates
    - Sampling from LLMs
    - Built-in security model

    Example:
        ```python
        adapter = MCPAdapter({
            "agent_id": "mcp-rag",
            "name": "MCP RAG Agent",
            "mcp_server_url": "http://localhost:3000",
            "tools": ["search", "retrieve"],
            "model": "claude-3-opus-20240229"
        })
        ```
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCP adapter

        Args:
            config: Configuration with:
                - mcp_server_url: URL of MCP server
                - tools: List of available tools
                - resources: List of available resources
                - model: Model to use (optional)
                - api_key: API key for MCP server (optional)
        """
        if "type" not in config:
            config["type"] = "custom"

        super().__init__(config)

        # MCP configuration
        self.mcp_server_url = config.get("mcp_server_url")
        self.tools = config.get("tools", [])
        self.resources = config.get("resources", [])
        self.model = config.get("model", "claude-3-opus-20240229")
        self.api_key = config.get("api_key")

        if not self.mcp_server_url:
            raise ValueError("mcp_server_url is required")

        # Initialize HTTP client
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.mcp_server_url,
            headers=headers,
            timeout=httpx.Timeout(60.0)
        )

        logger.info(f"Initialized MCP adapter: {self.agent_id} -> {self.mcp_server_url}")

    async def execute(
        self,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Execute agent via MCP

        Args:
            query: User's question
            context: Execution context

        Returns:
            AgentResponse with answer
        """
        start_time = time.time()
        started_at = datetime.utcnow()

        try:
            logger.info(f"Executing MCP agent: {self.agent_id}")

            # Step 1: List available tools and resources
            tools_list = await self._list_tools()
            resources_list = await self._list_resources()

            # Step 2: Create prompt with context
            prompt = await self._create_prompt(query, context)

            # Step 3: Execute sampling (get LLM response with tool use)
            response = await self._sample(prompt, tools_list)

            # Step 4: If tools were used, get results and continue
            thoughts = []
            tools_used = []

            if "tool_calls" in response:
                for tool_call in response["tool_calls"]:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["arguments"]

                    tools_used.append(tool_name)

                    # Call tool via MCP
                    tool_result = await self._call_tool(tool_name, tool_args)

                    thoughts.append(AgentThought(
                        step=f"tool_{tool_name}",
                        thought=f"Used {tool_name} with {tool_args}, got: {tool_result}"
                    ))

                    # Continue sampling with tool results
                    response = await self._sample_with_tools(
                        prompt,
                        tool_call,
                        tool_result,
                        tools_list
                    )

            # Extract final answer
            answer = response.get("content", "No response generated")

            execution_time = time.time() - start_time

            return AgentResponse(
                answer=answer,
                citations=self._extract_citations(response),
                thoughts=thoughts,
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.COMPLETED,
                execution_time=execution_time,
                tools_used=tools_used,
                metadata={
                    "mcp_server": self.mcp_server_url,
                    "model": self.model,
                    "tools_available": len(tools_list)
                },
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error in MCP execution: {e}", exc_info=True)

            return AgentResponse(
                answer=f"MCP error: {str(e)}",
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.FAILED,
                execution_time=time.time() - start_time,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

    async def execute_streaming(
        self,
        query: str,
        context: AgentContext
    ) -> AsyncIterator[AgentStreamChunk]:
        """
        Execute MCP agent with streaming

        Args:
            query: User's question
            context: Execution context

        Yields:
            AgentStreamChunk objects
        """
        try:
            # For now, fall back to non-streaming
            response = await self.execute(query, context)

            # Yield the answer in chunks
            words = response.answer.split()
            for i, word in enumerate(words):
                yield AgentStreamChunk(
                    chunk_type="text",
                    content=word + " ",
                    metadata={}
                )

            yield AgentStreamChunk(
                chunk_type="completion",
                content="",
                metadata={"status": "completed"}
            )

        except Exception as e:
            logger.error(f"Error in MCP streaming: {e}")
            yield AgentStreamChunk(
                chunk_type="error",
                content=str(e),
                metadata={"status": "failed"}
            )

    def get_capabilities(self) -> AgentCapabilities:
        """Get MCP agent capabilities"""
        return AgentCapabilities(
            supports_streaming=True,
            supports_tools=len(self.tools) > 0,
            supports_memory=True,
            supports_multimodal=False,
            supports_rag=True,
            supports_code_execution=False,
            max_context_length=200000,
            supported_languages=["en"],
            supported_file_types=["txt", "json", "pdf"]
        )

    async def health_check(self) -> HealthStatus:
        """Check if MCP server is accessible"""
        try:
            # Try to list tools
            response = await self.client.get("/mcp/v1/tools")

            if response.status_code == 200:
                return HealthStatus(
                    healthy=True,
                    message="MCP server is accessible",
                    details={
                        "mcp_server": self.mcp_server_url,
                        "status_code": response.status_code
                    }
                )
            else:
                return HealthStatus(
                    healthy=False,
                    message=f"MCP server returned {response.status_code}"
                )

        except Exception as e:
            return HealthStatus(
                healthy=False,
                message=f"MCP server unreachable: {str(e)}",
                details={"error": str(e)}
            )

    async def cleanup(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

    # ==================== MCP Protocol Methods ====================

    async def _list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server"""
        try:
            response = await self.client.get("/mcp/v1/tools")
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])
        except Exception as e:
            logger.warning(f"Could not list MCP tools: {e}")
            return []

    async def _list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from MCP server"""
        try:
            response = await self.client.get("/mcp/v1/resources")
            response.raise_for_status()
            data = response.json()
            return data.get("resources", [])
        except Exception as e:
            logger.warning(f"Could not list MCP resources: {e}")
            return []

    async def _create_prompt(
        self,
        query: str,
        context: AgentContext
    ) -> str:
        """Create prompt with MCP context"""
        # Build prompt with conversation history
        prompt_parts = []

        # Add system context
        prompt_parts.append("You are a helpful AI assistant with access to external tools and data.")

        # Add conversation history
        for msg in context.conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")

        # Add current query
        prompt_parts.append(f"user: {query}")

        return "\n\n".join(prompt_parts)

    async def _sample(
        self,
        prompt: str,
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sample from LLM via MCP

        This is the core MCP operation
        """
        try:
            response = await self.client.post(
                "/mcp/v1/sampling/create",
                json={
                    "prompt": prompt,
                    "model": self.model,
                    "tools": tools,
                    "max_tokens": 4096
                }
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"MCP sampling failed: {e}")
            return {"content": f"Sampling error: {str(e)}"}

    async def _call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool via MCP"""
        try:
            response = await self.client.post(
                f"/mcp/v1/tools/{tool_name}/call",
                json={"arguments": arguments}
            )

            response.raise_for_status()
            data = response.json()
            return data.get("result", "")

        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return f"Tool error: {str(e)}"

    async def _sample_with_tools(
        self,
        original_prompt: str,
        tool_call: Dict[str, Any],
        tool_result: Any,
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Continue sampling after tool use"""
        # Add tool result to prompt
        extended_prompt = f"{original_prompt}\n\nTool {tool_call['name']} returned: {tool_result}\n\nNow provide the final answer:"

        return await self._sample(extended_prompt, tools)

    def _extract_citations(self, response: Dict[str, Any]) -> List[Citation]:
        """Extract citations from MCP response"""
        citations = []

        # MCP may return sources in various formats
        if "sources" in response:
            for source in response["sources"]:
                citations.append(Citation(
                    source=source.get("name", "unknown"),
                    content=source.get("content", ""),
                    relevance_score=source.get("score"),
                    metadata=source.get("metadata", {})
                ))

        return citations
