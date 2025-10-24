# 🚀 Enterprise SaaS Enhancement Master Plan
## Advanced Data Analytics Platform with RAG & AI

**Generated:** 2024-01-XX  
**Current Status:** 85/100 ⭐⭐⭐⭐  
**Target Status:** 98/100 ⭐⭐⭐⭐⭐

---

## 📊 Executive Summary

Your **Agentic RAG Platform** is an impressive enterprise-level SaaS application with:
- ✅ Solid architecture (React + FastAPI + Supabase)
- ✅ Advanced features (RAG, AI Agents, Analytics, Multi-tenancy)
- ✅ Comprehensive security (JWT, FGAC, RLS)
- ✅ Extensive documentation

**Key Findings:**
- **Code Quality:** 90/100 - Excellent structure and patterns
- **Feature Completeness:** 75/100 - Core features implemented, advanced features in progress
- **Security:** 70/100 - Good foundation, needs hardening
- **Performance:** 60/100 - Needs optimization
- **Scalability:** 70/100 - Good foundation, needs enhancement
- **DevOps:** 40/100 - Missing CI/CD, monitoring, testing

---

## 🎯 Strategic Enhancement Areas

### 1. **Production Readiness** (Critical Priority)
### 2. **Performance & Scalability** (High Priority)
### 3. **Advanced Analytics Features** (High Priority)
### 4. **Developer Experience** (Medium Priority)
### 5. **Enterprise Features** (Medium Priority)
### 6. **AI/ML Enhancements** (Long-term)

---

## 🔥 PHASE 1: PRODUCTION READINESS (Week 1-2)

### 1.1 Infrastructure & DevOps

#### A. Containerization & Orchestration
**Status:** ❌ Missing  
**Priority:** CRITICAL  
**Effort:** 8 hours

**Implementation:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL with pgvector
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: ragplatform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching & rate limiting
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/ragplatform
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_BACKEND_URL=http://backend:8000
    volumes:
      - .:/app
      - /app/node_modules
    command: npm run dev

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

  # Celery worker for async tasks
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/ragplatform
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  # Celery beat for scheduled tasks
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/ragplatform
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

---

#### B. CI/CD Pipeline
**Status:** ❌ Missing  
**Priority:** CRITICAL  
**Effort:** 6 hours

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Frontend Tests & Build
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linter
        run: npm run lint
      
      - name: Type check
        run: npm run typecheck
      
      - name: Run tests
        run: npm run test:coverage
      
      - name: Build
        run: npm run build
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
          flags: frontend

  # Backend Tests & Build
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: ankane/pgvector:latest
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run linter
        run: |
          cd backend
          ruff check .
          black --check .
      
      - name: Run type checker
        run: |
          cd backend
          mypy app/
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
          REDIS_URL: redis://localhost:6379
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  # Security Scanning
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  # Build and Push Docker Images
  build-push:
    needs: [frontend, backend, security]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
      
      - name: Build and push Backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-backend
          labels: ${{ steps.meta.outputs.labels }}
      
      - name: Build and push Frontend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile.frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-frontend
          labels: ${{ steps.meta.outputs.labels }}

  # Deploy to Staging
  deploy-staging:
    needs: build-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Deploy to staging
        run: |
          # Add deployment script here
          echo "Deploying to staging..."

  # Deploy to Production
  deploy-production:
    needs: build-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://your-domain.com
    steps:
      - name: Deploy to production
        run: |
          # Add deployment script here
          echo "Deploying to production..."
