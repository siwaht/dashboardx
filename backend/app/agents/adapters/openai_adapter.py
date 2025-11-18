"""
OpenAI Direct Adapter

Direct integration with OpenAI API (GPT-4, GPT-3.5, etc.)
Supports chat completions, streaming, function calling, and vision.
"""

import logging
from typing import Dict, Any, AsyncIterator, List, Optional
from datetime import datetime
import time
import json

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

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


class OpenAIAdapter(BaseAgent):
    """
    Direct OpenAI API adapter

    Provides a lightweight integration with OpenAI's API without LangChain overhead.
    Supports all OpenAI models including GPT-4, GPT-3.5-turbo, and vision models.

    Example:
        ```python
        adapter = OpenAIAdapter({
            "agent_id": "openai-gpt4",
            "name": "OpenAI GPT-4",
            "model": "gpt-4-turbo-preview",
            "api_key": "sk-...",
            "temperature": 0.7
        })

        response = await adapter.execute("Hello!", context)
        ```
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI adapter

        Args:
            config: Configuration dictionary with:
                - model: Model name (e.g., "gpt-4-turbo-preview")
                - api_key: OpenAI API key
                - temperature: Generation temperature (0-2)
                - max_tokens: Maximum tokens in response
                - system_prompt: Optional system prompt
        """
        if "type" not in config:
            config["type"] = "custom"

        super().__init__(config)

        # OpenAI-specific configuration
        self.model = config.get("model", "gpt-4-turbo-preview")
        self.api_key = config.get("api_key")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
        self.system_prompt = config.get(
            "system_prompt",
            "You are a helpful AI assistant. Provide accurate, concise answers."
        )
        self.support_functions = config.get("support_functions", False)
        self.functions = config.get("functions", [])

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)

        logger.info(f"Initialized OpenAI adapter: {self.agent_id} with model {self.model}")

    async def execute(
        self,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Execute OpenAI chat completion

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
                f"Executing OpenAI agent for query: '{query}' "
                f"(tenant: {context.tenant_id})"
            )

            # Prepare messages
            messages = self._prepare_messages(query, context)

            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": context.temperature or self.temperature,
                "max_tokens": context.max_tokens or self.max_tokens,
            }

            # Add function calling if supported
            if self.support_functions and self.functions:
                request_params["functions"] = self.functions
                request_params["function_call"] = "auto"

            # Make API call
            response: ChatCompletion = await self.client.chat.completions.create(
                **request_params
            )

            # Extract response
            message = response.choices[0].message
            answer = message.content or ""

            # Handle function calls if present
            tools_used = []
            thoughts = []
            if message.function_call:
                function_name = message.function_call.name
                function_args = message.function_call.arguments
                tools_used.append(function_name)
                thoughts.append(AgentThought(
                    step="function_call",
                    thought=f"Called function {function_name} with args: {function_args}"
                ))

            execution_time = time.time() - start_time

            # Create response
            return AgentResponse(
                answer=answer,
                citations=[],
                thoughts=thoughts,
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.COMPLETED,
                execution_time=execution_time,
                tokens_used=response.usage.total_tokens if response.usage else None,
                tools_used=tools_used,
                metadata={
                    "model": self.model,
                    "temperature": request_params["temperature"],
                    "finish_reason": response.choices[0].finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                },
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error in OpenAI execution: {e}", exc_info=True)

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
        Execute OpenAI chat with streaming

        Args:
            query: User's question
            context: Execution context

        Yields:
            AgentStreamChunk objects with incremental updates
        """
        try:
            logger.info(
                f"Executing OpenAI agent with streaming for: '{query}'"
            )

            # Prepare messages
            messages = self._prepare_messages(query, context)

            # Stream response
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=context.temperature or self.temperature,
                max_tokens=context.max_tokens or self.max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield AgentStreamChunk(
                        chunk_type="text",
                        content=chunk.choices[0].delta.content,
                        metadata={
                            "model": self.model,
                            "finish_reason": chunk.choices[0].finish_reason
                        }
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
        Get OpenAI agent capabilities

        Returns:
            AgentCapabilities describing what this agent can do
        """
        is_vision_model = "vision" in self.model.lower() or "gpt-4" in self.model

        return AgentCapabilities(
            supports_streaming=True,
            supports_tools=self.support_functions,
            supports_memory=True,
            supports_multimodal=is_vision_model,
            supports_rag=False,
            supports_code_execution=False,
            max_context_length=self._get_context_length(),
            supported_languages=["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"],
            supported_file_types=["txt", "json"] if not is_vision_model else ["txt", "json", "png", "jpg", "jpeg"]
        )

    async def health_check(self) -> HealthStatus:
        """
        Check if OpenAI API is accessible

        Returns:
            HealthStatus with health information
        """
        try:
            # Try a simple API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )

            if response and response.choices:
                return HealthStatus(
                    healthy=True,
                    message="OpenAI API is accessible",
                    details={
                        "agent_id": self.agent_id,
                        "model": self.model,
                        "api_accessible": True
                    }
                )
            else:
                return HealthStatus(
                    healthy=False,
                    message="OpenAI API returned empty response"
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
        Prepare messages for OpenAI API

        Args:
            query: User query
            context: Execution context

        Returns:
            List of message dictionaries
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add conversation history
        for msg in context.conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role in ["user", "assistant", "system"]:
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
            "gpt-4-turbo-preview": 128000,
            "gpt-4-1106-preview": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385,
        }

        return context_lengths.get(self.model, 4096)
