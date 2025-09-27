from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
import os
import uuid
from datetime import datetime
import aiofiles
import fitz  # PyMuPDF

from src.app.models.problem import Problem, ProblemResponse, ProblemStatus, MultipleProblemsResponse
from src.app.services.firebase_service import firebase_service
from src.app.services.markdown_ocr_service import markdown_ocr_service
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


def get_pdf_page_count(file_path: str) -> int:
    """Get the number of pages in a PDF file"""
    try:
        doc = fitz.open(file_path)
        page_count = doc.page_count
        doc.close()
        return page_count
    except Exception as e:
        print(f"Error getting PDF page count: {str(e)}")
        return 1  # Default to 1 page if we can't determine


async def process_uploaded_file_pages(file_path: str, problem_ids_with_pages: list, user_id: str):
    """Background task to process uploaded PDF file page by page - convert to markdown"""
    try:
        # Convert PDF to markdown for each page
        page_results = await markdown_ocr_service.convert_pdf_to_markdown(file_path)
        
        # Process each page
        for i, (page_num, markdown_content) in enumerate(page_results):
            if i < len(problem_ids_with_pages):
                problem_id = problem_ids_with_pages[i]
                
                # Determine status based on content extraction
                if markdown_content and markdown_content.strip() and markdown_content != "*(Empty page)*":
                    status = ProblemStatus.COMPLETED.value
                    print(f"Successfully extracted content for problem {problem_id} (page {page_num}): {len(markdown_content)} characters")
                else:
                    status = ProblemStatus.COMPLETED.value  # Still completed, just no text
                    print(f"Problem {problem_id} (page {page_num}): No text extracted - likely image-based content")
                
                # Update problem with markdown content in database
                update_data = {
                    'markdown_content': markdown_content or "*(No text extracted - PDF may contain images or complex formatting)*",
                    'status': status
                }
                
                try:
                    await firebase_service.update_problem(problem_id, update_data)
                except Exception as db_error:
                    print(f"Database update failed for problem {problem_id}: {str(db_error)}")
                    # Update status to failed if database update fails
                    try:
                        await firebase_service.update_problem(problem_id, {
                            'status': ProblemStatus.FAILED.value,
                            'error_message': f"Database update failed: {str(db_error)}"
                        })
                    except Exception:
                        pass  # If this fails too, we can't do much more
        
        # Clean up local file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        print(f"Error processing file pages: {str(e)}")
        # Update all problems to failed status
        for problem_id in problem_ids_with_pages:
            try:
                await firebase_service.update_problem(problem_id, {
                    'status': ProblemStatus.FAILED.value,
                    'error_message': str(e)
                })
            except Exception:
                pass  # If database update fails, we can't do much more


async def process_uploaded_file(file_path: str, problem_id: str, user_id: str):
    """Background task to process uploaded PDF file (legacy single-problem support)"""
    try:
        # Convert PDF to markdown
        markdown_content = await markdown_ocr_service.convert_single_pdf_to_markdown(file_path)
        
        # Update problem with markdown content in database
        update_data = {
            'markdown_content': markdown_content,
            'status': ProblemStatus.COMPLETED.value
        }
        
        try:
            await firebase_service.update_problem(problem_id, update_data)
            print(f"Successfully processed problem {problem_id}: {len(markdown_content)} characters of markdown")
        except Exception as db_error:
            print(f"Database update failed for problem {problem_id}: {str(db_error)}")
            # Update status to failed if database update fails
            try:
                await firebase_service.update_problem(problem_id, {
                    'status': ProblemStatus.FAILED.value,
                    'error_message': f"Database update failed: {str(db_error)}"
                })
            except Exception:
                pass  # If this fails too, we can't do much more
        
        # Clean up local file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        print(f"Error processing file for problem {problem_id}: {str(e)}")
        # Update status to failed in database
        try:
            await firebase_service.update_problem(problem_id, {
                'status': ProblemStatus.FAILED.value,
                'error_message': str(e)
            })
        except Exception:
            pass  # If database update fails, we can't do much more


