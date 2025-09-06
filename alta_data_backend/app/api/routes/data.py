import os
import mimetypes
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...database import get_db
from ...models.data import Document, VoiceSample, RawText
from ...models.project import ProjectMember, Project
from ...core.storage import upload_bytes
from ...config import settings
from ..dependencies import get_current_user, project_role_required
from ..dependencies import get_current_user as CurrentUser
from ...schemas.data_validators import (
    DocumentUploadRequest, VoiceUploadRequest, DocumentUpdateRequest,
    VoiceUpdateRequest, DocumentSearchRequest, VoiceSearchRequest,
    RawTextCreateRequest, RawTextUpdateRequest, RawTextSearchRequest,
    MassSubmissionRequest, FileUploadValidator
)


router = APIRouter(tags=['data'])

# File upload limits and allowed types
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_DOC_TYPES = {
    'application/pdf',
    'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp',
    'text/plain', 'text/csv',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
}
ALLOWED_AUDIO_TYPES = {
    'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/flac'
}


def validate_file_upload(file: UploadFile, allowed_types: set, max_size: int = MAX_FILE_SIZE) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail='No filename provided')
    
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > max_size:
        raise HTTPException(status_code=413, detail=f'File too large. Maximum size: {max_size // (1024*1024)}MB')
    
    # Check content type
    if file.content_type and file.content_type not in allowed_types:
        # Try to guess from filename if content_type is missing/wrong
        guessed_type, _ = mimetypes.guess_type(file.filename)
        if guessed_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f'File type not allowed. Allowed: {", ".join(sorted(allowed_types))}')


