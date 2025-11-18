"""
Universal HTTP Adapter

Generic adapter for connecting to any HTTP/REST AI endpoint.
Supports custom request/response formats, headers, authentication.
Perfect for connecting to proprietary or self-hosted AI services.
"""

import logging
from typing import Dict, Any, AsyncIterator, Optional
from datetime import datetime
import time
import json

import httpx
from pydantic import BaseModel, Field

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


class HTTPAdapterConfig(BaseModel):
    """Configuration for HTTP adapter"""
    endpoint_url: str = Field(..., description="Base URL of the API endpoint")
    method: str = Field(default="POST", description="HTTP method (GET, POST, etc.)")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom HTTP headers")
    auth_type: Optional[str] = Field(default=None, description="Authentication type: bearer, api_key, basic")
    auth_token: Optional[str] = Field(default=None, description="Authentication token/key")
    request_template: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON template for request body"
    )
    response_path: str = Field(
        default="response",
        description="JSON path to extract answer from response"
    )
    timeout: int = Field(default=60, description="Request timeout in seconds")
    supports_streaming: bool = Field(default=False, description="Whether endpoint supports streaming")
    stream_delimiter: str = Field(default="\n", description="Delimiter for streaming responses")


class HTTPAdapter(BaseAgent):
    """
    Universal HTTP/REST adapter

    Can connect to any HTTP-based AI service by configuring request/response format.
    Perfect for:
    - Self-hosted LLMs (LLaMA, Falcon, etc.)
    - Custom AI endpoints
    - Proprietary AI services
    - AI gateways and proxies

    Example:
        ```python
        adapter = HTTPAdapter({
            "agent_id": "custom-llm",
            "name": "Custom LLM",
            "endpoint_url": "https://my-llm.com/api/chat",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "auth_type": "bearer",
            "auth_token": "your-token",
            "request_template": {
                "model": "llama-70b",
                "messages": "{{messages}}",
                "temperature": "{{temperature}}"
            },
            "response_path": "choices.0.message.content"
        })

        response = await adapter.execute("Hello!", context)
        ```
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize HTTP adapter

        Args:
            config: Configuration dictionary
        """
        if "type" not in config:
            config["type"] = "custom"

        super().__init__(config)

        # Parse HTTP-specific configuration
        self.http_config = HTTPAdapterConfig(**config)

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.http_config.timeout),
            follow_redirects=True
        )

        logger.info(
            f"Initialized HTTP adapter: {self.agent_id} "
            f"pointing to {self.http_config.endpoint_url}"
        )

    async def execute(
        self,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Execute HTTP request to custom endpoint

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
                f"Executing HTTP agent for query: '{query}' "
                f"(tenant: {context.tenant_id})"
            )

            # Prepare request
            url, headers, body = self._prepare_request(query, context)

            # Make HTTP request
            response = await self.client.request(
                method=self.http_config.method,
                url=url,
                headers=headers,
                json=body
            )

            response.raise_for_status()

            # Parse response
            response_data = response.json()
            answer = self._extract_answer(response_data)

            execution_time = time.time() - start_time

            # Create response
            return AgentResponse(
                answer=answer,
                citations=self._extract_citations(response_data),
                thoughts=self._extract_thoughts(response_data),
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.COMPLETED,
                execution_time=execution_time,
                metadata={
                    "endpoint": self.http_config.endpoint_url,
                    "method": self.http_config.method,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                },
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return self._create_error_response(
                f"HTTP error {e.response.status_code}: {e.response.text}",
                start_time,
                started_at
            )

        except Exception as e:
            logger.error(f"Error in HTTP execution: {e}", exc_info=True)
            return self._create_error_response(str(e), start_time, started_at)

    async def execute_streaming(
        self,
        query: str,
        context: AgentContext
    ) -> AsyncIterator[AgentStreamChunk]:
        """
        Execute HTTP request with streaming

        Args:
            query: User's question
            context: Execution context

        Yields:
            AgentStreamChunk objects with incremental updates
        """
        if not self.http_config.supports_streaming:
            # Fallback to non-streaming
            response = await self.execute(query, context)
            yield AgentStreamChunk(
                chunk_type="text",
                content=response.answer,
                metadata={}
            )
            return

        try:
            logger.info(
                f"Executing HTTP agent with streaming for: '{query}'"
            )

            # Prepare request
            url, headers, body = self._prepare_request(query, context)

            # Make streaming request
            async with self.client.stream(
                method=self.http_config.method,
                url=url,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        # Parse streaming chunk
                        chunk_data = self._parse_stream_chunk(line)
                        if chunk_data:
                            yield AgentStreamChunk(
                                chunk_type="text",
                                content=chunk_data,
                                metadata={}
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
        Get HTTP agent capabilities

        Returns:
            AgentCapabilities describing what this agent can do
        """
        # For generic HTTP adapters, capabilities are limited
        # Users can override this in configuration
        return AgentCapabilities(
            supports_streaming=self.http_config.supports_streaming,
            supports_tools=False,
            supports_memory=True,
            supports_multimodal=False,
            supports_rag=False,
            supports_code_execution=False,
            max_context_length=4096,
            supported_languages=["en"],
            supported_file_types=["txt", "json"]
        )

    async def health_check(self) -> HealthStatus:
        """
        Check if HTTP endpoint is accessible

        Returns:
            HealthStatus with health information
        """
        try:
            # Try a simple request to the endpoint
            response = await self.client.get(
                self.http_config.endpoint_url,
                timeout=10.0
            )

            # Accept any 2xx or 3xx status as healthy
            # (some endpoints return 405 for GET when only POST is allowed)
            is_healthy = response.status_code < 500

            return HealthStatus(
                healthy=is_healthy,
                message=f"Endpoint returned status {response.status_code}",
                details={
                    "agent_id": self.agent_id,
                    "endpoint": self.http_config.endpoint_url,
                    "status_code": response.status_code
                }
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthStatus(
                healthy=False,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def cleanup(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

    def _prepare_request(
        self,
        query: str,
        context: AgentContext
    ) -> tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        Prepare HTTP request

        Args:
            query: User query
            context: Execution context

        Returns:
            Tuple of (url, headers, body)
        """
        # URL
        url = self.http_config.endpoint_url

        # Headers
        headers = dict(self.http_config.headers)

        # Add authentication
        if self.http_config.auth_type == "bearer" and self.http_config.auth_token:
            headers["Authorization"] = f"Bearer {self.http_config.auth_token}"
        elif self.http_config.auth_type == "api_key" and self.http_config.auth_token:
            headers["X-API-Key"] = self.http_config.auth_token

        # Body - apply template with variable substitution
        body = self._apply_template(query, context)

        return url, headers, body

    def _apply_template(
        self,
        query: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Apply request template with variable substitution

        Args:
            query: User query
            context: Execution context

        Returns:
            Request body dictionary
        """
        # Start with template
        body = dict(self.http_config.request_template)

        # Prepare variables for substitution
        variables = {
            "query": query,
            "messages": self._format_messages(query, context),
            "temperature": context.temperature or 0.7,
            "max_tokens": context.max_tokens or 2000,
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id
        }

        # Recursive template substitution
        return self._substitute_variables(body, variables)

    def _substitute_variables(
        self,
        obj: Any,
        variables: Dict[str, Any]
    ) -> Any:
        """
        Recursively substitute {{variable}} placeholders

        Args:
            obj: Object to process
            variables: Variables to substitute

        Returns:
            Object with substitutions applied
        """
        if isinstance(obj, str):
            # Replace {{variable}} with value
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in obj:
                    return value if obj == placeholder else obj.replace(placeholder, str(value))
            return obj

        elif isinstance(obj, dict):
            return {k: self._substitute_variables(v, variables) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._substitute_variables(item, variables) for item in obj]

        else:
            return obj

    def _format_messages(
        self,
        query: str,
        context: AgentContext
    ) -> list:
        """Format conversation history as messages"""
        messages = []

        for msg in context.conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        messages.append({"role": "user", "content": query})

        return messages

    def _extract_answer(self, response_data: Dict[str, Any]) -> str:
        """
        Extract answer from response using configured path

        Args:
            response_data: Response JSON

        Returns:
            Extracted answer string
        """
        # Navigate JSON path (e.g., "choices.0.message.content")
        path_parts = self.http_config.response_path.split(".")
        value = response_data

        for part in path_parts:
            if part.isdigit():
                value = value[int(part)]
            else:
                value = value.get(part, "")

        return str(value) if value else "No response"

    def _extract_citations(self, response_data: Dict[str, Any]) -> list[Citation]:
        """Extract citations from response if present"""
        # This is optional - implement based on your API's format
        return []

    def _extract_thoughts(self, response_data: Dict[str, Any]) -> list[AgentThought]:
        """Extract agent thoughts from response if present"""
        # This is optional - implement based on your API's format
        return []

    def _parse_stream_chunk(self, line: str) -> Optional[str]:
        """
        Parse a streaming response chunk

        Args:
            line: Line from streaming response

        Returns:
            Extracted content or None
        """
        try:
            # Try to parse as JSON (common for SSE)
            if line.startswith("data: "):
                line = line[6:]

            if line.strip() == "[DONE]":
                return None

            data = json.loads(line)
            return self._extract_answer(data)

        except json.JSONDecodeError:
            # If not JSON, return line as-is
            return line

        except Exception:
            return None

    def _create_error_response(
        self,
        error: str,
        start_time: float,
        started_at: datetime
    ) -> AgentResponse:
        """Create standardized error response"""
        return AgentResponse(
            answer=f"I apologize, but I encountered an error: {error}",
            agent_id=self.agent_id,
            agent_type=AgentType.CUSTOM,
            status=AgentStatus.FAILED,
            execution_time=time.time() - start_time,
            error=error,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )
