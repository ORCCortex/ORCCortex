from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model for authentication and user management"""
    uid: str
    email: str
    display_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    """Model for user creation"""
    email: str
    password: str
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user data"""
    uid: str
    email: str
    display_name: Optional[str] = None
    created_at: datetime