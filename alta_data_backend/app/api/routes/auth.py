from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
import os
import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from passlib.context import CryptContext
from ...database import get_db
from ...models.user import User
from ...models.invitation import EmailVerificationToken
from ...schemas.auth import TokenResponse, UserResponse
from ...schemas.auth_validators import (
    RegisterRequest, LoginRequest, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirmRequest, ChangePasswordRequest,
    UpdateProfileRequest
)
from ...core.security import create_access_token
from ...core.email import send_email
from ...api.dependencies import get_current_user


router = APIRouter(prefix='/auth', tags=['auth'])
_redis = None


def get_redis():
    global _redis
    if _redis is None:
        url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        _redis = redis.Redis.from_url(url)
    return _redis


def ratelimit(key: str, limit: int, window_sec: int) -> bool:
    r = get_redis()
    count = r.incr(key)
    if count == 1:
        r.expire(key, window_sec)
    return count <= limit

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


@router.post('/register', response_model=UserResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not ratelimit(f"rl:register:{payload.email}", 10, 60):
        raise HTTPException(status_code=429, detail='Too many requests')
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')
    user = User(email=payload.email, hashed_password=hash_password(payload.password), is_verified=False, global_role='user')
    db.add(user)
    await db.flush()

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    exp = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(EmailVerificationToken(user_id=user.id, token_hash=token_hash, expires_at=exp))
    await db.commit()

    verify_link = f'https://frontend.example.com/verify-email?token={raw_token}'
    try:
        # Create outbox event for email sending
        from ...services.outbox_service import outbox_service
        from ...models.outbox import OutboxEventType
        
        await outbox_service.create_event(
            session=db,
            event_type=OutboxEventType.EMAIL_SEND_REQUESTED,
            aggregate_id=user.id,
            aggregate_type="User",
            payload={
                "to_email": user.email,
                "subject": "Verify your email",
                "body": f'Click to verify: {verify_link}',
                "email_type": "email_verification"
            }
        )
    except Exception:
        pass

    return UserResponse(id=user.id, email=user.email, is_verified=user.is_verified, global_role=user.global_role)


@router.post('/login', response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    if not ratelimit(f"rl:login:{payload.email}", 10, 60):
        raise HTTPException(status_code=429, detail='Too many requests')
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    token = create_access_token(subject=user.id, global_role=user.global_role)
    return TokenResponse(access_token=token)


@router.get('/verify-email')
async def verify_email(request: EmailVerificationRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    res = await db.execute(select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash))
    rec = res.scalar_one_or_none()
    if not rec or rec.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid or expired token')
    await db.execute(update(User).where(User.id == rec.user_id).values(is_verified=True))
    await db.execute(delete(EmailVerificationToken).where(EmailVerificationToken.user_id == rec.user_id))
    await db.commit()
    return {'verified': True}


@router.get('/me', response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email, is_verified=current_user.is_verified, global_role=current_user.global_role)


@router.post('/passkeys/register')
async def passkeys_register():
    return {'todo': 'webauthn options'}


@router.post('/passkeys/register/verify')
async def passkeys_register_verify():
    return {'todo': 'webauthn verify'}


@router.post('/passkeys/login')
async def passkeys_login():
    return {'todo': 'webauthn options'}


@router.post('/passkeys/login/verify')
async def passkeys_login_verify():
    return {'todo': 'webauthn verify'}




