from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
import uuid


class TimeFrame(str, Enum):
    """Analytics timeframes"""
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    THREE_SIXTY_FIVE_DAYS = "365d"


class AnalyticsSummaryRequest(BaseModel):
    """Analytics summary request"""
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    project_id: Optional[str] = Field(None, description="Project ID for project-specific analytics")
    include_details: bool = Field(True, description="Include detailed breakdown")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError('Invalid project ID format')
        return v


class UserAnalyticsRequest(BaseModel):
    """User analytics request"""
    user_id: str = Field(..., description="User ID")
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    include_contributions: bool = Field(True, description="Include contribution statistics")
    include_reviews: bool = Field(True, description="Include review statistics")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid user ID format')


class ProjectAnalyticsRequest(BaseModel):
    """Project analytics request"""
    project_id: str = Field(..., description="Project ID")
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    include_members: bool = Field(True, description="Include member statistics")
    include_contributions: bool = Field(True, description="Include contribution statistics")
    include_reviews: bool = Field(True, description="Include review statistics")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid project ID format')


class DocumentAnalyticsRequest(BaseModel):
    """Document analytics request"""
    project_id: Optional[str] = Field(None, description="Project ID filter")
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    include_status_breakdown: bool = Field(True, description="Include status breakdown")
    include_domain_breakdown: bool = Field(True, description="Include domain breakdown")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError('Invalid project ID format')
        return v


class VoiceAnalyticsRequest(BaseModel):
    """Voice analytics request"""
    project_id: Optional[str] = Field(None, description="Project ID filter")
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    include_language_breakdown: bool = Field(True, description="Include language breakdown")
    include_duration_stats: bool = Field(True, description="Include duration statistics")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError('Invalid project ID format')
        return v


class ReviewAnalyticsRequest(BaseModel):
    """Review analytics request"""
    project_id: Optional[str] = Field(None, description="Project ID filter")
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    reviewer_id: Optional[str] = Field(None, description="Reviewer ID filter")
    include_approval_rates: bool = Field(True, description="Include approval rates")
    include_reviewer_performance: bool = Field(True, description="Include reviewer performance")
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError('Invalid project ID format')
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


class SystemAnalyticsRequest(BaseModel):
    """System analytics request"""
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    include_user_stats: bool = Field(True, description="Include user statistics")
    include_project_stats: bool = Field(True, description="Include project statistics")
    include_storage_stats: bool = Field(True, description="Include storage statistics")
    include_performance_stats: bool = Field(True, description="Include performance statistics")


class CustomAnalyticsRequest(BaseModel):
    """Custom analytics request"""
    metrics: list = Field(..., description="List of metrics to include")
    filters: Optional[dict] = Field(None, description="Additional filters")
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    group_by: Optional[str] = Field(None, description="Group results by field")
    
    @validator('metrics')
    def validate_metrics(cls, v):
        """Validate metrics"""
        if not isinstance(v, list):
            raise ValueError('Metrics must be a list')
        if len(v) == 0:
            raise ValueError('Metrics list cannot be empty')
        if len(v) > 20:
            raise ValueError('Cannot request more than 20 metrics at once')
        
        allowed_metrics = [
            'user_count', 'project_count', 'document_count', 'voice_count',
            'review_count', 'approval_rate', 'storage_usage', 'active_users',
            'contributions_per_day', 'reviews_per_day', 'average_review_time',
            'top_contributors', 'top_reviewers', 'project_activity',
            'file_type_breakdown', 'language_breakdown', 'status_breakdown'
        ]
        
        for metric in v:
            if not isinstance(metric, str):
                raise ValueError('Each metric must be a string')
            if metric not in allowed_metrics:
                raise ValueError(f'Invalid metric: {metric}. Allowed metrics: {", ".join(allowed_metrics)}')
        
        return v
    
    @validator('filters')
    def validate_filters(cls, v):
        """Validate filters"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Filters must be a dictionary')
            # Limit filter size
            import json
            if len(json.dumps(v)) > 5000:  # 5KB limit
                raise ValueError('Filters too large (max 5KB)')
        return v
    
    @validator('group_by')
    def validate_group_by(cls, v):
        """Validate group_by"""
        if v is not None:
            allowed_group_by = [
                'day', 'week', 'month', 'year', 'project', 'user', 'status',
                'domain', 'language', 'file_type', 'reviewer'
            ]
            if v not in allowed_group_by:
                raise ValueError(f'Invalid group_by. Must be one of: {", ".join(allowed_group_by)}')
        return v


class ExportAnalyticsRequest(BaseModel):
    """Export analytics request"""
    analytics_request: dict = Field(..., description="Analytics request parameters")
    format: str = Field("json", description="Export format")
    include_charts: bool = Field(False, description="Include chart data")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate export format"""
        allowed_formats = ["json", "csv", "xlsx", "pdf"]
        if v not in allowed_formats:
            raise ValueError(f'Invalid format. Must be one of: {", ".join(allowed_formats)}')
        return v
    
    @validator('analytics_request')
    def validate_analytics_request(cls, v):
        """Validate analytics request"""
        if not isinstance(v, dict):
            raise ValueError('Analytics request must be a dictionary')
        # Limit request size
        import json
        if len(json.dumps(v)) > 10000:  # 10KB limit
            raise ValueError('Analytics request too large (max 10KB)')
        return v


class AnalyticsDashboardRequest(BaseModel):
    """Analytics dashboard request"""
    dashboard_type: str = Field(..., description="Dashboard type")
    project_id: Optional[str] = Field(None, description="Project ID for project dashboard")
    timeframe: TimeFrame = Field(TimeFrame.SEVEN_DAYS, description="Time frame for analytics")
    refresh_interval: Optional[int] = Field(None, ge=60, le=3600, description="Refresh interval in seconds")
    
    @validator('dashboard_type')
    def validate_dashboard_type(cls, v):
        """Validate dashboard type"""
        allowed_types = ["overview", "project", "user", "system", "custom"]
        if v not in allowed_types:
            raise ValueError(f'Invalid dashboard type. Must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('project_id')
    def validate_project_id(cls, v):
        """Validate project ID format"""
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError('Invalid project ID format')
        return v
    
    @validator('refresh_interval')
    def validate_refresh_interval(cls, v):
        """Validate refresh interval"""
        if v is not None:
            if v < 60:
                raise ValueError('Refresh interval must be at least 60 seconds')
            if v > 3600:
                raise ValueError('Refresh interval cannot exceed 3600 seconds')
        return v
