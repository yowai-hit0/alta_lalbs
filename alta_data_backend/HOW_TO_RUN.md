# How to Run Alta Data Backend

### **Dummy Guide for celia**


docker-compose up --build  -d //starts and builds the app + apply changes made to the code + initial load takes time
docker-compose down //stops the services (ddo this everytime before you run the above command)
docker-compose logs <service-name> //show the logs for the service running ex:  docker-compose logs worker-email or  docker-compose logs api


## 🎯 Quick Start (Minimal Setup)

### **Prerequisites**
- Docker and Docker Compose installed
- Git (to clone the repository)

### **1. Clone and Start**
```bash
# Clone the repository
git clone <your-repo-url>
cd alta_data_backend

# Start with minimal configuration (no external services)
./start.sh
```

That's it! The application will:
- ✅ Create a `.env` file from `env.example`
- ✅ Start all required services (PostgreSQL, Redis, RabbitMQ)
- ✅ Run the FastAPI application
- ✅ Work without any external service configuration

## 🚀 Different Setup Options

### **Option 1: Development Mode (Recommended for Development)**
Perfect for active development with hot reload, debugging, and full control over the environment.

```bash
# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or use the development script
./dev-start.sh
```

**Development Features:**
- ✅ **Hot Reload**: Code changes automatically restart the API
- ✅ **Debug Mode**: Enhanced logging and error details
- ✅ **Volume Mounting**: Local code changes reflect immediately
- ✅ **Development Tools**: Debugger support, enhanced logging
- ✅ **All Services**: Full functionality with external services
- ✅ **Database Persistence**: Data persists between restarts
- ✅ **Worker Debugging**: Enhanced worker logging and monitoring

**What works:**
- ✅ User registration and authentication
- ✅ Project creation and management
- ✅ Document and voice uploads (with GCS if configured)
- ✅ Raw text creation and management
- ✅ Review workflow
- ✅ All API endpoints
- ✅ OCR processing (if Document AI configured)
- ✅ Speech-to-text transcription (if configured)
- ✅ Email notifications (if SMTP configured)
- ✅ Cloud storage (if GCS configured)

### **Option 2: Minimal Setup (No External Services)**
Perfect for testing or when you don't have Google Cloud credentials.

```bash
# Just run the start script
./start.sh
```

**What works:**
- ✅ User registration and authentication
- ✅ Project creation and management
- ✅ Document and voice uploads (stored locally)
- ✅ Raw text creation and management
- ✅ Review workflow
- ✅ All API endpoints

