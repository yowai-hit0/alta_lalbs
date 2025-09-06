from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import traceback
import logging
from typing import Union
from contextvars import ContextVar

from ..utils.audit_logger import log_audit_event
from ..schemas.errors import (
    ErrorResponse, ErrorInfo, ErrorType, ErrorDetail,
    ValidationErrorResponse, AuthenticationErrorResponse,
    AuthorizationErrorResponse, NotFoundErrorResponse,
    ConflictErrorResponse, RateLimitErrorResponse,
    ServerErrorResponse, DatabaseErrorResponse,
    ExternalServiceErrorResponse, BusinessLogicErrorResponse
)

# Context variable for request correlation
request_id_var: ContextVar[str] = ContextVar('request_id', default=None)

logger = logging.getLogger(__name__)


class AltaDataException(Exception):
    """Base exception for Alta Data application"""
    def __init__(self, message: str, error_code: str = None, status_code: int = 400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class ValidationException(AltaDataException):
    """Validation error exception"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "validation_error", 400)
        self.field = field


class AuthenticationException(AltaDataException):
    """Authentication error exception"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "auth_error", 401)


class AuthorizationException(AltaDataException):
    """Authorization error exception"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "auth_error", 403)


class NotFoundException(AltaDataException):
    """Resource not found exception"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "not_found", 404)


class ConflictException(AltaDataException):
    """Resource conflict exception"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, "conflict", 409)


class RateLimitException(AltaDataException):
    """Rate limit exceeded exception"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "rate_limited", 429)


class ServerException(AltaDataException):
    """Internal server error exception"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, "server_error", 500)


async def alta_data_exception_handler(request: Request, exc: AltaDataException) -> JSONResponse:
    """Handle Alta Data custom exceptions"""
    request_id = request_id_var.get()
    
    # Log the error
    logger.error(f"AltaDataException: {exc.message}", extra={
        "request_id": request_id,
        "error_code": exc.error_code,
        "path": request.url.path,
        "method": request.method,
    })
    
    # Log audit event
    await log_audit_event(
        action="API_ERROR",
        status="failure",
        resource_type="API",
        resource_id=request_id,
        metadata={
            "error_type": "alta_data_exception",
            "error_code": exc.error_code,
            "message": exc.message,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # Create standardized error response
    error_response = ErrorResponse(
        error=ErrorInfo(
            type=ErrorType.BUSINESS_LOGIC_ERROR,
            message=exc.message,
            code=exc.error_code or "BUSINESS_LOGIC_ERROR"
        ),
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id} if request_id else {}
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    request_id = request_id_var.get()
    
    # Log the error
    logger.warning(f"HTTPException: {exc.detail}", extra={
        "request_id": request_id,
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
    })
    
    # Determine error type based on status code
    error_type = ErrorType.SERVER_ERROR
    if exc.status_code == 401:
        error_type = ErrorType.AUTHENTICATION_ERROR
    elif exc.status_code == 403:
        error_type = ErrorType.AUTHORIZATION_ERROR
    elif exc.status_code == 404:
        error_type = ErrorType.NOT_FOUND_ERROR
    elif exc.status_code == 409:
        error_type = ErrorType.CONFLICT_ERROR
    elif exc.status_code == 429:
        error_type = ErrorType.RATE_LIMIT_ERROR
    
    # Create standardized error response
    error_response = ErrorResponse(
        error=ErrorInfo(
            type=error_type,
            message=exc.detail,
            code=f"HTTP_{exc.status_code}"
        ),
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id} if request_id else {}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions"""
    request_id = request_id_var.get()
    
    # Format validation errors
    error_details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        error_details.append(ErrorDetail(
            field=field,
            message=error["msg"],
            code=error["type"],
            value=error.get("input")
        ))
    
    # Log the error
    logger.warning(f"ValidationError: {len(error_details)} validation errors", extra={
        "request_id": request_id,
        "errors": [detail.dict() for detail in error_details],
        "path": request.url.path,
        "method": request.method,
    })
    
    # Create standardized error response
    error_response = ErrorResponse(
        error=ErrorInfo(
            type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            code="VALIDATION_ERROR",
            details=error_details
        ),
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id} if request_id else {}
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy exceptions"""
    request_id = request_id_var.get()
    
    # Log the error
    logger.error(f"SQLAlchemyError: {str(exc)}", extra={
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
    }, exc_info=True)
    
    # Log audit event
    await log_audit_event(
        action="DATABASE_ERROR",
        status="failure",
        resource_type="Database",
        resource_id=request_id,
        metadata={
            "error_type": "sqlalchemy_error",
            "message": str(exc),
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # Create standardized error response
    error_response = ErrorResponse(
        error=ErrorInfo(
            type=ErrorType.DATABASE_ERROR,
            message="Database operation failed",
            code="DATABASE_ERROR",
            metadata={"original_error": str(exc)}
        ),
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id} if request_id else {}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    request_id = request_id_var.get()
    
    # Log the error
    logger.error(f"Unhandled exception: {str(exc)}", extra={
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
    }, exc_info=True)
    
    # Log audit event
    await log_audit_event(
        action="UNHANDLED_ERROR",
        status="failure",
        resource_type="API",
        resource_id=request_id,
        metadata={
            "error_type": "unhandled_exception",
            "message": str(exc),
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # Create standardized error response
    error_response = ErrorResponse(
        error=ErrorInfo(
            type=ErrorType.SERVER_ERROR,
            message="An unexpected error occurred",
            code="SERVER_ERROR",
            metadata={"original_error": str(exc)}
        ),
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id} if request_id else {}
    )


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = 400,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """Create a standardized error response"""
    content = {
        "error": {
            "type": error_type,
            "message": message,
            "requestId": request_id,
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={"X-Request-ID": request_id} if request_id else {}
    )
