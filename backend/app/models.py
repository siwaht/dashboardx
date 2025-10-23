"""
Shared Data Models

Defines Pydantic models used across the application for type safety
and data validation.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class User(BaseModel):
    """
    User model compatible with AuthenticatedUser
    Used for API responses and internal operations
    """
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    role: str = Field(default="user", description="User role (admin, user, viewer)")
    tenant_id: str = Field(..., description="Tenant ID for multi-tenancy")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "role": "user",
                "tenant_id": "tenant-123",
                "full_name": "John Doe",
                "is_active": True
            }
        }


class Document(BaseModel):
    """Document model for RAG system"""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: Optional[str] = Field(None, description="Document content")
    file_path: Optional[str] = Field(None, description="File storage path")
    file_type: str = Field(..., description="File type (pdf, docx, txt, etc.)")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    status: str = Field(default="pending", description="Processing status")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="Owner user ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    
    class Config:
        from_attributes = True


class ChatSession(BaseModel):
    """Chat session model"""
    id: str = Field(..., description="Session ID")
    title: str = Field(..., description="Session title")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages")
    
    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Chat message model"""
    id: str = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session ID")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        from_attributes = True


class DataSource(BaseModel):
    """Data source model for analytics"""
    id: str = Field(..., description="Data source ID")
    name: str = Field(..., description="Data source name")
    type: str = Field(..., description="Data source type (postgres, mysql, s3, etc.)")
    config: Dict[str, Any] = Field(..., description="Connection configuration")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="Creator user ID")
    is_active: bool = Field(default=True, description="Whether data source is active")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        from_attributes = True


class AnalyticsQuery(BaseModel):
    """Analytics query model"""
    id: str = Field(..., description="Query ID")
    query: str = Field(..., description="Query text")
    query_type: str = Field(..., description="Query type (natural_language, sql)")
    data_source_id: Optional[str] = Field(None, description="Data source ID")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    result: Optional[Dict[str, Any]] = Field(None, description="Query result")
    status: str = Field(default="pending", description="Query status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        from_attributes = True


class Insight(BaseModel):
    """Insight model for analytics"""
    id: str = Field(..., description="Insight ID")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    insight_type: str = Field(..., description="Insight type (trend, anomaly, correlation)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    data: Optional[Dict[str, Any]] = Field(None, description="Supporting data")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        from_attributes = True


class AgentExecution(BaseModel):
    """Agent execution model"""
    id: str = Field(..., description="Execution ID")
    agent_type: str = Field(..., description="Agent type")
    input_data: Dict[str, Any] = Field(..., description="Input data")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data")
    status: str = Field(default="running", description="Execution status")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        from_attributes = True


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = Field(..., description="Whether request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"key": "value"},
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "has_next": True,
                "has_prev": False
            }
        }


# Export all models
__all__ = [
    "User",
    "Document",
    "ChatSession",
    "ChatMessage",
    "DataSource",
    "AnalyticsQuery",
    "Insight",
    "AgentExecution",
    "APIResponse",
    "PaginatedResponse",
]
