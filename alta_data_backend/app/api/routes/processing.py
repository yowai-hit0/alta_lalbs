from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ...database import get_db
from ...models.data import Document, VoiceSample
from ...models.project import ProjectMember
from ..dependencies import get_current_user, project_role_required
from ...worker.tasks import task_process_ocr, task_transcribe_audio
from ...schemas.data_validators import DocumentUploadRequest, VoiceUploadRequest
import uuid

router = APIRouter(prefix='/processing', tags=['processing'])


@router.post('/ocr')
async def trigger_ocr(
    document_id: str = Query(..., description="Document ID to process"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger OCR processing for a specific document"""
    # Get document
    doc = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = doc.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    
    # Check if user has access to the project
    project_member = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == doc.project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not project_member.scalar_one_or_none():
        raise HTTPException(status_code=403, detail='Access denied to project')
    
    # Check if document is already processed
    if doc.processed:
        return {'message': 'Document already processed', 'document_id': document_id}
    
    # Check if document is raw text (manual entry)
    if doc.is_raw:
        return {'message': 'Document is raw text, no OCR processing needed', 'document_id': document_id}
    
    # Trigger OCR processing
    try:
        task_process_ocr.delay(document_id)
        
        # Mark as processing
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(processed=True)
        )
        await db.commit()
        
        return {
            'message': 'OCR processing started',
            'document_id': document_id,
            'status': 'processing'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to start OCR processing: {str(e)}')


@router.post('/transcribe')
async def trigger_transcription(
    voice_sample_id: str = Query(..., description="Voice sample ID to process"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger transcription processing for a specific voice sample"""
    # Get voice sample
    voice = await db.execute(
        select(VoiceSample).where(VoiceSample.id == voice_sample_id)
    )
    voice = voice.scalar_one_or_none()
    
    if not voice:
        raise HTTPException(status_code=404, detail='Voice sample not found')
    
    # Check if user has access to the project
    project_member = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == voice.project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not project_member.scalar_one_or_none():
        raise HTTPException(status_code=403, detail='Access denied to project')
    
    # Check if voice sample is already processed
    if voice.processed:
        return {'message': 'Voice sample already processed', 'voice_sample_id': voice_sample_id}
    
    # Trigger transcription processing
    try:
        task_transcribe_audio.delay(voice_sample_id)
        
        # Mark as processing
        await db.execute(
            update(VoiceSample)
            .where(VoiceSample.id == voice_sample_id)
            .values(processed=True)
        )
        await db.commit()
        
        return {
            'message': 'Transcription processing started',
            'voice_sample_id': voice_sample_id,
            'status': 'processing'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to start transcription processing: {str(e)}')


@router.get('/status/{item_id}')
async def get_processing_status(
    item_id: str = Path(..., description="Document or voice sample ID"),
    item_type: str = Query(..., description="Type: 'document' or 'voice'"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get processing status for a document or voice sample"""
    if item_type == 'document':
        item = await db.execute(
            select(Document).where(Document.id == item_id)
        )
        item = item.scalar_one_or_none()
    elif item_type == 'voice':
        item = await db.execute(
            select(VoiceSample).where(VoiceSample.id == item_id)
        )
        item = item.scalar_one_or_none()
    else:
        raise HTTPException(status_code=400, detail='Invalid item type. Must be "document" or "voice"')
    
    if not item:
        raise HTTPException(status_code=404, detail='Item not found')
    
    # Check if user has access to the project
    project_member = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == item.project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not project_member.scalar_one_or_none():
        raise HTTPException(status_code=403, detail='Access denied to project')
    
    return {
        'id': item.id,
        'type': item_type,
        'processed': item.processed,
        'status': item.status,
        'has_content': bool(
            item.ocr_text if item_type == 'document' else item.transcription_text
        )
    }


@router.post('/batch-ocr')
async def batch_trigger_ocr(
    document_ids: list = Query(..., description="List of document IDs to process"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger OCR processing for multiple documents"""
    if len(document_ids) > 50:
        raise HTTPException(status_code=400, detail='Cannot process more than 50 documents at once')
    
    processed_docs = []
    skipped_docs = []
    
    for doc_id in document_ids:
        try:
            # Validate UUID format
            uuid.UUID(doc_id)
            
            # Get document
            doc = await db.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = doc.scalar_one_or_none()
            
            if not doc:
                skipped_docs.append({'id': doc_id, 'reason': 'Document not found'})
                continue
            
            # Check if user has access to the project
            project_member = await db.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == doc.project_id,
                    ProjectMember.user_id == current_user.id
                )
            )
            if not project_member.scalar_one_or_none():
                skipped_docs.append({'id': doc_id, 'reason': 'Access denied'})
                continue
            
            # Check if already processed or raw text
            if doc.processed:
                skipped_docs.append({'id': doc_id, 'reason': 'Already processed'})
                continue
            
            if doc.is_raw:
                skipped_docs.append({'id': doc_id, 'reason': 'Raw text, no OCR needed'})
                continue
            
            # Trigger OCR processing
            task_process_ocr.delay(doc_id)
            
            # Mark as processing
            await db.execute(
                update(Document)
                .where(Document.id == doc_id)
                .values(processed=True)
            )
            
            processed_docs.append(doc_id)
            
        except ValueError:
            skipped_docs.append({'id': doc_id, 'reason': 'Invalid document ID format'})
        except Exception as e:
            skipped_docs.append({'id': doc_id, 'reason': f'Error: {str(e)}'})
    
    await db.commit()
    
    return {
        'processed_count': len(processed_docs),
        'skipped_count': len(skipped_docs),
        'processed_documents': processed_docs,
        'skipped_documents': skipped_docs
    }


@router.post('/batch-transcribe')
async def batch_trigger_transcription(
    voice_sample_ids: list = Query(..., description="List of voice sample IDs to process"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger transcription processing for multiple voice samples"""
    if len(voice_sample_ids) > 50:
        raise HTTPException(status_code=400, detail='Cannot process more than 50 voice samples at once')
    
    processed_voices = []
    skipped_voices = []
    
    for voice_id in voice_sample_ids:
        try:
            # Validate UUID format
            uuid.UUID(voice_id)
            
            # Get voice sample
            voice = await db.execute(
                select(VoiceSample).where(VoiceSample.id == voice_id)
            )
            voice = voice.scalar_one_or_none()
            
            if not voice:
                skipped_voices.append({'id': voice_id, 'reason': 'Voice sample not found'})
                continue
            
            # Check if user has access to the project
            project_member = await db.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == voice.project_id,
                    ProjectMember.user_id == current_user.id
                )
            )
            if not project_member.scalar_one_or_none():
                skipped_voices.append({'id': voice_id, 'reason': 'Access denied'})
                continue
            
            # Check if already processed
            if voice.processed:
                skipped_voices.append({'id': voice_id, 'reason': 'Already processed'})
                continue
            
            # Trigger transcription processing
            task_transcribe_audio.delay(voice_id)
            
            # Mark as processing
            await db.execute(
                update(VoiceSample)
                .where(VoiceSample.id == voice_id)
                .values(processed=True)
            )
            
            processed_voices.append(voice_id)
            
        except ValueError:
            skipped_voices.append({'id': voice_id, 'reason': 'Invalid voice sample ID format'})
        except Exception as e:
            skipped_voices.append({'id': voice_id, 'reason': f'Error: {str(e)}'})
    
    await db.commit()
    
    return {
        'processed_count': len(processed_voices),
        'skipped_count': len(skipped_voices),
        'processed_voice_samples': processed_voices,
        'skipped_voice_samples': skipped_voices
    }
