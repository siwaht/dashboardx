"""
Universal Model Connectivity System

Provides a unified interface for connecting to multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Google (Gemini)
- Cohere (Command)
- Mistral (Mistral Large/Medium/Small)
- Ollama (Local models)
- Azure OpenAI
- AWS Bedrock
- Custom OpenAI-compatible APIs

Features:
- Intelligent model routing
- Cost optimization
- Automatic failover
- Load balancing
- Unified API
"""

from app.models.base import (
    BaseModelProvider,
    ModelConfig,
    ModelResponse,
    ModelCapabilities,
    StreamChunk,
    FunctionCall,
    ToolCall,
)
from app.models.registry import ModelRegistry, get_registry
from app.models.router import ModelRouter, get_router

__all__ = [
    "BaseModelProvider",
    "ModelConfig",
    "ModelResponse",
    "ModelCapabilities",
    "StreamChunk",
    "FunctionCall",
    "ToolCall",
    "ModelRegistry",
    "get_registry",
    "ModelRouter",
    "get_router",
]
