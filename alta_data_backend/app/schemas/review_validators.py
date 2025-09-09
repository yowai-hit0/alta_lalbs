from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
import uuid


class ReviewDecision(str, Enum):
    """Review decisions"""
    APPROVE = "approve"
    REJECT = "reject"


class ReviewDecisionRequest(BaseModel):
    """Review decision request"""
    decision: ReviewDecision = Field(..., description="Review decision")
    feedback: Optional[str] = Field(None, max_length=2000, description="Review feedback")
    
    @validator('feedback')
    def validate_feedback(cls, v):
        """Validate feedback"""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class SubmitForReviewRequest(BaseModel):
    """Submit for review request for any item type"""
    item_id: str = Field(..., description="ID of the item to submit")
    item_type: str = Field(..., description="Type: 'document', 'voice', or 'raw_text'")
    priority: Optional[str] = Field("normal", description="Review priority")
    notes: Optional[str] = Field(None, max_length=1000, description="Submission notes")
    
    @validator('item_id')
    def validate_item_id(cls, v):
        """Validate item ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid item ID format')
    
    @validator('item_type')
    def validate_item_type(cls, v):
        allowed_types = ['document', 'voice', 'raw_text']
        if v not in allowed_types:
            raise ValueError(f"Invalid item type. Must be one of: {', '.join(allowed_types)}")
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority"""
        allowed_priorities = ["low", "normal", "high", "urgent"]
        if v not in allowed_priorities:
            raise ValueError(f'Invalid priority. Must be one of: {", ".join(allowed_priorities)}')
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        """Validate notes"""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class ReviewQueueRequest(BaseModel):
    """Review queue request"""
    project_id: str = Field(..., description="Project ID")
    status: Optional[str] = Field("pending_review", description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    reviewer_id: Optional[str] = Field(None, description="Filter by reviewer")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid project ID format')
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status"""
        allowed_statuses = ["draft", "pending_review", "approved", "rejected"]
        if v not in allowed_statuses:
            raise ValueError(f'Invalid status. Must be one of: {", ".join(allowed_statuses)}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority"""
        if v is not None:
            allowed_priorities = ["low", "normal", "high", "urgent"]
            if v not in allowed_priorities:
                raise ValueError(f'Invalid priority. Must be one of: {", ".join(allowed_priorities)}')
        return v
    
    @validator('reviewer_id')
    def validate_reviewer_id(cls, v):
        """Validate reviewer ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError('Invalid reviewer ID format')
        return v


class ReviewHistoryRequest(BaseModel):
    """Review history request"""
    document_id: str = Field(..., description="Document ID")
    include_feedback: bool = Field(True, description="Include review feedback")
    
    @validator('document_id')
    def validate_document_id(cls, v):
        """Validate document ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid document ID format')


class ReviewStatisticsRequest(BaseModel):
    """Review statistics request"""
    project_id: str = Field(..., description="Project ID")
    timeframe: str = Field("7d", description="Time frame for statistics")
    reviewer_id: Optional[str] = Field(None, description="Filter by reviewer")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid project ID format')
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe"""
        allowed_timeframes = ["1d", "7d", "30d", "90d", "365d"]
        if v not in allowed_timeframes:
            raise ValueError(f'Invalid timeframe. Must be one of: {", ".join(allowed_timeframes)}')
        return v
    
    @validator('reviewer_id')
    def validate_reviewer_id(cls, v):
        """Validate reviewer ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError('Invalid reviewer ID format')
        return v


class ReviewAssignmentRequest(BaseModel):
    """Review assignment request"""
    document_id: str = Field(..., description="Document ID")
    reviewer_id: str = Field(..., description="Reviewer ID")
    priority: Optional[str] = Field("normal", description="Review priority")
    due_date: Optional[str] = Field(None, description="Review due date (ISO format)")
    notes: Optional[str] = Field(None, max_length=1000, description="Assignment notes")
    
    @validator('document_id')
    def validate_document_id(cls, v):
        """Validate document ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid document ID format')
    
    @validator('reviewer_id')
    def validate_reviewer_id(cls, v):
        """Validate reviewer ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid reviewer ID format')
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority"""
        allowed_priorities = ["low", "normal", "high", "urgent"]
        if v not in allowed_priorities:
            raise ValueError(f'Invalid priority. Must be one of: {", ".join(allowed_priorities)}')
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v):
        """Validate due date"""
        if v is not None:
            try:
                from datetime import datetime
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError('Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)')
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        """Validate notes"""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class ReviewBulkActionRequest(BaseModel):
    """Review bulk action request"""
    document_ids: list = Field(..., description="List of document IDs")
    action: str = Field(..., description="Bulk action to perform")
    feedback: Optional[str] = Field(None, max_length=2000, description="Bulk feedback")
    
    @validator('document_ids')
    def validate_document_ids(cls, v):
        """Validate document IDs"""
        if not isinstance(v, list):
            raise ValueError('Document IDs must be a list')
        if len(v) == 0:
            raise ValueError('Document IDs list cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot process more than 100 documents at once')
        
        for doc_id in v:
            if not isinstance(doc_id, str):
                raise ValueError('Each document ID must be a string')
            try:
                uuid.UUID(doc_id)
            except ValueError:
                raise ValueError(f'Invalid document ID format: {doc_id}')
        
        return v
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action"""
        allowed_actions = ["approve", "reject", "assign", "unassign"]
        if v not in allowed_actions:
            raise ValueError(f'Invalid action. Must be one of: {", ".join(allowed_actions)}')
        return v
    
    @validator('feedback')
    def validate_feedback(cls, v):
        """Validate feedback"""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
