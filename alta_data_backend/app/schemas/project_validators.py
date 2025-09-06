from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from enum import Enum


class ProjectRole(str, Enum):
    """Project roles"""
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"


class ProjectCreateRequest(BaseModel):
    """Project creation request"""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate project name"""
        if not v.strip():
            raise ValueError('Project name cannot be empty')
        if len(v.strip()) < 1:
            raise ValueError('Project name must be at least 1 character long')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """Validate project description"""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class ProjectUpdateRequest(BaseModel):
    """Project update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate project name"""
        if v is not None:
            if not v.strip():
                raise ValueError('Project name cannot be empty')
            if len(v.strip()) < 1:
                raise ValueError('Project name must be at least 1 character long')
            return v.strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate project description"""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class ProjectInvitationRequest(BaseModel):
    """Project invitation request"""
    email: EmailStr = Field(..., description="Email to invite")
    role: ProjectRole = Field(..., description="Role to assign")
    
    @validator('email')
    def validate_email(cls, v):
        """Normalize email"""
        return v.lower()


class InvitationAcceptRequest(BaseModel):
    """Invitation acceptance request"""
    token: str = Field(..., min_length=32, max_length=128, description="Invitation token")
    
    @validator('token')
    def validate_token(cls, v):
        """Validate token format"""
        if not v.strip():
            raise ValueError('Token cannot be empty')
        return v.strip()


class ProjectMemberUpdateRequest(BaseModel):
    """Project member role update request"""
    role: ProjectRole = Field(..., description="New role for the member")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate role"""
        if v not in [ProjectRole.ADMIN, ProjectRole.CONTRIBUTOR, ProjectRole.REVIEWER]:
            raise ValueError('Invalid role. Must be admin, contributor, or reviewer')
        return v


class ProjectSearchRequest(BaseModel):
    """Project search request"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    include_archived: bool = Field(False, description="Include archived projects")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()


class ProjectArchiveRequest(BaseModel):
    """Project archive request"""
    archive: bool = Field(..., description="Whether to archive or unarchive the project")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for archiving")
    
    @validator('reason')
    def validate_reason(cls, v):
        """Validate reason"""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class ProjectSettingsUpdateRequest(BaseModel):
    """Project settings update request"""
    allow_public_access: Optional[bool] = Field(None, description="Allow public access")
    require_approval: Optional[bool] = Field(None, description="Require approval for contributions")
    max_file_size: Optional[int] = Field(None, ge=1024, le=104857600, description="Max file size in bytes")
    allowed_file_types: Optional[list] = Field(None, description="Allowed file types")
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        """Validate max file size"""
        if v is not None:
            if v < 1024:  # 1KB minimum
                raise ValueError('Max file size must be at least 1KB')
            if v > 104857600:  # 100MB maximum
                raise ValueError('Max file size cannot exceed 100MB')
        return v
    
    @validator('allowed_file_types')
    def validate_allowed_file_types(cls, v):
        """Validate allowed file types"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Allowed file types must be a list')
            if len(v) == 0:
                raise ValueError('Allowed file types cannot be empty')
            # Validate each file type
            for file_type in v:
                if not isinstance(file_type, str):
                    raise ValueError('Each file type must be a string')
                if not file_type.strip():
                    raise ValueError('File type cannot be empty')
        return v


class ProjectStatisticsRequest(BaseModel):
    """Project statistics request"""
    timeframe: str = Field("7d", description="Time frame for statistics")
    include_members: bool = Field(True, description="Include member statistics")
    include_contributions: bool = Field(True, description="Include contribution statistics")
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe"""
        allowed_timeframes = ["1d", "7d", "30d", "90d", "365d"]
        if v not in allowed_timeframes:
            raise ValueError(f'Invalid timeframe. Must be one of: {", ".join(allowed_timeframes)}')
        return v
