from pydantic import BaseModel, Field, validator
from typing import Optional, List
import uuid


class DocumentUploadRequest(BaseModel):
    """Document upload request"""
    project_id: str = Field(..., description="Project ID")
    domain: Optional[str] = Field(None, max_length=120, description="Document domain")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid project ID format')
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 120:
                raise ValueError('Domain must be 120 characters or less')
            return v.strip()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot have more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag.strip()) > 50:
                    raise ValueError('Tag must be 50 characters or less')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('extra_metadata')
    def validate_metadata(cls, v):
        """Validate metadata"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            # Limit metadata size
            import json
            if len(json.dumps(v)) > 10000:  # 10KB limit
                raise ValueError('Metadata too large (max 10KB)')
        return v


class VoiceUploadRequest(BaseModel):
    """Voice upload request"""
    project_id: str = Field(..., description="Project ID")
    language: Optional[str] = Field(None, max_length=10, description="Audio language code")
    tags: Optional[List[str]] = Field(None, description="Audio tags")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid project ID format')
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language code"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 10:
                raise ValueError('Language code must be 10 characters or less')
            return v.strip().lower()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot have more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag.strip()) > 50:
                    raise ValueError('Tag must be 50 characters or less')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('extra_metadata')
    def validate_metadata(cls, v):
        """Validate metadata"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            # Limit metadata size
            import json
            if len(json.dumps(v)) > 10000:  # 10KB limit
                raise ValueError('Metadata too large (max 10KB)')
        return v


class DocumentUpdateRequest(BaseModel):
    """Document update request"""
    domain: Optional[str] = Field(None, max_length=120, description="Document domain")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 120:
                raise ValueError('Domain must be 120 characters or less')
            return v.strip()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot have more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag.strip()) > 50:
                    raise ValueError('Tag must be 50 characters or less')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('extra_metadata')
    def validate_metadata(cls, v):
        """Validate metadata"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            # Limit metadata size
            import json
            if len(json.dumps(v)) > 10000:  # 10KB limit
                raise ValueError('Metadata too large (max 10KB)')
        return v


class VoiceUpdateRequest(BaseModel):
    """Voice update request"""
    language: Optional[str] = Field(None, max_length=10, description="Audio language code")
    tags: Optional[List[str]] = Field(None, description="Audio tags")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language code"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 10:
                raise ValueError('Language code must be 10 characters or less')
            return v.strip().lower()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot have more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag.strip()) > 50:
                    raise ValueError('Tag must be 50 characters or less')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('extra_metadata')
    def validate_metadata(cls, v):
        """Validate metadata"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            # Limit metadata size
            import json
            if len(json.dumps(v)) > 10000:  # 10KB limit
                raise ValueError('Metadata too large (max 10KB)')
        return v


class DocumentSearchRequest(BaseModel):
    """Document search request"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    domain: Optional[str] = Field(None, max_length=120, description="Filter by domain")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    status: Optional[str] = Field(None, description="Filter by status")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain"""
        if v is not None:
            if not v.strip():
                return None
            return v.strip()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot filter by more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status"""
        if v is not None:
            allowed_statuses = ["draft", "pending_review", "approved", "rejected"]
            if v not in allowed_statuses:
                raise ValueError(f'Invalid status. Must be one of: {", ".join(allowed_statuses)}')
        return v


class VoiceSearchRequest(BaseModel):
    """Voice search request"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    language: Optional[str] = Field(None, max_length=10, description="Filter by language")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language code"""
        if v is not None:
            if not v.strip():
                return None
            return v.strip().lower()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot filter by more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
            return [tag.strip() for tag in v if tag.strip()]
        return v


class RawTextCreateRequest(BaseModel):
    """Raw text creation request"""
    project_id: str = Field(..., description="Project ID")
    title: str = Field(..., min_length=1, max_length=255, description="Text title")
    content: str = Field(..., min_length=1, description="Text content")
    domain: Optional[str] = Field(None, max_length=120, description="Text domain")
    tags: Optional[List[str]] = Field(None, description="Text tags")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid project ID format')
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title"""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """Validate content"""
        if not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v.strip()) > 100000:  # 100KB limit
            raise ValueError('Content must be 100KB or less')
        return v.strip()
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 120:
                raise ValueError('Domain must be 120 characters or less')
            return v.strip()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot have more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag.strip()) > 50:
                    raise ValueError('Tag must be 50 characters or less')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('extra_metadata')
    def validate_metadata(cls, v):
        """Validate metadata"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            # Limit metadata size
            import json
            if len(json.dumps(v)) > 10000:  # 10KB limit
                raise ValueError('Metadata too large (max 10KB)')
        return v


