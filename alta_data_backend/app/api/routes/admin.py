from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...database import get_db
from ...models.user import User
from ..dependencies import require_global_roles


router = APIRouter(prefix='/admin', tags=['admin'])


@router.get('/users')
async def list_users(db: AsyncSession = Depends(get_db), current_user=Depends(require_global_roles('super_admin'))):
    res = await db.execute(select(User))
    return [{'id': u.id, 'email': u.email, 'role': u.global_role} for u in res.scalars().all()]