**What doesn't work:**
- ❌ OCR processing (documents won't be processed)
- ❌ Speech-to-text transcription
- ❌ Email notifications
- ❌ Cloud storage (files stored locally)

### **Option 2: Partial Setup (Some External Services)**
Configure only the services you need.

```bash
# Edit .env file to add only the services you want
nano .env

# Example: Add email service only
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com

# Start the application
./start.sh
```

### **Option 3: Full Setup (All External Services)**
Complete setup with all Google Cloud services and email.

```bash
# Follow the Google Cloud setup guide
# See: GOOGLE_CLOUD_SETUP.md

# Configure all services in .env
nano .env

# Start the application
./start.sh
```

## 📋 System Requirements

### **Minimum Requirements**
- **RAM**: 2GB
- **Storage**: 5GB free space
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### **Recommended Requirements**
- **RAM**: 4GB+
- **Storage**: 10GB+ free space
- **CPU**: 2+ cores

## 🛠️ Installation Methods

### **Method 1: Docker Compose (Recommended)**

#### **Windows**
```powershell
# Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Start application
./start.sh
```

#### **macOS**
```bash
# Install Docker Desktop for Mac
# Download from: https://www.docker.com/products/docker-desktop

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Make script executable
chmod +x start.sh

# Start application
./start.sh
```

#### **Linux (Ubuntu/Debian)**
```bash
# Install Docker
sudo apt update
sudo apt install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Make script executable
chmod +x start.sh

# Start application
./start.sh
```

#### **Linux (CentOS/RHEL)**
```bash
# Install Docker
sudo yum install docker docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Make script executable
chmod +x start.sh

# Start application
./start.sh
```

### **Method 2: Manual Setup (Advanced)**

If you prefer to run without Docker:

```bash
# Install Python 3.11+
# Install PostgreSQL 15+
# Install Redis 7+
# Install RabbitMQ 3.12+

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit configuration
nano .env

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.worker.celery_app worker --loglevel=info
```

## 🔧 Configuration

### **Environment Variables**

The application uses a `.env` file for configuration. The `start.sh` script will create this file automatically from `env.example`.

#### **Required Variables (Core Services)**
```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_URL=redis://localhost:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672//

# Application
SECRET_KEY=your-super-secret-key-change-this-in-production
```

#### **Optional Variables (External Services)**
```env
# Google Cloud Storage (leave empty to disable)
GCS_PROJECT_ID=
GCS_BUCKET_NAME=
GOOGLE_APPLICATION_CREDENTIALS=

# Document AI (leave empty to disable)
DOCUMENT_AI_PROCESSOR_ID=
DOCUMENT_AI_LOCATION=us

# Email Service (leave empty to disable)
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
```

### **Configuration Examples**

#### **Development (Minimal)**
```env
# Core services only
POSTGRES_HOST=localhost
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672//
SECRET_KEY=dev-secret-key

# All external services disabled
GCS_PROJECT_ID=
DOCUMENT_AI_PROCESSOR_ID=
SMTP_HOST=
```

#### **Production (Full)**
```env
# Core services
POSTGRES_HOST=your-db-host
POSTGRES_DB=alta_data
POSTGRES_USER=alta_user
POSTGRES_PASSWORD=secure-password
REDIS_URL=redis://your-redis-host:6379/0
RABBITMQ_URL=amqp://user:pass@your-rabbitmq-host:5672//
SECRET_KEY=your-super-secure-secret-key

# Google Cloud Services
GCS_PROJECT_ID=your-gcp-project
GCS_BUCKET_NAME=your-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
DOCUMENT_AI_PROCESSOR_ID=your-processor-id

# Email Service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

## 🛠️ Development Mode

### **Development Setup**

Development mode provides enhanced debugging, hot reload, and development tools for active development.

#### **Prerequisites for Development**
- Docker and Docker Compose installed
- Git (to clone the repository)
- Code editor with Docker support (VS Code, PyCharm, etc.)

#### **Quick Start Development**
```bash
# Clone the repository
git clone <your-repo-url>
cd alta_data_backend

# Create development configuration files
cp docker-compose.dev.yml.example docker-compose.dev.yml
cp .env.dev.example .env.dev

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or use the development script (if available)
./dev-start.sh
```

#### **Creating Development Files**

If the development files don't exist, create them:

**1. Create `docker-compose.dev.yml`:**
```bash
# Copy the example or create from scratch
cp docker-compose.dev.yml.example docker-compose.dev.yml
```

**2. Create `.env.dev`:**
```bash
# Copy the example or create from scratch
cp .env.dev.example .env.dev
```

**3. Create `dev-start.sh` script:**
```bash
#!/bin/bash
# Development startup script

echo "🚀 Starting Alta Data Backend in Development Mode..."

# Check if .env.dev exists
if [ ! -f .env.dev ]; then
    echo "⚠️  .env.dev not found, creating from .env..."
    cp .env .env.dev
fi

# Check if docker-compose.dev.yml exists
if [ ! -f docker-compose.dev.yml ]; then
    echo "⚠️  docker-compose.dev.yml not found, creating from example..."
    cp docker-compose.dev.yml.example docker-compose.dev.yml
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "✅ Development environment started!"
echo "📊 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo "📈 Flower: http://localhost:5555"
echo "🐰 RabbitMQ: http://localhost:15672"

# Show logs
echo "📋 Showing API logs (Ctrl+C to exit)..."
docker-compose logs -f api
```

#### **Development Features**

**Hot Reload & Live Updates:**
- ✅ Code changes automatically restart the API container
- ✅ Volume mounting ensures local changes reflect immediately
- ✅ No need to rebuild containers for code changes
- ✅ Fast iteration cycle

**Enhanced Debugging:**
- ✅ Debug mode enabled with detailed error messages
- ✅ Enhanced logging with timestamps and context
- ✅ Stack traces for better error diagnosis
- ✅ Development-specific environment variables

**Development Tools:**
- ✅ Debugger support (VS Code, PyCharm)
- ✅ Enhanced worker logging and monitoring
- ✅ Database query logging
- ✅ Request/response logging

### **Development Configuration**

#### **Environment Variables for Development**
```env
# Development-specific settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=debug

# Enable development features
ENABLE_DEBUG_TOOLBAR=true
ENABLE_SQL_LOGGING=true
ENABLE_REQUEST_LOGGING=true

# Development database (optional - uses same as production)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=alta_data_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Development Redis
REDIS_URL=redis://localhost:6379/1

# Development RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672//

# Development secret (not for production)
SECRET_KEY=dev-secret-key-change-in-production
```

#### **Development Docker Compose Override**
Create `docker-compose.dev.yml` for development-specific overrides:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
      - RELOAD=true
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
      - "5678:5678"  # Debug port

  worker-email:
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    command: celery -A app.worker.celery_app worker --loglevel=debug --concurrency=1

  worker-ocr:
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    command: celery -A app.worker.celery_app worker --loglevel=debug --concurrency=1

  worker-transcription:
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    command: celery -A app.worker.celery_app worker --loglevel=debug --concurrency=1

  beat:
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    command: celery -A app.worker.celery_app beat --loglevel=debug
```

### **Development Workflow**

#### **Starting Development Environment**
```bash
# Start all services in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

#### **Making Code Changes**
```bash
# 1. Make your code changes
# 2. The API will automatically restart due to hot reload
# 3. Check logs to see the restart
docker-compose logs -f api

# For worker changes, restart workers
docker-compose restart worker-email worker-ocr worker-transcription
```

#### **Database Migrations in Development**
```bash
# Create a new migration
docker-compose exec api alembic revision --autogenerate -m "Add new feature"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1
```

#### **Testing in Development**
```bash
# Run tests
docker-compose exec api python -m pytest

# Run specific test
docker-compose exec api python -m pytest tests/test_auth.py

# Run tests with coverage
docker-compose exec api python -m pytest --cov=app
```

### **Development Debugging**

#### **API Debugging**
```bash
# View API logs with debug info
docker-compose logs -f api

# Check API health
curl http://localhost:8000/health

# Check service status
curl http://localhost:8000/health/services
```

#### **Worker Debugging**
```bash
# View worker logs
docker-compose logs -f worker-email

# Check worker status
docker-compose exec worker-email celery -A app.worker.celery_app inspect active

# Check registered tasks
docker-compose exec worker-email celery -A app.worker.celery_app inspect registered
```

#### **Database Debugging**
```bash
# Connect to development database
docker-compose exec db psql -U postgres -d alta_data_dev

# Check outbox events
docker-compose exec db psql -U postgres -d alta_data_dev -c "SELECT * FROM outbox_events ORDER BY created_at DESC LIMIT 10;"

# Check user registrations
docker-compose exec db psql -U postgres -d alta_data_dev -c "SELECT id, email, is_verified, created_at FROM users ORDER BY created_at DESC LIMIT 5;"
```

### **Development Tools Integration**

#### **VS Code Development**
Create `.vscode/launch.json` for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app/main.py",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "APP_ENV": "development"
            },
            "args": ["--reload"]
        },
        {
            "name": "Python: Celery Worker",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app/worker/celery_app.py",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "APP_ENV": "development"
            },
            "args": ["worker", "--loglevel=debug"]
        }
    ]
}
```

#### **PyCharm Development**
1. Configure Docker Compose as interpreter
2. Set environment variables in run configuration
3. Enable debug mode
4. Set breakpoints in code

### **Development Best Practices**

#### **Code Organization**
```bash
# Keep development and production configs separate
docker-compose.yml          # Production config
docker-compose.dev.yml      # Development overrides
.env                        # Production environment
.env.dev                    # Development environment
```

#### **Git Workflow**
```bash
# Use development branch
git checkout -b feature/new-feature

# Make changes and test
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Commit changes
git add .
git commit -m "Add new feature"

# Push to remote
git push origin feature/new-feature
```

#### **Environment Management**
```bash
# Switch between environments
cp .env.dev .env              # Development
cp .env.prod .env             # Production

# Restart with new environment
docker-compose down
docker-compose up -d
```

### **Development Troubleshooting**

#### **Hot Reload Not Working**
```bash
# Check if volumes are mounted correctly
docker-compose exec api ls -la /app

# Restart API container
docker-compose restart api

# Check file permissions
docker-compose exec api ls -la /app/app/
```

#### **Workers Not Updating**
```bash
# Restart workers after code changes
docker-compose restart worker-email worker-ocr worker-transcription

# Check worker logs
docker-compose logs worker-email
```

#### **Database Issues**
```bash
# Reset development database
docker-compose down
docker volume rm alta_data_postgres_data
docker-compose up -d db
sleep 10
docker-compose exec api alembic upgrade head
```

## 🌐 Accessing the Application

Once started, the application will be available at:

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Services Status**: http://localhost:8000/health/services
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **Flower (Celery Monitor)**: http://localhost:5555

## 📊 Service Status

### **Check Service Health**
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed service status
curl http://localhost:8000/health/services
```

### **Expected Responses**

#### **All Services Available**
```json
{
  "status": "all_services_available",
  "services": {
    "google_cloud_storage": {"available": true},
    "document_ai": {"available": true},
    "speech_to_text": {"available": true},
    "email": {"available": true}
  }
}
```

#### **Some Services Unavailable**
```json
{
  "status": "some_services_unavailable",
  "services": {
    "google_cloud_storage": {"available": false, "status": "not_configured"},
    "document_ai": {"available": false, "status": "not_configured"},
    "speech_to_text": {"available": false, "status": "not_configured"},
    "email": {"available": false, "status": "not_configured"}
  },
  "message": "Some services are not configured but the application will continue to run"
}
```

## 🧪 Testing the Application

### **1. Register a User**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### **2. Create a Project**
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "My test project"
  }'
```

### **3. Upload a Document**
```bash
curl -X POST "http://localhost:8000/api/documents?project_id=PROJECT_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/your/document.pdf"
```

### **4. Check Service Status**
```bash
curl http://localhost:8000/health/services
```

## 🐳 Docker Commands Reference

### **Basic Docker Operations**

#### **Production Mode**
```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d api db redis rabbitmq

# Stop all services
docker-compose down

# Stop and remove all data (WARNING: deletes database)
docker-compose down -v

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api

# Rebuild and start (after code changes)
docker-compose up --build -d

# View running containers
docker-compose ps

# View container status
docker ps
```

#### **Development Mode**
```bash
# Start in development mode (with hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start specific services in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d api db redis

# Stop development services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Restart development services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart

# Rebuild development containers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# View development containers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

# Follow development logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f api
```

### **Worker Management**

#### **Production Mode**
```bash
# Start all workers
docker-compose up -d worker-ocr worker-transcription worker-email beat

# Start specific worker
docker-compose up -d worker-email

# Restart workers
docker-compose restart worker-ocr worker-transcription worker-email

# Check worker logs
docker-compose logs worker-email
docker-compose logs worker-ocr
docker-compose logs worker-transcription
```

#### **Development Mode**
```bash
# Start all workers in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d worker-ocr worker-transcription worker-email beat

# Start specific worker in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d worker-email

# Restart development workers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart worker-ocr worker-transcription worker-email

# Check development worker logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs worker-email
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs worker-ocr
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs worker-transcription

# Follow development worker logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f worker-email
```

### **Database Operations**

#### **Production Mode**
```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Connect to database
docker-compose exec db psql -U postgres -d alta_data

# Backup database
docker-compose exec db pg_dump -U postgres alta_data > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres -d alta_data < backup.sql
```

#### **Development Mode**
```bash
# Run database migrations in development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# Create new migration in development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "description"

# Connect to development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev

# Backup development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db pg_dump -U postgres alta_data_dev > backup_dev.sql

# Restore development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T db psql -U postgres -d alta_data_dev < backup_dev.sql

# Reset development database (WARNING: deletes all data)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
docker volume rm alta_data_postgres_data
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
sleep 10
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head
```

## 📊 Logging and Monitoring

### **Viewing Logs**

#### **All Services Logs**
```bash
# Follow all logs in real-time
docker-compose logs -f

# View last 100 lines of all logs
docker-compose logs --tail=100

# View logs with timestamps
docker-compose logs -t
```

#### **Individual Service Logs**

**Production Mode:**
```bash
# API logs
docker-compose logs -f api

# Database logs
docker-compose logs -f db

# Redis logs
docker-compose logs -f redis

# RabbitMQ logs
docker-compose logs -f rabbitmq

# Worker logs
docker-compose logs -f worker-email
docker-compose logs -f worker-ocr
docker-compose logs -f worker-transcription

# Celery Beat logs
docker-compose logs -f beat

# Flower logs
docker-compose logs -f flower
```

**Development Mode:**
```bash
# API logs (with debug info)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f api

# Database logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f db

# Redis logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f redis

# RabbitMQ logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f rabbitmq

# Worker logs (with debug info)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f worker-email
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f worker-ocr
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f worker-transcription

# Celery Beat logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f beat

# Flower logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f flower
```

#### **Log Filtering and Search**

**Production Mode:**
```bash
# Search for specific text in logs
docker-compose logs | grep "ERROR"

# Search in specific service
docker-compose logs api | grep "email"

# View logs from last 10 minutes
docker-compose logs --since=10m

# View logs between specific times
docker-compose logs --since=2024-01-01T10:00:00 --until=2024-01-01T11:00:00
```

**Development Mode:**
```bash
# Search for specific text in development logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs | grep "ERROR"

# Search in specific development service
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs api | grep "email"

# View development logs from last 10 minutes
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs --since=10m

# View development logs between specific times
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs --since=2024-01-01T10:00:00 --until=2024-01-01T11:00:00

# Search for debug messages
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs | grep "DEBUG"

# Search for SQL queries (if enabled)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs api | grep "SQL"
```

### **Health Monitoring**

#### **Service Health Checks**

**Production Mode:**
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed service status
curl http://localhost:8000/health/services

# Readiness check
curl http://localhost:8000/health/ready

# Liveness check
curl http://localhost:8000/health/live
```

**Development Mode:**
```bash
# Basic health check (development)
curl http://localhost:8000/health

# Detailed service status (development)
curl http://localhost:8000/health/services

# Readiness check (development)
curl http://localhost:8000/health/ready

# Liveness check (development)
curl http://localhost:8000/health/live

# Check development environment variables
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api env | grep -E "(DEBUG|LOG_LEVEL|APP_ENV)"

# Check development database connection
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api python -c "import asyncio; from app.database import engine; print('DB OK' if asyncio.run(engine.connect()) else 'DB FAIL')"
```

#### **Queue Monitoring**

**Production Mode:**
```bash
# Check RabbitMQ management UI
open http://localhost:15672
# Username: guest, Password: guest

# Check Celery Flower (task monitoring)
open http://localhost:5555

# Check queue status via API
curl http://localhost:8000/health/services | jq '.services'
```

**Development Mode:**
```bash
# Check RabbitMQ management UI (development)
open http://localhost:15672
# Username: guest, Password: guest

# Check Celery Flower (task monitoring) (development)
open http://localhost:5555

# Check queue status via API (development)
curl http://localhost:8000/health/services | jq '.services'

# Check development worker status
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app inspect active

# Check development worker stats
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app inspect stats

# Check development outbox events
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev -c "SELECT * FROM outbox_events ORDER BY created_at DESC LIMIT 10;"
```

### **Debugging Commands**

#### **Container Debugging**

**Production Mode:**
```bash
# Execute shell in running container
docker-compose exec api bash
docker-compose exec db bash
docker-compose exec worker-email bash

# Check container resource usage
docker stats

# Inspect container configuration
docker-compose config

# Check container environment variables
docker-compose exec api env
```

**Development Mode:**
```bash
# Execute shell in running development container
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email bash

# Check development container resource usage
docker stats

# Inspect development container configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml config

# Check development container environment variables
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api env

# Check development volume mounts
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api ls -la /app

# Check development file permissions
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api ls -la /app/app/
```

#### **Database Debugging**

**Production Mode:**
```bash
# Connect to database
docker-compose exec db psql -U postgres -d alta_data

# Check database size
docker-compose exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('alta_data'));"

