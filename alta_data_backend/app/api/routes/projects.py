from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete
from ...database import get_db
from ...models.project import Project, ProjectMember
from ...models.user import User
from ...models.invitation import EmailVerificationToken, ProjectInvitation
from ...models.data import Document, VoiceSample, RawText
from ...schemas.project import ProjectResponse
from ...schemas.project_validators import (
    ProjectCreateRequest, ProjectUpdateRequest, ProjectInvitationRequest, 
    InvitationAcceptRequest, ProjectMemberUpdateRequest, ProjectSearchRequest,
    ProjectArchiveRequest, ProjectSettingsUpdateRequest, ProjectStatisticsRequest
)
from ...schemas.review_validators import SubmitForReviewRequest
from ..dependencies import get_current_user, project_role_required, require_global_roles


router = APIRouter(prefix='/projects', tags=['projects'])


@router.get('', response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    res = await db.execute(select(Project))
    return [ProjectResponse(id=p.id, name=p.name, description=p.description, created_by_id=p.created_by_id) for p in res.scalars().all()]


@router.post('', response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreateRequest = Body(...), db: AsyncSession = Depends(get_db), current_user=Depends(require_global_roles('user', 'super_admin'))
):
    owner = current_user
    project = Project(name=payload.name, description=payload.description or '', created_by_id=owner.id)
    db.add(project)
    await db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=owner.id, role='admin'))
    await db.commit()
    return ProjectResponse(id=project.id, name=project.name, description=project.description, created_by_id=project.created_by_id)


@router.get('/{project_id}', response_model=ProjectResponse)
async def get_project(project_id: str = Path(..., description='Project ID'), db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('admin', 'contributor', 'reviewer'))):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail='Project not found')
    return ProjectResponse(id=p.id, name=p.name, description=p.description, created_by_id=p.created_by_id)


@router.put('/{project_id}', response_model=ProjectResponse)
async def update_project(
    project_id: str = Path(..., description='Project ID'),
    payload: ProjectUpdateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin')),
):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail='Project not found')
    if payload.name is not None:
        p.name = payload.name
    if payload.description is not None:
        p.description = payload.description
    await db.commit()
    return ProjectResponse(id=p.id, name=p.name, description=p.description, created_by_id=p.created_by_id)


@router.delete('/{project_id}')
async def delete_project(project_id: str = Path(..., description='Project ID'), db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('admin'))):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail='Project not found')
    await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()
    return {'deleted': True}


@router.post('/{project_id}/invite')
async def invite_member(
    project_id: str = Path(..., description='Project ID'),
    payload: ProjectInvitationRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin')),
):
    # Create invitation token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    db.add(ProjectInvitation(project_id=project_id, email=payload.email, role=payload.role, token_hash=token_hash, invited_by_id=current_user.id, expires_at=exp))
    await db.flush()  # Get the ID without committing

    # Send invitation email via outbox
    try:
        from ...services.outbox_service import outbox_service
        from ...models.outbox import OutboxEventType
        
        invite_link = f'https://frontend.example.com/accept-invitation?token={raw_token}'
        project_name = (await db.execute(select(Project.name).where(Project.id == project_id))).scalar_one()
        
        await outbox_service.create_event(
            session=db,
            event_type=OutboxEventType.EMAIL_SEND_REQUESTED,
            aggregate_id=project_id,
            aggregate_type="Project",
            payload={
                "to_email": payload.email,
                "subject": f"Invitation to join project: {project_name}",
                "body": f"You have been invited to join the project '{project_name}' as a {payload.role}. Click the link to accept: {invite_link}",
                "email_type": "project_invitation"
            }
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        # Don't fail the invitation if email fails
        pass

    return {'invited': True, 'token': raw_token}


@router.post('/invitations/{token}/accept')
async def accept_invitation(request: InvitationAcceptRequest = Body(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    inv = (await db.execute(select(ProjectInvitation).where(ProjectInvitation.token_hash == token_hash))).scalar_one_or_none()
    if not inv or inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail='Invalid or expired token')
    # Ensure user exists
    user = (await db.execute(select(User).where(User.email == current_user.email))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail='User not found')
    existing = (await db.execute(select(ProjectMember).where(ProjectMember.project_id == inv.project_id, ProjectMember.user_id == user.id))).scalar_one_or_none()
    if not existing:
        db.add(ProjectMember(project_id=inv.project_id, user_id=user.id, role=inv.role))
    inv.accepted_at = datetime.now(timezone.utc)
    await db.commit()
    return {'accepted': True, 'projectId': inv.project_id}


@router.post('/{project_id}/review')
async def submit_for_review(project_id: str = Path(..., description='Project ID'), body: SubmitForReviewRequest = Body(...), db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('admin', 'contributor'))):
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    item = None
    if body.item_type == 'document':
        item = (await db.execute(select(Document).where(Document.id == body.item_id, Document.project_id == project_id))).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail='Document not found')
        # Ownership for contributors
        if current_user.global_role != 'super_admin' and current_user.id != item.uploaded_by_id and current_user.global_role != 'admin':
            raise HTTPException(status_code=403, detail='Not allowed to submit this document')
    elif body.item_type == 'voice':
        item = (await db.execute(select(VoiceSample).where(VoiceSample.id == body.item_id, VoiceSample.project_id == project_id))).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail='Voice sample not found')
        if current_user.global_role != 'super_admin' and current_user.id != item.uploaded_by_id and current_user.global_role != 'admin':
            raise HTTPException(status_code=403, detail='Not allowed to submit this voice sample')
    elif body.item_type == 'raw_text':
        item = (await db.execute(select(RawText).where(RawText.id == body.item_id, RawText.project_id == project_id))).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail='Raw text not found')
        if current_user.global_role != 'super_admin' and current_user.id != item.created_by_id and current_user.global_role != 'admin':
            raise HTTPException(status_code=403, detail='Not allowed to submit this raw text')
    else:
        raise HTTPException(status_code=400, detail='Invalid item type')

    if item.status != 'draft':
        raise HTTPException(status_code=400, detail='Only draft items can be submitted')

    item.status = 'pending_review'
    item.submitted_at = datetime.now(timezone.utc)
    await db.commit()
    return {'submitted': True, 'id': body.item_id, 'type': body.item_type}


