from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import DateTime, Column
from datetime import datetime, timezone
from .config import settings


class BaseModel:
    """Base model with common fields for all tables"""
    __abstract__ = True
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True, default=None)


Base = declarative_base(cls=BaseModel)

# Import all models to ensure they're registered with SQLAlchemy
from .models.user import User
from .models.project import Project, ProjectMember
from .models.data import Document, VoiceSample, RawText
from .models.invitation import EmailVerificationToken, ProjectInvitation
from .models.audit import AuditLog
from .models.outbox import OutboxEvent
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session




