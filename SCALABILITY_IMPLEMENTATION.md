# Scalability Implementation Guide

## Overview
This document provides step-by-step implementation details for making the application scalable to hundreds of concurrent users.

## Phase 1: Immediate Optimizations (Week 1-2)

### 1. Multi-Worker Configuration & Production Settings

**Files to modify:**
- `backend/app/config.py`
- `backend/app/main.py`
- Create: `backend/gunicorn_config.py`
- Create: `backend/start.sh`

**Changes:**
1. Update production settings in config
2. Add Gunicorn configuration
3. Implement graceful shutdown
4. Add worker health checks

### 2. Database Connection Pooling

**Files to create:**
- `backend/app/database.py` - Database connection pool manager
- `backend/app/dependencies.py` - FastAPI dependencies

**Changes:**
1. Implement async SQLAlchemy engine with pooling
2. Create database session management
3. Add connection lifecycle management
4. Implement connection health checks

### 3. Rate Limiting Middleware

**Files to create:**
- `backend/app/middleware/rate_limiter.py`
- `backend/app/middleware/__init__.py`

**Changes:**
1. Implement token bucket algorithm
2. Add per-user and per-tenant limits
3. Store rate limit data in Redis (or in-memory initially)
4. Add rate limit headers to responses

### 4. Async Database Operations

**Files to modify:**
- `backend/app/api/users.py`
- `backend/app/rag/retrieval.py`
- `backend/app/rag/ingestion.py`

**Changes:**
1. Convert Supabase client to async
2. Update all database queries to async/await
3. Implement connection pooling for Supabase
4. Add retry logic for transient failures

### 5. Redis Caching Layer

**Files to create:**
- `backend/app/cache/redis_client.py`
- `backend/app/cache/cache_manager.py`
- `backend/app/cache/__init__.py`

**Changes:**
1. Implement Redis connection with connection pooling
2. Create cache decorators for common operations
3. Implement cache invalidation strategies
4. Add cache warming for critical data

## Phase 2: Enhanced Performance (Week 3-4)

### 6. Background Task Queue

**Files to create:**
- `backend/app/tasks/__init__.py`
- `backend/app/tasks/celery_app.py`
- `backend/app/tasks/document_tasks.py`
- `backend/app/tasks/embedding_tasks.py`

**Changes:**
1. Set up Celery with Redis broker
2. Move document processing to background tasks
3. Implement task status tracking
4. Add task retry and error handling

### 7. Streaming Responses

**Files to create:**
- `backend/app/api/streaming.py`
- `backend/app/streaming/__init__.py`
- `backend/app/streaming/sse_manager.py`

**Changes:**
1. Implement Server-Sent Events (SSE) for chat
2. Add streaming response handlers
3. Implement connection management
4. Add heartbeat mechanism

### 8. Enhanced Monitoring

**Files to create:**
- `backend/app/monitoring/metrics.py`
- `backend/app/monitoring/middleware.py`
- `backend/app/monitoring/__init__.py`

**Changes:**
1. Add Prometheus metrics
2. Implement custom metrics collection
3. Add request duration tracking
4. Create health check endpoints

### 9. Query Optimization

**Files to create:**
- `supabase/migrations/20240120000000_add_performance_indexes.sql`
- `supabase/migrations/20240120000001_optimize_rls_policies.sql`

**Changes:**
1. Add composite indexes for common queries
2. Optimize RLS policies
3. Add materialized views for aggregations
4. Implement query result pagination

## Detailed Implementation

### 1.1 Multi-Worker Configuration

#### backend/gunicorn_config.py
```python
import multiprocessing
import os

# Server socket
bind = f"{os.getenv('BACKEND_HOST', '0.0.0.0')}:{os.getenv('BACKEND_PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('BACKEND_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'agentic-rag-platform'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Graceful shutdown
graceful_timeout = 30

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting Gunicorn server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading workers...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Server is ready. Listening on {bind}")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Forking new master process...")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"Worker received ABORT signal (pid: {worker.pid})")
```

#### backend/start.sh
```bash
#!/bin/bash

# Production startup script for Agentic RAG Platform

set -e

echo "Starting Agentic RAG Platform..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Run database migrations (if needed)
# python -m alembic upgrade head

# Start the application with Gunicorn
exec gunicorn app.main:app \
    --config gunicorn_config.py \
    --log-config logging.conf
```

### 1.2 Database Connection Pooling

