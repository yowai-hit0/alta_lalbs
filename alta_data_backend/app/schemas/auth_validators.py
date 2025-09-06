from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
import re


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('email')
    def validate_email_domain(cls, v):
        """Validate email domain"""
        # Add domain validation if needed
        return v.lower()


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")
    
    @validator('email')
    def validate_email(cls, v):
        """Normalize email"""
        return v.lower()


class EmailVerificationRequest(BaseModel):
    """Email verification request"""
    token: str = Field(..., min_length=32, max_length=128, description="Verification token")
    
    @validator('token')
    def validate_token(cls, v):
        """Validate token format"""
        if not v.strip():
            raise ValueError('Token cannot be empty')
        return v.strip()


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="User email address")
    
    @validator('email')
    def validate_email(cls, v):
        """Normalize email"""
        return v.lower()


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request"""
    token: str = Field(..., min_length=32, max_length=128, description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('token')
    def validate_token(cls, v):
        """Validate token format"""
        if not v.strip():
            raise ValueError('Token cannot be empty')
        return v.strip()
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=1, max_length=128, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('current_password')
    def validate_current_password(cls, v):
        """Validate current password"""
        if not v.strip():
            raise ValueError('Current password cannot be empty')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UpdateProfileRequest(BaseModel):
    """Update user profile request"""
    email: Optional[EmailStr] = Field(None, description="New email address")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    
    @validator('email')
    def validate_email(cls, v):
        """Normalize email if provided"""
        if v is not None:
            return v.lower()
        return v
    
    @validator('first_name')
    def validate_first_name(cls, v):
        """Validate first name"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 100:
                raise ValueError('First name must be 100 characters or less')
            return v.strip()
        return v
    
    @validator('last_name')
    def validate_last_name(cls, v):
        """Validate last name"""
        if v is not None:
            if not v.strip():
                return None
            if len(v.strip()) > 100:
                raise ValueError('Last name must be 100 characters or less')
            return v.strip()
        return v
