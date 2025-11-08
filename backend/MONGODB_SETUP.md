# MongoDB Setup Guide

This guide explains how MongoDB has been integrated into the DashboardX application.

## Overview

MongoDB has been configured as a database option for the DashboardX application, with a collection named `dashboardx` for storing all application data.

## Configuration

### Environment Variables

The following environment variables have been added to `/backend/.env`:

```bash
MONGODB_URL=mongodb+srv://siwaht:Mega173@n8n.yeklig.mongodb.net/?appName=n8n
MONGODB_DATABASE=dashboardx
MONGODB_COLLECTION=dashboardx
```

### What's Been Added

1. **Dependencies** (`requirements.txt`):
   - `pymongo==4.6.1` - Official MongoDB Python driver
   - `motor==3.3.2` - Async MongoDB driver for FastAPI

2. **Configuration** (`app/config.py`):
   - MongoDB connection settings
   - Database and collection names

3. **Connection Management** (`app/mongodb.py`):
   - `MongoDB` class for connection lifecycle
   - Auto-connects on app startup
   - Auto-disconnects on app shutdown

4. **Data Models** (`app/mongodb_models.py`):
   - `MongoUser` - User documents
   - `MongoDocument` - Document storage for RAG
   - `MongoChatSession` - Chat sessions with messages
   - `MongoAgent` - Custom AI agents
   - `MongoAgentExecution` - Agent execution logs
   - `MongoDataSource` - External data source connectors
   - `MongoAnalyticsEvent` - Analytics tracking
   - `MongoFeedback` - User feedback
   - `MongoAPIKey` - API key management

5. **Service Layer** (`app/mongodb_service.py`):
   - CRUD operations for all document types
   - Type-safe data validation
   - Error handling

## Database Schema

All documents in the `dashboardx` collection include a `type` field to differentiate between different data types:

- `type: "user"` - User accounts
- `type: "document"` - RAG documents
- `type: "chat_session"` - Chat sessions
- `type: "agent"` - AI agents
- `type: "agent_execution"` - Agent runs
- `type: "data_source"` - External connectors
- `type: "analytics_event"` - Event tracking
- `type: "feedback"` - User feedback
- `type: "api_key"` - API keys

## Indexes

The initialization script creates the following indexes for optimal performance:

1. **user_lookup_idx**: `(type, email, tenant_id)` - Fast user lookups
2. **document_tenant_user_idx**: `(type, tenant_id, user_id)` - Document queries
3. **chat_session_idx**: `(type, tenant_id, created_at)` - Chat session retrieval
4. **analytics_event_idx**: `(type, tenant_id, event_type, timestamp)` - Analytics queries
5. **agent_execution_idx**: `(type, tenant_id, status)` - Agent execution tracking
6. **type_created_at_idx**: `(type, created_at)` - Chronological sorting

## Usage Examples

### Creating a User

```python
from app.mongodb_service import MongoDBService
from app.mongodb_models import MongoUserCreate

user_data = MongoUserCreate(
    email="user@example.com",
    full_name="John Doe",
    role="user",
    tenant_id="tenant-123",
    password="hashed_password"
)

user = await MongoDBService.create_user(user_data)
```

### Creating a Document

```python
from app.mongodb_service import MongoDBService
from app.mongodb_models import MongoDocumentCreate

doc_data = MongoDocumentCreate(
    title="My Document",
    content="Document content...",
    file_type="pdf",
    tenant_id="tenant-123",
    user_id="user-456"
)

document = await MongoDBService.create_document(doc_data)
```

### Creating a Chat Session

```python
from app.mongodb_service import MongoDBService
from app.mongodb_models import MongoChatSessionCreate, MongoChatMessageCreate

# Create session
session_data = MongoChatSessionCreate(
    title="My Chat",
    tenant_id="tenant-123",
    user_id="user-456"
)

session = await MongoDBService.create_chat_session(session_data)

# Add message
message_data = MongoChatMessageCreate(
    session_id=str(session.id),
    role="user",
    content="Hello, AI!"
)

updated_session = await MongoDBService.add_message_to_session(message_data)
```

## Initialization

To initialize MongoDB with indexes, run:

```bash
cd backend
python scripts/init_mongodb.py
```

This script will:
- Test the MongoDB connection
- Create all necessary indexes
- Insert and verify a test document
- Display collection statistics

## Testing the Connection

The MongoDB connection is automatically established when the FastAPI application starts. Check the logs for:

```
MongoDB connected successfully
```

If the connection fails, the app will still start but MongoDB features won't be available.

## Production Considerations

1. **Security**:
   - The MongoDB URL contains credentials - keep `.env` files secure
   - Never commit `.env` files to version control
   - Use environment-specific credentials for dev/staging/prod

2. **Scaling**:
   - MongoDB Atlas auto-scales based on load
   - Connection pooling is configured (min: 10, max: 50 connections)
   - Indexes are optimized for multi-tenant queries

3. **Backup**:
   - MongoDB Atlas provides automatic backups
   - Configure backup schedules in the Atlas dashboard

4. **Monitoring**:
   - Use MongoDB Atlas monitoring dashboard
   - Check the `/health` endpoint for application status

## API Integration

MongoDB is now available throughout the FastAPI application:

```python
from app.mongodb import get_dashboardx_collection

# In any FastAPI route
@app.get("/api/data")
async def get_data():
    collection = await get_dashboardx_collection()
    documents = await collection.find({"type": "document"}).to_list(length=100)
    return {"data": documents}
```

## Migration from Supabase

If you're migrating from Supabase to MongoDB:

1. The existing Supabase code remains functional
2. You can gradually migrate collections to MongoDB
3. Both databases can coexist during migration
4. Use the service layer (`mongodb_service.py`) for consistent interfaces

## Troubleshooting

### Connection Issues

If you see "ConfigurationError: no nameservers":
- This is a DNS resolution issue
- Ensure your environment can resolve MongoDB SRV records
- In Docker, ensure proper DNS configuration

### Authentication Failures

If you see authentication errors:
- Verify the MongoDB URL credentials
- Check that the database user has proper permissions
- Ensure IP whitelist includes your application's IP

### Performance Issues

If queries are slow:
- Run the init script to ensure indexes are created
- Check MongoDB Atlas metrics for slow queries
- Consider adding more specific indexes for your use case

## Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Motor Documentation](https://motor.readthedocs.io/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