class RawTextUpdateRequest(BaseModel):
    """Raw text update request"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Text title")
    content: Optional[str] = Field(None, min_length=1, description="Text content")
    domain: Optional[str] = Field(None, max_length=120, description="Text domain")
    tags: Optional[List[str]] = Field(None, description="Text tags")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title"""
        if v is not None:
            if not v.strip():
                raise ValueError('Title cannot be empty')
            return v.strip()
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Validate content"""
        if v is not None:
            if not v.strip():
                raise ValueError('Content cannot be empty')
            if len(v.strip()) > 100000:  # 100KB limit
                raise ValueError('Content must be 100KB or less')
            return v.strip()
        return v
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 120:
                raise ValueError('Domain must be 120 characters or less')
            return v.strip()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot have more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag.strip()) > 50:
                    raise ValueError('Tag must be 50 characters or less')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('extra_metadata')
    def validate_metadata(cls, v):
        """Validate metadata"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Metadata must be a dictionary')
            # Limit metadata size
            import json
            if len(json.dumps(v)) > 10000:  # 10KB limit
                raise ValueError('Metadata too large (max 10KB)')
        return v


class RawTextSearchRequest(BaseModel):
    """Raw text search request"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    domain: Optional[str] = Field(None, max_length=120, description="Filter by domain")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    status: Optional[str] = Field(None, description="Filter by status")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain"""
        if v is not None:
            if not v.strip():
                return None
            return v.strip()
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Tags must be a list')
            if len(v) > 10:
                raise ValueError('Cannot filter by more than 10 tags')
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Each tag must be a string')
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
            return [tag.strip() for tag in v if tag.strip()]
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status"""
        if v is not None:
            allowed_statuses = ["draft", "pending_review", "approved", "rejected"]
            if v not in allowed_statuses:
                raise ValueError(f'Invalid status. Must be one of: {", ".join(allowed_statuses)}')
        return v


class MassSubmissionRequest(BaseModel):
    """Mass submission request"""
    document_ids: Optional[List[str]] = Field(None, description="Document IDs to submit")
    voice_sample_ids: Optional[List[str]] = Field(None, description="Voice sample IDs to submit")
    raw_text_ids: Optional[List[str]] = Field(None, description="Raw text IDs to submit")
    
    @validator('document_ids')
    def validate_document_ids(cls, v):
        """Validate document IDs"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Document IDs must be a list')
            if len(v) > 100:
                raise ValueError('Cannot submit more than 100 documents at once')
            for doc_id in v:
                if not isinstance(doc_id, str):
                    raise ValueError('Each document ID must be a string')
                try:
                    uuid.UUID(doc_id)
                except ValueError:
                    raise ValueError(f'Invalid document ID format: {doc_id}')
        return v
    
    @validator('voice_sample_ids')
    def validate_voice_sample_ids(cls, v):
        """Validate voice sample IDs"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Voice sample IDs must be a list')
            if len(v) > 100:
                raise ValueError('Cannot submit more than 100 voice samples at once')
            for voice_id in v:
                if not isinstance(voice_id, str):
                    raise ValueError('Each voice sample ID must be a string')
                try:
                    uuid.UUID(voice_id)
                except ValueError:
                    raise ValueError(f'Invalid voice sample ID format: {voice_id}')
        return v
    
    @validator('raw_text_ids')
    def validate_raw_text_ids(cls, v):
        """Validate raw text IDs"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Raw text IDs must be a list')
            if len(v) > 100:
                raise ValueError('Cannot submit more than 100 raw texts at once')
            for text_id in v:
                if not isinstance(text_id, str):
                    raise ValueError('Each raw text ID must be a string')
                try:
                    uuid.UUID(text_id)
                except ValueError:
                    raise ValueError(f'Invalid raw text ID format: {text_id}')
        return v


class FileUploadValidator:
    """File upload validation utilities"""
    
    # File size limits (in bytes)
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_AUDIO_SIZE = 100 * 1024 * 1024     # 100MB
    
    # Allowed file types
    ALLOWED_DOCUMENT_TYPES = {
        'application/pdf',
        'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp',
        'text/plain', 'text/csv',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    ALLOWED_AUDIO_TYPES = {
        'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/flac'
    }
    
    @classmethod
    def validate_document_file(cls, filename: str, content_type: str, size: int) -> None:
        """Validate document file upload"""
        if not filename:
            raise ValueError('Filename is required')
        
        if size > cls.MAX_DOCUMENT_SIZE:
            raise ValueError(f'File size exceeds maximum allowed size of {cls.MAX_DOCUMENT_SIZE // (1024*1024)}MB')
        
        if content_type not in cls.ALLOWED_DOCUMENT_TYPES:
            raise ValueError(f'File type {content_type} is not allowed for documents')
    
    @classmethod
    def validate_audio_file(cls, filename: str, content_type: str, size: int) -> None:
        """Validate audio file upload"""
        if not filename:
            raise ValueError('Filename is required')
        
        if size > cls.MAX_AUDIO_SIZE:
            raise ValueError(f'File size exceeds maximum allowed size of {cls.MAX_AUDIO_SIZE // (1024*1024)}MB')
        
        if content_type not in cls.ALLOWED_AUDIO_TYPES:
            raise ValueError(f'File type {content_type} is not allowed for audio files')
