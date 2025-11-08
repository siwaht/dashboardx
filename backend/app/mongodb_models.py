"""
MongoDB Models and Schemas

Defines MongoDB document schemas and CRUD operations for the dashboardx collection.
Provides type-safe interfaces for MongoDB operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class MongoBaseModel(BaseModel):
    """Base model for MongoDB documents"""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


# ==================== User Management ====================

class MongoUser(MongoBaseModel):
    """MongoDB User document"""
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    tenant_id: str
    is_active: bool = True
    password_hash: Optional[str] = None
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoUserCreate(BaseModel):
    """Schema for creating a new user"""
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    tenant_id: str
    password: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoUserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


# ==================== Document Management ====================

class MongoDocument(MongoBaseModel):
    """MongoDB Document for RAG system"""
    title: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    file_type: str
    file_size: Optional[int] = None
    status: str = "pending"
    tenant_id: str
    user_id: str
    embeddings: Optional[List[float]] = None
    chunks: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processed_at: Optional[datetime] = None


class MongoDocumentCreate(BaseModel):
    """Schema for creating a new document"""
    title: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    file_type: str
    file_size: Optional[int] = None
    tenant_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoDocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    embeddings: Optional[List[float]] = None
    chunks: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None


# ==================== Chat Management ====================

class MongoChatMessage(BaseModel):
    """Single chat message"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoChatSession(MongoBaseModel):
    """MongoDB Chat Session"""
    title: str
    tenant_id: str
    user_id: str
    messages: List[MongoChatMessage] = Field(default_factory=list)
    message_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    title: str
    tenant_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoChatMessageCreate(BaseModel):
    """Schema for adding a message to a chat session"""
    session_id: str
    role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==================== Agent Management ====================

class MongoAgent(MongoBaseModel):
    """MongoDB Custom Agent"""
    name: str
    description: Optional[str] = None
    agent_type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str
    user_id: str
    is_active: bool = True
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoAgentCreate(BaseModel):
    """Schema for creating a new agent"""
    name: str
    description: Optional[str] = None
    agent_type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoAgentExecution(MongoBaseModel):
    """MongoDB Agent Execution Log"""
    agent_id: str
    agent_type: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: str = "running"  # running, completed, failed
    tenant_id: str
    user_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoAgentExecutionCreate(BaseModel):
    """Schema for creating an agent execution"""
    agent_id: str
    agent_type: str
    input_data: Dict[str, Any]
    tenant_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==================== Data Source Management ====================

class MongoDataSource(MongoBaseModel):
    """MongoDB Data Source for external integrations"""
    name: str
    type: str  # s3, google_drive, sharepoint, confluence, etc.
    config: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str
    user_id: str
    is_active: bool = True
    last_sync: Optional[datetime] = None
    sync_status: str = "idle"  # idle, syncing, error
    sync_error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoDataSourceCreate(BaseModel):
    """Schema for creating a new data source"""
    name: str
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==================== Analytics ====================

class MongoAnalyticsEvent(MongoBaseModel):
    """MongoDB Analytics Event"""
    event_type: str
    event_name: str
    tenant_id: str
    user_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MongoAnalyticsEventCreate(BaseModel):
    """Schema for creating an analytics event"""
    event_type: str
    event_name: str
    tenant_id: str
    user_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


# ==================== Feedback ====================

class MongoFeedback(MongoBaseModel):
    """MongoDB Feedback"""
    tenant_id: str
    user_id: str
    item_type: str  # message, agent, document, etc.
    item_id: str
    rating: int  # 1-5 stars
    comment: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoFeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    tenant_id: str
    user_id: str
    item_type: str
    item_id: str
    rating: int
    comment: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==================== API Keys ====================

class MongoAPIKey(MongoBaseModel):
    """MongoDB API Key"""
    name: str
    key_hash: str
    tenant_id: str
    user_id: str
    is_active: bool = True
    permissions: List[str] = Field(default_factory=list)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MongoAPIKeyCreate(BaseModel):
    """Schema for creating an API key"""
    name: str
    tenant_id: str
    user_id: str
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Export all models
__all__ = [
    "PyObjectId",
    "MongoBaseModel",
    "MongoUser",
    "MongoUserCreate",
    "MongoUserUpdate",
    "MongoDocument",
    "MongoDocumentCreate",
    "MongoDocumentUpdate",
    "MongoChatSession",
    "MongoChatSessionCreate",
    "MongoChatMessage",
    "MongoChatMessageCreate",
    "MongoAgent",
    "MongoAgentCreate",
    "MongoAgentExecution",
    "MongoAgentExecutionCreate",
    "MongoDataSource",
    "MongoDataSourceCreate",
    "MongoAnalyticsEvent",
    "MongoAnalyticsEventCreate",
    "MongoFeedback",
    "MongoFeedbackCreate",
    "MongoAPIKey",
    "MongoAPIKeyCreate",
]
