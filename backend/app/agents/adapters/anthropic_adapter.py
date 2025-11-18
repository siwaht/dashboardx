"""
Anthropic Claude Adapter

Direct integration with Anthropic's Claude API.
Supports Claude 3 (Opus, Sonnet, Haiku) and Claude 2.x models.
"""

import logging
from typing import Dict, Any, AsyncIterator, List
from datetime import datetime
import time

from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageStreamEvent

from app.agents.base import (
    BaseAgent,
    AgentResponse,
    AgentContext,
    AgentCapabilities,
    AgentType,
    AgentStatus,
    AgentStreamChunk,
    HealthStatus,
    AgentThought
)

logger = logging.getLogger(__name__)


class AnthropicAdapter(BaseAgent):
    """
    Direct Anthropic Claude API adapter

    Provides integration with Claude models without additional frameworks.
    Supports Claude 3 Opus, Sonnet, Haiku, and Claude 2.x.

    Example:
        ```python
        adapter = AnthropicAdapter({
            "agent_id": "claude-opus",
            "name": "Claude 3 Opus",
            "model": "claude-3-opus-20240229",
            "api_key": "sk-ant-...",
            "temperature": 1.0
        })

        response = await adapter.execute("Hello!", context)
        ```
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anthropic adapter

        Args:
            config: Configuration dictionary
        """
        if "type" not in config:
            config["type"] = "custom"

        super().__init__(config)

        # Anthropic-specific configuration
        self.model = config.get("model", "claude-3-sonnet-20240229")
        self.api_key = config.get("api_key")
        self.temperature = config.get("temperature", 1.0)
        self.max_tokens = config.get("max_tokens", 4096)
        self.system_prompt = config.get(
            "system_prompt",
            "You are Claude, a helpful AI assistant created by Anthropic."
        )

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        # Initialize Anthropic client
        self.client = AsyncAnthropic(api_key=self.api_key)

        logger.info(f"Initialized Anthropic adapter: {self.agent_id} with model {self.model}")

    async def execute(
        self,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Execute Claude completion

        Args:
            query: User's question
            context: Execution context

        Returns:
            AgentResponse with answer and metadata
        """
        start_time = time.time()
        started_at = datetime.utcnow()

        try:
            logger.info(
                f"Executing Anthropic agent for query: '{query}' "
                f"(tenant: {context.tenant_id})"
            )

            # Prepare messages
            messages = self._prepare_messages(query, context)

            # Make API call
            response: Message = await self.client.messages.create(
                model=self.model,
                max_tokens=context.max_tokens or self.max_tokens,
                temperature=context.temperature or self.temperature,
                system=self.system_prompt,
                messages=messages
            )

            # Extract response
            answer = ""
            if response.content:
                answer = " ".join([
                    block.text for block in response.content
                    if hasattr(block, 'text')
                ])

            execution_time = time.time() - start_time

            # Create response
            return AgentResponse(
                answer=answer,
                citations=[],
                thoughts=[],
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.COMPLETED,
                execution_time=execution_time,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                    "stop_reason": response.stop_reason,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error in Anthropic execution: {e}", exc_info=True)

            return AgentResponse(
                answer=f"I apologize, but I encountered an error: {str(e)}",
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
        Execute Claude with streaming

        Args:
            query: User's question
            context: Execution context

        Yields:
            AgentStreamChunk objects with incremental updates
        """
        try:
            logger.info(
                f"Executing Anthropic agent with streaming for: '{query}'"
            )

            # Prepare messages
            messages = self._prepare_messages(query, context)

            # Stream response
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=context.max_tokens or self.max_tokens,
                temperature=context.temperature or self.temperature,
                system=self.system_prompt,
                messages=messages
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield AgentStreamChunk(
                                chunk_type="text",
                                content=event.delta.text,
                                metadata={"model": self.model}
                            )

            # Send completion chunk
            yield AgentStreamChunk(
                chunk_type="completion",
                content="",
                metadata={"status": "completed"}
            )

        except Exception as e:
            logger.error(f"Error in streaming execution: {e}", exc_info=True)

            yield AgentStreamChunk(
                chunk_type="error",
                content=str(e),
                metadata={"status": "failed"}
            )

    def get_capabilities(self) -> AgentCapabilities:
        """
        Get Anthropic agent capabilities

        Returns:
            AgentCapabilities describing what this agent can do
        """
        is_claude_3 = "claude-3" in self.model

        return AgentCapabilities(
            supports_streaming=True,
            supports_tools=is_claude_3,  # Claude 3 supports tools
            supports_memory=True,
            supports_multimodal=is_claude_3,  # Claude 3 supports vision
            supports_rag=False,
            supports_code_execution=False,
            max_context_length=self._get_context_length(),
            supported_languages=["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"],
            supported_file_types=["txt", "json"] if not is_claude_3 else ["txt", "json", "png", "jpg", "jpeg", "pdf"]
        )

    async def health_check(self) -> HealthStatus:
        """
        Check if Anthropic API is accessible

        Returns:
            HealthStatus with health information
        """
        try:
            # Try a simple API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )

            if response and response.content:
                return HealthStatus(
                    healthy=True,
                    message="Anthropic API is accessible",
                    details={
                        "agent_id": self.agent_id,
                        "model": self.model,
                        "api_accessible": True
                    }
                )
            else:
                return HealthStatus(
                    healthy=False,
                    message="Anthropic API returned empty response"
                )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthStatus(
                healthy=False,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)}
            )

    def _prepare_messages(
        self,
        query: str,
        context: AgentContext
    ) -> List[Dict[str, str]]:
        """
        Prepare messages for Anthropic API

        Args:
            query: User query
            context: Execution context

        Returns:
            List of message dictionaries
        """
        messages = []

        # Add conversation history
        for msg in context.conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Anthropic only accepts 'user' and 'assistant' roles
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})

        # Add current query
        messages.append({"role": "user", "content": query})

        return messages

    def _get_context_length(self) -> int:
        """
        Get context length for the model

        Returns:
            Maximum context length in tokens
        """
        context_lengths = {
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
        }

        return context_lengths.get(self.model, 100000)
