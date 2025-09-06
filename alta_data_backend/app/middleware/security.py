from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
from typing import Callable
from contextvars import ContextVar
import re
from ..utils.audit_logger import log_audit_event

# Context variable for request correlation
request_id_var: ContextVar[str] = ContextVar('request_id')
user_id_var: ContextVar[str] = ContextVar('user_id', default=None)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Add request correlation ID and timing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate input data for security"""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content={"error": {"type": "request_too_large", "message": "Request too large"}}
            )
        
        # Validate file uploads
        if request.url.path in ["/documents", "/voice"]:
            if request.method == "POST":
                # Additional validation will be done in the route handler
                pass
        
        # Validate email endpoints
        if request.url.path == "/auth/register" and request.method == "POST":
            # Email validation will be done in the route handler
            pass
        
        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limits = {
            "/auth/login": {"limit": 5, "window": 300},  # 5 requests per 5 minutes
            "/auth/register": {"limit": 3, "window": 3600},  # 3 requests per hour
            "/auth/verify-email": {"limit": 10, "window": 300},  # 10 requests per 5 minutes
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.redis_client:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Check rate limits
        path = request.url.path
        for pattern, limits in self.rate_limits.items():
            if path.startswith(pattern):
                if await self._is_rate_limited(client_ip, path, limits["limit"], limits["window"]):
                    return JSONResponse(
                        status_code=429,
                        content={"error": {"type": "rate_limited", "message": "Too many requests"}}
                    )
                break
        
        response = await call_next(request)
        return response
    
    async def _is_rate_limited(self, client_ip: str, path: str, limit: int, window: int) -> bool:
        """Check if client is rate limited"""
        if not self.redis_client:
            return False
        
        key = f"rate_limit:{client_ip}:{path}"
        try:
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, window)
            return current > limit
        except Exception:
            # If Redis is down, allow the request
            return False


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit purposes"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get user ID if available
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
            user_id_var.set(user_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log request
        await self._log_request(request, response, processing_time, user_id)
        
        return response
    
    async def _log_request(self, request: Request, response: Response, processing_time: float, user_id: str = None):
        """Log request details"""
        try:
            log_audit_event(
                action="API_REQUEST",
                status="success" if response.status_code < 400 else "failure",
                resource_type="API",
                resource_id=request_id_var.get(),
                actor_user_id=user_id,
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "user_agent": request.headers.get("user-agent", ""),
                    "ip_address": request.client.host,
                }
            )
        except Exception as e:
            # Don't let logging errors break the request
            print(f"Audit logging failed: {e}")


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_filename(filename: str) -> bool:
    """Validate filename for security"""
    if not filename:
        return False
    
    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in dangerous_chars):
        return False
    
    # Check length
    if len(filename) > 255:
        return False
    
    return True


def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return text
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    if len(text) > 10000:
        text = text[:10000]
    
    return text
