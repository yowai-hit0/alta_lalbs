from datetime import datetime, timedelta, timezone
from jose import jwt
from ..config import settings


def create_access_token(subject: str, global_role: str | None = None, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode = {'sub': subject, 'exp': expire, 'global_role': global_role}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_alg)




