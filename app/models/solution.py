from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SolutionStatus(str, Enum):
    """Solution processing status"""
    PENDING = "pending"
    SOLVING = "solving"
    COMPLETED = "completed"
    FAILED = "failed"


class Solution(BaseModel):
    """Math solution model"""
    id: str
    problem_id: str
    user_id: str
    math_expression: str
    solution_steps: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None
    status: SolutionStatus = SolutionStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SolutionCreate(BaseModel):
    """Model for creating a new solution"""
    problem_id: str
    user_id: str
    math_expression: str


class SolutionResponse(BaseModel):
    """Response model for solution data"""
    id: str
    problem_id: str
    user_id: str
    math_expression: str
    solution_steps: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None
    status: SolutionStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SolutionUpdate(BaseModel):
    """Model for updating solution data"""
    solution_steps: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None
    status: Optional[SolutionStatus] = None
    error_message: Optional[str] = None