# Alta Data Backend - Validation & Error Handling Guide

## 🎯 Overview

This guide covers the centralized error schema and comprehensive request validation system implemented for the Alta Data Backend API.

## 🏗️ Architecture

### **Centralized Error Schema**
- **Base Model**: `ErrorResponse` with consistent structure
- **Error Types**: Standardized error categories
- **Error Details**: Detailed validation error information
- **Request Correlation**: Integrated with request tracking

### **Request Validation**
- **Pydantic Models**: Type-safe request validation
- **Custom Validators**: Business logic validation
- **File Upload Validation**: Size, type, and content validation
- **Middleware Integration**: Automatic validation on all endpoints

## 📋 Error Schema Structure

### **Base Error Response**
```json
{
  "error": {
    "type": "validation_error",
    "message": "Validation failed",
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format",
        "code": "value_error.email",
        "value": "invalid-email"
      }
    ],
    "metadata": {}
  },
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/auth/register",
  "method": "POST"
}
```

### **Error Types**
- `validation_error` - Input validation failures
- `authentication_error` - Authentication issues
- `authorization_error` - Permission/access issues
- `not_found_error` - Resource not found
- `conflict_error` - Resource conflicts
- `rate_limit_error` - Rate limiting
- `server_error` - Internal server errors
- `database_error` - Database operation failures
- `external_service_error` - Third-party service issues
- `business_logic_error` - Business rule violations

## 🔍 Request Validators

### **Authentication Validators**

#### **RegisterRequest**
```python
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        # Password strength validation
        # - At least 8 characters
        # - Uppercase, lowercase, digit, special character
        return v
```

#### **LoginRequest**
```python
class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=128)
```

### **Project Validators**

#### **ProjectCreateRequest**
```python
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('name')
    def validate_name(cls, v):
        # Name cannot be empty or whitespace
        return v.strip()
```

#### **ProjectUpdateRequest**
```python
class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
```

### **Data Upload Validators**

#### **DocumentUploadRequest**
```python
class DocumentUploadRequest(BaseModel):
    project_id: str = Field(..., description="Project ID")
    domain: Optional[str] = Field(None, max_length=120)
    
    @validator('project_id')
    def validate_project_id(cls, v):
        # UUID format validation
        return v
```

#### **VoiceUploadRequest**
```python
class VoiceUploadRequest(BaseModel):
    project_id: str = Field(..., description="Project ID")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        # UUID format validation
        return v
```

### **File Upload Validation**

#### **Document Files**
- **Max Size**: 50MB
- **Allowed Types**: PDF, images (JPEG, PNG, TIFF, BMP), text files, Office documents
- **Validation**: File type, size, and content validation

#### **Audio Files**
- **Max Size**: 100MB
- **Allowed Types**: WAV, MP3, MP4, AAC, OGG, FLAC
- **Validation**: Audio format and quality validation

### **Review Validators**

#### **ReviewDecisionRequest**
```python
class ReviewDecisionRequest(BaseModel):
    decision: ReviewDecision = Field(..., description="Review decision")
    feedback: Optional[str] = Field(None, max_length=2000)
    
    # decision: "approve" | "reject"
```

### **Analytics Validators**

#### **AnalyticsSummaryRequest**
```python
class AnalyticsSummaryRequest(BaseModel):
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS)
    project_id: Optional[str] = Field(None)
    
    # timeframe: "7d" | "30d" | "365d"
```

## 🛠️ Validation Middleware

### **Automatic Validation**
The `ValidationMiddleware` automatically validates requests based on:
- **Path Pattern**: Route-specific validation rules
- **HTTP Method**: Method-specific validation
- **Content Type**: JSON, form-data, multipart validation
- **Query Parameters**: URL parameter validation

### **Validation Flow**
```
1. Request arrives → ValidationMiddleware
2. Extract request data (body, query, path params)
3. Apply route-specific validation rules
4. Return validation errors or pass to route handler
```

### **Custom Validators**

#### **UUID Validation**
```python
def validate_uuid(value: str, field_name: str = "ID") -> str:
    """Validate UUID format"""
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValueError(f'Invalid {field_name} format')
```

#### **String Validation**
```python
def validate_required_string(
    value: str,
    field_name: str,
    min_length: int = 1,
    max_length: int = 255
) -> str:
    """Validate required string field"""
    # Length, content, and format validation
    return value
```

#### **File Upload Validation**
```python
def validate_file_upload(
    filename: str,
    content_type: str,
    size: int,
    file_type: str = "document"
) -> None:
    """Validate file upload parameters"""
    # Size, type, and content validation
```

## 🔧 Error Handling

### **Exception Handlers**

#### **Validation Errors**
- **Status Code**: 422
- **Error Type**: `validation_error`
- **Details**: Field-specific error information
- **Logging**: Structured error logging

#### **Authentication Errors**
- **Status Code**: 401
- **Error Type**: `authentication_error`
- **Message**: Clear authentication failure message

#### **Authorization Errors**
- **Status Code**: 403
- **Error Type**: `authorization_error`
- **Message**: Access denied information

#### **Not Found Errors**
- **Status Code**: 404
- **Error Type**: `not_found_error`
- **Message**: Resource not found

#### **Server Errors**
- **Status Code**: 500
- **Error Type**: `server_error`
- **Message**: Generic server error message
- **Logging**: Full error details with stack trace

### **Error Response Examples**