```

---

#### C. Monitoring & Observability
**Status:** ⚠️ Partial (Sentry configured)  
**Priority:** HIGH  
**Effort:** 10 hours

**Add to requirements.txt:**
```txt
# Monitoring & Observability
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-exporter-prometheus==0.42b0
structlog==24.1.0
```

**Create `backend/app/monitoring/__init__.py`:**
```python
"""
Monitoring and Observability Module
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import structlog
import time
from typing import Callable
from fastapi import Request, Response

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

RAG_QUERY_DURATION = Histogram(
    'rag_query_duration_seconds',
    'RAG query processing duration',
    ['query_type']
)

AGENT_EXECUTION_DURATION = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration',
    ['agent_type']
)

DOCUMENT_PROCESSING_DURATION = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration',
    ['document_type']
)

EMBEDDING_GENERATION_DURATION = Histogram(
    'embedding_generation_duration_seconds',
    'Embedding generation duration'
)

# OpenTelemetry setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

metrics.set_meter_provider(MeterProvider())
meter = metrics.get_meter(__name__)


async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to collect metrics"""
    ACTIVE_REQUESTS.inc()
    
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=method,
            endpoint=path,
            status=status
        ).inc()
        
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=method,
            endpoint=path
        ).observe(duration)
        
        # Structured logging
        logger.info(
            "http_request",
            method=method,
            path=path,
            status=status,
            duration=duration,
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host if request.client else None
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "http_request_error",
            method=method,
            path=path,
            error=str(e),
            exc_info=True
        )
        raise
        
    finally:
        ACTIVE_REQUESTS.dec()


def instrument_app(app):
    """Instrument FastAPI app with monitoring"""
    # Add metrics middleware
    app.middleware("http")(metrics_middleware)
    
    # Add OpenTelemetry instrumentation
    FastAPIInstrumentor.instrument_app(app)
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )
    
    logger.info("Monitoring instrumentation complete")
```

**Grafana Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "RAG Platform Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "RAG Query Performance",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(rag_query_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

---

### 1.2 Testing Infrastructure

#### A. Frontend Testing
**Status:** ❌ Missing  
**Priority:** CRITICAL  
**Effort:** 12 hours

**Install dependencies:**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
npm install -D @testing-library/user-event jsdom @vitest/ui
npm install -D @vitest/coverage-v8 happy-dom
npm install -D msw  # For API mocking
```

**Create `vitest.config.ts`:**
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/main.tsx'
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80
      }
    },
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

**Create `src/test/setup.ts`:**
```typescript
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    VITE_SUPABASE_URL: 'https://test.supabase.co',
    VITE_SUPABASE_ANON_KEY: 'test-key',
    VITE_BACKEND_URL: 'http://localhost:8000'
  }
}))

// Mock Supabase client
vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
      signIn: vi.fn(),
      signOut: vi.fn(),
      onAuthStateChange: vi.fn()
    },
    from: vi.fn(() => ({
      select: vi.fn().mockReturnThis(),
      insert: vi.fn().mockReturnThis(),
      update: vi.fn().mockReturnThis(),
      delete: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn()
    }))
  }
}))
```

**Example Test: `src/components/auth/SignInForm.test.tsx`:**
```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SignInForm } from './SignInForm'
import { AuthContext } from '@/contexts/AuthContext'

describe('SignInForm', () => {
  const mockSignIn = vi.fn()
  
  const renderWithAuth = (component: React.ReactElement) => {
    return render(
      <AuthContext.Provider value={{ signIn: mockSignIn, user: null, loading: false }}>
        {component}
      </AuthContext.Provider>
    )
  }

  it('renders sign in form', () => {
    renderWithAuth(<SignInForm />)
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    renderWithAuth(<SignInForm />)
    
    const emailInput = screen.getByLabelText(/email/i)
    await user.type(emailInput, 'invalid-email')
    await user.tab()
    
    await waitFor(() => {
      expect(screen.getByText(/invalid email/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid credentials', async () => {
    const user = userEvent.setup()
    mockSignIn.mockResolvedValueOnce({ error: null })
    
    renderWithAuth(<SignInForm />)
    
    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'password123')
    })
  })

  it('displays error message on failed sign in', async () => {
    const user = userEvent.setup()
    mockSignIn.mockResolvedValueOnce({ error: { message: 'Invalid credentials' } })
    
    renderWithAuth(<SignInForm />)
    
    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })
})
```

