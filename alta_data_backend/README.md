# Alta Data Backend

A comprehensive FastAPI-based backend for the Alta Data platform, designed for collection, annotation, and labeling of text and audio data with robust role-based access control and analytics capabilities.

## 🏗️ Architecture Overview

- **Framework**: FastAPI (async-first)
- **Database**: PostgreSQL with SQLAlchemy 2.0 + Alembic migrations
- **Authentication**: JWT + WebAuthn (Passkeys) - *partially implemented*
- **Cache/Queue**: Redis for rate limiting and Celery task queue
- **Object Storage**: Google Cloud Storage (GCS)
- **Background Processing**: Celery workers for OCR/transcription
- **External AI Services**: Google Document AI (OCR), Google Speech-to-Text
- **Logging**: Structlog with JSON formatting
- **Email**: SMTP for transactional emails

## 📁 Project Structure

```
alta_data_backend/
├── app/
│   ├── main.py                  # FastAPI app with CORS and route registration
│   ├── config.py                # Pydantic settings configuration
│   ├── database.py              # Async database engine and session factory
│   ├── logs.py                  # Structlog configuration
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py             # User model with global roles
│   │   ├── project.py          # Project and ProjectMember models
│   │   ├── data.py             # Document and VoiceSample models
│   │   ├── invitation.py       # Email verification and project invitations
│   │   └── audit.py            # Audit logging model
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── auth.py             # Authentication schemas
│   │   └── project.py          # Project-related schemas
│   ├── api/
│   │   ├── dependencies.py     # Authentication and RBAC dependencies
│   │   └── routes/             # API route handlers
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── projects.py     # Project management
│   │       ├── data.py         # File upload endpoints
│   │       ├── review.py       # Review workflow
│   │       ├── analytics.py    # Analytics and metrics
│   │       └── admin.py        # Admin-only endpoints
│   ├── core/                   # Core business logic
│   │   ├── security.py         # JWT token creation
│   │   ├── email.py            # SMTP email service
│   │   └── storage.py          # Google Cloud Storage integration
│   ├── utils/                  # Utility functions
│   │   └── audit_logger.py     # Audit logging utility
│   └── worker/                 # Background task processing
│       └── celery_app.py       # Celery configuration
├── alembic/                    # Database migrations
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis
- Google Cloud Storage bucket
- Google Cloud credentials for Document AI and Speech-to-Text

### Installation

1. **Clone and setup environment:**
```bash
cd alta_data_backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment configuration:**
Create a `.env` file in the project root:

```env
# Application
APP_ENV=development
APP_NAME=alta_data
SECRET_KEY=your-super-secret-key-here
JWT_ALG=HS256

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (SMTP)
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=no-reply@altadata.local

# Google Cloud
GCS_PROJECT_ID=your-gcp-project-id
GCS_BUCKET_NAME=your-gcs-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# WebAuthn
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=Alta Data

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

3. **Database setup:**
```bash
# Create database
createdb alta_data

# Run migrations (if Alembic is configured)
alembic upgrade head
```

4. **Start the application:**
```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with custom settings
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --env-file .env
```

5. **Start Celery worker (in separate terminal):**
```bash
celery -A app.worker.celery_app worker --loglevel=info
```

### Health Check

Visit `http://localhost:8000/health` to verify the API is running.

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔐 Authentication & Authorization

### User Roles

1. **Super Admin** (`super_admin`): Platform-wide access to all features
2. **User** (`user`): Default role, can create projects and become project admin
3. **Project Admin** (`admin`): Full control within assigned projects
4. **Contributor** (`contributor`): Can upload and manage data within projects
5. **Reviewer** (`reviewer`): Can review and approve/reject submissions

### Authentication Methods

#### ✅ Implemented
- **JWT Authentication**: Email/password login with JWT tokens
- **Email Verification**: Required for account activation
- **Rate Limiting**: Redis-based rate limiting on auth endpoints

