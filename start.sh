#!/bin/bash

# DashboardX Universal Startup Script
# Works on Replit, Render, Railway, Vercel, AWS, GCP, DigitalOcean, and more

set -e

echo "🚀 Starting DashboardX..."

# Detect environment
if [ -n "$REPL_SLUG" ]; then
    ENV="replit"
    echo "📍 Detected environment: Replit"
elif [ -n "$RENDER" ]; then
    ENV="render"
    echo "📍 Detected environment: Render"
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    ENV="railway"
    echo "📍 Detected environment: Railway"
elif [ -n "$VERCEL" ]; then
    ENV="vercel"
    echo "📍 Detected environment: Vercel"
elif [ -n "$AWS_EXECUTION_ENV" ]; then
    ENV="aws"
    echo "📍 Detected environment: AWS"
elif [ -n "$K_SERVICE" ]; then
    ENV="gcp"
    echo "📍 Detected environment: Google Cloud"
elif [ -n "$DOCKER_CONTAINER" ]; then
    ENV="docker"
    echo "📍 Detected environment: Docker"
else
    ENV="local"
    echo "📍 Detected environment: Local"
fi

# Set default port
PORT=${PORT:-5173}
BACKEND_PORT=${BACKEND_PORT:-8000}

echo "🔧 Configuration:"
echo "   Frontend Port: $PORT"
echo "   Backend Port: $BACKEND_PORT"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env || echo "Note: Please configure your .env file"
fi

if [ ! -f "backend/.env" ]; then
    echo "⚠️  No backend/.env file found. Copying from backend/.env.example..."
    cp backend/.env.example backend/.env || echo "Note: Please configure your backend/.env file"
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Build frontend if not in development
if [ "$NODE_ENV" = "production" ]; then
    echo "🏗️  Building frontend..."
    npm run build
fi

# Start application based on environment
case $ENV in
    replit|local)
        echo "🎯 Starting full-stack application..."
        npm run dev
        ;;
    render|railway|docker)
        echo "🎯 Starting production server..."
        npm run start
        ;;
    aws|gcp)
        echo "🎯 Starting containerized application..."
        npm run start
        ;;
    vercel)
        echo "🎯 Building for serverless deployment..."
        npm run build
        ;;
    *)
        echo "🎯 Starting default configuration..."
        npm run dev
        ;;
esac
