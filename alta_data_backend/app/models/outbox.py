from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Integer, Enum
from enum import Enum as PyEnum
from uuid import uuid4
from ..database import Base


class OutboxEventStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutboxEventType(PyEnum):
    DOCUMENT_OCR_REQUESTED = "document_ocr_requested"
    VOICE_TRANSCRIPTION_REQUESTED = "voice_transcription_requested"
    EMAIL_SEND_REQUESTED = "email_send_requested"
    USER_REGISTERED = "user_registered"
    PROJECT_CREATED = "project_created"
    DOCUMENT_APPROVED = "document_approved"
    DOCUMENT_REJECTED = "document_rejected"


class OutboxEvent(Base):
    """Outbox table for reliable message delivery using the outbox pattern"""
    __tablename__ = 'outbox_events'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)  # ID of the entity that triggered the event
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Type of entity (Document, User, etc.)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON payload
    status: Mapped[str] = mapped_column(String(20), default=OutboxEventStatus.PENDING.value)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_attempt_at: Mapped[str] = mapped_column(String(50), nullable=True)  # ISO timestamp
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    processed_at: Mapped[str] = mapped_column(String(50), nullable=True)  # ISO timestamp
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)  # ISO timestamp
