# Alta Data Backend Implementation (FastAPI)

## Objective
Build a complete, production-ready FastAPI backend for the Alta Data platform. The backend must be structured for scalability, security, and maintainability, implementing all features from the project description, including user roles, data processing, analytics, audit logging, and email verification.

## Core Technologies & Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL (v12+)
- **ORM:** SQLAlchemy 2.0 + AsyncPG
- **Authentication:** JWT (Bearer tokens) & WebAuthn (Passkeys) via `fastapi-webauthn` or similar
- **Email Service:** SMTP (for transactional emails - verification, invitations)
- **Cloud Services:** Google Cloud Client Libraries for Python (GCS, Document AI, Speech-to-Text)
- **Background Tasks:** Celery with Redis as the broker & result backend
- **Caching:** Redis
- **Logging:** Structlog for structured, JSON-formatted logs

## Project Structure
Generate the code to create the following directory structure:
```
alta_data_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app creation, middleware, CORS, etc.
│   ├── config.py                # Pydantic Settings for configuration
│   ├── database.py              # Database engine, session factory, base class
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── data.py              # Document, VoiceSample models
│   │   └── ...                  # Other models (Invitation, AuditLog, etc.)
│   ├── schemas/                 # Pydantic schemas (request/response models)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   └── ...
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py      # Custom FastAPI dependencies (e.g., get_current_user, RBAC)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── projects.py
│   │   │   ├── data.py          # Endpoints for /documents, /voice
│   │   │   ├── review.py
│   │   │   ├── analytics.py
│   │   │   └── admin.py
│   │   └── utils.py             # Common route utilities
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py          # JWT, password hashing, WebAuthn setup
│   │   ├── email.py             # Email templating and sending functions
│   │   └── storage.py           # GCS client wrapper and operations
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── data_service.py      # Logic for initiating OCR/transcription
│   │   ├── analytics_service.py
│   │   └── background_processor.py # Functions called by Celery workers
│   ├── worker/                  # Celery-specific configuration
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery instance creation
│   │   └── tasks.py             # Celery task definitions (e.g., task_send_email, task_process_ocr)
│   ├── utils/                   # General utilities
│   │   ├── __init__.py
│   │   ├── role_checker.py      # Centralized RBAC logic
│   │   └── audit_logger.py      # Function to write to audit_logs table
│   └── logs.py                  # Structlog configuration
├── alembic/                     # Database migrations
│   ├── versions/
│   └── env.py
├── requirements.txt
├── .env.example
└── README.md
```

## Core Implementation Requirements

### 1. Database Schema (SQLAlchemy Models in `app/models/`)
Implement the following models with async support. Include `is_deleted` or `deleted_at` for soft deletes on all main tables.

**Key Models & Relationships:**
- **User:** `id`, `email`, `hashed_password`, `is_verified`, `global_role`, `created_at`, `passkeys` relationship.
- **Project:** `id`, `name`, `description`, `created_by_id` (FK to User).
- **ProjectMember:** `id`, `project_id` (FK), `user_id` (FK), `role` ('admin', 'contributor', 'reviewer').
- **Document:** `id`, `project_id` (FK), `uploaded_by_id` (FK to User), `original_filename`, `gcs_uri`, `ocr_text` (TEXT, nullable), `status`, `domain`, `submitted_at`, `reviewed_by_id` (FK to User), `feedback`.
- **VoiceSample:** `id`, `project_id` (FK), `uploaded_by_id` (FK), `original_filename`, `gcs_uri`, `transcription_text` (TEXT, nullable), `status`, `duration_seconds`.
- **AuditLog:** `id`, `actor_user_id` (FK), `action`, `resource_type`, `resource_id`, `status`, `ip_address`, `user_agent`, `metadata` (JSON), `created_at`.
- **EmailVerificationToken:** `id`, `user_id` (FK, unique), `token`, `expires_at`.
- **ProjectInvitation:** `id`, `project_id` (FK), `email`, `token`, `role`, `invited_by_id` (FK), `expires_at`, `accepted_at`.

