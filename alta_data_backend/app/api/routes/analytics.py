from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from ...schemas.analytics_validators import (
    AnalyticsSummaryRequest, UserAnalyticsRequest, ProjectAnalyticsRequest,
    DocumentAnalyticsRequest, VoiceAnalyticsRequest, ReviewAnalyticsRequest,
    SystemAnalyticsRequest, CustomAnalyticsRequest, ExportAnalyticsRequest,
    AnalyticsDashboardRequest
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...database import get_db
from ...models.user import User
from ...models.project import Project, ProjectMember
from ...models.data import Document, VoiceSample
from ..dependencies import get_current_user, project_role_required


router = APIRouter(prefix='/analytics', tags=['analytics'])


def parse_timeframe(tf: str) -> datetime:
    now = datetime.now(timezone.utc)
    if tf == '7d':
        return now - timedelta(days=7)
    if tf == '30d':
        return now - timedelta(days=30)
    if tf == '365d':
        return now - timedelta(days=365)
    raise HTTPException(status_code=400, detail='Invalid timeframe')


@router.get('/summary')
async def analytics_summary(
    timeframe: str = Query('7d'),
    projectId: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    since = parse_timeframe(timeframe)

    if projectId:
        # Project-scoped metrics (admin or super_admin)
        # Validate user is admin in project or super_admin
        try:
            await project_role_required('admin')(project_id=projectId, current_user=current_user, db=db)
        except Exception:
            if getattr(current_user, 'global_role', None) != 'super_admin':
                raise
        doc_counts = (await db.execute(
            select(Document.status, func.count()).where(Document.project_id == projectId, Document.created_at >= since).group_by(Document.status)
        )).all()
        contrib_daily = (await db.execute(
            select(func.date_trunc('day', Document.created_at).label('day'), func.count()).where(Document.project_id == projectId, Document.created_at >= since).group_by('day').order_by('day')
        )).all()
        return {
            'documentCounts': {k: v for k, v in doc_counts},
            'contributionDaily': [{'day': str(d), 'count': c} for d, c in contrib_daily],
        }

    # Global metrics (super_admin only)
    if getattr(current_user, 'global_role', None) != 'super_admin':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail='Forbidden')
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    total_projects = (await db.execute(select(func.count()).select_from(Project))).scalar()
    doc_counts = (await db.execute(
        select(Document.status, func.count()).where(Document.created_at >= since).group_by(Document.status)
    )).all()
    user_signup_daily = (await db.execute(
        select(func.date_trunc('day', User.created_at).label('day'), func.count()).where(User.created_at >= since).group_by('day').order_by('day')
    )).all()
    return {
        'totalUsers': total_users,
        'totalProjects': total_projects,
        'documentCounts': {k: v for k, v in doc_counts},
        'userSignupDaily': [{'day': str(d), 'count': c} for d, c in user_signup_daily],
    }


@router.get('/user/{userId}')
async def user_analytics(userId: str = Path(..., description='User ID'), timeframe: str = Query('7d'), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    since = parse_timeframe(timeframe)
    total_contribs = (await db.execute(select(func.count()).select_from(Document).where(Document.uploaded_by_id == userId, Document.created_at >= since))).scalar()
    contrib_daily = (await db.execute(
        select(func.date_trunc('day', Document.created_at).label('day'), func.count()).where(Document.uploaded_by_id == userId, Document.created_at >= since).group_by('day').order_by('day')
    )).all()
    approved = (await db.execute(select(func.count()).select_from(Document).where(Document.uploaded_by_id == userId, Document.status == 'approved', Document.created_at >= since))).scalar()
    approval_rate = (approved / total_contribs) if total_contribs else 0
    return {
        'totalContributions': total_contribs,
        'contributionDaily': [{'day': str(d), 'count': c} for d, c in contrib_daily],
        'approvalRate': approval_rate,
    }


