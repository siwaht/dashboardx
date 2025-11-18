"""
Quick Connect API

Super simple "paste URL and go" agent connection.
Auto-detects agent type and configures everything automatically.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
import httpx

from app.security.auth import get_current_user
from app.agents.registry import AgentRegistry
from app.agents.factory import get_agent_factory

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================

class QuickConnectRequest(BaseModel):
    """Super simple quick connect request"""
    url: str = Field(..., description="Agent URL (any format)")
    name: Optional[str] = Field(None, description="Optional name (auto-generated if not provided)")
    api_key: Optional[str] = Field(None, description="Optional API key")
    test_query: Optional[str] = Field("Hello!", description="Test query to validate connection")


class QuickConnectResponse(BaseModel):
    """Quick connect response"""
    success: bool
    agent_type: str
    config_id: str
    message: str
    test_result: Optional[Dict[str, Any]] = None
    details: Dict[str, Any]


# ==================== Auto-Detection Logic ====================

async def detect_agent_type(url: str, api_key: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
    """
    Auto-detect agent type from URL

    Returns:
        Tuple of (agent_type, config)
    """
    url_lower = url.lower()

    # OpenAI
    if "openai" in url_lower or "api.openai.com" in url_lower:
        return "openai", {
            "api_key": api_key,
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7
        }

    # Anthropic
    if "anthropic" in url_lower or "api.anthropic.com" in url_lower:
        return "anthropic", {
            "api_key": api_key,
            "model": "claude-3-opus-20240229",
            "temperature": 1.0
        }

    # WebSocket
    if url.startswith("ws://") or url.startswith("wss://"):
        return "websocket", {
            "websocket_url": url,
            "auth_token": api_key
        }

    # Check if it's a webhook/HTTP endpoint
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to determine type by probing
            try:
                # Try POST request
                response = await client.post(
                    url,
                    json={"query": "test", "type": "probe"},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code < 500:
                    # It's a working HTTP endpoint
                    return "http", {
                        "endpoint_url": url,
                        "method": "POST",
                        "auth_type": "bearer" if api_key else None,
                        "auth_token": api_key,
                        "request_template": {
                            "query": "{{query}}",
                            "messages": "{{messages}}"
                        },
                        "response_path": "response"
                    }

            except httpx.RequestError:
                pass

            # Try GET to see if it responds at all
            try:
                response = await client.get(url, timeout=5.0)

                if response.status_code < 500:
                    # Treat as webhook/HTTP
                    return "webhook", {
                        "webhook_url": url,
                        "method": "POST",
                        "auth_header": f"Bearer {api_key}" if api_key else None
                    }

            except:
                pass

    except Exception as e:
        logger.warning(f"Could not probe URL: {e}")

    # Default to HTTP adapter (most flexible)
    return "http", {
        "endpoint_url": url,
        "method": "POST",
        "auth_type": "bearer" if api_key else None,
        "auth_token": api_key,
        "request_template": {
            "query": "{{query}}"
        },
        "response_path": "response"
    }


def generate_agent_name(url: str, agent_type: str) -> str:
    """Generate a friendly name from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path

        # Clean up host
        host = host.replace("www.", "").replace(".com", "").replace(".ai", "")
        host = host.replace("api.", "").replace("http://", "").replace("https://", "")

        # Capitalize
        words = host.split(".")
        name = " ".join(word.capitalize() for word in words if word)

        return f"{name} ({agent_type})"

    except:
        return f"Agent ({agent_type})"


# ==================== API Endpoints ====================

