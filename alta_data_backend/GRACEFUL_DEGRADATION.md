# Graceful Degradation Guide

The Alta Data Backend is designed to run even when external services like Google Cloud Storage, Document AI, Speech-to-Text, and Email are not configured or available. This guide explains how the application handles missing services gracefully.

## 🎯 Overview

The application implements **graceful degradation** - it continues to function with reduced capabilities when external services are unavailable, rather than failing completely.

## 🔧 Service Availability Checks

### **Google Cloud Storage (GCS)**
- **Availability Check**: `is_gcs_available()` function
- **Fallback**: Uses local storage URIs (`local://...`)
- **Impact**: File uploads work but are stored locally instead of in the cloud

### **Document AI (OCR)**
- **Availability Check**: `document_ai_service.is_available()`
- **Fallback**: Documents are marked as processed but without OCR text
- **Impact**: OCR processing is skipped, documents remain in draft status

### **Speech-to-Text**
- **Availability Check**: `speech_to_text_service.is_available()`
- **Fallback**: Audio files are marked as processed but without transcription
- **Impact**: Transcription is skipped, voice samples remain in draft status

### **Email Service**
- **Availability Check**: `is_email_available()`
- **Fallback**: Email sending is skipped, events are logged
- **Impact**: No email notifications are sent (verification, invitations, etc.)

## 📊 Health Check Endpoints

### **Service Status Check**
```http
GET /health/services
```

**Response when all services are available:**
```json
{
  "status": "all_services_available",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "google_cloud_storage": {
      "available": true,
      "status": "available"
    },
    "document_ai": {
      "available": true,
      "status": "available"
    },
    "speech_to_text": {
      "available": true,
      "status": "available"
    },
    "email": {
      "available": true,
      "status": "available"
    }
  },
  "message": "All services are available"
}
```

**Response when some services are unavailable:**
```json
{
  "status": "some_services_unavailable",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "google_cloud_storage": {
      "available": false,
      "status": "not_configured"
    },
    "document_ai": {
      "available": false,
      "status": "not_configured"
    },
    "speech_to_text": {
      "available": false,
      "status": "not_configured"
    },
    "email": {
      "available": false,
      "status": "not_configured"
    }
  },
  "message": "Some services are not configured but the application will continue to run"
}
```

## 🚀 Running Without External Services

### **Minimal Configuration**
To run the application with minimal external dependencies, use this `.env` configuration:

```env
# Application Configuration
APP_ENV=development
APP_NAME=alta_data
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALG=HS256

# Database Configuration (Required)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration (Required for rate limiting and sessions)
REDIS_URL=redis://localhost:6379/0

# RabbitMQ Configuration (Required for background processing)
RABBITMQ_URL=amqp://guest:guest@localhost:5672//

# Email Configuration (Optional - leave empty to disable)
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=

# Google Cloud Configuration (Optional - leave empty to disable)
GCS_PROJECT_ID=
GCS_BUCKET_NAME=
GOOGLE_APPLICATION_CREDENTIALS=

# Document AI Configuration (Optional - leave empty to disable)
DOCUMENT_AI_PROCESSOR_ID=
DOCUMENT_AI_LOCATION=us

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### **What Works Without External Services**

✅ **Core Functionality**
- User registration and authentication
- Project creation and management
- User role management (admin, contributor, reviewer)
- Database operations
- API endpoints for CRUD operations

✅ **Data Management**
- Document and voice sample uploads (stored locally)
- Raw text creation and management
- Draft management and submission
- Review workflow

✅ **Background Processing**
- Celery workers continue to run
- Tasks are processed but skip unavailable services
- Audit logging continues

❌ **What Doesn't Work**
- File storage in Google Cloud Storage
- OCR processing of documents
- Speech-to-text transcription
- Email notifications

## 🔄 Background Task Behavior

### **OCR Processing Task**
```python
# When Document AI is not available
{
  "status": "skipped",
  "document_id": "doc-uuid",
  "reason": "Document AI service not available"
}
```

### **Transcription Task**
```python
# When Speech-to-Text is not available
{
  "status": "skipped", 
  "voice_sample_id": "voice-uuid",
  "reason": "Speech-to-Text service not available"
}
```

### **Email Task**
```python
# When Email service is not available
{
  "status": "skipped",
  "to": "user@example.com",
  "subject": "Email Subject",
  "reason": "Email service not available"
}
```

## 📝 Logging and Monitoring

### **Service Availability Logs**
```
WARNING: GCS not configured: Missing project_id or bucket_name
WARNING: Document AI not configured: Missing processor_id or location
WARNING: Speech-to-Text not configured: Missing GCS project ID
WARNING: Email not configured: Missing SMTP host or port
```

### **Task Processing Logs**
```
INFO: Document AI service is not available. Cannot process document.
INFO: Speech-to-Text service is not available. Cannot transcribe audio.
INFO: Email service is not available. Cannot send email.
```

### **Audit Events**
All service unavailability events are logged in the audit trail:
- `DOCUMENT_OCR_SKIPPED`
- `VOICE_SAMPLE_TRANSCRIPTION_SKIPPED`
- `EMAIL_SKIPPED`

## 🛠️ Development Workflow

### **1. Start with Minimal Setup**
```bash
# Copy minimal configuration
cp env.example .env

