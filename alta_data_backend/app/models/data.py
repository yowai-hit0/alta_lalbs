from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Text, Integer, DateTime, Boolean
from datetime import datetime, timezone
from uuid import uuid4
from ..database import Base


class Document(Base):
    __tablename__ = 'documents'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'))
    uploaded_by_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'))
    original_filename: Mapped[str] = mapped_column(String(255))
    gcs_uri: Mapped[str] = mapped_column(String(512))
    ocr_text: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(32), default='draft')  # draft|pending_review|approved|rejected
    domain: Mapped[str | None] = mapped_column(String(120), default=None)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reviewed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('users.id'), default=None)
    feedback: Mapped[str | None] = mapped_column(Text, default=None)
    is_raw: Mapped[bool] = mapped_column(Boolean, default=False)  # True for manual data entry
    processed: Mapped[bool] = mapped_column(Boolean, default=False)  # True if OCR has been processed
    tags: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string of tags
    metadata: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string of additional metadata


class VoiceSample(Base):
    __tablename__ = 'voice_samples'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'))
    uploaded_by_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'))
    original_filename: Mapped[str] = mapped_column(String(255))
    gcs_uri: Mapped[str] = mapped_column(String(512))
    transcription_text: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(32), default='draft')  # draft|pending_review|approved|rejected
    duration_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reviewed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('users.id'), default=None)
    feedback: Mapped[str | None] = mapped_column(Text, default=None)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)  # True if transcription has been processed
    language: Mapped[str | None] = mapped_column(String(10), default=None)  # Language code
    tags: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string of tags
    metadata: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string of additional metadata


class RawText(Base):
    __tablename__ = 'raw_texts'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'))
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default='draft')  # draft|pending_review|approved|rejected
    domain: Mapped[str | None] = mapped_column(String(120), default=None)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reviewed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('users.id'), default=None)
    feedback: Mapped[str | None] = mapped_column(Text, default=None)
    tags: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string of tags
    metadata: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string of additional metadata


