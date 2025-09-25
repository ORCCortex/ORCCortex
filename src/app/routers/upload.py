from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
import os
import uuid
from datetime import datetime
import aiofiles

from src.app.models.problem import Problem, ProblemResponse, ProblemStatus
from src.app.services.firebase_service import firebase_service
from src.app.services.ocr_service import ocr_service
from src.app.utils.config import settings
from src.app.utils.exceptions import create_http_exception, ValidationError, FileProcessingError

router = APIRouter()
security = HTTPBearer()


async def verify_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify user authentication"""
    try:
        token = credentials.credentials
        decoded_token = await firebase_service.verify_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


async def process_uploaded_file(file_path: str, problem_id: str, user_id: str):
    """Background task to process uploaded PDF file"""
    try:
        # Extract text and math expressions
        text, math_expressions = await ocr_service.process_pdf(file_path)
        
        # Update problem with extracted data
        # In a real application, you would update the database here
        print(f"Processed problem {problem_id}: {len(text)} characters, {len(math_expressions)} expressions")
        
        # Clean up local file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        print(f"Error processing file for problem {problem_id}: {str(e)}")


@router.post("/upload", response_model=ProblemResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(verify_user)
) -> ProblemResponse:
    """
    Upload a PDF file for OCR processing
    
    - **file**: PDF file to upload
    - Returns problem information with processing status
    """
    try:
        # Validate file
        if not file.filename:
            raise ValidationError("No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise ValidationError("Only PDF files are allowed")
        
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise ValidationError(f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes")
        
        # Generate unique problem ID and file path
        problem_id = str(uuid.uuid4())
        user_id = user.get('uid', 'anonymous')
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file locally first
        file_extension = os.path.splitext(file.filename)[1]
        local_filename = f"{problem_id}{file_extension}"
        local_file_path = os.path.join(settings.UPLOAD_DIR, local_filename)
        
        # Save uploaded file
        async with aiofiles.open(local_file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)
        
        # Create problem record
        problem = Problem(
            id=problem_id,
            user_id=user_id,
            original_filename=file.filename,
            file_path=local_file_path,
            status=ProblemStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Upload to Firebase Storage (if configured)
        try:
            firebase_path = f"problems/{user_id}/{local_filename}"
            await firebase_service.upload_file(local_file_path, firebase_path)
            problem.file_path = firebase_path
        except Exception as e:
            print(f"Firebase upload warning: {str(e)}")
            # Continue with local file path
        
        # Start background processing
        background_tasks.add_task(
            process_uploaded_file,
            local_file_path,
            problem_id,
            user_id
        )
        
        # Update status to processing
        problem.status = ProblemStatus.PROCESSING
        problem.updated_at = datetime.now()
        
        return ProblemResponse(
            id=problem.id,
            user_id=problem.user_id,
            original_filename=problem.original_filename,
            status=problem.status,
            created_at=problem.created_at,
            updated_at=problem.updated_at
        )
        
    except ValidationError as e:
        raise create_http_exception(e)
    except FileProcessingError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/upload/status/{problem_id}")
async def get_upload_status(
    problem_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Get the status of an uploaded file processing
    
    - **problem_id**: ID of the problem to check
    - Returns processing status and results if available
    """
    try:
        # In a real application, you would query the database here
        # For now, return a mock response
        return {
            "problem_id": problem_id,
            "status": "processing",
            "message": "File is being processed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")