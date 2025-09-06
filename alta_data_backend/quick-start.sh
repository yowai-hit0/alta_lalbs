#!/bin/bash

# Alta Data Backend Quick Start Script
# This script provides the fastest way to get the application running

set -e

echo "🚀 Alta Data Backend - Quick Start"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   Windows/Mac: https://www.docker.com/products/docker-desktop"
    echo "   Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists, create if not
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file with minimal configuration"
    echo "   (No external services configured - app will run in minimal mode)"
else
    echo "✅ .env file already exists"
fi

echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start the application
echo "🐳 Starting Alta Data Backend..."
echo "   This will start:"
echo "   - PostgreSQL database"
echo "   - Redis cache"
echo "   - RabbitMQ message queue"
echo "   - FastAPI application"
echo "   - Celery background workers"
echo ""

# Start with Docker Compose
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running"
else
    echo "⚠️  API is starting up (this may take a moment)"
fi

# Check database
if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Database is running"
else
    echo "⚠️  Database is starting up"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is starting up"
fi

echo ""
echo "🎉 Alta Data Backend is starting up!"
echo ""
echo "🌐 Access your application:"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo "   Services Status: http://localhost:8000/health/services"
echo ""
echo "📊 Management Interfaces:"
echo "   RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "   Flower (Celery Monitor): http://localhost:5555"
echo ""
echo "🧪 Quick Test:"
echo "   curl http://localhost:8000/health"
echo ""
echo "📋 Useful Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Full restart: docker-compose down && docker-compose up -d"
echo ""
echo "📖 For more information, see: HOW_TO_RUN.md"
echo ""
echo "⏳ Services are starting up. You can check the status at:"
echo "   http://localhost:8000/health/services"
echo ""
echo "Press Ctrl+C to stop viewing logs, or wait for services to fully start..."

# Show logs for a few seconds, then exit
timeout 30 docker-compose logs -f 2>/dev/null || true

echo ""
echo "✅ Quick start complete! Your Alta Data Backend is running."
echo "   Visit http://localhost:8000/docs to explore the API"
