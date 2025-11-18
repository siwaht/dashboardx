"""
Agent Configuration Management API

Provides endpoints for managing agent configurations, connections,
and settings in the enterprise RAG frontend.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from app.agents.registry import AgentRegistry
from app.agents.factory import get_agent_factory
from app.agents.base import AgentCapabilities

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================

class AgentConfigCreate(BaseModel):
    """Request model for creating agent configuration"""
    name: str = Field(..., description="Human-readable name for this agent")
    agent_type: str = Field(..., description="Type of agent (openai, anthropic, langchain, etc.)")
    description: Optional[str] = Field(None, description="Description of this agent")
    enabled: bool = Field(True, description="Whether this agent is enabled")
    priority: int = Field(999, description="Priority for agent selection (lower = higher priority)")
    config: Dict[str, Any] = Field(..., description="Agent-specific configuration")


class AgentConfigUpdate(BaseModel):
    """Request model for updating agent configuration"""
    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Description")
    enabled: Optional[bool] = Field(None, description="Whether enabled")
    priority: Optional[int] = Field(None, description="Priority")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration updates")


class AgentConfigResponse(BaseModel):
    """Response model for agent configuration"""
    id: str = Field(..., description="Configuration ID")
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    description: Optional[str] = Field(None, description="Description")
    enabled: bool = Field(..., description="Enabled status")
    priority: int = Field(..., description="Priority")
    config: Dict[str, Any] = Field(..., description="Configuration (with secrets masked)")
    tenant_id: str = Field(..., description="Tenant ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="Agent capabilities")
    health_status: Optional[str] = Field(None, description="Current health status")


class AgentTypeInfo(BaseModel):
    """Information about available agent types"""
    id: str = Field(..., description="Agent type ID")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Description")
    config_schema: Dict[str, Any] = Field(..., description="JSON schema for configuration")
    example_config: Dict[str, Any] = Field(..., description="Example configuration")


class HealthCheckResponse(BaseModel):
    """Response for agent health check"""
    config_id: str
    healthy: bool
    message: str
    details: Dict[str, Any]
    checked_at: datetime


# ==================== Helper Functions ====================

def mask_secrets(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive fields in configuration

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with secrets masked
    """
    masked = config.copy()
    secret_fields = ['api_key', 'auth_token', 'password', 'secret', 'key']

    for field in secret_fields:
        if field in masked and masked[field]:
            # Show first 4 and last 4 characters
            value = str(masked[field])
            if len(value) > 8:
                masked[field] = f"{value[:4]}...{value[-4:]}"
            else:
                masked[field] = "***"

    return masked


# ==================== API Endpoints ====================

@router.get("/types", response_model=List[AgentTypeInfo])
async def list_agent_types(
    current_user: dict = Depends(get_current_user)
):
    """
    List all available agent types

    Returns information about each agent adapter type including
    configuration schema and examples.
    """
    try:
        agent_types = []

        # Get all registered agent types
        for agent_id in AgentRegistry.list_agents():
            agent_class = AgentRegistry.get(agent_id)
            metadata = AgentRegistry.get_metadata(agent_id)

            if not agent_class:
                continue

            # Build configuration schema
            schema = get_agent_config_schema(agent_id)

            agent_types.append(AgentTypeInfo(
                id=agent_id,
                name=metadata.get("name", agent_id),
                description=metadata.get("description", ""),
                config_schema=schema,
                example_config=get_example_config(agent_id)
            ))

        return agent_types

    except Exception as e:
        logger.error(f"Error listing agent types: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agent types: {str(e)}"
        )


