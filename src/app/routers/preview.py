from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
from datetime import datetime

from src.app.services.firebase_service import firebase_service
from src.app.utils.exceptions import create_http_exception, ValidationError

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


@router.get("/preview/{problem_id}")
async def preview_problem_content(
    problem_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Get the parsed markdown content of a problem for preview
    
    - **problem_id**: ID of the problem to preview
    - Returns markdown content and metadata
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
        
        return {
            "problem_id": problem_id,
            "original_filename": problem_data.get('original_filename'),
            "page_number": problem_data.get('page_number'),
            "markdown_content": problem_data.get('markdown_content'),
            "status": problem_data.get('status', 'unknown'),
            "created_at": problem_data.get('created_at'),
            "updated_at": problem_data.get('updated_at'),
            "is_ready_to_solve": problem_data.get('markdown_content') is not None and problem_data.get('status') == 'completed'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/preview/multiple")
async def preview_multiple_problems(
    problem_ids: str,  # Comma-separated list of problem IDs
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Get the parsed markdown content of multiple problems for preview
    
    - **problem_ids**: Comma-separated list of problem IDs to preview
    - Returns list of problems with their markdown content
    """
    try:
        user_id = user.get('uid', 'anonymous')
        
        # Parse problem IDs
        ids = [pid.strip() for pid in problem_ids.split(',') if pid.strip()]
        if not ids:
            raise ValidationError("No problem IDs provided")
        
        problems = []
        for problem_id in ids:
            try:
                # Get problem from database
                problem_data = await firebase_service.get_problem(problem_id)
                
                if not problem_data:
                    problems.append({
                        "problem_id": problem_id,
                        "error": "Problem not found"
                    })
                    continue
                
                # Verify user owns this problem
                if problem_data.get('user_id') != user_id:
                    problems.append({
                        "problem_id": problem_id,
                        "error": "Access denied"
                    })
                    continue
                
                problems.append({
                    "problem_id": problem_id,
                    "original_filename": problem_data.get('original_filename'),
                    "page_number": problem_data.get('page_number'),
                    "markdown_content": problem_data.get('markdown_content'),
                    "status": problem_data.get('status', 'unknown'),
                    "created_at": problem_data.get('created_at'),
                    "updated_at": problem_data.get('updated_at'),
                    "is_ready_to_solve": problem_data.get('markdown_content') is not None and problem_data.get('status') == 'completed'
                })
                
            except Exception as e:
                problems.append({
                    "problem_id": problem_id,
                    "error": str(e)
                })
        
        return {
            "total_requested": len(ids),
            "total_found": len([p for p in problems if 'error' not in p]),
            "problems": problems
        }
        
    except ValidationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multiple preview failed: {str(e)}")


@router.post("/preview/batch")
async def preview_batch_problems(
    request_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Get the parsed content of problems by original filename (useful for batch operations)
    
    - **original_filename**: Filename to get all problems for
    - Returns all problems from that PDF with their markdown content
    """
    try:
        user_id = user.get('uid', 'anonymous')
        original_filename = request_data.get('original_filename', '').strip()
        
        if not original_filename:
            raise ValidationError("No filename provided")
        
        # Get all problems for this user and filename
        # Note: This requires implementing a query method in firebase_service
        # For now, we'll return an error suggesting to use individual problem IDs
        
        return {
            "error": "Batch preview by filename not yet implemented",
            "suggestion": "Please use individual problem IDs or the multiple preview endpoint",
            "requested_filename": original_filename
        }
        
    except ValidationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch preview failed: {str(e)}")