# Check active connections
docker-compose exec db psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Check outbox events
docker-compose exec db psql -U postgres -d alta_data -c "SELECT * FROM outbox_events ORDER BY created_at DESC LIMIT 10;"
```

**Development Mode:**
```bash
# Connect to development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev

# Check development database size
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('alta_data_dev'));"

# Check active connections in development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Check development outbox events
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev -c "SELECT * FROM outbox_events ORDER BY created_at DESC LIMIT 10;"

# Check development user registrations
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev -c "SELECT id, email, is_verified, created_at FROM users ORDER BY created_at DESC LIMIT 5;"

# Check development projects
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev -c "SELECT id, name, created_at FROM projects ORDER BY created_at DESC LIMIT 5;"

# Check development documents
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev -c "SELECT id, original_filename, status, created_at FROM documents ORDER BY created_at DESC LIMIT 5;"
```

#### **Worker Debugging**

**Production Mode:**
```bash
# Check Celery worker status
docker-compose exec worker-email celery -A app.worker.celery_app inspect active

# Check registered tasks
docker-compose exec worker-email celery -A app.worker.celery_app inspect registered

# Check worker stats
docker-compose exec worker-email celery -A app.worker.celery_app inspect stats

# Purge all queues (WARNING: deletes all pending tasks)
docker-compose exec worker-email celery -A app.worker.celery_app purge
```

**Development Mode:**
```bash
# Check development Celery worker status
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app inspect active

