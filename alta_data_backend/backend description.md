# Alta Data Backend Implementation Specification (FastAPI)

This document describes a production-ready backend implementation for Alta Data, consolidating requirements from the product description and API plan. It emphasizes security, scalability, and maintainability, and is structured to be executable by an engineering team.

## 1. Architecture Overview

- Framework: FastAPI (async-first)
- Database: PostgreSQL (12+)
- ORM: SQLAlchemy 2.0 with asyncio + Alembic migrations
- Auth: JWT (Bearer) + WebAuthn (Passkeys)
- Cache/Queues: Redis (rate limiting, caching, Celery broker/result)
- Background Processing: Celery workers for OCR/transcription/emails
- Object Storage: Google Cloud Storage (GCS)
- External AI Services: Google Document AI (OCR), Google Speech-to-Text
- Email: SMTP (transactional emails: verification, invitations)
- Logging: Structlog (JSON), centralized request correlation
- Containerization: Docker (dev/prod parity)
- Cloud: Deploy to Azure (compute, secrets, monitoring). Google Cloud used for data services only.

Key qualities:
- Async I/O end-to-end for performance
- Clear layering (API -> Services -> Repositories/Integrations)
- Centralized RBAC and auditing
- Soft deletes for recoverability
- Idempotency for critical mutations
- Strong observability (structured logs, correlations, health checks)

## 2. Project Layout

Create the following structure:

```
alta_data_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, middleware, CORS, routers
│   ├── config.py                # Pydantic Settings
│   ├── database.py              # Async engine, session factory, Base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── data.py              # Document, VoiceSample
│   │   ├── invitation.py        # EmailVerificationToken, ProjectInvitation
│   │   └── audit.py             # AuditLog
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── data.py
│   │   ├── auth.py
│   │   └── analytics.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py      # current_user, RoleChecker, pagination, etc.
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── projects.py
│   │   │   ├── data.py          # /documents, /voice
│   │   │   ├── review.py
│   │   │   ├── analytics.py
│   │   │   └── admin.py
│   │   └── utils.py             # common response helpers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py          # JWT, hashing, WebAuthn setup
│   │   ├── email.py             # SMTP client + templates
│   │   └── storage.py           # GCS wrapper
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── data_service.py      # Upload, OCR/transcription orchestration
│   │   ├── analytics_service.py
│   │   └── background_processor.py
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery configuration, app factory
│   │   └── tasks.py             # task_send_email, task_process_ocr, task_transcribe
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── role_checker.py      # Centralized RBAC
│   │   └── audit_logger.py      # Write to audit_logs
│   └── logs.py                  # Structlog config
├── alembic/
│   ├── versions/
│   └── env.py
├── requirements.txt
├── .env.example
└── README.md
```

## 3. Configuration

Use Pydantic Settings in `config.py` reading from environment variables. Provide `.env.example` with keys:

- APP_ENV, APP_NAME, SECRET_KEY, JWT_ALG
- POSTGRES_* (host, port, db, user, password)
- REDIS_URL
- SMTP_* (host, port, user, password, from)
- GCS_PROJECT_ID, GCS_BUCKET_NAME, GOOGLE_APPLICATION_CREDENTIALS
- WEBAUTHN_RP_ID, WEBAUTHN_RP_NAME
- RATE_LIMITS (e.g., 20/min login)
- CORS origins

Configuration is injected into app lifespan and Celery. Secrets are expected to be stored in Azure Key Vault in production; local dev uses .env.

## 4. Database Models (Soft Deletes Enabled)

All major tables include `deleted_at TIMESTAMP WITH TIME ZONE NULL` for soft deletes and `created_at/updated_at` timestamps.

### 4.1 User
- id (UUID), email (unique), hashed_password, is_verified (bool), global_role (enum: super_admin, user), created_at, updated_at
- passkeyCredentials relation (optional separate table if needed by WebAuthn library)

### 4.2 Project
- id (UUID), name, description, created_by_id (FK User), created_at, updated_at

### 4.3 ProjectMember
- id (UUID), project_id (FK), user_id (FK), role (enum: admin, contributor, reviewer), created_at
- unique constraint (project_id, user_id)

### 4.4 Document
- id (UUID), project_id, uploaded_by_id, original_filename, gcs_uri, ocr_text (TEXT NULL), status (enum: draft, pending_review, approved, rejected), domain (nullable string), submitted_at (nullable), reviewed_by_id (FK User, nullable), feedback (nullable TEXT), created_at/updated_at

