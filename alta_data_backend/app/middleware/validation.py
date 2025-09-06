from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable, Dict, Any
import json
import re
from urllib.parse import parse_qs
from ..schemas.errors import ErrorResponse, ErrorInfo, ErrorType, ErrorDetail
from ..schemas.data_validators import FileUploadValidator
from ..schemas.auth_validators import RegisterRequest, LoginRequest
from ..schemas.project_validators import ProjectCreateRequest, ProjectUpdateRequest
from ..schemas.data_validators import DocumentUploadRequest, VoiceUploadRequest
from ..schemas.review_validators import ReviewDecisionRequest
from ..schemas.analytics_validators import AnalyticsSummaryRequest
from contextvars import ContextVar

# Context variable for request data
request_data_var: ContextVar[Dict[str, Any]] = ContextVar('request_data', default={})


class ValidationMiddleware:
    """Middleware for request validation"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Validate request based on path and method
        try:
            await self._validate_request(request)
        except HTTPException as e:
            response = JSONResponse(
                status_code=e.status_code,
                content=self._create_error_response(e, request)
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)
    
    async def _validate_request(self, request: Request):
        """Validate incoming request"""
        path = request.url.path
        method = request.method
        
        # Store request data in context
        request_data = await self._extract_request_data(request)
        request_data_var.set(request_data)
        
        # Route-specific validation
        if path.startswith("/api/auth/register") and method == "POST":
            await self._validate_registration(request, request_data)
        elif path.startswith("/api/auth/login") and method == "POST":
            await self._validate_login(request, request_data)
        elif path.startswith("/api/projects") and method == "POST":
            await self._validate_project_creation(request, request_data)
        elif path.startswith("/api/projects/") and method in ["PUT", "PATCH"]:
            await self._validate_project_update(request, request_data)
        elif path.startswith("/api/documents") and method == "POST":
            await self._validate_document_upload(request, request_data)
        elif path.startswith("/api/voice") and method == "POST":
            await self._validate_voice_upload(request, request_data)
        elif path.startswith("/api/review/") and method == "PATCH":
            await self._validate_review_decision(request, request_data)
        elif path.startswith("/api/analytics") and method == "GET":
            await self._validate_analytics_request(request, request_data)
    
    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract request data for validation"""
        data = {}
        
        # Extract query parameters
        data["query_params"] = dict(request.query_params)
        
        # Extract path parameters
        data["path_params"] = dict(request.path_params)
        
        # Extract headers
        data["headers"] = dict(request.headers)
        
        # Extract body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data["body"] = json.loads(body.decode())
                    elif "multipart/form-data" in content_type:
                        # For file uploads, we'll validate in the route handler
                        data["is_multipart"] = True
            except Exception:
                # If body parsing fails, we'll handle it in route validation
                pass
        
        return data
    
    async def _validate_registration(self, request: Request, data: Dict[str, Any]):
        """Validate user registration request"""
        body = data.get("body", {})
        
        # Validate email
        email = body.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        if not self._is_valid_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password
        password = body.get("password")
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
        
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
    
    async def _validate_login(self, request: Request, data: Dict[str, Any]):
        """Validate user login request"""
        body = data.get("body", {})
        
        # Validate email
        email = body.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        if not self._is_valid_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password
        password = body.get("password")
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
    
    async def _validate_project_creation(self, request: Request, data: Dict[str, Any]):
        """Validate project creation request"""
        body = data.get("body", {})
        
        # Validate name
        name = body.get("name")
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name is required"
            )
        
        if not name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name cannot be empty"
            )
        
        if len(name.strip()) > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name must be 200 characters or less"
            )
        
        # Validate description
        description = body.get("description")
        if description and len(description) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project description must be 1000 characters or less"
            )
    
    async def _validate_project_update(self, request: Request, data: Dict[str, Any]):
        """Validate project update request"""
        body = data.get("body", {})
        
        # Validate name if provided
        name = body.get("name")
        if name is not None:
            if not name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project name cannot be empty"
                )
            
            if len(name.strip()) > 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project name must be 200 characters or less"
                )
        
        # Validate description if provided
        description = body.get("description")
        if description is not None and len(description) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project description must be 1000 characters or less"
            )
    
    async def _validate_document_upload(self, request: Request, data: Dict[str, Any]):
        """Validate document upload request"""
        query_params = data.get("query_params", {})
        
        # Validate project_id
        project_id = query_params.get("project_id")
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project ID is required"
            )
        
        if not self._is_valid_uuid(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )
    
    async def _validate_voice_upload(self, request: Request, data: Dict[str, Any]):
        """Validate voice upload request"""
        query_params = data.get("query_params", {})
        
        # Validate project_id
        project_id = query_params.get("project_id")
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project ID is required"
            )
        
        if not self._is_valid_uuid(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )
    
    async def _validate_review_decision(self, request: Request, data: Dict[str, Any]):
        """Validate review decision request"""
        query_params = data.get("query_params", {})
        
        # Validate decision
        decision = query_params.get("decision")
        if not decision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review decision is required"
            )
        
        if decision not in ["approve", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review decision must be 'approve' or 'reject'"
            )
    
    async def _validate_analytics_request(self, request: Request, data: Dict[str, Any]):
        """Validate analytics request"""
        query_params = data.get("query_params", {})
        
        # Validate timeframe
        timeframe = query_params.get("timeframe", "7d")
        if timeframe not in ["7d", "30d", "365d"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timeframe. Must be '7d', '30d', or '365d'"
            )
        
        # Validate project_id if provided
        project_id = query_params.get("projectId")
        if project_id and not self._is_valid_uuid(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Validate UUID format"""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return re.match(pattern, uuid_string, re.IGNORECASE) is not None
    
    def _create_error_response(self, exception: HTTPException, request: Request) -> Dict[str, Any]:
        """Create standardized error response"""
        from contextvars import ContextVar
        request_id_var = ContextVar('request_id', default=None)
        
        error_response = ErrorResponse(
            error=ErrorInfo(
                type=ErrorType.VALIDATION_ERROR,
                message=exception.detail,
                code="VALIDATION_ERROR"
            ),
            request_id=request_id_var.get(),
            path=request.url.path,
            method=request.method
        )
        
        return error_response.dict()


def validate_file_upload(
    filename: str,
    content_type: str,
    size: int,
    file_type: str = "document"
) -> None:
    """Validate file upload parameters"""
    if file_type == "document":
        FileUploadValidator.validate_document_file(filename, content_type, size)
    elif file_type == "audio":
        FileUploadValidator.validate_audio_file(filename, content_type, size)
    else:
        raise ValueError(f"Unknown file type: {file_type}")


def validate_uuid(value: str, field_name: str = "ID") -> str:
    """Validate UUID format"""
    return UUIDValidator.validate_uuid(value, field_name)


def validate_required_string(
    value: str,
    field_name: str,
    min_length: int = 1,
    max_length: int = 255
) -> str:
    """Validate required string field"""
    return CommonValidators.validate_required_string(value, field_name, min_length, max_length)


def validate_optional_string(
    value: str,
    field_name: str,
    max_length: int = 255
) -> str:
    """Validate optional string field"""
    return CommonValidators.validate_optional_string(value, field_name, max_length)