#### backend/app/database.py
```python
"""
Database Connection Pool Manager

Provides async database connections with connection pooling
for optimal performance under high load.
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections with pooling"""
    
    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker | None = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database engine and session factory"""
        if self._initialized:
            return
        
        # Convert Supabase connection string to async format
        db_url = settings.supabase_db_connection
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            db_url,
            echo=settings.debug,
            pool_size=20,  # Base pool size
            max_overflow=40,  # Additional connections when pool is full
            pool_timeout=30,  # Timeout for getting connection from pool
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before using
            poolclass=QueuePool,
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        # Add connection pool event listeners
        @event.listens_for(self.engine.sync_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Called when a new DB-API connection is created"""
            logger.debug("New database connection created")
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Called when a connection is retrieved from the pool"""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Called when a connection is returned to the pool"""
            logger.debug("Connection returned to pool")
        
        self._initialized = True
        logger.info("Database connection pool initialized")
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session from pool"""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with db_manager.get_session() as session:
        yield session
```

#### backend/app/dependencies.py
```python
"""
FastAPI Dependencies

Provides reusable dependencies for request handling.
"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.security.auth import get_current_user, AuthenticatedUser
from app.cache.cache_manager import CacheManager


async def get_cache() -> CacheManager:
    """Get cache manager instance"""
    from app.cache.redis_client import cache_manager
    return cache_manager


async def get_current_active_user(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """Get current active user"""
    # Add additional checks if needed
    return current_user


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async for session in get_db_session():
        yield session
```

### 1.3 Rate Limiting Middleware

#### backend/app/middleware/rate_limiter.py
```python
"""
Rate Limiting Middleware

Implements token bucket algorithm for rate limiting
to prevent abuse and ensure fair resource allocation.
"""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_retry_after(self) -> int:
        """Get seconds until next token is available"""
        if self.tokens >= 1:
            return 0
        
        tokens_needed = 1 - self.tokens
        return int(tokens_needed / self.refill_rate) + 1


class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self):
        self.user_buckets: Dict[str, TokenBucket] = {}
        self.tenant_buckets: Dict[str, TokenBucket] = {}
        self.ip_buckets: Dict[str, TokenBucket] = {}
        
        # Cleanup old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def _get_or_create_bucket(
        self,
        buckets: Dict[str, TokenBucket],
        key: str,
        capacity: int,
        refill_rate: float
    ) -> TokenBucket:
        """Get existing bucket or create new one"""
        if key not in buckets:
            buckets[key] = TokenBucket(capacity, refill_rate)
        return buckets[key]
    
    def check_rate_limit(
        self,
        user_id: str = None,
        tenant_id: str = None,
        ip_address: str = None
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limits
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            ip_address: IP address
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        self._cleanup_old_buckets()
        
        retry_after = 0
        
        # Check user rate limit
        if user_id:
            bucket = self._get_or_create_bucket(
                self.user_buckets,
                user_id,
                capacity=settings.rate_limit_per_minute,
                refill_rate=settings.rate_limit_per_minute / 60.0
            )
            if not bucket.consume():
                retry_after = max(retry_after, bucket.get_retry_after())
                return False, retry_after
        
        # Check tenant rate limit (higher limit)
        if tenant_id:
            bucket = self._get_or_create_bucket(
                self.tenant_buckets,
                tenant_id,
                capacity=settings.rate_limit_per_hour,
                refill_rate=settings.rate_limit_per_hour / 3600.0
            )
            if not bucket.consume():
                retry_after = max(retry_after, bucket.get_retry_after())
                return False, retry_after
        
        # Check IP rate limit (fallback)
        if ip_address:
            bucket = self._get_or_create_bucket(
                self.ip_buckets,
                ip_address,
                capacity=settings.rate_limit_per_minute * 2,
                refill_rate=(settings.rate_limit_per_minute * 2) / 60.0
            )
            if not bucket.consume():
                retry_after = max(retry_after, bucket.get_retry_after())
                return False, retry_after
        
        return True, 0
    
    def _cleanup_old_buckets(self):
        """Remove old unused buckets to prevent memory leak"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove buckets that are full (haven't been used recently)
        for buckets in [self.user_buckets, self.tenant_buckets, self.ip_buckets]:
            keys_to_remove = [
                key for key, bucket in buckets.items()
                if bucket.tokens >= bucket.capacity * 0.9
            ]
            for key in keys_to_remove:
                del buckets[key]
        
        self.last_cleanup = now
        logger.debug("Cleaned up old rate limit buckets")


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Extract identifiers
        user_id = None
        tenant_id = None
        
        # Try to get user info from request state (set by auth middleware)
        if hasattr(request.state, "user"):
            user_id = request.state.user.user_id
            tenant_id = request.state.user.tenant_id
        
        # Get IP address
        ip_address = request.client.host if request.client else None
        
        # Check rate limit
        allowed, retry_after = rate_limiter.check_rate_limit(
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for user={user_id}, "
                f"tenant={tenant_id}, ip={ip_address}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = "1"  # Simplified
        
        return response
```

### 1.4 Redis Caching Layer

