# Agentic RAG Platform - Setup Guide

## 🚀 Quick Start Guide

This guide will help you set up and run the Agentic RAG Platform locally.

---

## 📋 Prerequisites

### Required Software
- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.10 or higher) - [Download](https://www.python.org/)
- **Git** - [Download](https://git-scm.com/)
- **Supabase Account** - [Sign up](https://supabase.com/)

### Optional Tools
- **VS Code** - Recommended IDE
- **Postman** - For API testing

---

## 🗄️ Database Setup (Supabase)

### Step 1: Create Supabase Project
1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Click "New Project"
3. Fill in project details:
   - **Name**: agentic-rag-platform
   - **Database Password**: (save this securely)
   - **Region**: Choose closest to you
4. Wait for project to be created (~2 minutes)

### Step 2: Get API Keys
1. Go to **Settings** → **API**
2. Copy the following:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key**
   - **service_role key** (keep this secret!)

### Step 3: Enable pgvector Extension
1. Go to **Database** → **Extensions**
2. Search for "vector"
3. Enable **pgvector** extension

### Step 4: Run Database Migrations

#### Option A: Using Supabase SQL Editor
1. Go to **SQL Editor** in Supabase Dashboard
2. Click "New Query"
3. Copy contents of `supabase/migrations/20251022174515_create_initial_schema_with_vector_support.sql`
4. Paste and run
5. Repeat for `supabase/migrations/20240115000000_add_user_management_and_admin.sql`

#### Option B: Using Supabase CLI (Advanced)
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Run migrations
supabase db push
```

### Step 5: Create Storage Bucket
1. Go to **Storage** in Supabase Dashboard
2. Click "New Bucket"
3. Name: `documents`
4. Set to **Public** bucket
5. Click "Create Bucket"

### Step 6: Configure Storage Policies
1. Click on the `documents` bucket
2. Go to **Policies** tab
3. Add the following policies:

**Policy 1: Allow authenticated users to upload**
```sql
CREATE POLICY "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'documents');
```

**Policy 2: Allow public read access**
```sql
CREATE POLICY "Allow public read"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'documents');
```

**Policy 3: Allow users to delete their own files**
```sql
CREATE POLICY "Allow users to delete own files"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
```

---

## 🔧 Frontend Setup

### Step 1: Install Dependencies
```bash
# Navigate to project root
cd dashboardx

# Install Node.js dependencies
npm install
```

### Step 2: Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your values
```

Edit `.env` file:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
VITE_BACKEND_URL=http://localhost:8000
```

### Step 3: Verify TypeScript Configuration
```bash
# Run type checking
npm run typecheck
```

Should complete without errors.

### Step 4: Start Development Server
```bash
# Start Vite dev server
npm run dev
```

Frontend should be available at: **http://localhost:5173**

---

## 🐍 Backend Setup

### Step 1: Create Virtual Environment
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Python Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn
- LangChain & LangGraph
- LlamaIndex
- Supabase client
- OpenAI SDK
- And more...

### Step 3: Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your values
```

Edit `backend/.env` file:
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# JWT (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-generated-secret-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true
BACKEND_CORS_ORIGINS=["http://localhost:5173"]

# Logging
LOG_LEVEL=INFO
DEBUG=true
```

### Step 4: Generate JWT Secret Key
```bash
# Generate a secure secret key
openssl rand -hex 32

# Copy the output and paste it as JWT_SECRET_KEY in .env
```

### Step 5: Start Backend Server
```bash
# Make sure you're in the backend directory with venv activated
python -m app.main
```

Backend should be available at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

---

## 👤 Create Admin User

### Option 1: Using Supabase Dashboard
1. Go to **Authentication** → **Users**
2. Click "Add User"
3. Enter email and password
4. Click "Create User"
5. Go to **Table Editor** → **profiles**
6. Find the user's profile
7. Edit the row:
   - Set `role` to `admin`
   - Set `is_active` to `true`
8. Save changes

### Option 2: Using SQL
```sql
-- First, create the user in Supabase Auth UI
-- Then run this SQL to make them admin:

UPDATE profiles
SET role = 'admin', is_active = true
WHERE email = 'your-admin-email@example.com';
```

---

## ✅ Verify Installation

### 1. Check Frontend
- [ ] Navigate to http://localhost:5173
- [ ] Should see login page
- [ ] No console errors in browser DevTools

### 2. Check Backend
- [ ] Navigate to http://localhost:8000/health
- [ ] Should see: `{"status": "healthy", ...}`
- [ ] Navigate to http://localhost:8000/docs
- [ ] Should see API documentation

### 3. Test Authentication
- [ ] Try signing up with a new account
- [ ] Verify email confirmation (if enabled)
- [ ] Try signing in
- [ ] Should redirect to dashboard

### 4. Test Admin Features
- [ ] Log in as admin user
- [ ] Navigate to "Users" page
- [ ] Should see list of users
- [ ] Try creating a new user

### 5. Test Document Upload
- [ ] Navigate to "Documents" page
- [ ] Click "Upload Document"
- [ ] Select a file (PDF, DOCX, TXT)
- [ ] Fill in title and description
- [ ] Click Upload
- [ ] Verify file appears in list
- [ ] Check Supabase Storage to confirm file uploaded

---

## 🐛 Troubleshooting

### Frontend Issues

#### "Missing Supabase environment variables"
**Solution:** Make sure `.env` file exists in project root with correct values

#### "Failed to fetch" errors
**Solution:** 
- Check backend is running on http://localhost:8000
- Verify CORS settings in `backend/app/main.py`
- Check `VITE_BACKEND_URL` in `.env`

#### TypeScript errors
**Solution:**
```bash
npm run typecheck
# Fix any reported errors
```

### Backend Issues

#### "Module not found" errors
**Solution:**
```bash
# Make sure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

#### "Supabase service role key not configured"
**Solution:** Add `SUPABASE_SERVICE_KEY` to `backend/.env`

#### "OpenAI API key not found"
**Solution:** Add `OPENAI_API_KEY` to `backend/.env`

#### Port already in use
**Solution:**
```bash
# Change port in backend/.env
BACKEND_PORT=8001

# Or kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### Database Issues

#### "relation does not exist"
**Solution:** Run database migrations again

#### "pgvector extension not found"
**Solution:** Enable pgvector extension in Supabase Dashboard

#### "permission denied for table"
**Solution:** Check RLS policies are correctly configured

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Use strong JWT secret key
- [ ] Enable RLS on all Supabase tables
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up proper backup strategy
- [ ] Configure rate limiting
- [ ] Enable Supabase Auth email confirmation
- [ ] Review and test all security policies
- [ ] Set up monitoring and logging

---

## 📚 Next Steps

After successful setup:

1. **Read the Documentation**
   - Review `VERIFICATION_CHECKLIST.md`
   - Check `TODO.md` for development roadmap
   - Read `IMPLEMENTATION_PLAN.md` for architecture details

2. **Test Core Features**
   - Authentication flow
   - User management
   - Document upload
   - Chat interface

3. **Continue Development**
   - Implement RAG pipeline (Phase 2)
   - Add LangGraph agents (Phase 3)
   - Integrate CopilotKit (Phase 4)
   - Add streaming (Phase 6)

4. **Deploy to Production**
   - Choose hosting provider (Vercel, AWS, etc.)
   - Set up CI/CD pipeline
   - Configure production environment
   - Set up monitoring

---

## 🆘 Getting Help

### Resources
- **Documentation**: Check all `.md` files in project root
- **API Docs**: http://localhost:8000/docs (when backend is running)
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/

### Common Commands

```bash
# Frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run typecheck    # Check TypeScript types
npm run lint         # Run ESLint

# Backend
python -m app.main   # Start backend server
pytest               # Run tests (when implemented)
black .              # Format code
ruff check .         # Lint code

# Database
supabase db push     # Apply migrations
supabase db reset    # Reset database (careful!)
```

---

## ✨ Success!

If you've completed all steps, you should have:
- ✅ Frontend running on http://localhost:5173
- ✅ Backend running on http://localhost:8000
- ✅ Database configured with migrations applied
- ✅ Admin user created
- ✅ Able to sign in and access dashboard
- ✅ Document upload working

**You're ready to start developing!** 🎉

---

**Last Updated:** 2024-01-XX
**Version:** 1.0.0