### 4.5 VoiceSample
- id (UUID), project_id, uploaded_by_id, original_filename, gcs_uri, transcription_text (TEXT NULL), status (enum), duration_seconds (INT), created_at/updated_at

### 4.6 AuditLog
- id (UUID), actor_user_id (FK), action (string), resource_type (string), resource_id (UUID/string), status (success/failure), ip_address, user_agent, metadata (JSONB), created_at

### 4.7 EmailVerificationToken
- id (UUID), user_id (unique FK), token_hash (string), expires_at (timestamp)

### 4.8 ProjectInvitation
- id (UUID), project_id (FK), email, token_hash, role (enum), invited_by_id (FK User), expires_at, accepted_at (nullable)

Alembic migrations are generated for initial schema and subsequent changes. Default scopes filter out `deleted_at IS NOT NULL`.

## 5. Authentication

### 5.1 JWT (Email/Password)
- Endpoint: POST `/api/auth/login`
- Password hashing with Argon2 or bcrypt
- JWT contains `sub` (user_id), `global_role`, `exp`
- Token lifetime configurable (e.g., 15m access + optional refresh)
- Dependency `get_current_user` validates token and `is_verified` unless endpoint is public

### 5.2 Registration & Email Verification
- Endpoint: POST `/api/auth/register` creates user with `is_verified=False`
- Generate random token, persist only `token_hash` in `EmailVerificationToken` with 24h expiry
- Send verification email via Celery `task_send_email` with link `https://frontend.com/verify-email?token=<raw>`
- Endpoint: GET `/api/auth/verify-email?token=...` verifies token, sets `is_verified=True`, deletes token record, logs audit event
- Most endpoints require verified users; enforced via dependency

### 5.3 Passkeys (WebAuthn)
- Endpoints:
  - POST `/api/auth/passkeys/register`
  - POST `/api/auth/passkeys/register/verify`
  - POST `/api/auth/passkeys/login`
  - POST `/api/auth/passkeys/login/verify`
- Use `fastapi-webauthn` (or equivalent) for options/challenge generation and assertion verification

### 5.4 Rate Limiting
- Apply stricter limits to `/auth/*` endpoints via Redis counters (e.g., 10/min per IP, lower for login)

## 6. Centralized RBAC

Implement `RoleChecker` in `utils/role_checker.py` and expose dependencies in `api/dependencies.py`:

- Platform roles via `User.global_role` (e.g., `super_admin`)
- Project-scoped roles via `ProjectMember.role`
- Resolver pulls `project_id`/`document_id` from path/query to determine scope
- Raises HTTP 403 for unauthorized

Examples:
- Super Admin: allowed on `/api/admin/*` and global analytics
- Project Manager (admin): full control within project
- Contributor: can upload/manage own drafts until submitted
- Reviewer: can review but not modify project settings

## 7. File Storage & Data Processing

### 7.1 Upload Flow (Documents & Voice)
1) RBAC: must be project `admin` or `contributor`
2) Create DB record status=`draft`
3) Stream upload bytes to GCS; store `gcs_uri`
4) Enqueue Celery task for OCR/transcription:
   - Documents: `task_process_ocr(document_id)`
   - Voice: `task_transcribe(voice_sample_id)`

### 7.2 Celery Workers
- `task_process_ocr`:
  - Download from GCS
  - Call Document AI; update `ocr_text`
  - If project has reviewers: set `pending_review`; else auto-approve
  - Log audit event
- `task_transcribe`:
  - Download from GCS
  - Call Speech-to-Text; update `transcription_text`
  - Transition to `pending_review` similarly

### 7.3 Submission & Review
- POST `/api/projects/{project_id}/review` to submit item for review (or automatic after processing)
- GET `/api/review?project_id=...` returns queue for reviewers
- PATCH `/api/review/{document_id}` approve/reject with feedback; writes AuditLog

## 8. API Endpoints

Base path prefix: `/api`.

### 8.1 Auth
- POST `/auth/register`
- POST `/auth/login`
- GET `/auth/verify-email`
- GET `/auth/me`
- Passkeys: see §5.3

### 8.2 Projects
- GET/POST `/projects`
- GET/PUT/DELETE `/projects/{project_id}` (soft delete)
- POST `/projects/{project_id}/invite` (ProjectInvitation, email via Celery)
- POST `/invitations/{token}/accept`

### 8.3 Data Ingestion
- POST `/documents` (multipart upload)
- POST `/voice` (multipart upload)