@router.post("/", response_model=AgentConfigResponse)
async def create_agent_config(
    config_data: AgentConfigCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new agent configuration

    Validates the configuration and stores it for the current tenant.
    """
    try:
        # Verify agent type exists
        if not AgentRegistry.exists(config_data.agent_type):
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {config_data.agent_type}"
            )

        # Generate config ID
        config_id = f"{config_data.agent_type}_{current_user['tenant_id']}_{int(datetime.utcnow().timestamp())}"

        # Prepare full configuration
        full_config = {
            "agent_id": config_id,
            "name": config_data.name,
            "type": config_data.agent_type,
            "enabled": config_data.enabled,
            "priority": config_data.priority,
            **config_data.config
        }

        # Validate by trying to create agent
        factory = get_agent_factory()
        try:
            agent = await factory.create_agent(
                agent_id=config_data.agent_type,
                config=full_config,
                validate=True,
                initialize=False
            )
            await factory.destroy_agent(agent)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration: {str(e)}"
            )

        # Store configuration in database
        # TODO: Implement database storage
        # For now, just store in MongoDB or Supabase

        from supabase import create_client
        from app.config import settings

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

        config_record = {
            "id": config_id,
            "name": config_data.name,
            "agent_type": config_data.agent_type,
            "description": config_data.description,
            "enabled": config_data.enabled,
            "priority": config_data.priority,
            "config": config_data.config,
            "tenant_id": current_user["tenant_id"],
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Insert into database
        # Note: You'll need to create the 'agent_configs' table in Supabase
        result = supabase.from_('agent_configs').insert(config_record).execute()

        # Return response with masked secrets
        return AgentConfigResponse(
            id=config_id,
            name=config_data.name,
            agent_type=config_data.agent_type,
            description=config_data.description,
            enabled=config_data.enabled,
            priority=config_data.priority,
            config=mask_secrets(config_data.config),
            tenant_id=current_user["tenant_id"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent config: {str(e)}"
        )


@router.get("/", response_model=List[AgentConfigResponse])
async def list_agent_configs(
    enabled_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    List all agent configurations for the current tenant
    """
    try:
        from supabase import create_client
        from app.config import settings

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

        # Query configurations
        query = supabase.from_('agent_configs').select('*').eq(
            'tenant_id', current_user['tenant_id']
        ).order('priority')

        if enabled_only:
            query = query.eq('enabled', True)

        result = query.execute()

        configs = []
        for record in result.data:
            configs.append(AgentConfigResponse(
                id=record['id'],
                name=record['name'],
                agent_type=record['agent_type'],
                description=record.get('description'),
                enabled=record['enabled'],
                priority=record['priority'],
                config=mask_secrets(record['config']),
                tenant_id=record['tenant_id'],
                created_at=datetime.fromisoformat(record['created_at']),
                updated_at=datetime.fromisoformat(record['updated_at'])
            ))

        return configs

    except Exception as e:
        logger.error(f"Error listing agent configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agent configs: {str(e)}"
        )


@router.get("/{config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific agent configuration
    """
    try:
        from supabase import create_client
        from app.config import settings

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

        result = supabase.from_('agent_configs').select('*').eq(
            'id', config_id
        ).eq(
            'tenant_id', current_user['tenant_id']
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Agent configuration not found")

        record = result.data[0]

        return AgentConfigResponse(
            id=record['id'],
            name=record['name'],
            agent_type=record['agent_type'],
            description=record.get('description'),
            enabled=record['enabled'],
            priority=record['priority'],
            config=mask_secrets(record['config']),
            tenant_id=record['tenant_id'],
            created_at=datetime.fromisoformat(record['created_at']),
            updated_at=datetime.fromisoformat(record['updated_at'])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent config: {str(e)}"
        )


@router.put("/{config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    config_id: str,
    updates: AgentConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an agent configuration
    """
    try:
        from supabase import create_client
        from app.config import settings

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

        # Get existing config
        result = supabase.from_('agent_configs').select('*').eq(
            'id', config_id
        ).eq(
            'tenant_id', current_user['tenant_id']
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Agent configuration not found")

        existing = result.data[0]

        # Prepare updates
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if updates.name is not None:
            update_data["name"] = updates.name
        if updates.description is not None:
            update_data["description"] = updates.description
        if updates.enabled is not None:
            update_data["enabled"] = updates.enabled
        if updates.priority is not None:
            update_data["priority"] = updates.priority
        if updates.config is not None:
            # Merge with existing config
            merged_config = {**existing['config'], **updates.config}
            update_data["config"] = merged_config

        # Update in database
        result = supabase.from_('agent_configs').update(update_data).eq(
            'id', config_id
        ).execute()

        updated = result.data[0]

        return AgentConfigResponse(
            id=updated['id'],
            name=updated['name'],
            agent_type=updated['agent_type'],
            description=updated.get('description'),
            enabled=updated['enabled'],
            priority=updated['priority'],
            config=mask_secrets(updated['config']),
            tenant_id=updated['tenant_id'],
            created_at=datetime.fromisoformat(updated['created_at']),
            updated_at=datetime.fromisoformat(updated['updated_at'])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent config: {str(e)}"
        )


@router.delete("/{config_id}")
async def delete_agent_config(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an agent configuration
    """
    try:
        from supabase import create_client
        from app.config import settings

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

        # Delete from database
        result = supabase.from_('agent_configs').delete().eq(
            'id', config_id
        ).eq(
            'tenant_id', current_user['tenant_id']
        ).execute()

        return {
            "status": "success",
            "message": "Agent configuration deleted",
            "config_id": config_id
        }

    except Exception as e:
        logger.error(f"Error deleting agent config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete agent config: {str(e)}"
        )


@router.post("/{config_id}/test", response_model=HealthCheckResponse)
async def test_agent_config(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Test an agent configuration by performing a health check
    """
    try:
        from supabase import create_client
        from app.config import settings

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

        # Get configuration
        result = supabase.from_('agent_configs').select('*').eq(
            'id', config_id
        ).eq(
            'tenant_id', current_user['tenant_id']
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Agent configuration not found")

        record = result.data[0]

        # Create agent and test
        factory = get_agent_factory()
        full_config = {
            "agent_id": config_id,
            "name": record['name'],
            "type": record['agent_type'],
            **record['config']
        }

        agent = await factory.create_agent(
            agent_id=record['agent_type'],
            config=full_config
        )

        # Perform health check
        health = await agent.health_check()

        # Clean up
        await factory.destroy_agent(agent)

        return HealthCheckResponse(
            config_id=config_id,
            healthy=health.healthy,
            message=health.message or "Health check completed",
            details=health.details,
            checked_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing agent config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test agent config: {str(e)}"
        )


# ==================== Helper Functions ====================

def get_agent_config_schema(agent_id: str) -> Dict[str, Any]:
    """
    Get JSON schema for agent configuration

    Args:
        agent_id: Agent type ID

    Returns:
        JSON schema dictionary
    """
    # Define schemas for each agent type
    schemas = {
        "openai": {
            "type": "object",
            "required": ["api_key", "model"],
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "OpenAI API key"
                },
                "model": {
                    "type": "string",
                    "description": "Model name (e.g., gpt-4-turbo-preview)",
                    "enum": ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]
                },
                "temperature": {
                    "type": "number",
                    "description": "Temperature (0-2)",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 0.7
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens in response",
                    "default": 4096
                }
            }
        },
        "anthropic": {
            "type": "object",
            "required": ["api_key", "model"],
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Anthropic API key"
                },
                "model": {
                    "type": "string",
                    "description": "Claude model name",
                    "enum": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
                },
                "temperature": {
                    "type": "number",
                    "description": "Temperature (0-1)",
                    "minimum": 0,
                    "maximum": 1,
                    "default": 1.0
                }
            }
        },
        "http": {
            "type": "object",
            "required": ["endpoint_url"],
            "properties": {
                "endpoint_url": {
                    "type": "string",
                    "description": "API endpoint URL"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method",
                    "enum": ["GET", "POST", "PUT"],
                    "default": "POST"
                },
                "auth_type": {
                    "type": "string",
                    "description": "Authentication type",
                    "enum": ["bearer", "api_key", "basic", null]
                },
                "auth_token": {
                    "type": "string",
                    "description": "Authentication token"
                },
                "request_template": {
                    "type": "object",
                    "description": "Request body template"
                },
                "response_path": {
                    "type": "string",
                    "description": "JSON path to extract answer",
                    "default": "response"
                }
            }
        }
    }

    return schemas.get(agent_id, {
        "type": "object",
        "properties": {}
    })


def get_example_config(agent_id: str) -> Dict[str, Any]:
    """
    Get example configuration for agent type

    Args:
        agent_id: Agent type ID

    Returns:
        Example configuration dictionary
    """
    examples = {
        "openai": {
            "api_key": "sk-...",
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 4096
        },
        "anthropic": {
            "api_key": "sk-ant-...",
            "model": "claude-3-opus-20240229",
            "temperature": 1.0
        },
        "http": {
            "endpoint_url": "https://api.example.com/chat",
            "method": "POST",
            "auth_type": "bearer",
            "auth_token": "your-token",
            "request_template": {
                "model": "llama-70b",
                "messages": "{{messages}}",
                "temperature": "{{temperature}}"
            },
            "response_path": "choices.0.message.content"
        }
    }

    return examples.get(agent_id, {})
