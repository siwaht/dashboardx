"""
Configuration Management

Loads and validates environment variables using Pydantic Settings.
Provides type-safe access to all configuration values.
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ==================== Supabase ====================
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    supabase_jwt_secret: str = Field(..., env="SUPABASE_JWT_SECRET")
    supabase_db_connection: str = Field(..., env="SUPABASE_DB_CONNECTION")

    # ==================== OpenAI ====================
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_organization_id: Optional[str] = Field(None, env="OPENAI_ORGANIZATION_ID")
    openai_embedding_model: str = Field(
        "text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL"
    )
    openai_chat_model: str = Field("gpt-4-turbo-preview", env="OPENAI_CHAT_MODEL")
    openai_temperature: float = Field(0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(2000, env="OPENAI_MAX_TOKENS")

    # ==================== Anthropic (Optional) ====================
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-opus-20240229", env="ANTHROPIC_MODEL")

    # ==================== LangSmith (Optional) ====================
    langchain_tracing_v2: bool = Field(False, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(None, env="LANGCHAIN_API_KEY")
    langchain_project: str = Field("agentic-rag-platform", env="LANGCHAIN_PROJECT")
    langchain_endpoint: str = Field(
        "https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT"
    )

    # ==================== CopilotKit ====================
    copilotkit_api_key: Optional[str] = Field(None, env="COPILOTKIT_API_KEY")

    # ==================== Server Configuration ====================
    backend_host: str = Field("0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(8000, env="BACKEND_PORT")
    backend_reload: bool = Field(True, env="BACKEND_RELOAD")
    backend_workers: int = Field(1, env="BACKEND_WORKERS")
    backend_cors_origins: List[str] = Field(
        ["http://localhost:5173", "http://localhost:3000"],
        env="BACKEND_CORS_ORIGINS",
    )

    @validator("backend_cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    # ==================== RAG Configuration ====================
    chunk_size: int = Field(512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(50, env="CHUNK_OVERLAP")
    chunking_strategy: str = Field("recursive", env="CHUNKING_STRATEGY")
    
    top_k_documents: int = Field(5, env="TOP_K_DOCUMENTS")
    similarity_threshold: float = Field(0.7, env="SIMILARITY_THRESHOLD")
    enable_reranking: bool = Field(True, env="ENABLE_RERANKING")
    reranking_model: str = Field(
        "cross-encoder/ms-marco-MiniLM-L-6-v2", env="RERANKING_MODEL"
    )
    
    embedding_batch_size: int = Field(100, env="EMBEDDING_BATCH_SIZE")
    embedding_dimensions: int = Field(1536, env="EMBEDDING_DIMENSIONS")

    # ==================== Agent Configuration ====================
    agent_max_iterations: int = Field(10, env="AGENT_MAX_ITERATIONS")
    agent_timeout_seconds: int = Field(120, env="AGENT_TIMEOUT_SECONDS")
    enable_query_rewrite: bool = Field(True, env="ENABLE_QUERY_REWRITE")
    enable_hyde: bool = Field(False, env="ENABLE_HYDE")

    # ==================== Security ====================
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(60, env="JWT_EXPIRATION_MINUTES")
    
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(1000, env="RATE_LIMIT_PER_HOUR")

    # ==================== Data Connectors ====================
    # AWS S3
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    aws_s3_bucket: Optional[str] = Field(None, env="AWS_S3_BUCKET")

    # Google Drive
    google_client_id: Optional[str] = Field(None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(None, env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = Field(None, env="GOOGLE_REDIRECT_URI")

    # SharePoint
    sharepoint_site_url: Optional[str] = Field(None, env="SHAREPOINT_SITE_URL")
    sharepoint_client_id: Optional[str] = Field(None, env="SHAREPOINT_CLIENT_ID")
    sharepoint_client_secret: Optional[str] = Field(None, env="SHAREPOINT_CLIENT_SECRET")

    # Confluence
    confluence_url: Optional[str] = Field(None, env="CONFLUENCE_URL")
    confluence_username: Optional[str] = Field(None, env="CONFLUENCE_USERNAME")
    confluence_api_token: Optional[str] = Field(None, env="CONFLUENCE_API_TOKEN")

    # ==================== Monitoring & Logging ====================
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    sentry_environment: str = Field("development", env="SENTRY_ENVIRONMENT")
    sentry_traces_sample_rate: float = Field(1.0, env="SENTRY_TRACES_SAMPLE_RATE")
    
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")

    # ==================== Feature Flags ====================
    enable_streaming: bool = Field(True, env="ENABLE_STREAMING")
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    enable_audit_logging: bool = Field(True, env="ENABLE_AUDIT_LOGGING")
    enable_performance_monitoring: bool = Field(True, env="ENABLE_PERFORMANCE_MONITORING")

    # ==================== Cache Configuration ====================
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    cache_ttl_seconds: int = Field(3600, env="CACHE_TTL_SECONDS")

    # ==================== Development ====================
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