### 8.4 Review
- GET `/review?project_id=...`
- PATCH `/review/{document_id}`

### 8.5 Analytics
- GET `/analytics/summary?timeframe=7d|30d|365d[&projectId=...]`
- GET `/analytics/user/{userId}`
- GET `/admin/users` (super_admin only)

## 9. Analytics Implementation

Use SQLAlchemy with aggregates and time bucketing:
- Counts by status for documents and voice samples
- Trends: group by `date_trunc('day', created_at)`
- Storage usage: sum of object sizes (from GCS metadata cached in DB or on-demand and cached)
- Top contributors: order by count of submissions within timeframe
- Scope: if `projectId` provided, restrict to that project; else global

## 10. Audit Logging

`utils/audit_logger.py` provides `log_audit_event(action, status, resource_type, resource_id, metadata)` and captures:
- actor_user_id (from dependency)
- ip_address, user_agent (from request)
- Correlates with `request_id`

Events to log:
- Auth: login success/failure, logout, passkey register, email verify
- Projects: created/deleted, role changes, invitations sent/accepted
- Data: uploaded, submitted, OCR/transcribed, approved/rejected
- Admin: user role changed

## 11. Error Handling & Responses

Global exception handlers return structured errors:
```
{
  "error": {
    "type": "validation_error|auth_error|not_found|rate_limited|server_error",
    "message": "...",
    "requestId": "..."
  }
}
```
Include `request_id` in every response header and body error.

## 12. Logging & Observability

- Structlog JSON logs with bindings: `request_id`, `user_id`, `project_id`, `path`, `latency_ms`
- Access logs (high volume) vs Audit logs (business events)
- Integrate with Azure Monitor / Application Insights
- Health checks: `/health` checks DB and Redis connectivity

## 13. Caching & Rate Limiting

- Redis-based request counters for auth endpoints
- Optional Redis caching for frequently requested analytics (short TTL, e.g., 60s)

## 14. Security

- Hash all secrets and tokens at rest (store verification/invite tokens as hashes)
- Enforce `is_verified=True` on protected endpoints
- Validate file types and sizes on upload; virus/malware scanning hook optional
- Principle of least privilege for GCS credentials
- RBAC enforced centrally; avoid scattered checks
- Parameterized queries via ORM; no raw SQL without bind params

## 15. Testing

- Unit tests for services and utilities
- Integration tests with ephemeral Postgres and Redis (Testcontainers) and local GCS emulator or mocks
- E2E smoke tests for critical flows (register -> verify -> login -> upload -> review)
- CI pipeline runs test suite and Alembic migrations

## 16. Deployment (Azure)

- Containerize API and worker images
- Use Azure Container Apps/Azure Kubernetes Service
- Azure Key Vault for secrets; inject via environment
- Azure Monitor for logs/metrics; dashboards for key SLOs
- Managed Redis (Azure Cache for Redis)
- Postgres (Azure Database for PostgreSQL)

## 17. Idempotency & Soft Deletes

- For uploads and mutations, accept `Idempotency-Key` header and persist keys for a short window to deduplicate retries
- Use `deleted_at` for soft deletes; exclude by default; allow admin-only hard delete jobs

## 18. Example Requirements and .env

`requirements.txt` (excerpt):
- fastapi
- uvicorn[standard]
- pydantic>=2
- sqlalchemy>=2, asyncpg
- alembic
- passlib[bcrypt]
- python-jose[cryptography] or pyjwt
- fastapi-webauthn (or library of choice)
- structlog
- celery, redis
- google-cloud-storage, google-cloud-documentai, google-cloud-speech
- httpx
- email-normalize, jinja2

`.env.example` (excerpt):
```
APP_ENV=development
SECRET_KEY=changeme
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
REDIS_URL=redis://localhost:6379/0
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=no-reply@altadata.local
GCS_PROJECT_ID=
GCS_BUCKET_NAME=
GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=Alta Data
CORS_ORIGINS=http://localhost:3000
```

## 19. Implementation Notes

- Prefer service layer for business logic, routes remain thin
- Always wrap background triggers in try/catch and log failures with context
- Use pagination and filtering on list endpoints
- Normalize emails and enforce unique constraints
- Document API with OpenAPI tags and examples

## 20. Done Criteria

- All endpoints implemented and protected by RBAC
- Email verification flow works end-to-end
- Uploads store to GCS; Celery processes OCR/transcription
- Review workflow produces AuditLog entries
- Analytics return correct scoped metrics with timeframe filter
- Structured logs with request correlation and health checks pass


