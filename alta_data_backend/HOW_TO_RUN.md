# How to Run Alta Data Backend

This guide will help you run the Alta Data Backend on any device, with or without external services like Google Cloud Storage, Document AI, Speech-to-Text, and Email.

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

### **Option 1: Minimal Setup (No External Services)**
Perfect for development, testing, or when you don't have Google Cloud credentials.

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

## 🚨 Troubleshooting

### **Common Issues**

#### **1. Docker Not Running**
```bash
# Check Docker status
docker --version
docker-compose --version

# Start Docker service (Linux)
sudo systemctl start docker
```

#### **2. Port Already in Use**
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Stop conflicting services or change ports in docker-compose.yml
```

#### **3. Permission Denied (Linux/macOS)**
```bash
# Make script executable
chmod +x start.sh

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
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
```

#### **5. Database Connection Issues**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### **Debug Commands**

```bash
# Check all running containers
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api

# Restart specific service
docker-compose restart api

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## 🔄 Managing the Application

### **Starting the Application**
```bash
# Start all services
./start.sh

# Or manually
docker-compose up -d
```

### **Stopping the Application**
```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

### **Restarting the Application**
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
```

### **Updating the Application**
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

## 📱 Running on Different Devices

### **Raspberry Pi**
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

### **Cloud VPS (DigitalOcean, AWS, etc.)**
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

### **Windows Server**
```powershell
# Install Docker Desktop for Windows Server
# Download from: https://www.docker.com/products/docker-desktop

# Clone repository
git clone <your-repo-url>
cd alta_data_backend

# Start application
./start.sh
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

### **Environment Variables Security**
```env
# Use strong, unique passwords
POSTGRES_PASSWORD=your-very-strong-password-here
SECRET_KEY=your-very-long-and-random-secret-key-here

# Use environment-specific settings
APP_ENV=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 📈 Performance Optimization

### **Resource Limits**
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

### **Database Optimization**
```yaml
services:
  db:
    environment:
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
```

## 🆘 Getting Help

### **Check Logs**
```bash
# Application logs
docker-compose logs api

# Database logs
docker-compose logs db

# All services logs
docker-compose logs
```

### **Health Checks**
```bash
# Basic health
curl http://localhost:8000/health

# Service status
curl http://localhost:8000/health/services

# API documentation
open http://localhost:8000/docs
```

### **Common Solutions**
1. **Restart services**: `docker-compose restart`
2. **Check logs**: `docker-compose logs`
3. **Verify configuration**: Check `.env` file
4. **Check ports**: Ensure ports 8000, 5432, 6379, 5672 are free
5. **Update Docker**: Ensure Docker and Docker Compose are up to date

---

**The Alta Data Backend is designed to run on any device with Docker support, providing flexibility for development, testing, and production environments!** 🚀
