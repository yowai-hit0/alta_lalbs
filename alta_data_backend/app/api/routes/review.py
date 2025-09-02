from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ...database import get_db
from ...models.data import Document
from ..dependencies import project_role_required
from ...utils.audit_logger import log_audit_event


router = APIRouter(prefix='/review', tags=['review'])


@router.get('')
async def review_queue(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('reviewer', 'admin'))):
    res = await db.execute(select(Document).where(Document.project_id == project_id, Document.status == 'pending_review'))
    docs = res.scalars().all()
    return [{'id': d.id, 'filename': d.original_filename, 'status': d.status} for d in docs]


@router.patch('/{document_id}')
async def review_decision(document_id: str, decision: str = Query(..., pattern='^(approve|reject)$'), feedback: str | None = None, db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('reviewer', 'admin'))):
    d = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail='Document not found')
    d.status = 'approved' if decision == 'approve' else 'rejected'
    d.feedback = feedback
    d.reviewed_by_id = current_user.id
    await db.commit()
    log_audit_event('DOCUMENT_REVIEW_DECISION', 'success', 'Document', d.id, {'decision': d.status})
    return {'id': d.id, 'status': d.status}