# Check registered tasks in development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app inspect registered

# Check development worker stats
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app inspect stats

# Purge all development queues (WARNING: deletes all pending tasks)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app purge

# Check development worker logs with debug info
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs worker-email | grep -i debug

# Check development worker environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email env | grep -E "(DEBUG|LOG_LEVEL|APP_ENV)"

# Test development worker connectivity
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app inspect ping
```

## 🚨 Troubleshooting

### **Common Issues**

#### **1. Docker Not Running**
```bash
# Check Docker status
docker --version
docker-compose --version

# Start Docker service (Linux)
sudo systemctl start docker

# Check Docker daemon
sudo systemctl status docker
```

#### **2. Port Already in Use**
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Check all ports used by the app
docker-compose ps

# Stop conflicting services or change ports in docker-compose.yml
```

#### **3. Permission Denied (Linux/macOS)**
```bash
# Make script executable
chmod +x start.sh

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in

# Check if user is in docker group
groups $USER
```

#### **4. Services Not Starting**
```bash
# Check Docker Compose logs
docker-compose logs

# Check individual service logs
docker-compose logs api
docker-compose logs db
docker-compose logs redis
docker-compose logs rabbitmq

# Check if containers are running
docker-compose ps

# Check container health
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

#### **5. Database Connection Issues**
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db

# Check database connectivity
docker-compose exec api python -c "import asyncio; from app.database import engine; print('DB OK' if asyncio.run(engine.connect()) else 'DB FAIL')"
```

