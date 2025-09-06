from celery import Celery
from google.cloud import documentai, speech
from google.cloud import storage
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from datetime import datetime, timezone
import os
import tempfile
import json
import asyncio
from typing import Optional

from .celery_app import celery_app
from ..config import settings
from ..models.data import Document, VoiceSample
from ..models.audit import AuditLog
from ..core.email import send_email
from ..core.document_ai import document_ai_service
from ..core.speech_to_text import speech_to_text_service
from ..utils.audit_logger import log_audit_event


# Database setup for Celery tasks
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@celery_app.task(
    bind=True, 
    max_retries=3,
    default_retry_delay=60,
    queue='ocr_queue',
    routing_key='ocr'
)
def task_process_ocr(self, document_id: str):
    """Process OCR for a document using Google Document AI"""
    try:
        # Get document from database
        result = asyncio.run(_get_document(document_id))
        if not result:
            raise Exception(f"Document {document_id} not found")
        
        document = result
        
        # Check if Document AI service is available
        if not document_ai_service.is_available():
            # Mark as processed but with no OCR text
            asyncio.run(_update_document_ocr(document_id, None))
            
            # Log audit event
            asyncio.run(_log_audit_event(
                action="DOCUMENT_OCR_SKIPPED",
                status="warning",
                resource_type="Document",
                resource_id=document_id,
                metadata={"reason": "Document AI service not available"}
            ))
            
            return {"status": "skipped", "document_id": document_id, "reason": "Document AI service not available"}
        
        # Process with Google Document AI
        ocr_text = document_ai_service.process_document(
            gcs_uri=document.gcs_uri,
            processor_id=settings.document_ai_processor_id,
            location=settings.document_ai_location
        )
        
        # Update document in database
        asyncio.run(_update_document_ocr(document_id, ocr_text))
        
        # Log audit event
        asyncio.run(_log_audit_event(
            action="DOCUMENT_OCR_PROCESSED",
            status="success",
            resource_type="Document",
            resource_id=document_id,
            metadata={"ocr_text_length": len(ocr_text) if ocr_text else 0}
        ))
        
        return {"status": "success", "document_id": document_id, "ocr_text_length": len(ocr_text) if ocr_text else 0}
        
    except Exception as exc:
        # Log error
        asyncio.run(_log_audit_event(
            action="DOCUMENT_OCR_FAILED",
            status="failure",
            resource_type="Document",
            resource_id=document_id,
            metadata={"error": str(exc), "retry_count": self.request.retries}
        ))
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    bind=True, 
    max_retries=3,
    default_retry_delay=60,
    queue='transcription_queue',
    routing_key='transcription'
)
def task_transcribe_audio(self, voice_sample_id: str):
    """Transcribe audio using Google Speech-to-Text"""
    try:
        # Get voice sample from database
        result = asyncio.run(_get_voice_sample(voice_sample_id))
        if not result:
            raise Exception(f"Voice sample {voice_sample_id} not found")
        
        voice_sample = result
        
        # Check if Speech-to-Text service is available
        if not speech_to_text_service.is_available():
            # Mark as processed but with no transcription
            asyncio.run(_update_voice_sample_transcription(voice_sample_id, None, None))
            
            # Log audit event
            asyncio.run(_log_audit_event(
                action="VOICE_SAMPLE_TRANSCRIPTION_SKIPPED",
                status="warning",
                resource_type="VoiceSample",
                resource_id=voice_sample_id,
                metadata={"reason": "Speech-to-Text service not available"}
            ))
            
            return {"status": "skipped", "voice_sample_id": voice_sample_id, "reason": "Speech-to-Text service not available"}
        
        # Process with Google Speech-to-Text
        transcription_text, duration = speech_to_text_service.transcribe_audio(
            gcs_uri=voice_sample.gcs_uri,
            language_code="en-US"
        )
        
        # Update voice sample in database
        asyncio.run(_update_voice_sample_transcription(voice_sample_id, transcription_text, duration))
        
        # Log audit event
        asyncio.run(_log_audit_event(
            action="VOICE_SAMPLE_TRANSCRIBED",
            status="success",
            resource_type="VoiceSample",
            resource_id=voice_sample_id,
            metadata={"transcription_length": len(transcription_text) if transcription_text else 0, "duration": duration}
        ))
        
        return {"status": "success", "voice_sample_id": voice_sample_id, "transcription_length": len(transcription_text) if transcription_text else 0}
        
    except Exception as exc:
        # Log error
        asyncio.run(_log_audit_event(
            action="VOICE_SAMPLE_TRANSCRIPTION_FAILED",
            status="failure",
            resource_type="VoiceSample",
            resource_id=voice_sample_id,
            metadata={"error": str(exc), "retry_count": self.request.retries}
        ))
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    bind=True, 
    max_retries=3,
    default_retry_delay=30,
    queue='email_queue',
    routing_key='email'
)
def task_send_email(self, to_email: str, subject: str, body: str, email_type: str = "general"):
    """Send email asynchronously"""
    try:
        # Check if email service is available
        from ..core.email import is_email_available
        if not is_email_available():
            # Log audit event for skipped email
            asyncio.run(_log_audit_event(
                action="EMAIL_SKIPPED",
                status="warning",
                resource_type="Email",
                resource_id=None,
                metadata={"to": to_email, "subject": subject, "type": email_type, "reason": "Email service not available"}
            ))
            
            return {"status": "skipped", "to": to_email, "subject": subject, "reason": "Email service not available"}
        
        # Send email
        success = send_email(to_email, subject, body)
        
        if success:
            # Log audit event
            asyncio.run(_log_audit_event(
                action="EMAIL_SENT",
                status="success",
                resource_type="Email",
                resource_id=None,
                metadata={"to": to_email, "subject": subject, "type": email_type}
            ))
            
            return {"status": "success", "to": to_email, "subject": subject}
        else:
            # Log audit event for failed email
            asyncio.run(_log_audit_event(
                action="EMAIL_FAILED",
                status="failure",
                resource_type="Email",
                resource_id=None,
                metadata={"to": to_email, "subject": subject, "type": email_type, "reason": "Email sending failed"}
            ))
            
            return {"status": "failed", "to": to_email, "subject": subject, "reason": "Email sending failed"}
        
    except Exception as exc:
        # Log error
        asyncio.run(_log_audit_event(
            action="EMAIL_FAILED",
            status="failure",
            resource_type="Email",
            resource_id=None,
            metadata={"to": to_email, "error": str(exc), "retry_count": self.request.retries}
        ))
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


