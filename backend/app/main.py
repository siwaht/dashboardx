"""
FastAPI Main Application

Entry point for the Agentic RAG Platform backend.
Configures middleware, routes, and application lifecycle.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import settings
from app.mongodb import MongoDB

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Agentic RAG Platform Backend...")
    logger.info(f"Environment: {settings.sentry_environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize MongoDB
    try:
        await MongoDB.connect()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.warning("Application starting without MongoDB connection")

    # Initialize Sentry if configured
    if settings.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.sentry_environment,
                traces_sample_rate=settings.sentry_traces_sample_rate,
            )
            logger.info("Sentry initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")
    
    # Initialize LangSmith if configured
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        logger.info("LangSmith tracing enabled")
    
    logger.info("Backend startup complete")
    
    yield

    # Shutdown
    logger.info("Shutting down Agentic RAG Platform Backend...")

    # Close MongoDB connection
    try:
        await MongoDB.close()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


# Create FastAPI application
app = FastAPI(
    title="Agentic RAG Platform API",
    description="Backend API for the Agentic RAG Platform with LangGraph and LlamaIndex",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# ==================== Middleware ====================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.3f}s"
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# ==================== Exception Handlers ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
        },
    )


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.sentry_environment,
        "timestamp": time.time(),
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic RAG Platform API",
        "version": "0.1.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
    }


# ==================== API Routes ====================

# Import and include routers
from app.api import users, rag, agents, copilotkit, analytics, agent_config

app.include_router(users.router, prefix="/api/users", tags=["User Management"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG Pipeline"])
app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents"])
app.include_router(agent_config.router, prefix="/api/agent-configs", tags=["Agent Configuration"])
app.include_router(copilotkit.router, tags=["CopilotKit"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

# Additional routers (will be created in future phases)
# from app.api import streaming, data_sources
# app.include_router(streaming.router, prefix="/stream", tags=["Streaming"])
# app.include_router(data_sources.router, prefix="/data-sources", tags=["Data Sources"])


# ==================== Development Endpoints ====================

if settings.debug:
    @app.get("/debug/config")
    async def debug_config():
        """Debug endpoint to view configuration (only in debug mode)"""
        return {
            "openai_model": settings.openai_chat_model,
            "embedding_model": settings.openai_embedding_model,
            "chunk_size": settings.chunk_size,
            "top_k_documents": settings.top_k_documents,
            "enable_streaming": settings.enable_streaming,
            "cors_origins": settings.backend_cors_origins,
        }


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.backend_reload,
        workers=settings.backend_workers,
        log_level=settings.log_level.lower(),
    )
