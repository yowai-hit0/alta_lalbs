from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete
from ...database import get_db
from ...models.project import Project, ProjectMember
from ...models.user import User
from ...models.invitation import EmailVerificationToken, ProjectInvitation
from ...schemas.project import ProjectResponse
from ...schemas.project_validators import (
    ProjectCreateRequest, ProjectUpdateRequest, ProjectInvitationRequest, 
    InvitationAcceptRequest, ProjectMemberUpdateRequest, ProjectSearchRequest,
    ProjectArchiveRequest, ProjectSettingsUpdateRequest, ProjectStatisticsRequest
)
from ..dependencies import get_current_user, project_role_required, require_global_roles


router = APIRouter(prefix='/projects', tags=['projects'])


@router.get('', response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    res = await db.execute(select(Project))
    return [ProjectResponse(id=p.id, name=p.name, description=p.description, created_by_id=p.created_by_id) for p in res.scalars().all()]


@router.post('', response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreateRequest, db: AsyncSession = Depends(get_db), current_user=Depends(require_global_roles('user', 'super_admin'))
):
    owner = current_user
    project = Project(name=payload.name, description=payload.description or '', created_by_id=owner.id)
    db.add(project)
    await db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=owner.id, role='admin'))
    await db.commit()
    return ProjectResponse(id=project.id, name=project.name, description=project.description, created_by_id=project.created_by_id)


@router.get('/{project_id}', response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('admin', 'contributor', 'reviewer'))):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail='Project not found')
    return ProjectResponse(id=p.id, name=p.name, description=p.description, created_by_id=p.created_by_id)


@router.put('/{project_id}', response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
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
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('admin'))):
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail='Project not found')
    await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()
    return {'deleted': True}


@router.post('/{project_id}/invite')
async def invite_member(
    project_id: str,
    payload: ProjectInvitationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin')),
):
    # Create invitation token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    db.add(ProjectInvitation(project_id=project_id, email=payload.email, role=payload.role, token_hash=token_hash, invited_by_id=current_user.id, expires_at=exp))
    await db.commit()
    return {'invited': True, 'token': raw_token}


@router.post('/invitations/{token}/accept')
async def accept_invitation(request: InvitationAcceptRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
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
async def submit_for_review(project_id: str, body: SubmitForReviewRequest, db: AsyncSession = Depends(get_db), current_user=Depends(project_role_required('admin', 'contributor'))):
    d = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail='Project not found')
    doc = (await db.execute(select(Document).where(Document.id == body.documentId, Document.project_id == project_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    doc.status = 'pending_review'
    doc.submitted_at = datetime.now(timezone.utc)
    await db.commit()
    return {'submitted': True, 'id': doc.id}


