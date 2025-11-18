"""
WebSocket Adapter

Real-time bidirectional communication with AI agents via WebSocket.
Perfect for interactive agents that need continuous conversation.
"""

import logging
from typing import Dict, Any, AsyncIterator, Optional
from datetime import datetime
import time
import json
import asyncio

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


class WebSocketAdapter(BaseAgent):
    """
    WebSocket-based agent adapter

    Maintains persistent connection for real-time agent interaction.
    Great for:
    - Interactive agents with state
    - Real-time collaboration
    - Live agent responses
    - Bidirectional communication

    Example:
        ```python
        adapter = WebSocketAdapter({
            "agent_id": "ws-agent",
            "name": "WebSocket Agent",
            "websocket_url": "ws://localhost:8080/agent"
        })
        ```
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize WebSocket adapter

        Args:
            config: Configuration with:
                - websocket_url: WebSocket URL
                - auth_token: Optional authentication token
                - reconnect: Auto-reconnect on disconnect
                - ping_interval: Keepalive ping interval
        """
        if "type" not in config:
            config["type"] = "custom"

        super().__init__(config)

        # WebSocket configuration
        self.websocket_url = config.get("websocket_url")
        self.auth_token = config.get("auth_token")
        self.reconnect = config.get("reconnect", True)
        self.ping_interval = config.get("ping_interval", 30)

        if not self.websocket_url:
            raise ValueError("websocket_url is required")

        # WebSocket connection
        self.ws = None
        self.connected = False
        self._message_queue = asyncio.Queue()

        logger.info(f"Initialized WebSocket adapter: {self.agent_id} -> {self.websocket_url}")

    async def initialize(self) -> None:
        """Initialize WebSocket connection"""
        try:
            # Import websockets library
            import websockets

            # Connect to WebSocket
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            self.ws = await websockets.connect(
                self.websocket_url,
                extra_headers=headers,
                ping_interval=self.ping_interval
            )

            self.connected = True

            # Start message receiver task
            asyncio.create_task(self._receive_messages())

            logger.info(f"WebSocket connected: {self.agent_id}")

        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            self.connected = False
            raise

    async def execute(
        self,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Execute agent via WebSocket

        Args:
            query: User's question
            context: Execution context

        Returns:
            AgentResponse with answer
        """
        start_time = time.time()
        started_at = datetime.utcnow()

        try:
            # Ensure connected
            if not self.connected or not self.ws:
                await self.initialize()

            logger.info(f"Sending query via WebSocket: {query}")

            # Prepare message
            message = {
                "type": "query",
                "query": query,
                "session_id": context.session_id,
                "user_id": context.user_id,
                "tenant_id": context.tenant_id,
                "conversation_history": context.conversation_history,
                "metadata": context.metadata
            }

            # Send message
            await self.ws.send(json.dumps(message))

            # Wait for response
            response_data = await asyncio.wait_for(
                self._message_queue.get(),
                timeout=60.0
            )

            # Parse response
            answer = response_data.get("answer", "No response")
            execution_time = time.time() - start_time

            return AgentResponse(
                answer=answer,
                citations=response_data.get("citations", []),
                thoughts=response_data.get("thoughts", []),
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.COMPLETED,
                execution_time=execution_time,
                metadata={
                    "websocket_url": self.websocket_url,
                    "connected": self.connected
                },
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except asyncio.TimeoutError:
            return AgentResponse(
                answer="WebSocket timeout - no response received",
                agent_id=self.agent_id,
                agent_type=AgentType.CUSTOM,
                status=AgentStatus.TIMEOUT,
                execution_time=time.time() - start_time,
                error="Timeout waiting for response",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error in WebSocket execution: {e}", exc_info=True)

            return AgentResponse(
                answer=f"WebSocket error: {str(e)}",
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
        Execute WebSocket with streaming

        Args:
            query: User's question
            context: Execution context

        Yields:
            AgentStreamChunk objects
        """
        try:
            # Ensure connected
            if not self.connected or not self.ws:
                await self.initialize()

            # Prepare message
            message = {
                "type": "query",
                "query": query,
                "session_id": context.session_id,
                "stream": True
            }

            # Send message
            await self.ws.send(json.dumps(message))

            # Stream responses
            while True:
                try:
                    response_data = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=60.0
                    )

                    # Check if complete
                    if response_data.get("type") == "complete":
                        break

                    # Yield chunk
                    if "content" in response_data:
                        yield AgentStreamChunk(
                            chunk_type="text",
                            content=response_data["content"],
                            metadata={}
                        )

                except asyncio.TimeoutError:
                    break

            # Send completion
            yield AgentStreamChunk(
                chunk_type="completion",
                content="",
                metadata={"status": "completed"}
            )

        except Exception as e:
            logger.error(f"Error in WebSocket streaming: {e}")
            yield AgentStreamChunk(
                chunk_type="error",
                content=str(e),
                metadata={"status": "failed"}
            )

    def get_capabilities(self) -> AgentCapabilities:
        """Get WebSocket agent capabilities"""
        return AgentCapabilities(
            supports_streaming=True,
            supports_tools=False,
            supports_memory=True,
            supports_multimodal=False,
            supports_rag=True,
            supports_code_execution=False,
            max_context_length=8000,
            supported_languages=["en"],
            supported_file_types=["txt", "json"]
        )

    async def health_check(self) -> HealthStatus:
        """Check if WebSocket is connected"""
        try:
            if self.connected and self.ws:
                # Try to ping
                try:
                    await self.ws.ping()
                    return HealthStatus(
                        healthy=True,
                        message="WebSocket connected",
                        details={
                            "websocket_url": self.websocket_url,
                            "connected": True
                        }
                    )
                except:
                    pass

            return HealthStatus(
                healthy=False,
                message="WebSocket not connected",
                details={
                    "websocket_url": self.websocket_url,
                    "connected": False
                }
            )

        except Exception as e:
            return HealthStatus(
                healthy=False,
                message=f"WebSocket error: {str(e)}",
                details={"error": str(e)}
            )

    async def cleanup(self) -> None:
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            logger.info(f"WebSocket closed: {self.agent_id}")

    async def _receive_messages(self) -> None:
        """Background task to receive WebSocket messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._message_queue.put(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from WebSocket: {message}")

        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
            self.connected = False

            # Attempt reconnect if enabled
            if self.reconnect:
                await asyncio.sleep(5)
                try:
                    await self.initialize()
                except:
                    pass
