from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict
import hashlib
import json
from ..models.audit import AuditLog


class IdempotencyKey:
    """Model for storing idempotency keys"""
    __tablename__ = 'idempotency_keys'
    
    def __init__(self, key: str, request_hash: str, response_data: Dict[str, Any], expires_at: datetime):
        self.key = key
        self.request_hash = request_hash
        self.response_data = response_data
        self.expires_at = expires_at
        self.created_at = datetime.now(timezone.utc)


async def get_idempotency_key(session: AsyncSession, key: str) -> Optional[IdempotencyKey]:
    """Get idempotency key from database"""
    # This would be implemented with a proper model in production
    # For now, return None to indicate no existing key
    return None


async def store_idempotency_key(session: AsyncSession, key: str, request_hash: str, response_data: Dict[str, Any], ttl_hours: int = 24):
    """Store idempotency key in database"""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    idempotency_key = IdempotencyKey(key, request_hash, response_data, expires_at)
    
    # In production, you would insert this into a proper idempotency_keys table
    # For now, we'll just log it
    print(f"Storing idempotency key: {key}, expires at: {expires_at}")


def generate_request_hash(request_data: Dict[str, Any]) -> str:
    """Generate hash for request data to detect duplicate requests"""
    # Sort keys to ensure consistent hashing
    sorted_data = json.dumps(request_data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def get_idempotency_key_from_request(request: Request) -> Optional[str]:
    """Extract idempotency key from request headers"""
    return request.headers.get('Idempotency-Key')


async def check_idempotency(
    session: AsyncSession, 
    request: Request, 
    request_data: Dict[str, Any],
    operation_name: str
) -> Optional[Dict[str, Any]]:
    """
    Check if request is idempotent and return cached response if available
    
    Args:
        session: Database session
        request: FastAPI request object
        request_data: Request data to hash
        operation_name: Name of the operation for logging
        
    Returns:
        Cached response data if idempotent, None if new request
    """
    idempotency_key = get_idempotency_key_from_request(request)
    
    if not idempotency_key:
        return None
    
    # Generate request hash
    request_hash = generate_request_hash(request_data)
    
    # Check if key exists
    existing_key = await get_idempotency_key(session, idempotency_key)
    
    if existing_key:
        # Check if request is identical
        if existing_key.request_hash == request_hash:
            # Check if not expired
            if existing_key.expires_at > datetime.now(timezone.utc):
                # Log idempotent request
                await log_idempotent_request(session, idempotency_key, operation_name)
                return existing_key.response_data
            else:
                # Key expired, treat as new request
                return None
        else:
            # Different request with same key - this is an error
            raise HTTPException(
                status_code=409,
                detail=f"Idempotency key '{idempotency_key}' already used with different request data"
            )
    
    return None


async def store_idempotent_response(
    session: AsyncSession,
    request: Request,
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    operation_name: str,
    ttl_hours: int = 24
):
    """
    Store response data for idempotent requests
    
    Args:
        session: Database session
        request: FastAPI request object
        request_data: Original request data
        response_data: Response data to cache
        operation_name: Name of the operation for logging
        ttl_hours: Time to live in hours
    """
    idempotency_key = get_idempotency_key_from_request(request)
    
    if not idempotency_key:
        return
    
    request_hash = generate_request_hash(request_data)
    
    await store_idempotency_key(session, idempotency_key, request_hash, response_data, ttl_hours)
    
    # Log idempotent response storage
    await log_idempotent_response(session, idempotency_key, operation_name)


async def log_idempotent_request(session: AsyncSession, key: str, operation_name: str):
    """Log idempotent request"""
    audit_log = AuditLog(
        actor_user_id=None,
        action="IDEMPOTENT_REQUEST",
        resource_type="IdempotencyKey",
        resource_id=key,
        status="success",
        metadata={"operation": operation_name, "type": "request"}
    )
    session.add(audit_log)


async def log_idempotent_response(session: AsyncSession, key: str, operation_name: str):
    """Log idempotent response storage"""
    audit_log = AuditLog(
        actor_user_id=None,
        action="IDEMPOTENT_RESPONSE_STORED",
        resource_type="IdempotencyKey",
        resource_id=key,
        status="success",
        metadata={"operation": operation_name, "type": "response"}
    )
    session.add(audit_log)