#### **6. Email Service Not Working**
```bash
# Check email service status
curl http://localhost:8000/health/services | jq '.services.email'

# Check email worker logs
docker-compose logs worker-email | grep -i email

# Test email configuration
docker-compose exec api python -c "from app.core.email import is_email_available; print('Email available:', is_email_available())"

# Check outbox events for emails
docker-compose exec db psql -U postgres -d alta_data -c "SELECT * FROM outbox_events WHERE event_type = 'email_send_requested' ORDER BY created_at DESC LIMIT 5;"
```

#### **7. Workers Not Processing Tasks**
```bash
# Check worker status
docker-compose logs worker-email | tail -20

# Check RabbitMQ queues
open http://localhost:15672

# Check Celery Flower
open http://localhost:5555

# Restart workers
docker-compose restart worker-email worker-ocr worker-transcription

# Check outbox processor
docker-compose logs api | grep -i outbox
```

#### **8. File Upload Issues**
```bash
# Check GCS configuration
curl http://localhost:8000/health/services | jq '.services.google_cloud_storage'

# Check file storage logs
docker-compose logs api | grep -i "upload\|storage"

# Test file upload
curl -X POST "http://localhost:8000/api/documents?project_id=test" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.txt"
```

#### **9. Development-Specific Issues**

**Hot Reload Not Working:**
```bash
# Check if volumes are mounted correctly
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api ls -la /app

# Restart API container
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart api

# Check file permissions
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api ls -la /app/app/

# Check if development compose file exists
ls -la docker-compose.dev.yml
```