@router.post('/documents')
async def upload_document(
    project_id: str = Query(..., description="Project ID"),
    domain: str | None = Query(None, description="Document domain"),
    is_raw: bool = Query(False, description="Mark as raw text (manual entry)"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    # Validate request parameters
    upload_request = DocumentUploadRequest(project_id=project_id, domain=domain)
    
    # Validate file before processing
    validate_file_upload(file, ALLOWED_DOC_TYPES)
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail='Empty file')
    
    # Check size after reading
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB')
    
    # Verify project exists and user has access
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    
    # Upload to GCS (if available) or use local storage
    from ...core.storage import is_gcs_available
    
    if is_gcs_available():
        blob_path = f'documents/{project_id}/{datetime.now(timezone.utc).timestamp()}_{file.filename}'
        bucket = settings.gcs_bucket_name
    
    try:
        gcs_uri = upload_bytes(bucket, blob_path, content, file.content_type or 'application/octet-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {str(e)}')
    else:
        # Use local storage when GCS is not available
        gcs_uri = f'local://documents/{project_id}/{datetime.now(timezone.utc).timestamp()}_{file.filename}'
        # In a production environment, you might want to implement local file storage here
    
    doc = Document(
        project_id=project_id,
        uploaded_by_id=current_user.id,
        original_filename=file.filename,
        gcs_uri=gcs_uri,
        domain=domain,
        is_raw=is_raw,
        processed=is_raw,  # Raw documents are considered "processed" since no OCR needed
    )
    db.add(doc)
    await db.flush()  # Get the ID without committing
    
    try:
        # Only create outbox event for OCR processing if not raw text
        if not is_raw:
            from ...services.outbox_service import outbox_service
            from ...models.outbox import OutboxEventType

            await outbox_service.create_event(
                session=db,
                event_type=OutboxEventType.DOCUMENT_OCR_REQUESTED,
                aggregate_id=doc.id,
                aggregate_type="Document",
                payload={
                    "document_id": doc.id,
                    "gcs_uri": gcs_uri,
                    "filename": file.filename,
                    "domain": domain
                }
            )

        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')
    
    return {
        'id': doc.id, 
        'gcs_uri': gcs_uri, 
        'status': 'draft',
        'is_raw': is_raw,
        'processed': is_raw
    }


@router.post('/voice')
async def upload_voice(
    project_id: str = Query(..., description="Project ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    # Validate request parameters
    upload_request = VoiceUploadRequest(project_id=project_id)
    
    # Validate file before processing
    validate_file_upload(file, ALLOWED_AUDIO_TYPES)
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail='Empty file')
    
    # Check size after reading
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB')
    
    # Verify project exists and user has access
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    
    # Upload to GCS (if available) or use local storage
    from ...core.storage import is_gcs_available
    
    if is_gcs_available():
        blob_path = f'voice/{project_id}/{datetime.now(timezone.utc).timestamp()}_{file.filename}'
        bucket = settings.gcs_bucket_name
    
    try:
        gcs_uri = upload_bytes(bucket, blob_path, content, file.content_type or 'application/octet-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {str(e)}')
    else:
        # Use local storage when GCS is not available
        gcs_uri = f'local://voice/{project_id}/{datetime.now(timezone.utc).timestamp()}_{file.filename}'
        # In a production environment, you might want to implement local file storage here
    
    voice = VoiceSample(
        project_id=project_id,
        uploaded_by_id=current_user.id,
        original_filename=file.filename,
        gcs_uri=gcs_uri,
        processed=False,  # Will be processed by background task
    )
    db.add(voice)
    await db.flush()  # Get the ID without committing
    
    try:
        # Create outbox event for transcription processing
        from ...services.outbox_service import outbox_service
        from ...models.outbox import OutboxEventType
        
        await outbox_service.create_event(
            session=db,
            event_type=OutboxEventType.VOICE_TRANSCRIPTION_REQUESTED,
            aggregate_id=voice.id,
            aggregate_type="VoiceSample",
            payload={
                "voice_sample_id": voice.id,
                "gcs_uri": gcs_uri,
                "filename": file.filename
            }
        )
        
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')
    
    return {
        'id': voice.id, 
        'gcs_uri': gcs_uri, 
        'status': 'draft',
        'processed': False
    }


# Raw Text Management Routes
@router.post('/raw-text')
async def create_raw_text(
    payload: RawTextCreateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    """Create raw text entry for manual data entry"""
    # Verify user has access to the project
    project_member = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == payload.project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not project_member.scalar_one_or_none():
        raise HTTPException(status_code=403, detail='Access denied to project')
    
    # Create raw text entry
    raw_text = RawText(
        project_id=payload.project_id,
        created_by_id=current_user.id,
        title=payload.title,
        content=payload.content,
        domain=payload.domain,
        tags=json.dumps(payload.tags) if payload.tags else None,
        metadata=json.dumps(payload.metadata) if payload.metadata else None,
        status='draft'
    )
    
    db.add(raw_text)
    await db.commit()
    
    return {
        'id': raw_text.id,
        'title': raw_text.title,
        'status': raw_text.status,
        'created_at': raw_text.created_at
    }


@router.get('/raw-text/{raw_text_id}')
async def get_raw_text(
    raw_text_id: str = Path(..., description='Raw text ID'),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get raw text entry"""
    raw_text = await db.execute(
        select(RawText).where(RawText.id == raw_text_id)
    )
    raw_text = raw_text.scalar_one_or_none()
    
    if not raw_text:
        raise HTTPException(status_code=404, detail='Raw text not found')
    
    # Check access permissions
    project_member = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == raw_text.project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not project_member.scalar_one_or_none():
        raise HTTPException(status_code=403, detail='Access denied')
    
    # Contributors can only see their own drafts, reviewers can see all submitted
    if (raw_text.status == 'draft' and raw_text.created_by_id != current_user.id):
        member = project_member.scalar_one()
        if member.role not in ['admin', 'reviewer']:
            raise HTTPException(status_code=403, detail='Access denied to draft')
    
    return {
        'id': raw_text.id,
        'title': raw_text.title,
        'content': raw_text.content,
        'domain': raw_text.domain,
        'status': raw_text.status,
        'tags': json.loads(raw_text.tags) if raw_text.tags else [],
        'metadata': json.loads(raw_text.metadata) if raw_text.metadata else {},
        'created_at': raw_text.created_at,
        'updated_at': raw_text.updated_at
    }


@router.put('/raw-text/{raw_text_id}')
async def update_raw_text(
    raw_text_id: str = Path(..., description='Raw text ID'),
    payload: RawTextUpdateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    """Update raw text entry (only if draft and owned by user)"""
    raw_text = await db.execute(
        select(RawText).where(RawText.id == raw_text_id)
    )
    raw_text = raw_text.scalar_one_or_none()
    
    if not raw_text:
        raise HTTPException(status_code=404, detail='Raw text not found')
    
    # Only allow updates if draft and owned by user
    if raw_text.status != 'draft':
        raise HTTPException(status_code=400, detail='Cannot update submitted raw text')
    
    if raw_text.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail='Can only update your own raw text')
    
    # Update fields
    if payload.title is not None:
        raw_text.title = payload.title
    if payload.content is not None:
        raw_text.content = payload.content
    if payload.domain is not None:
        raw_text.domain = payload.domain
    if payload.tags is not None:
        raw_text.tags = json.dumps(payload.tags) if payload.tags else None
    if payload.metadata is not None:
        raw_text.metadata = json.dumps(payload.metadata) if payload.metadata else None
    
    await db.commit()
    
    return {'id': raw_text.id, 'status': 'updated'}


@router.delete('/raw-text/{raw_text_id}')
async def delete_raw_text(
    raw_text_id: str = Path(..., description='Raw text ID'),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    """Delete raw text entry (only if draft and owned by user)"""
    raw_text = await db.execute(
        select(RawText).where(RawText.id == raw_text_id)
    )
    raw_text = raw_text.scalar_one_or_none()
    
    if not raw_text:
        raise HTTPException(status_code=404, detail='Raw text not found')
    
    # Only allow deletion if draft and owned by user
    if raw_text.status != 'draft':
        raise HTTPException(status_code=400, detail='Cannot delete submitted raw text')
    
    if raw_text.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail='Can only delete your own raw text')
    
    await db.delete(raw_text)
    await db.commit()
    
    return {'id': raw_text_id, 'status': 'deleted'}


# Mass Submission Route
@router.post('/submit')
async def mass_submit(
    payload: MassSubmissionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    """Submit multiple documents, voice samples, and raw texts for review"""
    submitted_items = []
    
    # Submit documents
    if payload.document_ids:
        for doc_id in payload.document_ids:
            doc = await db.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = doc.scalar_one_or_none()
            
            if not doc:
                continue
            
            # Check ownership and status
            if doc.uploaded_by_id != current_user.id or doc.status != 'draft':
                continue
            
            doc.status = 'pending_review'
            doc.submitted_at = datetime.now(timezone.utc)
            submitted_items.append({'type': 'document', 'id': doc_id})
    
    # Submit voice samples
    if payload.voice_sample_ids:
        for voice_id in payload.voice_sample_ids:
            voice = await db.execute(
                select(VoiceSample).where(VoiceSample.id == voice_id)
            )
            voice = voice.scalar_one_or_none()
            
            if not voice:
                continue
            
            # Check ownership and status
            if voice.uploaded_by_id != current_user.id or voice.status != 'draft':
                continue
            
            voice.status = 'pending_review'
            voice.submitted_at = datetime.now(timezone.utc)
            submitted_items.append({'type': 'voice_sample', 'id': voice_id})
    
    # Submit raw texts
    if payload.raw_text_ids:
        for text_id in payload.raw_text_ids:
            raw_text = await db.execute(
                select(RawText).where(RawText.id == text_id)
            )
            raw_text = raw_text.scalar_one_or_none()
            
            if not raw_text:
                continue
            
            # Check ownership and status
            if raw_text.created_by_id != current_user.id or raw_text.status != 'draft':
                continue
            
            raw_text.status = 'pending_review'
            raw_text.submitted_at = datetime.now(timezone.utc)
            submitted_items.append({'type': 'raw_text', 'id': text_id})
    
    await db.commit()
    
    return {
        'submitted_count': len(submitted_items),
        'submitted_items': submitted_items
    }


# Contributor Data Management Routes
@router.get('/my-drafts')
async def get_my_drafts(
    project_id: str = Query(..., description="Project ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    """Get current user's draft documents, voice samples, and raw texts"""
    drafts = {
        'documents': [],
        'voice_samples': [],
        'raw_texts': []
    }
    
    # Get draft documents
    docs = await db.execute(
        select(Document).where(
            Document.project_id == project_id,
            Document.uploaded_by_id == current_user.id,
            Document.status == 'draft'
        )
    )
    for doc in docs.scalars().all():
        drafts['documents'].append({
            'id': doc.id,
            'filename': doc.original_filename,
            'domain': doc.domain,
            'is_raw': doc.is_raw,
            'processed': doc.processed,
            'created_at': doc.created_at,
            'updated_at': doc.updated_at
        })
    
    # Get draft voice samples
    voices = await db.execute(
        select(VoiceSample).where(
            VoiceSample.project_id == project_id,
            VoiceSample.uploaded_by_id == current_user.id,
            VoiceSample.status == 'draft'
        )
    )
    for voice in voices.scalars().all():
        drafts['voice_samples'].append({
            'id': voice.id,
            'filename': voice.original_filename,
            'language': voice.language,
            'processed': voice.processed,
            'created_at': voice.created_at,
            'updated_at': voice.updated_at
        })
    
    # Get draft raw texts
    texts = await db.execute(
        select(RawText).where(
            RawText.project_id == project_id,
            RawText.created_by_id == current_user.id,
            RawText.status == 'draft'
        )
    )
    for text in texts.scalars().all():
        drafts['raw_texts'].append({
            'id': text.id,
            'title': text.title,
            'domain': text.domain,
            'created_at': text.created_at,
            'updated_at': text.updated_at
        })
    
    return drafts


@router.delete('/documents/{document_id}')
async def delete_document(
    document_id: str = Path(..., description='Document ID'),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    """Delete document (only if draft and owned by user)"""
    doc = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = doc.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    
    # Only allow deletion if draft and owned by user
    if doc.status != 'draft':
        raise HTTPException(status_code=400, detail='Cannot delete submitted document')
    
    if doc.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail='Can only delete your own documents')
    
    # Delete from GCS
    try:
        from ...core.storage import delete_file
        delete_file(doc.gcs_uri)
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Failed to delete file from GCS: {e}")
    
    # Delete from database
    await db.delete(doc)
    await db.commit()
    
    return {'id': document_id, 'status': 'deleted'}


@router.delete('/voice/{voice_sample_id}')
async def delete_voice_sample(
    voice_sample_id: str = Path(..., description='Voice sample ID'),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    """Delete voice sample (only if draft and owned by user)"""
    voice = await db.execute(
        select(VoiceSample).where(VoiceSample.id == voice_sample_id)
    )
    voice = voice.scalar_one_or_none()
    
    if not voice:
        raise HTTPException(status_code=404, detail='Voice sample not found')
    
    # Only allow deletion if draft and owned by user
    if voice.status != 'draft':
        raise HTTPException(status_code=400, detail='Cannot delete submitted voice sample')
    
    if voice.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail='Can only delete your own voice samples')
    
    # Delete from GCS
    try:
        from ...core.storage import delete_file
        delete_file(voice.gcs_uri)
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Failed to delete file from GCS: {e}")
    
    # Delete from database
    await db.delete(voice)
    await db.commit()
    
    return {'id': voice_sample_id, 'status': 'deleted'}

