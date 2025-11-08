"""
MongoDB Service Layer

Provides high-level CRUD operations for MongoDB collections.
Handles data validation, transformation, and error handling.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError
import logging

from .mongodb import get_mongodb, get_dashboardx_collection
from .mongodb_models import (
    MongoUser,
    MongoUserCreate,
    MongoUserUpdate,
    MongoDocument,
    MongoDocumentCreate,
    MongoDocumentUpdate,
    MongoChatSession,
    MongoChatSessionCreate,
    MongoChatMessage,
    MongoChatMessageCreate,
    MongoAgent,
    MongoAgentCreate,
    MongoAgentExecution,
    MongoAgentExecutionCreate,
    MongoDataSource,
    MongoDataSourceCreate,
    MongoAnalyticsEvent,
    MongoAnalyticsEventCreate,
    MongoFeedback,
    MongoFeedbackCreate,
    MongoAPIKey,
    MongoAPIKeyCreate,
)

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service class for MongoDB operations"""

    # ==================== User Operations ====================

    @staticmethod
    async def create_user(user_data: MongoUserCreate) -> MongoUser:
        """Create a new user"""
        try:
            collection = await get_dashboardx_collection()
            user_dict = user_data.model_dump()
            user_dict["type"] = "user"
            user_dict["created_at"] = datetime.utcnow()
            user_dict["updated_at"] = datetime.utcnow()

            result = await collection.insert_one(user_dict)
            user_dict["_id"] = result.inserted_id

            return MongoUser(**user_dict)
        except DuplicateKeyError:
            raise ValueError(f"User with email {user_data.email} already exists")
        except PyMongoError as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[MongoUser]:
        """Get user by ID"""
        try:
            collection = await get_dashboardx_collection()
            user_dict = await collection.find_one({
                "_id": ObjectId(user_id),
                "type": "user"
            })

            return MongoUser(**user_dict) if user_dict else None
        except PyMongoError as e:
            logger.error(f"Error getting user: {str(e)}")
            raise

    @staticmethod
    async def get_user_by_email(email: str, tenant_id: str) -> Optional[MongoUser]:
        """Get user by email and tenant"""
        try:
            collection = await get_dashboardx_collection()
            user_dict = await collection.find_one({
                "email": email,
                "tenant_id": tenant_id,
                "type": "user"
            })

            return MongoUser(**user_dict) if user_dict else None
        except PyMongoError as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise

    @staticmethod
    async def update_user(user_id: str, user_data: MongoUserUpdate) -> Optional[MongoUser]:
        """Update user"""
        try:
            collection = await get_dashboardx_collection()
            update_dict = {k: v for k, v in user_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()

            result = await collection.find_one_and_update(
                {"_id": ObjectId(user_id), "type": "user"},
                {"$set": update_dict},
                return_document=True
            )

            return MongoUser(**result) if result else None
        except PyMongoError as e:
            logger.error(f"Error updating user: {str(e)}")
            raise

    # ==================== Document Operations ====================

    @staticmethod
    async def create_document(doc_data: MongoDocumentCreate) -> MongoDocument:
        """Create a new document"""
        try:
            collection = await get_dashboardx_collection()
            doc_dict = doc_data.model_dump()
            doc_dict["type"] = "document"
            doc_dict["created_at"] = datetime.utcnow()
            doc_dict["updated_at"] = datetime.utcnow()

            result = await collection.insert_one(doc_dict)
            doc_dict["_id"] = result.inserted_id

            return MongoDocument(**doc_dict)
        except PyMongoError as e:
            logger.error(f"Error creating document: {str(e)}")
            raise

    @staticmethod
    async def get_document_by_id(doc_id: str) -> Optional[MongoDocument]:
        """Get document by ID"""
        try:
            collection = await get_dashboardx_collection()
            doc_dict = await collection.find_one({
                "_id": ObjectId(doc_id),
                "type": "document"
            })

            return MongoDocument(**doc_dict) if doc_dict else None
        except PyMongoError as e:
            logger.error(f"Error getting document: {str(e)}")
            raise

    @staticmethod
    async def list_documents(tenant_id: str, user_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[MongoDocument]:
        """List documents for a tenant"""
        try:
            collection = await get_dashboardx_collection()
            query = {"type": "document", "tenant_id": tenant_id}
            if user_id:
                query["user_id"] = user_id

            cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)

            return [MongoDocument(**doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise

    @staticmethod
    async def update_document(doc_id: str, doc_data: MongoDocumentUpdate) -> Optional[MongoDocument]:
        """Update document"""
        try:
            collection = await get_dashboardx_collection()
            update_dict = {k: v for k, v in doc_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()

            result = await collection.find_one_and_update(
                {"_id": ObjectId(doc_id), "type": "document"},
                {"$set": update_dict},
                return_document=True
            )

            return MongoDocument(**result) if result else None
        except PyMongoError as e:
            logger.error(f"Error updating document: {str(e)}")
            raise

    @staticmethod
    async def delete_document(doc_id: str) -> bool:
        """Delete document"""
        try:
            collection = await get_dashboardx_collection()
            result = await collection.delete_one({
                "_id": ObjectId(doc_id),
                "type": "document"
            })
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    # ==================== Chat Operations ====================

    @staticmethod
    async def create_chat_session(session_data: MongoChatSessionCreate) -> MongoChatSession:
        """Create a new chat session"""
        try:
            collection = await get_dashboardx_collection()
            session_dict = session_data.model_dump()
            session_dict["type"] = "chat_session"
            session_dict["created_at"] = datetime.utcnow()
            session_dict["updated_at"] = datetime.utcnow()
            session_dict["messages"] = []
            session_dict["message_count"] = 0

            result = await collection.insert_one(session_dict)
            session_dict["_id"] = result.inserted_id

            return MongoChatSession(**session_dict)
        except PyMongoError as e:
            logger.error(f"Error creating chat session: {str(e)}")
            raise

    @staticmethod
    async def add_message_to_session(message_data: MongoChatMessageCreate) -> Optional[MongoChatSession]:
        """Add a message to a chat session"""
        try:
            collection = await get_dashboardx_collection()
            message = MongoChatMessage(
                role=message_data.role,
                content=message_data.content,
                metadata=message_data.metadata
            )

            result = await collection.find_one_and_update(
                {"_id": ObjectId(message_data.session_id), "type": "chat_session"},
                {
                    "$push": {"messages": message.model_dump()},
                    "$inc": {"message_count": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                return_document=True
            )

            return MongoChatSession(**result) if result else None
        except PyMongoError as e:
            logger.error(f"Error adding message to session: {str(e)}")
            raise

    @staticmethod
    async def get_chat_session(session_id: str) -> Optional[MongoChatSession]:
        """Get chat session by ID"""
        try:
            collection = await get_dashboardx_collection()
            session_dict = await collection.find_one({
                "_id": ObjectId(session_id),
                "type": "chat_session"
            })

            return MongoChatSession(**session_dict) if session_dict else None
        except PyMongoError as e:
            logger.error(f"Error getting chat session: {str(e)}")
            raise

    # ==================== Agent Operations ====================

    @staticmethod
    async def create_agent(agent_data: MongoAgentCreate) -> MongoAgent:
        """Create a new agent"""
        try:
            collection = await get_dashboardx_collection()
            agent_dict = agent_data.model_dump()
            agent_dict["type"] = "agent"
            agent_dict["created_at"] = datetime.utcnow()
            agent_dict["updated_at"] = datetime.utcnow()

            result = await collection.insert_one(agent_dict)
            agent_dict["_id"] = result.inserted_id

            return MongoAgent(**agent_dict)
        except PyMongoError as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise

    @staticmethod
    async def create_agent_execution(execution_data: MongoAgentExecutionCreate) -> MongoAgentExecution:
        """Create a new agent execution log"""
        try:
            collection = await get_dashboardx_collection()
            execution_dict = execution_data.model_dump()
            execution_dict["type"] = "agent_execution"
            execution_dict["created_at"] = datetime.utcnow()
            execution_dict["updated_at"] = datetime.utcnow()
            execution_dict["status"] = "running"

            result = await collection.insert_one(execution_dict)
            execution_dict["_id"] = result.inserted_id

            return MongoAgentExecution(**execution_dict)
        except PyMongoError as e:
            logger.error(f"Error creating agent execution: {str(e)}")
            raise

    # ==================== Analytics Operations ====================

    @staticmethod
    async def log_analytics_event(event_data: MongoAnalyticsEventCreate) -> MongoAnalyticsEvent:
        """Log an analytics event"""
        try:
            collection = await get_dashboardx_collection()
            event_dict = event_data.model_dump()
            event_dict["type"] = "analytics_event"
            event_dict["created_at"] = datetime.utcnow()
            event_dict["updated_at"] = datetime.utcnow()

            result = await collection.insert_one(event_dict)
            event_dict["_id"] = result.inserted_id

            return MongoAnalyticsEvent(**event_dict)
        except PyMongoError as e:
            logger.error(f"Error logging analytics event: {str(e)}")
            raise

    # ==================== Feedback Operations ====================

    @staticmethod
    async def create_feedback(feedback_data: MongoFeedbackCreate) -> MongoFeedback:
        """Create feedback"""
        try:
            collection = await get_dashboardx_collection()
            feedback_dict = feedback_data.model_dump()
            feedback_dict["type"] = "feedback"
            feedback_dict["created_at"] = datetime.utcnow()
            feedback_dict["updated_at"] = datetime.utcnow()

            result = await collection.insert_one(feedback_dict)
            feedback_dict["_id"] = result.inserted_id

            return MongoFeedback(**feedback_dict)
        except PyMongoError as e:
            logger.error(f"Error creating feedback: {str(e)}")
            raise

    # ==================== Utility Operations ====================

    @staticmethod
    async def count_documents(collection_type: str, tenant_id: str) -> int:
        """Count documents by type and tenant"""
        try:
            collection = await get_dashboardx_collection()
            count = await collection.count_documents({
                "type": collection_type,
                "tenant_id": tenant_id
            })
            return count
        except PyMongoError as e:
            logger.error(f"Error counting documents: {str(e)}")
            raise
