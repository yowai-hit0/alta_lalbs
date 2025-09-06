from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ErrorType(str, Enum):
    """Standardized error types"""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    CONFLICT_ERROR = "conflict_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"


class ErrorDetail(BaseModel):
    """Detailed error information for validation errors"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    value: Optional[Any] = Field(None, description="Value that caused the error")


class ErrorResponse(BaseModel):
    """Centralized error response schema"""
    error: "ErrorInfo" = Field(..., description="Error information")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")
    path: Optional[str] = Field(None, description="API path where error occurred")
    method: Optional[str] = Field(None, description="HTTP method")


class ErrorInfo(BaseModel):
    """Core error information"""
    type: ErrorType = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional error metadata")


class ValidationErrorResponse(ErrorResponse):
    """Specific error response for validation errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            code="VALIDATION_ERROR"
        )
    )


class AuthenticationErrorResponse(ErrorResponse):
    """Specific error response for authentication errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.AUTHENTICATION_ERROR,
            message="Authentication failed",
            code="AUTH_ERROR"
        )
    )


class AuthorizationErrorResponse(ErrorResponse):
    """Specific error response for authorization errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.AUTHORIZATION_ERROR,
            message="Access denied",
            code="AUTH_ERROR"
        )
    )


class NotFoundErrorResponse(ErrorResponse):
    """Specific error response for not found errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.NOT_FOUND_ERROR,
            message="Resource not found",
            code="NOT_FOUND"
        )
    )


class ConflictErrorResponse(ErrorResponse):
    """Specific error response for conflict errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.CONFLICT_ERROR,
            message="Resource conflict",
            code="CONFLICT"
        )
    )


class RateLimitErrorResponse(ErrorResponse):
    """Specific error response for rate limit errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.RATE_LIMIT_ERROR,
            message="Rate limit exceeded",
            code="RATE_LIMITED"
        )
    )


class ServerErrorResponse(ErrorResponse):
    """Specific error response for server errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.SERVER_ERROR,
            message="Internal server error",
            code="SERVER_ERROR"
        )
    )


class DatabaseErrorResponse(ErrorResponse):
    """Specific error response for database errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.DATABASE_ERROR,
            message="Database operation failed",
            code="DATABASE_ERROR"
        )
    )


class ExternalServiceErrorResponse(ErrorResponse):
    """Specific error response for external service errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.EXTERNAL_SERVICE_ERROR,
            message="External service error",
            code="EXTERNAL_SERVICE_ERROR"
        )
    )


class BusinessLogicErrorResponse(ErrorResponse):
    """Specific error response for business logic errors"""
    error: ErrorInfo = Field(
        default_factory=lambda: ErrorInfo(
            type=ErrorType.BUSINESS_LOGIC_ERROR,
            message="Business logic error",
            code="BUSINESS_LOGIC_ERROR"
        )
    )


# Update forward references
ErrorResponse.model_rebuild()
