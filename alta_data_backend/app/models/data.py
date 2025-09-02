from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class VoiceSample(Base):
    __tablename__ = 'voice_samples'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey('projects.id', ondelete='CASCADE'))
    uploaded_by_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'))
    original_filename: Mapped[str] = mapped_column(String(255))
    gcs_uri: Mapped[str] = mapped_column(String(512))
    transcription_text: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(32), default='draft')
    duration_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