### 2. Authentication & Email Verification
- **JWT:** Implement OAuth2 password flow with JWT access tokens. Tokens must include `user_id` and `global_role`.
- **WebAuthn:** Integrate a library like `fastapi-webauthn` for passkey registration and authentication endpoints.
- **Email Verification:**
  1.  On `POST /auth/register`, create a user with `is_verified=False`.
  2.  Generate a unique token, store it hashed in `EmailVerificationToken`, and set an expiration (e.g., 24 hours).
  3.  Use the `email.py` service to send a verification link (`https://frontend.com/verify-email?token=raw_token`) to the user's inbox via a **Celery background task** (`task_send_email`).
  4.  Implement `GET /auth/verify-email?token=...` to validate the token and set `user.is_verified = True`.
  5.  **Critical:** Most API endpoints (except `/auth/login`, `/auth/register`) should have a dependency that checks `current_user.is_verified`.

### 3. Centralized RBAC (Role-Based Access Control)
- Create a powerful, reusable dependency in `dependencies.py` (e.g., `RoleChecker`).
- It should accept a list of required roles (e.g., `["super_admin"]` or `["project_admin", "project_reviewer"]`).
- It must resolve the `current_user` and the requested resource (e.g., from path parameter `project_id`).
- It must check the user's `global_role` for platform-wide endpoints and their role in the specific `project_members` table for project-scoped endpoints.
- Raise HTTP `403` exceptions for unauthorized requests.

### 4. Data Ingestion & Background Processing (Celery)
- **File Upload (`POST /documents`, `POST /voice`):**
  1.  RBAC check: User must be a `contributor`/`admin` in the project.
  2.  Save file metadata to DB with status `'draft'`.
  3.  Upload the file bytes to GCS.
  4.  **Enqueue a Celery task** (e.g., `task_process_ocr.delay(document_id)`) for async processing.
- **Celery Worker (`app/worker/tasks.py`):**
  1.  Task `task_process_ocr`: Fetches document record, downloads file from GCS, calls Google Document AI, updates the document's `ocr_text` field, and sets status to `'pending_review'` (or `'approved'` if no reviewers exist).
  2.  Task `task_send_email`: Sends emails (verification, invitations) asynchronously to avoid blocking the API.

### 5. Review Workflow & Analytics
- **Review Endpoints (`PATCH /review/{document_id}`):** Update status, log reviewer action, and write an `AuditLog` entry.
- **Analytics Endpoints (`GET /analytics/summary`):**
  - Implement complex SQLAlchemy queries with grouping and filtering based on the `timeFrame` parameter.
  - Use SQL functions like `func.count()`, `func.sum()`, and `func.date()` for trends.
  - Enforce strict RBAC: Super Admin gets global stats, Project Manager gets scoped stats.

### 6. Audit Logging
- Create a utility function `log_audit_event(action, status, resource_type, resource_id, metadata)`.
- Inject this into route dependencies or call it directly within services after critical actions (user login, document approval, role change).
- Ensure every log includes the `actor_user_id`, `ip_address`, and timestamp.

## API Endpoints to Implement
- `POST /auth/register` (with email verification flow)
- `POST /auth/login` (JWT & Passkey)
- `GET /auth/verify-email`
- `GET /auth/me`
- `GET/POST /projects`
- `GET/PUT/DELETE /projects/{project_id}`
- `POST /projects/{project_id}/invite`
- `POST /invitations/{token}/accept`
- `POST /documents` -> triggers Celery -> OCR -> DB update
- `POST /voice` -> triggers Celery -> Speech-to-Text -> DB update
- `GET /review?project_id=...`
- `PATCH /review/{document_id}`
- `GET /analytics/summary?timeframe=30d&project_id=optional`
- `GET /admin/users` (super_admin only)

## Non-Functional Requirements
- **Async Throughout:** Use `asyncpg`, `sqlalchemy.ext.asyncio`, and `httpx.AsyncClient` for all I/O operations.
- **Pydantic Validation:** Use Pydantic V2 for all request and response models, leveraging its powerful validation.
- **Security:** Hash all tokens (JWT secrets, email tokens). Never expose sensitive data in responses. Use rate limiting on auth endpoints.
- **Error Handling:** Implement a unified global exception handler to return structured JSON errors.
- **Logging:** Use Structlog. Correlate logs by including `request_id`, `user_id`, and `project_id` in every log entry for a request.
- **Health Checks:** Implement `/health` endpoint that checks database and Redis connectivity.
```