@router.post("/upload", response_model=MultipleProblemsResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(verify_user)
) -> MultipleProblemsResponse:
    """
    Upload a PDF file for OCR processing - splits into multiple problems (one per page)
    
    - **file**: PDF file to upload
    - Returns information about all problems created (one per page)
    """
    try:
        # Validate file
        if not file.filename:
            raise ValidationError("No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise ValidationError("Only PDF files are allowed")
        
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise ValidationError(f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes")
        
        user_id = user.get('uid', 'anonymous')
        
        # Save/update user information in database (if this is their first time)
        try:
            await firebase_service.save_user({
                'uid': user_id,
                'email': user.get('email', ''),
                'display_name': user.get('name', user.get('display_name')),
                'created_at': datetime.now()
            })
        except Exception as e:
            print(f"User save warning: {str(e)}")
            # Continue even if user save fails
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Generate unique filename for the uploaded file
        upload_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        local_filename = f"{upload_id}{file_extension}"
        local_file_path = os.path.join(settings.UPLOAD_DIR, local_filename)
        
        # Save uploaded file
        async with aiofiles.open(local_file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)
        
        # Get PDF page count
        page_count = get_pdf_page_count(local_file_path)
        
        # Create one problem per PDF page
        problems = []
        problem_ids = []
        
        for page_num in range(1, page_count + 1):
            problem_id = str(uuid.uuid4())
            problem_ids.append(problem_id)
            
            # Create problem record for this page
            problem = Problem(
                id=problem_id,
                user_id=user_id,
                original_filename=file.filename,
                file_path=local_file_path,
                page_number=page_num,
                status=ProblemStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Upload to Firebase Storage (if configured) - shared file path
            firebase_path = local_file_path
            try:
                firebase_path = f"problems/{user_id}/{local_filename}"
                await firebase_service.upload_file(local_file_path, firebase_path)
                problem.file_path = firebase_path
            except Exception as e:
                print(f"Firebase upload warning: {str(e)}")
                # Continue with local file path
            
            # Save problem to database
            try:
                await firebase_service.save_problem({
                    'id': problem.id,
                    'user_id': problem.user_id,
                    'original_filename': problem.original_filename,
                    'file_path': problem.file_path,
                    'page_number': problem.page_number,
                    'status': problem.status.value,
                    'created_at': problem.created_at,
                    'updated_at': problem.updated_at
                })
            except Exception as e:
                print(f"Database save warning for problem {problem_id}: {str(e)}")
                # Continue without database save for now
            
            problems.append(ProblemResponse(
                id=problem.id,
                user_id=problem.user_id,
                original_filename=problem.original_filename,
                page_number=problem.page_number,
                status=problem.status,
                created_at=problem.created_at,
                updated_at=problem.updated_at
            ))
        
        # Start background processing for all pages
        background_tasks.add_task(
            process_uploaded_file_pages,
            local_file_path,
            problem_ids,
            user_id
        )
        
        # Update all problems to processing status
        for problem_id in problem_ids:
            try:
                await firebase_service.update_problem(problem_id, {
                    'status': ProblemStatus.PROCESSING.value,
                    'updated_at': datetime.now()
                })
            except Exception as e:
                print(f"Database update warning for problem {problem_id}: {str(e)}")
        
        # Update problems status in response
        for problem in problems:
            problem.status = ProblemStatus.PROCESSING
            problem.updated_at = datetime.now()
        
        return MultipleProblemsResponse(
            total_pages=page_count,
            problems=problems,
            original_filename=file.filename,
            upload_status="processing"
        )
        
    except ValidationError as e:
        raise create_http_exception(e)
    except FileProcessingError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/single", response_model=ProblemResponse)
async def upload_pdf_single(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(verify_user)
) -> ProblemResponse:
    """
    Upload a PDF file for OCR processing as a single problem (legacy mode)
    
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
        
        # Save/update user information in database (if this is their first time)
        try:
            await firebase_service.save_user({
                'uid': user_id,
                'email': user.get('email', ''),
                'display_name': user.get('name', user.get('display_name')),
                'created_at': datetime.now()
            })
        except Exception as e:
            print(f"User save warning: {str(e)}")
            # Continue even if user save fails
        
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
        
        # Save problem to database
        try:
            await firebase_service.save_problem({
                'id': problem.id,
                'user_id': problem.user_id,
                'original_filename': problem.original_filename,
                'file_path': problem.file_path,
                'status': problem.status.value,
                'created_at': problem.created_at,
                'updated_at': problem.updated_at
            })
        except Exception as e:
            print(f"Database save warning: {str(e)}")
            # Continue without database save for now
        
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
        
        # Update status in database
        try:
            await firebase_service.update_problem(problem_id, {
                'status': problem.status.value,
                'updated_at': problem.updated_at
            })
        except Exception as e:
            print(f"Database update warning: {str(e)}")
        
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
        user_id = user.get('uid', 'anonymous')
        
        # Get problem from database
        problem_data = await firebase_service.get_problem(problem_id)
        
        if not problem_data:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # Verify user owns this problem
        if problem_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # For backward compatibility, provide both extracted_text and markdown_content
        markdown_content = problem_data.get('markdown_content', '')
        extracted_text = problem_data.get('extracted_text', '')
        
        # If we have markdown but no extracted_text, use markdown as extracted_text for compatibility
        if markdown_content and not extracted_text:
            extracted_text = markdown_content
        
        return {
            "problem_id": problem_id,
            "status": problem_data.get('status', 'unknown'),
            "message": f"Problem is {problem_data.get('status', 'unknown')}",
            "extracted_text": extracted_text,  # Legacy field (now includes markdown if available)
            "markdown_content": markdown_content,  # New markdown content
            "math_expressions": problem_data.get('math_expressions', []),  # Legacy field
            "created_at": problem_data.get('created_at'),
            "updated_at": problem_data.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")