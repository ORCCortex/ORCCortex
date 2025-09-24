from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProblemStatus(str, Enum):
    """Problem processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Problem(BaseModel):
    """Math problem model"""
    id: str
    user_id: str
    original_filename: str
    file_path: str
    extracted_text: Optional[str] = None
    math_expressions: Optional[List[str]] = None
    status: ProblemStatus = ProblemStatus.PENDING
    created_at: datetime
    updated_at: datetime


class ProblemCreate(BaseModel):
    """Model for creating a new problem"""
    user_id: str
    original_filename: str


class ProblemResponse(BaseModel):
    """Response model for problem data"""
    id: str
    user_id: str
    original_filename: str
    extracted_text: Optional[str] = None
    math_expressions: Optional[List[str]] = None
    status: ProblemStatus
    created_at: datetime
    updated_at: datetime


class ProblemUpdate(BaseModel):
    """Model for updating problem data"""
    extracted_text: Optional[str] = None
    math_expressions: Optional[List[str]] = None
    status: Optional[ProblemStatus] = None