#### backend/app/cache/redis_client.py
```python
"""
Redis Client for Caching

Provides Redis connection with connection pooling
and helper methods for caching operations.
"""

import json
import logging
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection pooling"""
    
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        if self._initialized:
            return
        
        if not settings.redis_url:
            logger.warning("Redis URL not configured. Caching disabled.")
            return
        
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=50,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            
            # Create Redis client
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            
            self._initialized = True
            logger.info("Redis connection pool initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.client = None
    
    async def close(self):
        """Close Redis connections"""
        if self.client:
            await self.client.close()
            logger.info("Redis connections closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """Set value in cache"""
        if not self.client:
            return False
        
        try:
            ttl = ttl or settings.cache_ttl_seconds
            serialized = json.dumps(value)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.client:
            return None
        
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key"""
        if not self.client:
            return False
        
        try:
            await self.client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()
```

## Configuration Updates

### Update backend/app/config.py

Add these new configuration options:

```python
# ==================== Performance & Scalability ====================
# Worker Configuration
backend_workers: int = Field(
    default_factory=lambda: multiprocessing.cpu_count() * 2 + 1,
    env="BACKEND_WORKERS"
)

# Database Connection Pool
db_pool_size: int = Field(20, env="DB_POOL_SIZE")
db_max_overflow: int = Field(40, env="DB_MAX_OVERFLOW")
db_pool_timeout: int = Field(30, env="DB_POOL_TIMEOUT")
db_pool_recycle: int = Field(3600, env="DB_POOL_RECYCLE")

# Redis Configuration
redis_url: Optional[str] = Field(None, env="REDIS_URL")
redis_max_connections: int = Field(50, env="REDIS_MAX_CONNECTIONS")

# Cache Configuration
cache_ttl_seconds: int = Field(3600, env="CACHE_TTL_SECONDS")
cache_user_profile_ttl: int = Field(300, env="CACHE_USER_PROFILE_TTL")
cache_permissions_ttl: int = Field(600, env="CACHE_PERMISSIONS_TTL")
cache_search_results_ttl: int = Field(1800, env="CACHE_SEARCH_RESULTS_TTL")

# Rate Limiting (already exists, but ensure these are present)
rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
rate_limit_per_hour: int = Field(1000, env="RATE_LIMIT_PER_HOUR")

# Background Tasks
celery_broker_url: Optional[str] = Field(None, env="CELERY_BROKER_URL")
celery_result_backend: Optional[str] = Field(None, env="CELERY_RESULT_BACKEND")

# Monitoring
enable_metrics: bool = Field(True, env="ENABLE_METRICS")
metrics_port: int = Field(9090, env="METRICS_PORT")
```

## Deployment Checklist

### Environment Variables to Add

```bash
# Worker Configuration
BACKEND_WORKERS=9  # (CPU cores * 2 + 1)

# Database Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Cache TTLs
CACHE_TTL_SECONDS=3600
CACHE_USER_PROFILE_TTL=300
CACHE_PERMISSIONS_TTL=600
CACHE_SEARCH_RESULTS_TTL=1800

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Dependencies to Add

Update `backend/requirements.txt`:

```txt
# Add these new dependencies
gunicorn==21.2.0
redis==5.0.1
celery==5.3.4
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
prometheus-client==0.19.0
```

## Testing Strategy

### Load Testing Script

Create `tests/load_test.py`:

```python
"""
Load testing script using Locust

Run with: locust -f tests/load_test.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random


class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None
    
    @task(3)
    def get_documents(self):
        """Get documents list"""
        if self.token:
            self.client.get(
                "/documents",
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(2)
    def search_documents(self):
        """Search documents"""
        if self.token:
            self.client.post(
                "/search",
                json={"query": "test query"},
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(1)
    def send_chat_message(self):
        """Send chat message"""
        if self.token:
            self.client.post(
                "/chat",
                json={
                    "message": "Hello, how are you?",
                    "session_id": "test-session"
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(1)
    def health_check(self):
        """Health check"""
        self.client.get("/health")
```

## Monitoring Setup

### Prometheus Metrics

Create `backend/app/monitoring/metrics.py`:

```python
"""
Prometheus Metrics Collection

Tracks application performance metrics.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Application metrics
active_users = Gauge(
    'active_users',
    'Number of active users'
)

async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

## Next Steps

1. ✅ Review this implementation plan
2. ⏳ Set up Redis instance
3. ⏳ Update dependencies
4. ⏳ Implement database connection pooling
5. ⏳ Add rate limiting middleware
6. ⏳ Implement caching layer
7. ⏳ Update main.py to use new components
8. ⏳ Test with load testing tools
9. ⏳ Deploy to staging environment
10. ⏳ Monitor and optimize

## Rollback Plan

If issues occur:
1. Revert to single worker mode
2. Disable rate limiting
3. Disable caching
4. Use direct database connections
5. Monitor error logs
6. Fix issues and redeploy incrementally