#### **Validation Error**
```json
{
  "error": {
    "type": "validation_error",
    "message": "Validation failed",
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "password",
        "message": "Password must contain at least one uppercase letter",
        "code": "value_error",
        "value": "weakpassword"
      }
    ]
  },
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/auth/register",
  "method": "POST"
}
```

#### **Authentication Error**
```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid credentials",
    "code": "AUTH_ERROR"
  },
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/auth/login",
  "method": "POST"
}
```

#### **File Upload Error**
```json
{
  "error": {
    "type": "validation_error",
    "message": "File type not allowed for documents",
    "code": "FILE_TYPE_ERROR",
    "details": [
      {
        "field": "file",
        "message": "File type application/zip is not allowed for documents",
        "code": "file_type_error",
        "value": "document.zip"
      }
    ]
  },
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/documents",
  "method": "POST"
}
```

## 🚀 Usage Examples

### **API Endpoint with Validation**
```python
@router.post('/documents')
async def upload_document(
    project_id: str = Query(..., description="Project ID"),
    domain: str | None = Query(None, description="Document domain"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(project_role_required('admin', 'contributor')),
):
    # Validate request parameters
    upload_request = DocumentUploadRequest(project_id=project_id, domain=domain)
    
    # Validate file before processing
    validate_file_upload(file, ALLOWED_DOC_TYPES)
    
    # Process file upload...
```

### **Custom Validation in Route**
```python
@router.post('/projects')
async def create_project(
    payload: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Pydantic validation is automatic
    # Additional business logic validation
    if len(payload.name.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Project name must be at least 3 characters"
        )
    
    # Create project...
```

### **Error Response in Client**
```python
try:
    response = requests.post('/api/auth/register', json={
        'email': 'invalid-email',
        'password': 'weak'
    })
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error_data = response.json()
    print(f"Error Type: {error_data['error']['type']}")
    print(f"Message: {error_data['error']['message']}")
    for detail in error_data['error']['details']:
        print(f"Field {detail['field']}: {detail['message']}")
```

## 📊 Monitoring & Debugging

### **Error Logging**
- **Structured Logging**: JSON format with correlation IDs
- **Error Context**: Request path, method, user, timestamp
- **Stack Traces**: Full error details for debugging
- **Audit Trail**: All errors logged to audit system

### **Request Correlation**
- **Request ID**: Unique identifier for each request
- **Error Tracking**: Link errors to specific requests
- **Debugging**: Trace request flow through system

### **Validation Metrics**
- **Validation Success Rate**: Track validation effectiveness
- **Common Errors**: Identify frequent validation issues
- **Performance Impact**: Monitor validation overhead

## 🔧 Configuration

### **Environment Variables**
```bash
# Validation settings
VALIDATION_STRICT_MODE=true
MAX_FILE_SIZE_DOCUMENT=52428800  # 50MB
MAX_FILE_SIZE_AUDIO=104857600    # 100MB
ALLOWED_DOCUMENT_TYPES=pdf,jpg,png,docx
ALLOWED_AUDIO_TYPES=wav,mp3,mp4,aac
```

### **Middleware Order**
```python
# Order matters for middleware
app.add_middleware(AuditLoggingMiddleware)      # 1. Log all requests
app.add_middleware(RequestCorrelationMiddleware) # 2. Add request ID
app.add_middleware(SecurityHeadersMiddleware)   # 3. Security headers
app.add_middleware(ValidationMiddleware)        # 4. Request validation
app.add_middleware(InputValidationMiddleware)   # 5. Input sanitization
app.add_middleware(RateLimitMiddleware)         # 6. Rate limiting
```

## 🎯 Best Practices

### **Validation Design**
1. **Fail Fast**: Validate early in request pipeline
2. **Clear Messages**: Provide actionable error messages
3. **Consistent Format**: Use standardized error schema
4. **Field-Level Details**: Specific validation error information
5. **Request Correlation**: Link errors to requests

### **Error Handling**
1. **Log Everything**: Comprehensive error logging
2. **Don't Expose Internals**: Generic error messages for users
3. **Include Context**: Request path, method, user information
4. **Audit Trail**: Track all errors for compliance
5. **Monitoring**: Alert on error rate increases

### **Client Integration**
1. **Handle All Error Types**: Implement error type handling
2. **Display User-Friendly Messages**: Transform technical errors
3. **Retry Logic**: Implement retry for transient errors
4. **Request Correlation**: Include request ID in support requests
5. **Validation Feedback**: Show field-level validation errors

## 🚨 Troubleshooting

### **Common Issues**

#### **Validation Not Working**
```bash
# Check middleware order
# Ensure ValidationMiddleware is added before route handlers
# Verify Pydantic models are imported correctly
```

#### **File Upload Validation Failing**
```bash
# Check file size limits
# Verify allowed file types
# Ensure content-type detection is working
```

#### **Error Response Format Issues**
```bash
# Verify error schema imports
# Check exception handler registration
# Ensure request correlation is working
```

### **Debugging Steps**
1. **Check Logs**: Review structured error logs
2. **Request Correlation**: Use request ID to trace issues
3. **Validation Rules**: Verify Pydantic model definitions
4. **Middleware Order**: Ensure correct middleware sequence
5. **Error Handlers**: Confirm exception handlers are registered

This comprehensive validation and error handling system ensures robust, user-friendly API responses with consistent error formatting and detailed validation feedback! 🚀
