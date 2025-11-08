"""
MongoDB Initialization Script

This script initializes the MongoDB database with necessary indexes
and validates the connection.
"""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def init_mongodb():
    """Initialize MongoDB with indexes and collections"""

    try:
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB...")
        client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)

        # Verify connection
        await client.admin.command('ping')
        logger.info("✓ Successfully connected to MongoDB")

        # Get database
        db = client[settings.mongodb_database]
        logger.info(f"✓ Using database: {settings.mongodb_database}")

        # Get collection
        collection = db[settings.mongodb_collection]
        logger.info(f"✓ Using collection: {settings.mongodb_collection}")

        # Create indexes
        logger.info("Creating indexes...")

        # 1. Index for user lookups
        await collection.create_index([("type", 1), ("email", 1), ("tenant_id", 1)],
                                      name="user_lookup_idx",
                                      unique=False)
        logger.info("  ✓ Created index: user_lookup_idx")

        # 2. Index for document queries
        await collection.create_index([("type", 1), ("tenant_id", 1), ("user_id", 1)],
                                      name="document_tenant_user_idx")
        logger.info("  ✓ Created index: document_tenant_user_idx")

        # 3. Index for chat sessions
        await collection.create_index([("type", 1), ("tenant_id", 1), ("created_at", -1)],
                                      name="chat_session_idx")
        logger.info("  ✓ Created index: chat_session_idx")

        # 4. Index for analytics events
        await collection.create_index([("type", 1), ("tenant_id", 1), ("event_type", 1), ("timestamp", -1)],
                                      name="analytics_event_idx")
        logger.info("  ✓ Created index: analytics_event_idx")

        # 5. Index for agent executions
        await collection.create_index([("type", 1), ("tenant_id", 1), ("status", 1)],
                                      name="agent_execution_idx")
        logger.info("  ✓ Created index: agent_execution_idx")

        # 6. Index for created_at (for sorting)
        await collection.create_index([("type", 1), ("created_at", -1)],
                                      name="type_created_at_idx")
        logger.info("  ✓ Created index: type_created_at_idx")

        # List all indexes
        logger.info("\nExisting indexes:")
        async for index in collection.list_indexes():
            logger.info(f"  - {index['name']}")

        # Insert a test document
        logger.info("\nInserting test document...")
        test_doc = {
            "type": "test",
            "message": "MongoDB connection successful!",
            "database": settings.mongodb_database,
            "collection": settings.mongodb_collection,
            "timestamp": asyncio.get_event_loop().time()
        }
        result = await collection.insert_one(test_doc)
        logger.info(f"✓ Test document inserted with ID: {result.inserted_id}")

        # Read the test document back
        found_doc = await collection.find_one({"_id": result.inserted_id})
        if found_doc:
            logger.info(f"✓ Test document retrieved successfully")

        # Clean up test document
        await collection.delete_one({"_id": result.inserted_id})
        logger.info(f"✓ Test document cleaned up")

        # Get collection stats
        stats = await db.command("collStats", settings.mongodb_collection)
        logger.info(f"\nCollection Statistics:")
        logger.info(f"  - Document count: {stats.get('count', 0)}")
        logger.info(f"  - Size: {stats.get('size', 0)} bytes")
        logger.info(f"  - Storage size: {stats.get('storageSize', 0)} bytes")

        logger.info("\n" + "="*50)
        logger.info("MongoDB initialization completed successfully!")
        logger.info("="*50)

        # Close connection
        client.close()

    except Exception as e:
        logger.error(f"\n❌ Error initializing MongoDB: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Starting MongoDB initialization...")
    logger.info(f"MongoDB URL: {settings.mongodb_url[:30]}...")
    logger.info(f"Database: {settings.mongodb_database}")
    logger.info(f"Collection: {settings.mongodb_collection}")
    logger.info("="*50 + "\n")

    asyncio.run(init_mongodb())
