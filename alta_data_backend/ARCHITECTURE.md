# Alta Data Backend - Hybrid Architecture

## 🏗️ Architecture Overview

This document describes the hybrid architecture implementation using **Redis** for caching/rate limiting and **RabbitMQ** for reliable background processing, with the **Outbox Pattern** to ensure data consistency.

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Requests                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    FastAPI Application                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Auth Routes   │  │  Project Routes │  │   Data Routes   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Review Routes  │  │ Analytics Routes│  │  Health Routes  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Middleware Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Security Headers│  │ Request Correl. │  │  Rate Limiting  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Input Validation│  │  Audit Logging  │  │ Error Handling  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Service Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Outbox Service │  │ Document AI Svc │  │ Speech-to-Text  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Email Service │  │  Storage Service│  │  Audit Service  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Data Layer                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │     Redis       │  │    RabbitMQ     │ │
│  │                 │  │                 │  │                 │ │
│  │ • Main Database │  │ • Rate Limiting │  │ • OCR Queue     │ │
│  │ • Audit Logs    │  │ • Caching       │  │ • Email Queue   │ │
│  │ • Outbox Events │  │ • Sessions      │  │ • Trans. Queue  │ │
│  │ • User Data     │  │ • Celery Results│  │ • Dead Letters  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                Background Processing                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  OCR Worker     │  │Transcription Wkr│  │  Email Worker   │ │
│  │  (Celery)       │  │   (Celery)      │  │   (Celery)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Outbox Processor│  │  Celery Beat    │  │  Flower Monitor │ │
│  │   (Async)       │  │  (Scheduler)    │  │   (Web UI)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. **File Upload Flow**
```
Client → FastAPI → Outbox Service → PostgreSQL
                ↓
        Outbox Processor → RabbitMQ → Celery Worker → Google Cloud AI
```

### 2. **Email Sending Flow**
```
User Registration → Outbox Service → PostgreSQL
                        ↓
                Outbox Processor → RabbitMQ → Email Worker → SMTP
```

### 3. **Rate Limiting Flow**
```
Client Request → Rate Limit Middleware → Redis → Allow/Deny
```

## 🛠️ Components

### **FastAPI Application**
- **Framework**: FastAPI with async/await
- **Port**: 8000
- **Features**: 
  - RESTful API endpoints
  - Request correlation
  - Security headers
  - Input validation
  - Error handling

### **PostgreSQL Database**
- **Purpose**: Main data storage
- **Port**: 5432
- **Tables**:
  - `users` - User accounts
  - `projects` - Project data
  - `documents` - Document metadata
  - `voice_samples` - Audio metadata
  - `outbox_events` - Outbox pattern events
  - `audit_logs` - Audit trail

### **Redis**
- **Purpose**: Caching, rate limiting, sessions
- **Port**: 6379
- **Usage**:
  - Rate limiting counters
  - Session storage
  - API response caching
  - Celery result backend

### **RabbitMQ**
- **Purpose**: Reliable message queuing
- **Ports**: 5672 (AMQP), 15672 (Management UI)
- **Queues**:
  - `ocr_queue` - Document OCR processing
  - `transcription_queue` - Audio transcription
  - `email_queue` - Email sending
  - `default` - General tasks

### **Celery Workers**
- **OCR Worker**: Processes documents with Google Document AI
- **Transcription Worker**: Transcribes audio with Google Speech-to-Text
- **Email Worker**: Sends emails via SMTP
- **Outbox Processor**: Processes outbox events

## 🔒 Outbox Pattern Implementation

### **Problem Solved**
The outbox pattern ensures **reliable message delivery** and **data consistency** by:
1. Storing events in the same database transaction as the business data
2. Processing events asynchronously to publish to RabbitMQ
3. Retrying failed events with exponential backoff
4. Preventing message loss during failures

### **Outbox Event Lifecycle**
```
1. Business Event → Outbox Event (PENDING)
2. Outbox Processor → Mark as PROCESSING
3. Publish to RabbitMQ → Mark as COMPLETED
4. If Failed → Mark as FAILED → Retry Later
```

