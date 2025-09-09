from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from ...schemas.review_validators import (
    ReviewDecisionRequest, SubmitForReviewRequest, ReviewQueueRequest,
    ReviewHistoryRequest, ReviewStatisticsRequest, ReviewAssignmentRequest,
    ReviewBulkActionRequest
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ...database import get_db
from ...models.data import Document, VoiceSample, RawText
from ..dependencies import project_role_required
from ...utils.audit_logger import log_audit_event


router = APIRouter(prefix='/review', tags=['review'])


@router.get('')
async def review_queue(project_id: str = Query(..., description="Project ID"), db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('reviewer', 'admin'))):
    """Get review queue for a project - includes documents, voice samples, and raw texts"""
    # Get pending documents
    docs = await db.execute(
        select(Document).where(
            Document.project_id == project_id, 
            Document.status == 'pending_review'
        )
    )
    documents = docs.scalars().all()
    
    # Get pending voice samples
    voices = await db.execute(
        select(VoiceSample).where(
            VoiceSample.project_id == project_id, 
            VoiceSample.status == 'pending_review'
        )
    )
    voice_samples = voices.scalars().all()
    
    # Get pending raw texts
    texts = await db.execute(
        select(RawText).where(
            RawText.project_id == project_id, 
            RawText.status == 'pending_review'
        )
    )
    raw_texts = texts.scalars().all()
    
    # Combine all items
    review_items = []
    
    for doc in documents:
        review_items.append({
            'id': doc.id,
            'type': 'document',
            'title': doc.original_filename,
            'status': doc.status,
            'submitted_at': doc.submitted_at,
            'uploaded_by_id': doc.uploaded_by_id
        })
    
    for voice in voice_samples:
        review_items.append({
            'id': voice.id,
            'type': 'voice_sample',
            'title': voice.original_filename,
            'status': voice.status,
            'submitted_at': voice.submitted_at,
            'uploaded_by_id': voice.uploaded_by_id
        })
    
    for text in raw_texts:
        review_items.append({
            'id': text.id,
            'type': 'raw_text',
            'title': text.title,
            'status': text.status,
            'submitted_at': text.submitted_at,
            'created_by_id': text.created_by_id
        })
    
    # Sort by submission date
    review_items.sort(key=lambda x: x['submitted_at'] or datetime.min.replace(tzinfo=timezone.utc))
    
    return review_items


@router.patch('/{item_id}')
async def review_decision(
    item_id: str = Path(..., description="ID of the item to review"),
    item_type: str = Query(..., description="Type: 'document', 'voice', or 'raw_text'"),
    request: ReviewDecisionRequest = Body(...),
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(project_role_required('reviewer', 'admin'))
):
    """Review decision for documents, voice samples, or raw texts"""
    new_status = 'approved' if request.decision == 'approve' else 'rejected'
    
    if item_type == 'document':
        item = await db.execute(select(Document).where(Document.id == item_id))
        item = item.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail='Document not found')
        
        item.status = new_status
        item.feedback = request.feedback
        item.reviewed_by_id = current_user.id
        
        await log_audit_event(
            'DOCUMENT_REVIEW_DECISION', 'success', 'Document', item.id, 
            {'decision': new_status, 'feedback': request.feedback}
        )
        
    elif item_type == 'voice':
        item = await db.execute(select(VoiceSample).where(VoiceSample.id == item_id))
        item = item.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail='Voice sample not found')
        
        item.status = new_status
        item.feedback = request.feedback
        item.reviewed_by_id = current_user.id
        
        await log_audit_event(
            'VOICE_REVIEW_DECISION', 'success', 'VoiceSample', item.id, 
            {'decision': new_status, 'feedback': request.feedback}
        )
        
    elif item_type == 'raw_text':
        item = await db.execute(select(RawText).where(RawText.id == item_id))
        item = item.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail='Raw text not found')
        
        item.status = new_status
        item.feedback = request.feedback
        item.reviewed_by_id = current_user.id
        
        await log_audit_event(
            'RAW_TEXT_REVIEW_DECISION', 'success', 'RawText', item.id, 
            {'decision': new_status, 'feedback': request.feedback}
        )
        
    else:
        raise HTTPException(status_code=400, detail='Invalid item type. Must be "document", "voice", or "raw_text"')
    
    await db.commit()
    
    return {
        'id': item.id, 
        'type': item_type,
        'status': new_status,
        'reviewed_by': current_user.id,
        'feedback': request.feedback
    }