# Edit .env to remove external service configurations
# Leave GCS_PROJECT_ID, DOCUMENT_AI_PROCESSOR_ID, etc. empty

# Start the application
./start.sh
```

### **2. Verify Service Status**
```bash
# Check service availability
curl http://localhost:8000/health/services

# Check basic health
curl http://localhost:8000/health
```

### **3. Test Core Functionality**
```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Create a project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "description": "Test project"}'
```

### **4. Add Services Gradually**
1. Configure Google Cloud Storage
2. Set up Document AI
3. Configure Speech-to-Text
4. Set up Email service

## 🔧 Configuration Examples

### **Local Development (No External Services)**
```env
# Minimal configuration for local development
POSTGRES_HOST=localhost
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672//

# All external services disabled
GCS_PROJECT_ID=
DOCUMENT_AI_PROCESSOR_ID=
SMTP_HOST=
```

### **Production with All Services**
```env
# Full production configuration
POSTGRES_HOST=your-db-host
POSTGRES_DB=alta_data
POSTGRES_USER=alta_user
POSTGRES_PASSWORD=secure-password

REDIS_URL=redis://your-redis-host:6379/0
RABBITMQ_URL=amqp://user:pass@your-rabbitmq-host:5672//

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

## 🚨 Troubleshooting

### **Common Issues**

1. **Application won't start**
   - Check database connection
   - Verify Redis is running
   - Ensure RabbitMQ is accessible

2. **File uploads fail**
   - Check if GCS is configured
   - Verify file size limits
   - Check file type restrictions

3. **Background tasks not processing**
   - Check Celery worker status
   - Verify RabbitMQ connection
   - Check task logs for errors

4. **No email notifications**
   - Verify SMTP configuration
   - Check email service availability
   - Review email task logs

### **Debug Commands**

```bash
# Check service status
curl http://localhost:8000/health/services

# Check Celery worker status
docker-compose exec worker celery -A app.worker.celery_app inspect active

# Check RabbitMQ queues
curl -u guest:guest http://localhost:15672/api/queues

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## 📈 Benefits of Graceful Degradation

1. **Development Flexibility**: Developers can work without setting up all external services
2. **Faster Onboarding**: New team members can start contributing immediately
3. **Cost Optimization**: Run development environments without expensive cloud services
4. **Reliability**: Application continues to function even when external services are down
5. **Gradual Migration**: Add services incrementally as needed

## 🎯 Best Practices

1. **Always check service availability** before using external services
2. **Log service unavailability** for monitoring and debugging
3. **Provide clear error messages** when services are unavailable
4. **Use health check endpoints** to monitor service status
5. **Implement proper fallbacks** for critical functionality
6. **Test with and without external services** during development