**Workers Not Updating in Development:**
```bash
# Restart development workers after code changes
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart worker-email worker-ocr worker-transcription

# Check development worker logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs worker-email

# Check if workers are using development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email env | grep DEBUG
```

**Development Database Issues:**
```bash
# Reset development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
docker volume rm alta_data_postgres_data
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
sleep 10
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# Check development database connection
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api python -c "import asyncio; from app.database import engine; print('DB OK' if asyncio.run(engine.connect()) else 'DB FAIL')"
```

**Development Environment Variables Not Loading:**
```bash
# Check if .env.dev exists
ls -la .env.dev

# Check environment variables in container
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api env | grep -E "(DEBUG|LOG_LEVEL|APP_ENV)"

# Recreate development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### **Advanced Debugging**

#### **Performance Issues**
```bash
# Check resource usage
docker stats

# Check container resource limits
docker-compose exec api cat /sys/fs/cgroup/memory/memory.limit_in_bytes

# Monitor database performance
docker-compose exec db psql -U postgres -d alta_data -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

#### **Memory Issues**
```bash
# Check memory usage
docker-compose exec api free -h
docker-compose exec db free -h

# Check for memory leaks
docker-compose logs api | grep -i "memory\|oom"

# Restart services to clear memory
docker-compose restart
```