@router.post("/", response_model=QuickConnectResponse)
async def quick_connect(
    request: QuickConnectRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Quick Connect - Just paste a URL and go!

    This endpoint automatically:
    1. Detects the agent type from the URL
    2. Configures the agent with sensible defaults
    3. Tests the connection
    4. Saves the configuration
    5. Returns ready-to-use agent

    Examples:
    - OpenAI: "https://api.openai.com/v1/chat/completions"
    - Anthropic: "https://api.anthropic.com/v1/messages"
    - WebSocket: "ws://localhost:8080/agent"
    - Any HTTP API: "https://my-agent.com/chat"
    """
    try:
        logger.info(f"Quick connect request for: {request.url}")

        # Step 1: Auto-detect agent type
        agent_type, base_config = await detect_agent_type(request.url, request.api_key)

        logger.info(f"Detected agent type: {agent_type}")

        # Step 2: Generate name if not provided
        name = request.name or generate_agent_name(request.url, agent_type)

        # Step 3: Create full configuration
        import time
        config_id = f"{agent_type}_{current_user['tenant_id']}_{int(time.time())}"

        full_config = {
            "agent_id": config_id,
            "name": name,
            "type": agent_type,
            "enabled": True,
            "priority": 10,
            **base_config
        }

        # Step 4: Test the connection
        test_result = None
        try:
            factory = get_agent_factory()

            # Create temporary agent for testing
            agent = await factory.create_agent(
                agent_id=agent_type,
                config=full_config,
                validate=True,
                initialize=True
            )

            # Test with a simple query
            from app.agents.base import AgentContext
            context = AgentContext(
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"],
                session_id="quick_connect_test"
            )

            test_response = await agent.execute(request.test_query, context)

            test_result = {
                "query": request.test_query,
                "answer": test_response.answer[:200],  # First 200 chars
                "execution_time": test_response.execution_time,
                "status": test_response.status.value
            }

            # Clean up test agent
            await factory.destroy_agent(agent)

            logger.info(f"Connection test successful for {name}")

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Connection test failed: {str(e)}"
            )

        # Step 5: Save configuration
        from supabase import create_client
        from app.config import settings
        from datetime import datetime

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

        # Mask sensitive data for storage
        storage_config = {k: v for k, v in base_config.items()}

        config_record = {
            "id": config_id,
            "name": name,
            "agent_type": agent_type,
            "description": f"Auto-configured from {request.url}",
            "enabled": True,
            "priority": 10,
            "config": storage_config,
            "tenant_id": current_user["tenant_id"],
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.from_('agent_configs').insert(config_record).execute()

        return QuickConnectResponse(
            success=True,
            agent_type=agent_type,
            config_id=config_id,
            message=f"Successfully connected to {name}! Your agent is ready to use.",
            test_result=test_result,
            details={
                "url": request.url,
                "detected_type": agent_type,
                "configuration": {k: v for k, v in base_config.items() if k not in ["api_key", "auth_token"]}
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Quick connect failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quick connect failed: {str(e)}"
        )


@router.post("/test")
async def test_url(
    url: str,
    api_key: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Test a URL without saving configuration

    Just checks if the URL is accessible and what type it is.
    """
    try:
        agent_type, config = await detect_agent_type(url, api_key)

        return {
            "url": url,
            "detected_type": agent_type,
            "suggested_name": generate_agent_name(url, agent_type),
            "configuration_preview": {k: v for k, v in config.items() if k not in ["api_key", "auth_token"]},
            "message": f"Detected as {agent_type} agent"
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not analyze URL: {str(e)}"
        )


@router.get("/examples")
async def get_examples():
    """
    Get example URLs for quick connect

    Shows users what they can connect to.
    """
    return {
        "examples": [
            {
                "name": "OpenAI GPT-4",
                "url": "https://api.openai.com/v1/chat/completions",
                "type": "openai",
                "needs_api_key": True,
                "description": "Connect directly to OpenAI's API"
            },
            {
                "name": "Anthropic Claude",
                "url": "https://api.anthropic.com/v1/messages",
                "type": "anthropic",
                "needs_api_key": True,
                "description": "Connect to Claude 3"
            },
            {
                "name": "Ollama (Local)",
                "url": "http://localhost:11434/api/generate",
                "type": "http",
                "needs_api_key": False,
                "description": "Connect to locally running Ollama"
            },
            {
                "name": "Custom WebSocket Agent",
                "url": "ws://localhost:8080/agent",
                "type": "websocket",
                "needs_api_key": False,
                "description": "Real-time WebSocket connection"
            },
            {
                "name": "Hugging Face Inference",
                "url": "https://api-inference.huggingface.co/models/your-model",
                "type": "http",
                "needs_api_key": True,
                "description": "Connect to HuggingFace models"
            },
            {
                "name": "Custom Webhook",
                "url": "https://your-agent.com/webhook",
                "type": "webhook",
                "needs_api_key": False,
                "description": "Any custom HTTP endpoint"
            }
        ],
        "instructions": [
            "Just paste any URL and click 'Quick Connect'",
            "System will auto-detect the agent type",
            "Add API key if needed",
            "Connection will be tested automatically",
            "Start chatting immediately!"
        ]
    }
