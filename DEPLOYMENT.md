# 🚀 Deployment Guide - DashboardX

Complete guide to deploy DashboardX on various cloud platforms.

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Platform-Specific Guides](#platform-specific-guides)
  - [Replit](#replit)
  - [Render](#render)
  - [Vercel](#vercel)
  - [Railway](#railway)
  - [DigitalOcean](#digitalocean)
  - [AWS](#aws)
  - [Google Cloud](#google-cloud)
  - [Docker](#docker)
- [Database Setup](#database-setup)
- [Production Checklist](#production-checklist)

---

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- Supabase account (for database & auth)
- OpenAI API key

### Environment Setup

1. **Copy environment files:**
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   ```

2. **Configure environment variables** (see [Environment Variables](#environment-variables))

3. **Install dependencies:**
   ```bash
   npm install
   cd backend && pip install -r requirements.txt
   ```

4. **Run database migrations** on Supabase

5. **Start development:**
   ```bash
   npm run dev
   ```

---

## 🔐 Environment Variables

### Frontend (.env)

```env
# Supabase
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# Backend API
VITE_BACKEND_URL=http://localhost:8000

# Optional: CopilotKit
VITE_COPILOTKIT_PUBLIC_KEY=your-key
```

### Backend (backend/.env)

```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key

# Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_CHAT_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_CORS_ORIGINS=["http://localhost:5173"]

# RAG Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_DOCUMENTS=5
ENABLE_STREAMING=true

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

---

## 🌐 Platform-Specific Guides

### Replit

**Deployment Type:** Full-stack on single container

1. **Import Repository:**
   - Click "Import from GitHub"
   - Connect your repository

2. **Configure Secrets:**
   - Go to "Secrets" tab
   - Add all environment variables

3. **Deploy:**
   - Click "Deploy"
   - Select "Autoscale" deployment

4. **Access:**
   - Frontend: `https://your-repl.your-username.repl.co`
   - Backend API: `https://your-repl.your-username.repl.co/api`

**Files:** `.replit` (already configured)

---

### Render

**Deployment Type:** Separate frontend and backend services

1. **Create Blueprint:**
   - Go to Render Dashboard
   - Click "New" → "Blueprint"
   - Connect your repository
   - Select `render.yaml`

2. **Configure Environment Variables:**
   - Backend service: Add all backend env vars
   - Frontend service: Add frontend env vars
   - Update `BACKEND_CORS_ORIGINS` to include frontend URL

3. **Deploy:**
   - Render will automatically deploy both services

4. **Access:**
   - Frontend: `https://dashboardx-frontend.onrender.com`
   - Backend: `https://dashboardx-backend.onrender.com`

**Files:** `render.yaml` (already configured)

**Free Tier:** ✅ Available with limitations

---

### Vercel

**Deployment Type:** Frontend only (backend needs separate hosting)

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Configure Environment Variables:**
   - Go to Project Settings
   - Add all `VITE_*` variables
   - Set `VITE_BACKEND_URL` to your backend URL

4. **Redeploy:**
   ```bash
   vercel --prod
   ```

**Note:** Deploy backend separately on Render, Railway, or AWS

**Files:** `vercel.json` (already configured)

**Free Tier:** ✅ Available

---

### Railway

**Deployment Type:** Full-stack with multiple services

1. **Create New Project:**
   - Go to Railway Dashboard
   - Click "New Project" → "Deploy from GitHub"

2. **Add Services:**
   - Add "Backend" service (Python)
   - Add "Frontend" service (Node.js)

3. **Configure Backend:**
   - **Build Command:** `cd backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables

4. **Configure Frontend:**
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm run start`
   - Add environment variables
   - Set `VITE_BACKEND_URL` to backend service URL

5. **Deploy:**
   - Railway auto-deploys on push

**Files:** `railway.json` (already configured)

**Free Tier:** ✅ $5/month credit

---

### DigitalOcean

**Deployment Type:** Docker containers on App Platform

1. **Create App:**
   - Go to DigitalOcean App Platform
   - Click "Create App"
   - Connect GitHub repository

2. **Configure Components:**

   **Backend Component:**
   - **Type:** Docker
   - **Dockerfile:** `Dockerfile.backend`
   - **HTTP Port:** 8000
   - Add environment variables

   **Frontend Component:**
   - **Type:** Docker
   - **Dockerfile:** `Dockerfile.frontend`
   - **HTTP Port:** 80
   - Add environment variables

3. **Deploy:**
   - Click "Create Resources"

**Docker Files:** `Dockerfile.backend`, `Dockerfile.frontend` (already configured)

**Free Tier:** ❌ Starts at $5/month

---

### AWS

#### Option 1: ECS with Fargate (Recommended)

1. **Build Docker Images:**
   ```bash
   docker build -f Dockerfile.backend -t dashboardx-backend .
   docker build -f Dockerfile.frontend -t dashboardx-frontend .
   ```

2. **Push to ECR:**
   ```bash
   aws ecr create-repository --repository-name dashboardx-backend
   aws ecr create-repository --repository-name dashboardx-frontend

   # Tag and push
   docker tag dashboardx-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/dashboardx-backend
   docker push <account>.dkr.ecr.<region>.amazonaws.com/dashboardx-backend
   ```

3. **Create ECS Task Definition:**
   - Define backend and frontend containers
   - Set environment variables
   - Configure networking

4. **Create ECS Service:**
   - Select Fargate launch type
   - Configure load balancer
   - Set auto-scaling

#### Option 2: Elastic Beanstalk

1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize:**
   ```bash
   eb init -p docker dashboardx
   ```

3. **Create Environment:**
   ```bash
   eb create dashboardx-prod
   ```

4. **Deploy:**
   ```bash
   eb deploy
   ```

**Free Tier:** ✅ 12 months free tier available

---

### Google Cloud

#### Cloud Run (Recommended)

1. **Build Images:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/dashboardx-backend -f Dockerfile.backend
   gcloud builds submit --tag gcr.io/PROJECT-ID/dashboardx-frontend -f Dockerfile.frontend
   ```

2. **Deploy Backend:**
   ```bash
   gcloud run deploy dashboardx-backend \
     --image gcr.io/PROJECT-ID/dashboardx-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Deploy Frontend:**
   ```bash
   gcloud run deploy dashboardx-frontend \
     --image gcr.io/PROJECT-ID/dashboardx-frontend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

4. **Set Environment Variables:**
   ```bash
   gcloud run services update dashboardx-backend \
     --set-env-vars SUPABASE_URL=...,OPENAI_API_KEY=...
   ```

**Free Tier:** ✅ 2 million requests/month

---

### Docker

**Local or Self-Hosted Deployment**

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. **Build and Run:**
   ```bash
   docker-compose up -d
   ```

3. **Access:**
   - Frontend: `http://localhost:80`
   - Backend: `http://localhost:8000`

4. **View Logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Stop:**
   ```bash
   docker-compose down
   ```

**Files:** `docker-compose.yml` (already configured)

---

## 🗄️ Database Setup

### Supabase (Recommended)

1. **Create Project:**
   - Go to [supabase.com](https://supabase.com)
   - Create new project

2. **Run Migrations:**
   - Go to SQL Editor
   - Run migrations from `supabase/migrations/` in order:
     1. `20251022174515_create_initial_schema_with_vector_support.sql`
     2. `20240115000000_add_user_management_and_admin.sql`
     3. `20240115000001_setup_admin_user.sql`
     4. `20240120000000_create_agent_management_tables.sql`

3. **Enable Extensions:**
   - Enable `pgvector` extension
   - Enable `uuid-ossp` extension

4. **Get Credentials:**
   - Project URL: Settings → API
   - Anon Key: Settings → API
   - Service Key: Settings → API (keep secret!)

---

## ✅ Production Checklist

### Security

- [ ] Change all default secrets and keys
- [ ] Use strong JWT_SECRET_KEY (min 32 characters)
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS origins correctly
- [ ] Set DEBUG=false in production
- [ ] Enable Supabase RLS policies
- [ ] Use environment variables for all secrets
- [ ] Regular security updates

### Performance

- [ ] Enable gzip compression
- [ ] Configure CDN for static assets
- [ ] Set up database connection pooling
- [ ] Enable Redis caching (optional)
- [ ] Configure rate limiting
- [ ] Set appropriate cache headers
- [ ] Monitor application performance

### Monitoring

- [ ] Set up error tracking (Sentry)
- [ ] Configure application logging
- [ ] Set up health check endpoints
- [ ] Monitor resource usage
- [ ] Set up alerts for errors
- [ ] Configure backup strategy

### Testing

- [ ] Test all API endpoints
- [ ] Verify WebSocket connections
- [ ] Test file uploads
- [ ] Verify authentication flow
- [ ] Test across browsers
- [ ] Mobile responsiveness check
- [ ] Load testing

---

## 🔧 Troubleshooting

### Common Issues

**CORS Errors:**
- Update `BACKEND_CORS_ORIGINS` to include your frontend URL
- Ensure protocol (http/https) matches

**Database Connection:**
- Verify Supabase credentials
- Check if pgvector extension is enabled
- Ensure migrations have run

**Build Failures:**
- Clear node_modules and reinstall
- Check Node.js and Python versions
- Verify all environment variables are set

**WebSocket Not Connecting:**
- Check WebSocket proxy configuration
- Verify backend URL is correct
- Check CORS settings

---

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Documentation](https://docs.docker.com/)

---

## 🆘 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/siwaht/dashboardx/issues)
- Documentation: Check this guide and README.md

---

**Made with ❤️ for multi-cloud deployment**