**Add to package.json:**
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:watch": "vitest --watch"
  }
}
```

---

#### B. Backend Testing
**Status:** ⚠️ Partial  
**Priority:** HIGH  
**Effort:** 16 hours

**Create `backend/tests/conftest.py`:**
```python
"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a test response"
                }
            }
        ]
    }


@pytest.fixture
def sample_document():
    """Sample document for testing"""
    return {
        "id": "test-doc-id",
        "title": "Test Document",
        "content": "This is test content",
        "tenant_id": "test-tenant"
    }


@pytest.fixture
def auth_headers():
    """Authentication headers for testing"""
    return {
        "Authorization": "Bearer test-token"
    }
```

**Example Test: `backend/tests/test_rag.py`:**
```python
"""
Tests for RAG pipeline
"""
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch

from app.rag.embeddings import generate_embeddings
from app.rag.retrieval import retrieve_documents
from app.rag.chunking import chunk_document


@pytest.mark.asyncio
async def test_generate_embeddings():
    """Test embedding generation"""
    text = "This is a test document"
    
    with patch('app.rag.embeddings.openai_client') as mock_client:
        mock_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        embeddings = await generate_embeddings(text)
        
        assert len(embeddings) == 1536
        assert all(isinstance(x, float) for x in embeddings)


@pytest.mark.asyncio
async def test_chunk_document():
    """Test document chunking"""
    content = "This is a test. " * 100  # Long document
    
    chunks = await chunk_document(content, chunk_size=100, overlap=20)
    
    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)  # chunk_size + overlap


@pytest.mark.asyncio
async def test_retrieve_documents(db_session):
    """Test document retrieval"""
    query = "test query"
    
    with patch('app.rag.retrieval.vector_search') as mock_search:
        mock_search.return_value = [
            {"id": "doc1", "content": "relevant content", "score": 0.9}
        ]
        
        results = await retrieve_documents(query, top_k=5)
        
        assert len(results) <= 5
        assert results[0]["score"] >= 0.0


@pytest.mark.asyncio
async def test_rag_endpoint(client: AsyncClient, auth_headers):
    """Test RAG API endpoint"""
    response = await client.post(
        "/api/rag/query",
        json={"query": "What is RAG?"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
```

**Run tests:**
```bash
cd backend
pytest --cov=app --cov-report=html --cov-report=term
```

---

### 1.3 Security Hardening

#### A. Rate Limiting & DDoS Protection
**Status:** ❌ Missing  
**Priority:** CRITICAL  
**Effort:** 4 hours

**Add to requirements.txt:**
```txt
slowapi==0.1.9
redis==5.0.1
```

**Create `backend/app/middleware/rate_limit.py`:**
```python
"""
Rate limiting middleware
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from redis import Redis
import hashlib
from typing import Callable

# Initialize Redis client
redis_client = Redis(host='localhost', port=6379, decode_responses=True)

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)


def get_user_identifier(request: Request) -> str:
    """Get unique identifier for rate limiting"""
    # Try to get user ID from auth token
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token = auth_header.replace("Bearer ", "")
        return hashlib.sha256(token.encode()).hexdigest()
    
    # Fall back to IP address
    return get_remote_address(request)


# Custom rate limit decorator
def rate_limit(limit: str):
    """
    Rate limit decorator
    Usage: @rate_limit("10/minute")
    """
    def decorator(func: Callable):
        return limiter.limit(limit, key_func=get_user_identifier)(func)
    return decorator


# Rate limit tiers
RATE_LIMITS = {
    "free": "100/hour",
    "pro": "1000/hour",
    "enterprise": "10000/hour"
}


async def check_rate_limit(request: Request, tier: str = "free"):
    """Check if request exceeds rate limit"""
    identifier = get_user_identifier(request)
    limit = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
    
    # Implement token bucket algorithm
    key = f"rate_limit:{identifier}"
    current = redis_client.get(key)
    
    if current is None:
        redis_client.setex(key, 3600, 1)
        return True
    
    if int(current) >= int(limit.
