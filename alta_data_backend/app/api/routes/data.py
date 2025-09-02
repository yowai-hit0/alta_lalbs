import os
import mimetypes
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...database import get_db
from ...models.data import Document, VoiceSample
from ...models.project import ProjectMember, Project
from ...core.storage import upload_bytes
from ...config import settings
from ..dependencies import get_current_user, project_role_required
from ..dependencies import get_current_user as CurrentUser


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
    project_id: str = Form(...),
    domain: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
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
    
    blob_path = f'documents/{project_id}/{datetime.now(timezone.utc).timestamp()}_{file.filename}'
    bucket = settings.gcs_bucket_name or os.getenv('GCS_BUCKET_NAME', 'alta-data-local')
    
    try:
        gcs_uri = upload_bytes(bucket, blob_path, content, file.content_type or 'application/octet-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {str(e)}')
    
    doc = Document(
        project_id=project_id,
        uploaded_by_id=current_user.id,
        original_filename=file.filename,
        gcs_uri=gcs_uri,
        domain=domain,
    )
    db.add(doc)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')
    
    return {'id': doc.id, 'gcs_uri': gcs_uri}


@router.post('/voice')
async def upload_voice(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
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
    
    blob_path = f'voice/{project_id}/{datetime.now(timezone.utc).timestamp()}_{file.filename}'
    bucket = settings.gcs_bucket_name or os.getenv('GCS_BUCKET_NAME', 'alta-data-local')
    
    try:
        gcs_uri = upload_bytes(bucket, blob_path, content, file.content_type or 'application/octet-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {str(e)}')
    
    voice = VoiceSample(
        project_id=project_id,
        uploaded_by_id=current_user.id,
        original_filename=file.filename,
        gcs_uri=gcs_uri,
    )
    db.add(voice)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')
    
    return {'id': voice.id, 'gcs_uri': gcs_uri}

