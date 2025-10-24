"""
Base Model Provider Interface

Defines the abstract interface that all model providers must implement.
Provides unified API for interacting with different LLM providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    MISTRAL = "mistral"
    OLLAMA = "ollama"
    AZURE = "azure"
    BEDROCK = "bedrock"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


class ModelCapability(str, Enum):
    """Model capabilities"""
    TEXT_GENERATION = "text_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    SYSTEM_MESSAGES = "system_messages"
    EMBEDDINGS = "embeddings"


@dataclass
class ModelCapabilities:
    """Model capabilities and limitations"""
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    supports_system_messages: bool = True
    max_context_length: int = 4096
    max_output_tokens: int = 2048
    supports_temperature: bool = True
    supports_top_p: bool = True
    supports_stop_sequences: bool = True
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0


@dataclass
class FunctionCall:
    """Function call from model"""
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class ToolCall:
    """Tool call from model (OpenAI format)"""
    id: str
    type: str
    function: FunctionCall


@dataclass
class StreamChunk:
    """Streaming response chunk"""
    content: str
    finish_reason: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    tool_calls: Optional[List[ToolCall]] = None


@dataclass
class ModelResponse:
    """Unified model response"""
    content: str
    model: str
    provider: ModelProvider
    finish_reason: str
    usage: Dict[str, int]
    function_call: Optional[FunctionCall] = None
    tool_calls: Optional[List[ToolCall]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    latency_ms: Optional[float] = None
    cost: Optional[float] = None


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class ModelConfig:
    """Model configuration"""
    provider: ModelProvider
    model_name: str
    api_key: str
    api_base: Optional[str] = None
    organization_id: Optional[str] = None
    
    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    
    # Advanced options
    timeout: int = 120
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    fallback_models: List[str] = field(default_factory=list)
    
    # Provider-specific options
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.api_key and self.provider != ModelProvider.OLLAMA:
            raise ValueError(f"API key required for {self.provider}")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be positive")


class BaseModelProvider(ABC):
    """
    Abstract base class for model providers
    
    All model providers must implement this interface to ensure
    consistent behavior across different LLM providers.
    """
    
    def __init__(self, config: ModelConfig):
        """
        Initialize model provider
        
        Args:
            config: Model configuration
        """
        self.config = config
        self.provider = config.provider
        self.model_name = config.model_name
        
        logger.info(
            f"Initialized {self.provider} provider with model {self.model_name}"
        )
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> ModelResponse:
        """
        Generate completion from messages
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional generation parameters
            
        Returns:
            ModelResponse with generated content
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate streaming completion from messages
        
        Args:
