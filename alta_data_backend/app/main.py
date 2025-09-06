from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import redis
import os
import asyncio

from .config import settings
from .database import engine, Base

# Import all models to ensure they're registered with SQLAlchemy
from .models.user import User
from .models.project import Project, ProjectMember
from .models.data import Document, VoiceSample, RawText
from .models.invitation import EmailVerificationToken, ProjectInvitation
from .models.audit import AuditLog
from .models.outbox import OutboxEvent
from .api.routes.auth import router as auth_router
from .api.routes.projects import router as projects_router
from .api.routes.data import router as data_router
from .api.routes.review import router as review_router
from .api.routes.analytics import router as analytics_router
from .api.routes.admin import router as admin_router
from .api.routes.health import router as health_router
from .api.routes.processing import router as processing_router

# Import middleware
from .middleware.security import (
    SecurityHeadersMiddleware,
    RequestCorrelationMiddleware,
    InputValidationMiddleware,
    RateLimitMiddleware,
    AuditLoggingMiddleware
)
from .middleware.validation import ValidationMiddleware
from .middleware.error_handling import (
    alta_data_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
    AltaDataException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException,
    RateLimitException,
    ServerException
)

# Import SQLAlchemy exceptions
from sqlalchemy.exc import SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Initialize Redis client
redis_client = None
try:
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.ping()  # Test connection
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev-only: create tables if not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start outbox processor
    from .worker.outbox_processor import start_outbox_processor, stop_outbox_processor
    outbox_task = asyncio.create_task(start_outbox_processor())
    
    try:
        yield
    finally:
        # Stop outbox processor
        await stop_outbox_processor()
        outbox_task.cancel()
        try:
            await outbox_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title='Alta Data API',
    version='0.1.0',
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc'
)

# Add CORS middleware FIRST (order matters!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allow_headers=['*'],
)

# Add other middleware
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(RequestCorrelationMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(ValidationMiddleware)  # Disabled - FastAPI handles validation automatically
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

# Add trusted host middleware for production
if settings.app_env == 'production':
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.yourdomain.com"])
    app.add_middleware(HTTPSRedirectMiddleware)

# Add exception handlers
app.add_exception_handler(AltaDataException, alta_data_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(data_router)
app.include_router(review_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(processing_router)