#### ❌ Not Implemented
- **WebAuthn/Passkeys**: Placeholder endpoints exist but not functional
- **Google OAuth**: Not implemented
- **Refresh Tokens**: Only access tokens implemented

## 📊 API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| POST | `/register` | User registration with email verification | ✅ |
| POST | `/login` | Email/password login | ✅ |
| GET | `/verify-email` | Email verification | ✅ |
| GET | `/me` | Get current user profile | ✅ |
| POST | `/passkeys/register` | WebAuthn registration | ❌ |
| POST | `/passkeys/register/verify` | WebAuthn registration verify | ❌ |
| POST | `/passkeys/login` | WebAuthn login | ❌ |
| POST | `/passkeys/login/verify` | WebAuthn login verify | ❌ |

### Projects (`/api/projects`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| GET | `/` | List projects | ✅ |
| POST | `/` | Create project | ✅ |
| GET | `/{project_id}` | Get project details | ✅ |
| PUT | `/{project_id}` | Update project | ✅ |
| DELETE | `/{project_id}` | Delete project | ✅ |
| POST | `/{project_id}/invite` | Invite user to project | ✅ |
| POST | `/invitations/{token}/accept` | Accept project invitation | ✅ |
| POST | `/{project_id}/review` | Submit document for review | ✅ |

### Data Management (`/api`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| POST | `/documents` | Upload document | ✅ |
| POST | `/voice` | Upload audio file | ✅ |

### Review Workflow (`/api/review`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| GET | `/?project_id=` | Get review queue | ✅ |
| PATCH | `/{document_id}` | Approve/reject document | ✅ |

### Analytics (`/api/analytics`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| GET | `/summary` | Platform/project analytics | ✅ |
| GET | `/user/{userId}` | User-specific analytics | ✅ |

### Admin (`/api/admin`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| GET | `/users` | List all users (super_admin only) | ✅ |

## 🚧 Missing Features & Implementation Gaps

### Critical Missing Features

1. **WebAuthn/Passkey Authentication**
   - Endpoints exist but return placeholder responses
   - No WebAuthn library integration
   - Missing credential storage model

2. **Background Processing**
   - Celery app configured but no tasks implemented
   - No OCR processing with Google Document AI
   - No Speech-to-Text processing
   - No email sending tasks

3. **Google Cloud Integration**
   - GCS upload works but no OCR/transcription services
   - Missing Google Document AI integration
   - Missing Google Speech-to-Text integration

4. **Soft Deletes**
   - Models don't have `deleted_at` fields
   - No soft delete implementation

5. **Idempotency**
   - No idempotency key support for critical operations
   - No retry protection

### Additional Missing Features

6. **Advanced Analytics**
   - Missing storage utilization metrics
   - No top contributors analytics
   - Limited timeframe filtering

7. **Error Handling**
   - Basic error responses
   - No structured error handling middleware
   - Missing request correlation IDs

8. **Logging & Monitoring**
   - Basic structlog setup
   - No request correlation
   - No health check endpoints beyond basic

9. **Security Enhancements**
   - No input validation middleware
   - No CORS configuration beyond basic
   - No security headers

10. **Testing**
    - No test suite
    - No test configuration

## 🏭 Production-Grade Recommendations

### 1. Security Enhancements

```python
# Add to main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Security headers
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.yourdomain.com"])
app.add_middleware(HTTPSRedirectMiddleware)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### 2. Implement Soft Deletes

```python
# Add to all models
from sqlalchemy import DateTime
from datetime import datetime, timezone

class BaseModel(Base):
    __abstract__ = True
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        default=None
    )
    
    @declared_attr
    def __mapper_cls__(cls):
        # Add soft delete filter
        return super().__mapper_cls__
```

### 3. Add Request Correlation

```python
# Add to main.py
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id')

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### 4. Implement Background Tasks

