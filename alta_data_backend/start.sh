#!/bin/bash

# Alta Data Backend Startup Script
# This script starts all services for the hybrid architecture
# Works with or without external services (Google Cloud, Email, etc.)

set -e

echo "🚀 Starting Alta Data Backend with Hybrid Architecture..."

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
    echo "📝 .env file not found. Creating from env.example..."
    cp env.example .env
    echo "✅ Created .env file. You can edit it to configure external services."
    echo "   The application will run with minimal configuration by default."
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to check if external services are configured
check_external_services() {
    echo "🔍 Checking external service configuration..."
    
    local services_configured=0
    local total_services=4
    
    # Check Google Cloud Storage
    if [ -n "$GCS_PROJECT_ID" ] && [ -n "$GCS_BUCKET_NAME" ]; then
        echo "✅ Google Cloud Storage: Configured"
        services_configured=$((services_configured + 1))
    else
        echo "⚠️  Google Cloud Storage: Not configured (will use local storage)"
    fi
    
    # Check Document AI
    if [ -n "$DOCUMENT_AI_PROCESSOR_ID" ]; then
        echo "✅ Document AI: Configured"
        services_configured=$((services_configured + 1))
    else
        echo "⚠️  Document AI: Not configured (OCR will be skipped)"
    fi
    
    # Check Email
    if [ -n "$SMTP_HOST" ] && [ -n "$SMTP_PORT" ]; then
        echo "✅ Email Service: Configured"
        services_configured=$((services_configured + 1))
    else
        echo "⚠️  Email Service: Not configured (emails will be skipped)"
    fi
    
    # Check Speech-to-Text (depends on GCS)
    if [ -n "$GCS_PROJECT_ID" ]; then
        echo "✅ Speech-to-Text: Available (requires GCS)"
        services_configured=$((services_configured + 1))
    else
        echo "⚠️  Speech-to-Text: Not available (requires GCS configuration)"
    fi
    
    echo ""
    echo "📊 External Services Status: $services_configured/$total_services configured"
    
    if [ $services_configured -eq 0 ]; then
        echo "ℹ️  Running in minimal mode - core functionality only"
    elif [ $services_configured -lt $total_services ]; then
        echo "ℹ️  Running in partial mode - some features may be limited"
    else
        echo "ℹ️  Running in full mode - all features available"
    fi
    echo ""
}

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

# Check external services configuration
check_external_services

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

echo "✅ All core services are ready!"

# Check service health
echo "🏥 Checking service health..."
sleep 5

# Check API health
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is healthy"
else
    echo "⚠️  API health check failed"
fi

# Check external services health
echo "🔍 Checking external services health..."
if curl -s http://localhost:8000/health/services > /dev/null; then
    echo "✅ External services health check available"
    echo "   Run: curl http://localhost:8000/health/services"
else
    echo "⚠️  External services health check failed"
fi

# Show service URLs
echo ""
echo "🌐 Service URLs:"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo "   Services Status: http://localhost:8000/health/services"
echo "   RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "   Flower (Celery Monitor): http://localhost:5555"
echo ""

# Show usage instructions
echo "📖 Quick Start Guide:"
echo "   1. Register a user: POST http://localhost:8000/api/auth/register"
echo "   2. Create a project: POST http://localhost:8000/api/projects"
echo "   3. Upload documents: POST http://localhost:8000/api/documents"
echo "   4. Check service status: GET http://localhost:8000/health/services"
echo ""

# Show logs
echo "📋 Showing logs (Ctrl+C to stop)..."
echo "   To stop all services: docker-compose down"
echo "   To restart: ./start.sh"
echo ""
docker-compose logs -f