#### **Network Issues**
```bash
# Check network connectivity
docker-compose exec api ping db
docker-compose exec api ping redis
docker-compose exec api ping rabbitmq

# Check port bindings
docker-compose port api 8000
docker-compose port db 5432
```

### **Recovery Commands**

#### **Reset Everything**
```bash
# Stop and remove everything
docker-compose down -v

# Remove all images (WARNING: will rebuild everything)
docker-compose down --rmi all

# Clean up Docker system
docker system prune -a

# Start fresh
./start.sh
```

#### **Database Recovery**
```bash
# Backup before recovery
docker-compose exec db pg_dump -U postgres alta_data > backup_before_recovery.sql

# Reset database
docker-compose down
docker volume rm alta_data_postgres_data
docker-compose up -d db
sleep 10
docker-compose exec api alembic upgrade head
```

#### **Worker Recovery**
```bash
# Restart all workers
docker-compose restart worker-email worker-ocr worker-transcription beat

# Clear failed tasks
docker-compose exec worker-email celery -A app.worker.celery_app purge

# Check worker health
docker-compose exec worker-email celery -A app.worker.celery_app inspect ping
```

#### **Development Recovery**
```bash
# Reset development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v

# Remove development images (WARNING: will rebuild everything)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --rmi all

# Clean up Docker system
docker system prune -a

# Start fresh development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# Reset development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
docker volume rm alta_data_postgres_data
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
sleep 10
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# Restart development workers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart worker-email worker-ocr worker-transcription beat

# Clear development queues
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app purge

# Check development worker health
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec worker-email celery -A app.worker.celery_app inspect ping
```

## 🔄 Managing the Application

### **Starting the Application**

#### **Production Mode**
```bash
# Start all services
./start.sh

# Or manually
docker-compose up -d
```

#### **Development Mode**
```bash
# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or use development script
./dev-start.sh
```

### **Stopping the Application**

#### **Production Mode**
```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

#### **Development Mode**
```bash
# Stop development services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop and remove all development data
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

### **Restarting the Application**

#### **Production Mode**
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
```

#### **Development Mode**
```bash
# Restart all development services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart

# Restart specific development service
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart api

# Restart development workers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart worker-email worker-ocr worker-transcription
```

### **Updating the Application**

#### **Production Mode**
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

#### **Development Mode**
```bash
# Pull latest changes
git pull

# Rebuild and restart development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# Update development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head
```

## 📱 Running on Different Devices

### **Raspberry Pi**

#### **Production Mode**
```bash
# Install Docker on Raspberry Pi OS
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker pi

# Clone and run
git clone <your-repo-url>
cd alta_data_backend
chmod +x start.sh
./start.sh
```

#### **Development Mode**
```bash
# Install Docker on Raspberry Pi OS
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker pi

# Clone and run in development mode
git clone <your-repo-url>
cd alta_data_backend
chmod +x start.sh dev-start.sh
./dev-start.sh

# Or manually start development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### **Cloud VPS (DigitalOcean, AWS, etc.)**

#### **Production Mode**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and run
git clone <your-repo-url>
cd alta_data_backend
chmod +x start.sh
./start.sh
```

#### **Development Mode**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and run in development mode
git clone <your-repo-url>
cd alta_data_backend
chmod +x start.sh dev-start.sh
./dev-start.sh

# Or manually start development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### **Windows Server**

#### **Production Mode**
```powershell
# Install Docker Desktop for Windows Server
# Download from: https://www.docker.com/products/docker-desktop

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Start application
./start.sh
```

#### **Development Mode**
```powershell
# Install Docker Desktop for Windows Server
# Download from: https://www.docker.com/products/docker-desktop

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or use development script
./dev-start.sh
```

## 🔐 Security Considerations

### **Production Deployment**
1. **Change default passwords** in `.env`
2. **Use strong SECRET_KEY**
3. **Configure proper CORS origins**
4. **Set up SSL/TLS certificates**
5. **Use environment-specific configurations**
6. **Enable firewall rules**
7. **Regular security updates**

### **Development Security**
1. **Use development-specific secrets** in `.env.dev`
2. **Enable debug mode only in development**
3. **Use separate development database**
4. **Disable production features in development**
5. **Use development-specific CORS settings**
6. **Regular security updates**

### **Environment Variables Security**

#### **Production Environment**
```env
# Use strong, unique passwords
POSTGRES_PASSWORD=your-very-strong-password-here
SECRET_KEY=your-very-long-and-random-secret-key-here