### **Event Types**
- `DOCUMENT_OCR_REQUESTED` - Document uploaded, needs OCR
- `VOICE_TRANSCRIPTION_REQUESTED` - Audio uploaded, needs transcription
- `EMAIL_SEND_REQUESTED` - Email needs to be sent
- `USER_REGISTERED` - New user registered
- `PROJECT_CREATED` - New project created

## 🚀 Getting Started

### **Prerequisites**
- Docker and Docker Compose
- Google Cloud credentials
- SMTP configuration

### **Quick Start**
```bash
# 1. Clone and setup
git clone <repository>
cd alta_data_backend

# 2. Configure environment
cp env.example .env
# Edit .env with your settings

# 3. Start all services
./start.sh

# Or manually:
docker-compose up -d
```

### **Service URLs**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **Flower (Celery Monitor)**: http://localhost:5555

## 📊 Monitoring

### **Health Checks**
```bash
# Basic health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/health/ready

# Liveness check
curl http://localhost:8000/health/live
```

### **Queue Monitoring**
- **RabbitMQ Management UI**: http://localhost:15672
- **Flower (Celery)**: http://localhost:5555

### **Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker-ocr
```

## 🔧 Configuration

### **Environment Variables**
```bash
# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//

# Google Cloud
GCS_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Outbox Pattern
OUTBOX_BATCH_SIZE=100
OUTBOX_PROCESSING_INTERVAL=5
OUTBOX_MAX_RETRIES=3
OUTBOX_RETRY_DELAY=60
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Outbox Events Not Processing**
   ```bash
   # Check outbox processor logs
   docker-compose logs -f api
   
   # Check for pending events
   docker-compose exec db psql -U postgres -d alta_data -c "SELECT * FROM outbox_events WHERE status = 'pending';"
   ```

2. **Celery Workers Not Starting**
   ```bash
   # Check RabbitMQ connection
   docker-compose logs -f worker-ocr
   
   # Check RabbitMQ management UI
   open http://localhost:15672
   ```

3. **Rate Limiting Issues**
   ```bash
   # Check Redis connection
   docker-compose logs -f redis
   
   # Test Redis
   docker-compose exec redis redis-cli ping
   ```

### **Performance Tuning**

1. **Increase Worker Concurrency**
   ```yaml
   # In docker-compose.yml
   worker-ocr:
     command: celery -A app.worker.celery_app worker --concurrency=4
   ```

2. **Adjust Outbox Batch Size**
   ```bash
   # In .env
   OUTBOX_BATCH_SIZE=200
   OUTBOX_PROCESSING_INTERVAL=2
   ```

3. **Redis Memory Optimization**
   ```yaml
   # In docker-compose.yml
   redis:
     command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
   ```

## 🔄 Scaling

### **Horizontal Scaling**
```bash
# Scale workers
docker-compose up -d --scale worker-ocr=3 --scale worker-email=2

# Scale API
docker-compose up -d --scale api=3
```

### **Production Deployment**
1. Use managed services (Azure Database, Redis Cache, Service Bus)
2. Implement load balancing
3. Add monitoring and alerting
4. Use secrets management (Azure Key Vault)
5. Implement CI/CD pipeline

## 📈 Benefits

### **Reliability**
- ✅ **Outbox Pattern**: Guaranteed message delivery
- ✅ **Retry Logic**: Automatic retry with exponential backoff
- ✅ **Dead Letter Queues**: Handle failed messages
- ✅ **Data Consistency**: ACID transactions

### **Performance**
- ✅ **Redis Caching**: Fast response times
- ✅ **Background Processing**: Non-blocking operations
- ✅ **Queue Separation**: Isolated processing
- ✅ **Horizontal Scaling**: Easy to scale workers

### **Observability**
- ✅ **Request Correlation**: Track requests across services
- ✅ **Audit Logging**: Complete audit trail
- ✅ **Health Checks**: Monitor service health
- ✅ **Queue Monitoring**: Track message processing

### **Security**
- ✅ **Rate Limiting**: Prevent abuse
- ✅ **Input Validation**: Secure data handling
- ✅ **Security Headers**: Protect against attacks
- ✅ **Audit Trail**: Track all actions

This hybrid architecture provides a robust, scalable, and maintainable foundation for the Alta Data platform! 🚀
