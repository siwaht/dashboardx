"""
MongoDB Connection Management

Provides async MongoDB client connection and database access.
Uses Motor for async operations compatible with FastAPI.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

from .config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Establish connection to MongoDB

        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongodb_url[:20]}...")

            # Create async MongoDB client
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=50,  # Maximum number of connections
                minPoolSize=10,  # Minimum number of connections
                retryWrites=True,
                w='majority'
            )

            # Verify connection
            await cls.client.admin.command('ping')

            # Get database
            cls.database = cls.client[settings.mongodb_database]

            logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_database}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def close(cls) -> None:
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get the MongoDB database instance

        Returns:
            AsyncIOMotorDatabase: The database instance

        Raises:
            RuntimeError: If not connected to MongoDB
        """
        if cls.database is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        return cls.database

    @classmethod
    def get_collection(cls, collection_name: str = None) -> AsyncIOMotorCollection:
        """
        Get a MongoDB collection

        Args:
            collection_name: Name of the collection (defaults to settings.mongodb_collection)

        Returns:
            AsyncIOMotorCollection: The collection instance
        """
        db = cls.get_database()
        collection = collection_name or settings.mongodb_collection
        return db[collection]


# Convenience function to get the database
async def get_mongodb() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance

    Returns:
        AsyncIOMotorDatabase: The database instance
    """
    return MongoDB.get_database()


# Convenience function to get the dashboardx collection
async def get_dashboardx_collection() -> AsyncIOMotorCollection:
    """
    Get the dashboardx collection

    Returns:
        AsyncIOMotorCollection: The dashboardx collection
    """
    return MongoDB.get_collection(settings.mongodb_collection)