# Helper functions for database operations
async def _get_document(document_id: str) -> Optional[Document]:
    """Get document from database"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()


async def _get_voice_sample(voice_sample_id: str) -> Optional[VoiceSample]:
    """Get voice sample from database"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(VoiceSample).where(VoiceSample.id == voice_sample_id))
        return result.scalar_one_or_none()


async def _update_document_ocr(document_id: str, ocr_text: str):
    """Update document with OCR text"""
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(ocr_text=ocr_text, status='pending_review')
        )
        await session.commit()


async def _update_voice_sample_transcription(voice_sample_id: str, transcription_text: str, duration: int):
    """Update voice sample with transcription"""
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(VoiceSample)
            .where(VoiceSample.id == voice_sample_id)
            .values(transcription_text=transcription_text, duration_seconds=duration, status='pending_review')
        )
        await session.commit()


async def _log_audit_event(action: str, status: str, resource_type: str, resource_id: Optional[str], metadata: dict):
    """Log audit event to database"""
    async with AsyncSessionLocal() as session:
        audit_log = AuditLog(
            actor_user_id=None,  # System action
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            metadata=metadata
        )
        session.add(audit_log)
        await session.commit()


# Note: Google Cloud service integration is now handled by:
# - app.core.document_ai.DocumentAIService
# - app.core.speech_to_text.SpeechToTextService
