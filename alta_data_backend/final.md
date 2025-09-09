# Alta Data Backend - Complete System Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [User Roles & Permissions](#user-roles--permissions)
5. [Data Models](#data-models)
6. [API Documentation](#api-documentation)
7. [Background Processing](#background-processing)
8. [Deployment & Infrastructure](#deployment--infrastructure)
9. [Security Features](#security-features)
10. [Monitoring & Observability](#monitoring--observability)

---

## Project Overview

**Alta Data Backend** is a comprehensive FastAPI-based platform designed for collection, annotation, and labeling of text and audio data. The system provides robust role-based access control, background processing capabilities, and analytics for managing data workflows from acquisition to high-quality dataset creation.

### Key Features
- **Multi-format Data Support**: Documents (PDF, images), Voice samples (audio files), and Raw text entries
- **AI-Powered Processing**: Google Document AI for OCR and Google Speech-to-Text for transcription
- **Role-Based Access Control**: Granular permissions for different user types
- **Background Processing**: Reliable message queuing with the Outbox pattern
- **Review Workflow**: Comprehensive approval/rejection system for data quality
- **Analytics Dashboard**: Detailed metrics and reporting capabilities
- **Audit Logging**: Complete audit trail for compliance and security

---

## System Architecture

### High-Level Architecture

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

### Data Flow

1. **File Upload Flow**:
   ```
   Client → FastAPI → Outbox Service → PostgreSQL
                   ↓
           Outbox Processor → RabbitMQ → Celery Worker → Google Cloud AI
   ```

2. **Email Sending Flow**:
   ```
   User Registration → Outbox Service → PostgreSQL
                           ↓
                   Outbox Processor → RabbitMQ → Email Worker → SMTP
   ```

3. **Rate Limiting Flow**:
   ```
   Client Request → Rate Limit Middleware → Redis → Allow/Deny
   ```

---

## Technology Stack

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs with Python 3.11+
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation and settings management using Python type annotations

### Database & ORM
- **PostgreSQL 15+**: Primary relational database for data persistence
- **SQLAlchemy 2.0**: Modern Python SQL toolkit and ORM with async support
- **AsyncPG**: High-performance PostgreSQL driver for Python
- **Alembic**: Database migration tool for SQLAlchemy

### Authentication & Security
- **JWT (python-jose)**: JSON Web Token implementation for stateless authentication
- **Passlib**: Password hashing utilities (bcrypt)
- **WebAuthn**: Passwordless authentication support (planned)

### Caching & Message Queuing
- **Redis 7+**: In-memory data structure store for caching, rate limiting, and session storage
- **RabbitMQ 3.12+**: Message broker for reliable background processing
- **Celery**: Distributed task queue for background job processing

### Cloud Services
- **Google Cloud Storage**: Object storage for uploaded files
- **Google Document AI**: OCR processing for document text extraction
- **Google Speech-to-Text**: Audio transcription services

### Background Processing
- **Celery**: Asynchronous task queue with Redis/RabbitMQ backend
- **Flower**: Web-based tool for monitoring Celery clusters
- **Outbox Pattern**: Reliable message delivery pattern for data consistency

### Development & Deployment
- **Docker & Docker Compose**: Containerization and orchestration
- **Structlog**: Structured logging with JSON formatting
- **Email-validator**: Email validation utilities
- **Jinja2**: Template engine for email templates

### Monitoring & Observability
- **Health Checks**: Built-in health monitoring endpoints
- **Request Correlation**: Unique request IDs for tracing
- **Audit Logging**: Comprehensive audit trail for all operations
- **Rate Limiting**: Redis-based request throttling

---

## User Roles & Permissions

### 1. Super Admin (`super_admin`)
**Global Platform Access**

**Capabilities:**
- Unrestricted access to all platform features and data
- Manage user accounts, roles, and system-wide configurations
- Create, view, update, and delete any project
- Access global analytics dashboards
- View and manage all documents and voice samples across projects
- System administration and maintenance

**API Access:**
- All endpoints with full permissions
- Global analytics: `GET /api/analytics/summary`
- User management: `GET /api/admin/users`

### 2. Project Manager (`admin` at project level)
**Project-Level Administration**

**Capabilities:**
- Full control over projects they create or are assigned to as admin
- Create new projects (becomes default admin)
- Invite users to projects and assign roles (contributor/reviewer)
- Upload documents and data to their projects
- Access review workflows to approve/reject submissions
- View project-specific analytics
- Modify project settings and configurations

**API Access:**
- Project management: `POST /api/projects`, `PUT /api/projects/{id}`
- User invitations: `POST /api/projects/{id}/invite`
- Review management: `GET /api/review`, `PATCH /api/review/{id}`
- Project analytics: `GET /api/analytics/summary?projectId={id}`

### 3. Contributor (`contributor` at project level)
**Data Contribution**

**Capabilities:**
- Upload files (documents, voice samples) to assigned projects
- Create raw text entries (manual data entry)
- CRUD operations on their own draft data
- Submit data for review
- Mass submission of multiple items
- View their own contribution history

**Restrictions:**
- Cannot see other contributors' draft data
- Cannot delete submitted data
- Cannot access review queue
- Cannot modify project settings

**API Access:**
- Data upload: `POST /api/documents`, `POST /api/voice`, `POST /api/raw-text`
- Draft management: `GET /api/my-drafts`
- Data submission: `POST /api/submit`
- Data updates: `PUT /api/documents/{id}`, `PUT /api/raw-text/{id}`

### 4. Reviewer (`reviewer` at project level)
**Quality Assurance**

**Capabilities:**
- Access review queue for assigned projects
- Approve, reject, or provide feedback on submissions
- Read-only access to all submitted data
- View review statistics and metrics

**Restrictions:**
- Cannot upload data
- Cannot modify project settings
- Cannot access draft data from contributors
- Cannot modify data content

**API Access:**
- Review queue: `GET /api/review?project_id={id}`
- Review decisions: `PATCH /api/review/{id}`
- Review analytics: `GET /api/analytics/review`

---

## Data Models

### Core Entities

#### User Model
```python
{
  "id": "uuid",
  "email": "string (unique)",
  "hashed_password": "string",
  "is_verified": "boolean",
  "global_role": "string (user|super_admin)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Project Model
```python
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "created_by_id": "uuid (FK to User)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### ProjectMember Model
```python
{
  "id": "uuid",
  "project_id": "uuid (FK to Project)",
  "user_id": "uuid (FK to User)",
  "role": "string (admin|contributor|reviewer)",
  "created_at": "datetime"
}
```

### Data Collection Models

#### Document Model
```python
{
  "id": "uuid",
  "project_id": "uuid (FK to Project)",
  "uploaded_by_id": "uuid (FK to User)",
  "original_filename": "string",
  "gcs_uri": "string",
  "ocr_text": "text (nullable)",
  "status": "string (draft|pending_review|approved|rejected)",
  "domain": "string (nullable)",
  "submitted_at": "datetime (nullable)",
  "reviewed_by_id": "uuid (FK to User, nullable)",
  "feedback": "text (nullable)",
  "is_raw": "boolean",
  "processed": "boolean",
  "tags": "json (nullable)",
  "extra_metadata": "json (nullable)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### VoiceSample Model
```python
{
  "id": "uuid",
  "project_id": "uuid (FK to Project)",
  "uploaded_by_id": "uuid (FK to User)",
  "original_filename": "string",
  "gcs_uri": "string",
  "transcription_text": "text (nullable)",
  "status": "string (draft|pending_review|approved|rejected)",
  "duration_seconds": "integer (nullable)",
  "submitted_at": "datetime (nullable)",
  "reviewed_by_id": "uuid (FK to User, nullable)",
  "feedback": "text (nullable)",
  "processed": "boolean",
  "language": "string (nullable)",
  "tags": "json (nullable)",
  "extra_metadata": "json (nullable)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### RawText Model
```python
{
  "id": "uuid",
  "project_id": "uuid (FK to Project)",
  "created_by_id": "uuid (FK to User)",
  "title": "string",
  "content": "text",
  "status": "string (draft|pending_review|approved|rejected)",
  "domain": "string (nullable)",
  "submitted_at": "datetime (nullable)",
  "reviewed_by_id": "uuid (FK to User, nullable)",
  "feedback": "text (nullable)",
  "tags": "json (nullable)",
  "extra_metadata": "json (nullable)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### System Models

#### OutboxEvent Model (Outbox Pattern)
```python
{
  "id": "uuid",
  "event_type": "string",
  "aggregate_id": "string",
  "aggregate_type": "string",
  "payload": "json",
  "status": "string (pending|processing|completed|failed)",
  "retry_count": "integer",
  "max_retries": "integer",
  "last_attempt_at": "datetime (nullable)",
  "error_message": "text (nullable)",
  "processed_at": "datetime (nullable)",
  "created_at": "datetime"
}
```

#### AuditLog Model
```python
{
  "id": "uuid",
  "actor_user_id": "uuid (FK to User, nullable)",
  "action": "string",
  "resource_type": "string",
  "resource_id": "string",
  "status": "string (success|failure)",
  "ip_address": "string",
  "user_agent": "string",
  "metadata": "json",
  "created_at": "datetime"
}
```

---

## API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication Endpoints

#### User Registration
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "id": "user-uuid",
  "email": "user@example.com",
  "is_verified": false,
  "global_role": "user"
}
```

#### User Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "access_token": "jwt-token-here"
}
```

#### Email Verification
```http
GET /api/auth/verify-email?token=verification-token

Response:
{
  "verified": true
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer jwt-token

Response:
{
  "id": "user-uuid",
  "email": "user@example.com",
  "is_verified": true,
  "global_role": "user"
}
```

### Project Management Endpoints

#### Create Project
```http
POST /api/projects
Authorization: Bearer jwt-token
Content-Type: application/json

{
  "name": "My Research Project",
  "description": "Project for collecting research data"
}

Response:
{
  "id": "project-uuid",
  "name": "My Research Project",
  "description": "Project for collecting research data",
  "created_by_id": "user-uuid"
}
```

#### List Projects
```http
GET /api/projects
Authorization: Bearer jwt-token

Response:
[
  {
    "id": "project-uuid",
    "name": "My Research Project",
    "description": "Project for collecting research data",
    "created_by_id": "user-uuid"
  }
]
```

#### Get Project Details
```http
GET /api/projects/{project_id}
Authorization: Bearer jwt-token

Response:
{
  "id": "project-uuid",
  "name": "My Research Project",
  "description": "Project for collecting research data",
  "created_by_id": "user-uuid"
}
```

#### Update Project
```http
PUT /api/projects/{project_id}
Authorization: Bearer jwt-token
Content-Type: application/json

{
  "name": "Updated Project Name",
  "description": "Updated description"
}

Response:
{
  "id": "project-uuid",
  "name": "Updated Project Name",
  "description": "Updated description",
  "created_by_id": "user-uuid"
}
```

#### Delete Project
```http
DELETE /api/projects/{project_id}
Authorization: Bearer jwt-token

Response:
{
  "deleted": true
}
```

#### Invite User to Project
```http
POST /api/projects/{project_id}/invite
Authorization: Bearer jwt-token
Content-Type: application/json

{
  "email": "contributor@example.com",
  "role": "contributor"
}

Response:
{
  "invited": true,
  "token": "invitation-token"
}
```

#### Accept Project Invitation
```http
POST /api/projects/invitations/{token}/accept
Authorization: Bearer jwt-token

Response:
{
  "accepted": true,
  "projectId": "project-uuid"
}
```

### Data Upload Endpoints

#### Upload Document
```http
POST /api/documents?project_id={project_id}&is_raw=false
Authorization: Bearer jwt-token
Content-Type: multipart/form-data

Body: file=document.pdf

Response:
{
  "id": "document-uuid",
  "gcs_uri": "gs://bucket/path/document.pdf",
  "status": "draft",
  "is_raw": false,
  "processed": false
}
```

#### Upload Voice Sample
```http
POST /api/voice?project_id={project_id}
Authorization: Bearer jwt-token
Content-Type: multipart/form-data

Body: file=audio.wav

Response:
{
  "id": "voice-uuid",
  "gcs_uri": "gs://bucket/path/audio.wav",
  "status": "draft",
  "processed": false
}
```

#### Create Raw Text Entry
```http
POST /api/raw-text
Authorization: Bearer jwt-token
Content-Type: application/json

{
  "project_id": "project-uuid",
  "title": "Manual Data Entry",
  "content": "This is manually entered text content",
  "domain": "research",
  "tags": ["important", "draft"]
}

Response:
{
  "id": "text-uuid",
  "title": "Manual Data Entry",
  "status": "draft",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Draft Management Endpoints

#### Get My Drafts
```http
GET /api/my-drafts?project_id={project_id}
Authorization: Bearer jwt-token

Response:
{
  "documents": [
    {
      "id": "doc-uuid",
      "filename": "document.pdf",
      "domain": "research",
      "is_raw": false,
      "processed": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "voice_samples": [
    {
      "id": "voice-uuid",
      "filename": "audio.wav",
      "language": "en",
      "processed": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "raw_texts": [
    {
      "id": "text-uuid",
      "title": "Manual Entry",
      "domain": "research",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Update Document
```http
PUT /api/documents/{document_id}
Authorization: Bearer jwt-token
Content-Type: application/json

{
  "domain": "updated-domain",
  "tags": ["updated", "tags"]
}

Response:
{
  "id": "document-uuid",
  "status": "updated"
}
```

#### Delete Document (Draft Only)
```http
DELETE /api/documents/{document_id}
Authorization: Bearer jwt-token

Response:
{
  "id": "document-uuid",
  "status": "deleted"
}
```

### Mass Submission Endpoints

#### Submit Multiple Items for Review
```http
POST /api/submit
Authorization: Bearer jwt-token
Content-Type: application/json

{
  "document_ids": ["doc-uuid-1", "doc-uuid-2"],
  "voice_sample_ids": ["voice-uuid-1"],
  "raw_text_ids": ["text-uuid-1", "text-uuid-2"]
}

Response:
{
  "submitted_count": 5,
  "submitted_items": [
    {"type": "document", "id": "doc-uuid-1"},
    {"type": "document", "id": "doc-uuid-2"},
    {"type": "voice_sample", "id": "voice-uuid-1"},
    {"type": "raw_text", "id": "text-uuid-1"},
    {"type": "raw_text", "id": "text-uuid-2"}
  ]
}
```

### Processing Endpoints

#### Manual OCR Trigger
```http
POST /api/processing/ocr?document_id={document_id}
Authorization: Bearer jwt-token

Response:
{
  "message": "OCR processing started",
  "document_id": "document-uuid",
  "status": "processing"
}
```

#### Manual Transcription Trigger
```http
POST /api/processing/transcribe?voice_sample_id={voice_sample_id}
Authorization: Bearer jwt-token

Response:
{
  "message": "Transcription processing started",
  "voice_sample_id": "voice-uuid",
  "status": "processing"
}
```

#### Batch OCR Processing
```http
POST /api/processing/batch-ocr?document_ids=["doc1","doc2","doc3"]
Authorization: Bearer jwt-token

Response:
{
  "processed_count": 2,
  "skipped_count": 1,
  "processed_documents": ["doc1", "doc2"],
  "skipped_documents": [
    {"id": "doc3", "reason": "Already processed"}
  ]
}
```

#### Check Processing Status
```http
GET /api/processing/status/{item_id}?item_type=document
Authorization: Bearer jwt-token

Response:
{
  "id": "document-uuid",
  "type": "document",
  "processed": true,
  "status": "draft",
  "has_content": true
}
```

### Review Endpoints

#### Get Review Queue
```http
GET /api/review?project_id={project_id}
Authorization: Bearer jwt-token

Response:
[
  {
    "id": "doc-uuid",
    "type": "document",
    "title": "document.pdf",
    "status": "pending_review",
    "submitted_at": "2024-01-15T10:30:00Z",
    "uploaded_by_id": "user-uuid"
  },
  {
    "id": "voice-uuid",
    "type": "voice_sample",
    "title": "audio.wav",
    "status": "pending_review",
    "submitted_at": "2024-01-15T10:30:00Z",
    "uploaded_by_id": "user-uuid"
  },
  {
    "id": "text-uuid",
    "type": "raw_text",
    "title": "Manual Entry",
    "status": "pending_review",
    "submitted_at": "2024-01-15T10:30:00Z",
    "created_by_id": "user-uuid"
  }
]
```

#### Review Decision
```http
PATCH /api/review/{item_id}?item_type=document
Authorization: Bearer jwt-token
Content-Type: application/json

{
  "decision": "approve",
  "feedback": "Good quality, approved for publication"
}

Response:
{
  "id": "document-uuid",
  "type": "document",
  "status": "approved",
  "reviewed_by": "reviewer-uuid",
  "feedback": "Good quality, approved for publication"
}
```

### Analytics Endpoints

#### Project Analytics
```http
GET /api/analytics/summary?timeframe=7d&project_id={project_id}
Authorization: Bearer jwt-token

Response:
{
  "documentCounts": {
    "approved": 45,
    "pending_review": 12,
    "rejected": 3
  },
  "contributionDaily": [
    {"day": "2024-01-15", "count": 8},
    {"day": "2024-01-16", "count": 12}
  ]
}
```

#### Global Analytics (Super Admin Only)
```http
GET /api/analytics/summary?timeframe=30d
Authorization: Bearer jwt-token

Response:
{
  "totalUsers": 150,
  "totalProjects": 25,
  "documentCounts": {
    "approved": 1200,
    "pending_review": 45,
    "rejected": 12
  },
  "userSignupDaily": [
    {"day": "2024-01-15", "count": 5},
    {"day": "2024-01-16", "count": 8}
  ]
}
```

#### User Analytics
```http
GET /api/analytics/user/{user_id}?timeframe=30d
Authorization: Bearer jwt-token

Response:
{
  "totalContributions": 25,
  "contributionDaily": [
    {"day": "2024-01-15", "count": 3},
    {"day": "2024-01-16", "count": 5}
  ],
  "approvalRate": 0.85
}
```

### Health Check Endpoints

#### Basic Health Check
```http
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "rabbitmq": "healthy"
  }
}
```

#### Readiness Check
```http
GET /api/health/ready

Response:
{
  "status": "ready",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Liveness Check
```http
GET /api/health/live

Response:
{
  "status": "alive",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Background Processing

### Outbox Pattern Implementation

The system uses the **Outbox Pattern** to ensure reliable message delivery and data consistency:

1. **Event Creation**: Business events are stored in the `outbox_events` table within the same database transaction
2. **Event Processing**: The outbox processor polls every 5 seconds for pending events
3. **Message Publishing**: Events are published to appropriate RabbitMQ queues
4. **Worker Processing**: Celery workers process tasks and update the database
5. **Status Tracking**: Events are marked as completed or failed with retry logic

### Celery Workers

#### OCR Worker
- **Queue**: `ocr_queue`
- **Task**: `task_process_ocr`
- **Function**: Processes documents with Google Document AI
- **Retry Logic**: Up to 3 retries with exponential backoff

#### Transcription Worker
- **Queue**: `transcription_queue`
- **Task**: `task_transcribe_audio`
- **Function**: Transcribes audio with Google Speech-to-Text
- **Retry Logic**: Up to 3 retries with exponential backoff

#### Email Worker
- **Queue**: `email_queue`
- **Task**: `task_send_email`
- **Function**: Sends transactional emails via SMTP
- **Retry Logic**: Up to 3 retries with exponential backoff

### Processing Flow

1. **File Upload** → Create outbox event → Store in database
2. **Outbox Processor** → Polls every 5 seconds → Publishes to RabbitMQ
3. **Celery Worker** → Processes task → Updates database
4. **Status Update** → Mark event as completed or failed

### Event Types

- `DOCUMENT_OCR_REQUESTED`: Document uploaded, needs OCR processing
- `VOICE_TRANSCRIPTION_REQUESTED`: Audio uploaded, needs transcription
- `EMAIL_SEND_REQUESTED`: Email needs to be sent
- `USER_REGISTERED`: New user registered
- `PROJECT_CREATED`: New project created

---

## Deployment & Infrastructure

### Docker Compose Services

#### Core Services
- **api**: FastAPI application (Port 8000)
- **db**: PostgreSQL 15 database (Port 5432)
- **redis**: Redis cache and rate limiting (Port 6379)
- **rabbitmq**: Message broker (Ports 5672, 15672)

#### Background Workers
- **worker-ocr**: Celery worker for OCR processing
- **worker-transcription**: Celery worker for audio transcription
- **worker-email**: Celery worker for email sending
- **beat**: Celery beat scheduler
- **flower**: Celery monitoring UI (Port 5555)

### Environment Configuration

#### Required Environment Variables
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

# Application
SECRET_KEY=your-secret-key
APP_ENV=development
```

#### Optional Environment Variables
```bash
# Google Cloud (Optional)
GCS_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
DOCUMENT_AI_LOCATION=us

# Email Service (Optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM=no-reply@altadata.com

# CORS
CORS_ORIGINS_RAW=http://localhost:3000,http://localhost:8000
```

### Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd alta_data_backend
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Start Services**:
   ```bash
   docker-compose up -d
   ```

3. **Run Migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

4. **Access Points**:
   - **API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **RabbitMQ Management**: http://localhost:15672 (guest/guest)
   - **Flower (Celery Monitor)**: http://localhost:5555

### Production Deployment

#### Azure Deployment
- **Compute**: Azure Container Apps or Azure Kubernetes Service
- **Database**: Azure Database for PostgreSQL
- **Cache**: Azure Cache for Redis
- **Storage**: Azure Blob Storage (alternative to GCS)
- **Secrets**: Azure Key Vault
- **Monitoring**: Azure Monitor and Application Insights

#### Scaling
```bash
# Scale workers
docker-compose up -d --scale worker-ocr=3 --scale worker-email=2

# Scale API
docker-compose up -d --scale api=3
```

---

## Security Features

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Email Verification**: Required for account activation
- **Role-Based Access Control**: Granular permissions per user role
- **Password Security**: Bcrypt hashing with salt

### Rate Limiting
- **Redis-based**: Request throttling per IP and user
- **Endpoint-specific**: Different limits for auth vs. data endpoints
- **Graceful Degradation**: System continues to function if Redis is unavailable

### Input Validation
- **Pydantic Models**: Request/response validation
- **File Upload Validation**: Type, size, and content validation
- **SQL Injection Prevention**: Parameterized queries via ORM

### Security Headers
- **CORS Protection**: Configurable allowed origins
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, etc.
- **Request Correlation**: Unique request IDs for tracing

### Audit Logging
- **Comprehensive Logging**: All user actions and system events
- **Immutable Records**: Audit logs cannot be modified
- **Compliance Ready**: Detailed audit trail for regulatory requirements

### Data Protection
- **Soft Deletes**: Data recovery capability
- **Encryption at Rest**: Database and file storage encryption
- **Secure Token Storage**: Hashed tokens in database
- **Principle of Least Privilege**: Minimal required permissions

---

## Monitoring & Observability

### Health Monitoring
- **Health Checks**: Database, Redis, and RabbitMQ connectivity
- **Readiness Probes**: Service availability checks
- **Liveness Probes**: Application health verification

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Request Tracing**: End-to-end request tracking
- **Error Tracking**: Detailed error context and stack traces
- **Audit Trail**: Complete action history

### Metrics & Analytics
- **Performance Metrics**: Response times, throughput, error rates
- **Business Metrics**: User activity, data processing statistics
- **System Metrics**: Resource utilization, queue depths
- **Custom Dashboards**: Project-specific analytics

### Monitoring Tools
- **Flower**: Celery worker monitoring
- **RabbitMQ Management**: Queue and message monitoring
- **Database Monitoring**: Query performance and connection pools
- **Application Insights**: Azure-based monitoring (production)

### Alerting
- **Service Health**: Automatic alerts for service failures
- **Performance Thresholds**: Response time and error rate alerts
- **Queue Monitoring**: Dead letter queue and processing delays
- **Security Events**: Failed authentication and suspicious activity

---

## API Usage Examples

### Complete Workflow Example

1. **User Registration**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "SecurePass123!"}'
   ```

2. **Email Verification**:
   ```bash
   curl -X GET "http://localhost:8000/api/auth/verify-email?token=verification-token"
   ```

3. **User Login**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "SecurePass123!"}'
   ```

4. **Create Project**:
   ```bash
   curl -X POST http://localhost:8000/api/projects \
     -H "Authorization: Bearer jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Research Project", "description": "Data collection project"}'
   ```

5. **Upload Document**:
   ```bash
   curl -X POST "http://localhost:8000/api/documents?project_id=project-uuid" \
     -H "Authorization: Bearer jwt-token" \
     -F "file=@document.pdf"
   ```

6. **Submit for Review**:
   ```bash
   curl -X POST http://localhost:8000/api/submit \
     -H "Authorization: Bearer jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"document_ids": ["doc-uuid"]}'
   ```

7. **Review Decision**:
   ```bash
   curl -X PATCH "http://localhost:8000/api/review/doc-uuid?item_type=document" \
     -H "Authorization: Bearer jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"decision": "approve", "feedback": "Good quality"}'
   ```

### Error Handling

All API endpoints return structured error responses:

```json
{
  "error": {
    "type": "validation_error|auth_error|not_found|rate_limited|server_error",
    "message": "Detailed error message",
    "requestId": "unique-request-id"
  }
}
```

### Rate Limiting

Rate limits are applied per endpoint:
- **Auth endpoints**: 10 requests/minute per IP
- **Data upload**: 20 requests/minute per user
- **General API**: 100 requests/minute per user

---

This comprehensive documentation covers all aspects of the Alta Data Backend system, from architecture and technology stack to detailed API usage and deployment instructions. The system is designed for scalability, security, and maintainability, providing a robust foundation for data collection and annotation workflows.

