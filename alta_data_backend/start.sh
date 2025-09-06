#!/bin/bash

# Alta Data Backend Startup Script
# This script starts all services for the hybrid architecture

set -e

echo "🚀 Starting Alta Data Backend with Hybrid Architecture..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy env.example to .env and configure it."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to check if a service is running
check_service() {
    local service_name=$1
    local host=$2
    local port=$3
    
    echo "🔍 Checking $service_name..."
    if nc -z $host $port 2>/dev/null; then
        echo "✅ $service_name is running on $host:$port"
        return 0
    else
        echo "❌ $service_name is not running on $host:$port"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_service "$service_name" "$host" "$port"; then
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Start services with Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL
wait_for_service "PostgreSQL" "$POSTGRES_HOST" "$POSTGRES_PORT"

# Wait for Redis
wait_for_service "Redis" "$REDIS_HOST" "$REDIS_PORT"

# Wait for RabbitMQ
wait_for_service "RabbitMQ" "$RABBITMQ_HOST" "$RABBITMQ_PORT"

# Wait for API
wait_for_service "API" "localhost" "8000"

echo "✅ All services are ready!"

# Show service URLs
echo ""
echo "🌐 Service URLs:"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo "   RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "   Flower (Celery Monitor): http://localhost:5555"
echo ""

# Show logs
echo "📋 Showing logs (Ctrl+C to stop)..."
docker-compose logs -f