# Use environment-specific settings
APP_ENV=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### **Development Environment**
```env
# Use development-specific passwords
POSTGRES_PASSWORD=dev-password
SECRET_KEY=dev-secret-key-change-in-production

# Use development-specific settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=debug
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 📈 Performance Optimization

### **Resource Limits**

#### **Production Resource Limits**
Add resource limits to `docker-compose.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

#### **Development Resource Limits**
Add resource limits to `docker-compose.dev.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
```

### **Database Optimization**

#### **Production Database**
```yaml
services:
  db:
    environment:
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
```

#### **Development Database**
```yaml
services:
  db:
    environment:
      POSTGRES_SHARED_BUFFERS: 128MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 512MB
```

### **Development Performance Tips**
1. **Use volume mounting** for faster code changes
2. **Enable debug logging** only when needed
3. **Use development-specific database** to avoid conflicts
4. **Restart workers** after code changes
5. **Use development-specific resource limits**

## 🆘 Getting Help

### **Check Logs**

#### **Production Mode**
```bash
# Application logs
docker-compose logs api

# Database logs
docker-compose logs db

# All services logs
docker-compose logs
```

#### **Development Mode**
```bash
# Application logs (with debug info)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs api

# Database logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs db

# All services logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs

# Worker logs with debug info
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs worker-email
```

### **Health Checks**

#### **Production Mode**
```bash
# Basic health
curl http://localhost:8000/health

# Service status
curl http://localhost:8000/health/services

# API documentation
open http://localhost:8000/docs
```

#### **Development Mode**
```bash
# Basic health (development)
curl http://localhost:8000/health

# Service status (development)
curl http://localhost:8000/health/services

# API documentation (development)
open http://localhost:8000/docs

# Check development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api env | grep -E "(DEBUG|LOG_LEVEL|APP_ENV)"
```

### **Common Solutions**

#### **Production Mode**
1. **Restart services**: `docker-compose restart`
2. **Check logs**: `docker-compose logs`
3. **Verify configuration**: Check `.env` file
4. **Check ports**: Ensure ports 8000, 5432, 6379, 5672 are free
5. **Update Docker**: Ensure Docker and Docker Compose are up to date

#### **Development Mode**
1. **Restart development services**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart`
2. **Check development logs**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs`
3. **Verify development configuration**: Check `.env.dev` file
4. **Check development ports**: Ensure ports 8000, 5432, 6379, 5672 are free
5. **Update Docker**: Ensure Docker and Docker Compose are up to date
6. **Restart workers after code changes**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart worker-email worker-ocr worker-transcription`

## 🚀 Development Quick Reference

### **Essential Development Commands**
```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Restart after code changes
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart api

# View development logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f api

# Run database migrations
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# Connect to development database
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U postgres -d alta_data_dev
```

### **Development URLs**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Services Status**: http://localhost:8000/health/services
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **Flower (Celery Monitor)**: http://localhost:5555

### **Development File Structure**
```
alta_data_backend/
├── docker-compose.yml          # Production configuration
├── docker-compose.dev.yml      # Development overrides
├── .env                        # Production environment
├── .env.dev                    # Development environment
├── dev-start.sh                # Development startup script
├── start.sh                    # Production startup script
└── app/                        # Application code
```

### **Development Workflow**
1. **Start development environment**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
2. **Make code changes**: Edit files in your IDE
3. **API auto-restarts**: Due to hot reload
4. **Workers need restart**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart worker-email worker-ocr worker-transcription`
5. **Test changes**: Use API endpoints or frontend
6. **Check logs**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f api`

---

**The Alta Data Backend is designed to run on any device with Docker support, providing flexibility for development, testing, and production environments!** 🚀
