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
    page_number: Optional[int] = None  # Page number in the original PDF
    extracted_text: Optional[str] = None  # Raw extracted text (legacy)
    markdown_content: Optional[str] = None  # Markdown formatted content
    math_expressions: Optional[List[str]] = None  # Legacy field for backward compatibility
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
    page_number: Optional[int] = None  # Page number in the original PDF
    extracted_text: Optional[str] = None  # Raw extracted text (legacy)
    markdown_content: Optional[str] = None  # Markdown formatted content
    math_expressions: Optional[List[str]] = None  # Legacy field for backward compatibility
    status: ProblemStatus
    created_at: datetime
    updated_at: datetime


class ProblemUpdate(BaseModel):
    """Model for updating problem data"""
    extracted_text: Optional[str] = None  # Raw extracted text (legacy)
    markdown_content: Optional[str] = None  # Markdown formatted content
    math_expressions: Optional[List[str]] = None  # Legacy field for backward compatibility
    status: Optional[ProblemStatus] = None


class MultipleProblemsResponse(BaseModel):
    """Response model for multiple problems created from a single PDF"""
    total_pages: int
    problems: List[ProblemResponse]
    original_filename: str
    upload_status: str