```python
# app/worker/tasks.py
from celery import Celery
from google.cloud import documentai, speech
from app.core.storage import get_gcs_client

@celery_app.task
def process_ocr(document_id: str):
    # Download from GCS
    # Call Google Document AI
    # Update database
    # Log audit event
    pass

@celery_app.task
def transcribe_audio(voice_sample_id: str):
    # Download from GCS
    # Call Google Speech-to-Text
    # Update database
    # Log audit event
    pass

@celery_app.task
def send_email(to: str, subject: str, body: str):
    # Send email via SMTP
    pass
```

### 5. Add Comprehensive Error Handling

```python
# app/api/exceptions.py
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class AltaDataException(Exception):
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code

@app.exception_handler(AltaDataException)
async def alta_data_exception_handler(request: Request, exc: AltaDataException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "alta_data_error",
                "message": exc.message,
                "code": exc.error_code,
                "requestId": request_id_var.get()
            }
        }
    )
```

### 6. Add Health Checks

```python
# app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow()}

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "disconnected", "error": str(e)}
        )
```

### 7. Add Input Validation

```python
# app/api/middleware.py
from fastapi import Request, HTTPException
import re

async def validate_input(request: Request, call_next):
    # Validate file uploads
    if request.url.path in ["/documents", "/voice"]:
        # Add file validation logic
        pass
    
    # Validate email formats
    if request.url.path == "/auth/register":
        # Add email validation
        pass
    
    response = await call_next(request)
    return response
```

### 8. Implement Caching

```python
# app/core/cache.py
import redis
from functools import wraps

redis_client = redis.Redis.from_url(settings.redis_url)

def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 9. Add Database Migrations

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 10. Add Testing

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_db():
    # Setup test database
    pass

# tests/test_auth.py
def test_user_registration(client):
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
```

## 🔧 Configuration Management

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_ENV` | Application environment | Yes | `development` |
| `SECRET_KEY` | JWT secret key | Yes | `changeme` |
| `POSTGRES_HOST` | Database host | Yes | `localhost` |
| `POSTGRES_PORT` | Database port | Yes | `5432` |
| `POSTGRES_DB` | Database name | Yes | `alta_data` |
| `POSTGRES_USER` | Database user | Yes | `postgres` |
| `POSTGRES_PASSWORD` | Database password | Yes | `postgres` |
| `REDIS_URL` | Redis connection URL | Yes | `redis://localhost:6379/0` |
| `GCS_PROJECT_ID` | Google Cloud project ID | Yes | - |
| `GCS_BUCKET_NAME` | GCS bucket name | Yes | - |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Yes | - |
| `SMTP_HOST` | SMTP server host | No | `localhost` |
| `SMTP_PORT` | SMTP server port | No | `25` |
| `SMTP_USER` | SMTP username | No | - |
| `SMTP_PASSWORD` | SMTP password | No | - |
| `SMTP_FROM` | From email address | No | `no-reply@altadata.local` |
| `CORS_ORIGINS` | Allowed CORS origins | No | `http://localhost:3000` |

## 🚀 Deployment

### Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: alta_data
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  worker:
    build: .
    command: celery -A app.worker.celery_app worker --loglevel=info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Production Deployment

1. **Use Azure Container Apps or AKS**
2. **Store secrets in Azure Key Vault**
3. **Use managed PostgreSQL and Redis**
4. **Implement proper monitoring with Application Insights**
5. **Set up CI/CD pipeline with GitHub Actions**

## 📈 Monitoring & Observability

### Recommended Metrics

- Request latency and throughput
- Database connection pool status
- Redis cache hit rates
- Background task queue length
- File upload success rates
- Authentication success/failure rates

### Logging Strategy

- Structured JSON logging with request correlation
- Separate access logs from audit logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized log aggregation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/docs`

---

**Note**: This backend is currently in development. Several critical features are missing and need to be implemented before production deployment. Refer to the "Missing Features" section for a complete list of required implementations.
