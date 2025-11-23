"""
Webhook Adapter

Simple adapter for agents that communicate via webhooks.
Perfect for testing custom agents - just provide a webhook URL!
"""

import logging
from typing import Dict, Any, AsyncIterator, Optional
from datetime import datetime
import time
import asyncio
import uuid

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
)

logger = logging.getLogger(__name__)


class WebhookAdapter(BaseAgent):
    """
    Webhook-based agent adapter

    Super simple way to connect any agent that can receive HTTP requests.
    Just provide a webhook URL and start using it!

    Perfect for:
    - Testing custom agents
    - Prototyping new AI services
    - Integrating with no-code platforms (Zapier, Make, n8n)
    - Connecting serverless functions
    - Quick demos

    Example:
        ```python
        adapter = WebhookAdapter({
            "agent_id": "my-webhook",
            "name": "My Agent",
            "webhook_url": "https://your-agent.com/webhook",
            "method": "POST",
            "response_timeout": 30
        })

        # That's it! Now use it:
        response = await adapter.execute("Hello!", context)
        ```
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Webhook adapter

        Args:
            config: Configuration with:
                - webhook_url: URL to send requests to
                - method: HTTP method (default: POST)
                - headers: Optional custom headers
                - auth_header: Optional auth header value
                - response_timeout: Timeout in seconds (default: 30)
                - callback_mode: If True, expects async callback
        """
        if "type" not in config:
            config["type"] = "custom"

        super().__init__(config)

        # Webhook configuration
        self.webhook_url = config.get("webhook_url")
        self.method = config.get("method", "POST")
        self.headers = config.get("headers", {})
        self.auth_header = config.get("auth_header")
        self.response_timeout = config.get("response_timeout", 30)
        self.callback_mode = config.get("callback_mode", False)

        if not self.webhook_url:
            raise ValueError("webhook_url is required")

        # Add auth header if provided
        if self.auth_header:
            self.headers["Authorization"] = self.auth_header

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.response_timeout),
            follow_redirects=True
        )

        # For callback mode
        self._pending_requests: Dict[str, asyncio.Future] = {}

        logger.info(f"Initialized Webhook adapter: {self.agent_id} -> {self.webhook_url}")

    async def execute(
        self,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Execute agent via webhook

        Args:
            query: User's question
            context: Execution context

        Returns:
            AgentResponse with answer
        """
        start_time = time.time()
        started_at = datetime.utcnow()

        try:
            logger.info(f"Calling webhook: {self.webhook_url}")

            # Prepare request payload
            payload = self._prepare_payload(query, context)

            # Make webhook request
            response = await self.client.request(
                method=self.method,
                url=self.webhook_url,
                headers=self.headers,
                json=payload
            )

            response.raise_for_status()

            # Parse response
            response_data = response.json()
            answer = self._extract_answer(response_data)

            execution_time = time.time() - start_time

            return AgentResponse(
                answer=answer,
                citations=self._extract_citations(response_data),
                thoughts=self._extract_thoughts(response_data),
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.COMPLETED,
                execution_time=execution_time,
                metadata={
                    "webhook_url": self.webhook_url,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                },
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Webhook error: {e.response.status_code}")
            return self._create_error_response(
                f"Webhook returned {e.response.status_code}",
                start_time,
                started_at
            )

        except Exception as e:
            logger.error(f"Error calling webhook: {e}", exc_info=True)
            return self._create_error_response(str(e), start_time, started_at)

    async def execute_streaming(
        self,
        query: str,
        context: AgentContext
    ) -> AsyncIterator[AgentStreamChunk]:
        """
        Execute webhook with streaming support

        Args:
            query: User's question
            context: Execution context

        Yields:
            AgentStreamChunk objects
        """
        try:
            logger.info(f"Calling webhook with streaming: {self.webhook_url}")

            payload = self._prepare_payload(query, context)
            payload["stream"] = True  # Tell webhook we want streaming

            async with self.client.stream(
                method=self.method,
                url=self.webhook_url,
                headers=self.headers,
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        # Parse SSE or JSON lines
                        content = self._parse_stream_line(line)
                        if content:
                            yield AgentStreamChunk(
                                chunk_type="text",
                                content=content,
                                metadata={}
                            )

            yield AgentStreamChunk(
                chunk_type="completion",
                content="",
                metadata={"status": "completed"}
            )

        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            yield AgentStreamChunk(
                chunk_type="error",
                content=str(e),
                metadata={"status": "failed"}
            )

    def get_capabilities(self) -> AgentCapabilities:
        """Get webhook agent capabilities"""
        return AgentCapabilities(
            supports_streaming=True,
            supports_tools=False,
            supports_memory=True,
            supports_multimodal=False,
            supports_rag=True,  # Webhook can implement RAG
            supports_code_execution=False,
            max_context_length=8000,
            supported_languages=["en"],
            supported_file_types=["txt", "json"]
        )

    async def health_check(self) -> HealthStatus:
        """Check if webhook is accessible"""
        try:
            # Try OPTIONS or GET request
            response = await self.client.request(
                method="GET",
                url=self.webhook_url,
                timeout=5.0
            )

            # Accept any non-5xx response
            is_healthy = response.status_code < 500

            return HealthStatus(
                healthy=is_healthy,
                message=f"Webhook responded with {response.status_code}",
                details={
                    "webhook_url": self.webhook_url,
                    "status_code": response.status_code
                }
            )

        except Exception as e:
            return HealthStatus(
                healthy=False,
                message=f"Webhook unreachable: {str(e)}",
                details={"error": str(e)}
            )

    async def cleanup(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

    def _prepare_payload(self, query: str, context: AgentContext) -> Dict[str, Any]:
        """
        Prepare webhook payload

        Standard format that most agents can understand
        """
        return {
            "query": query,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "tenant_id": context.tenant_id,
            "conversation_history": context.conversation_history,
            "metadata": context.metadata,
            "temperature": context.temperature,
            "max_tokens": context.max_tokens
        }

    def _extract_answer(self, response_data: Dict[str, Any]) -> str:
        """Extract answer from webhook response"""
        # Try common response formats
        if "answer" in response_data:
            return response_data["answer"]
        elif "response" in response_data:
            return response_data["response"]
        elif "text" in response_data:
            return response_data["text"]
        elif "message" in response_data:
            return response_data["message"]
        elif "content" in response_data:
            return response_data["content"]
        else:
            # Return entire response as string
            return str(response_data)

    def _extract_citations(self, response_data: Dict[str, Any]) -> list:
        """Extract citations if present"""
        return response_data.get("citations", [])

    def _extract_thoughts(self, response_data: Dict[str, Any]) -> list:
        """Extract agent thoughts if present"""
        return response_data.get("thoughts", [])

    def _parse_stream_line(self, line: str) -> Optional[str]:
        """Parse streaming response line"""
        try:
            # Handle SSE format
            if line.startswith("data: "):
                line = line[6:]

            if line.strip() == "[DONE]":
                return None

            # Try to parse as JSON
            import json
            data = json.loads(line)
            return self._extract_answer(data)

        except:
            # Return line as-is if not JSON
            return line.strip()

    def _create_error_response(
        self,
        error: str,
        start_time: float,
        started_at: datetime
    ) -> AgentResponse:
        """Create error response"""
        return AgentResponse(
            answer=f"Webhook error: {error}",
            agent_id=self.agent_id,
            agent_type=AgentType.CUSTOM,
            status=AgentStatus.FAILED,
            execution_time=time.time() - start_time,
            error=error,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )

    async def handle_callback(
        self,
        request_id: str,
        response_data: Dict[str, Any]
    ) -> None:
        """
        Handle async callback from webhook

        For webhooks that return immediately and callback later
        """
        if request_id in self._pending_requests:
            future = self._pending_requests[request_id]
            future.set_result(response_data)
            del self._pending_requests[request_id]
