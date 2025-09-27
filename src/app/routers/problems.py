from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.app.models.problem import ProblemResponse, ProblemStatus
from src.app.services.firebase_service import firebase_service
from src.app.utils.exceptions import create_http_exception, AuthorizationError

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


@router.get("/problems/{user_id}", response_model=List[ProblemResponse])
async def get_user_problems(
    user_id: str,
    user: Dict[str, Any] = Depends(verify_user),
    status: Optional[ProblemStatus] = Query(None, description="Filter by problem status"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of problems to return"),
    offset: int = Query(0, ge=0, description="Number of problems to skip")
) -> List[ProblemResponse]:
    """
    Get all problems for a specific user
    
    - **user_id**: ID of the user whose problems to retrieve
    - **status**: Optional filter by problem status
    - **limit**: Maximum number of problems to return (1-100)
    - **offset**: Number of problems to skip for pagination
    - Returns list of user's problems
    """
    try:
        # Verify user can access this user_id's problems
        requesting_user_id = user.get('uid')
        if requesting_user_id != user_id:
            # In a real application, you might check for admin privileges here
            raise AuthorizationError("You can only access your own problems")
        
        # Get problems from database
        status_filter = status.value if status else None
        problems_data = await firebase_service.get_user_problems(
            user_id=user_id,
            status=status_filter,
            limit=limit,
            offset=offset
        )
        
        # Convert to ProblemResponse objects
        problems = []
        for problem_data in problems_data:
            problems.append(ProblemResponse(
                id=problem_data.get('id', ''),
                user_id=problem_data.get('user_id', ''),
                original_filename=problem_data.get('original_filename', ''),
                extracted_text=problem_data.get('extracted_text'),
                math_expressions=problem_data.get('math_expressions', []),
                status=ProblemStatus(problem_data.get('status', 'pending')),
                created_at=problem_data.get('created_at', datetime.now()),
                updated_at=problem_data.get('updated_at', datetime.now())
            ))
        
        return problems
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve problems: {str(e)}")


@router.get("/problems/{user_id}/{problem_id}", response_model=ProblemResponse)
async def get_problem_details(
    user_id: str,
    problem_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> ProblemResponse:
    """
    Get detailed information about a specific problem
    
    - **user_id**: ID of the user who owns the problem
    - **problem_id**: ID of the problem to retrieve
    - Returns detailed problem information
    """
    try:
        # Verify user can access this user_id's problems
        requesting_user_id = user.get('uid')
        if requesting_user_id != user_id:
            raise AuthorizationError("You can only access your own problems")
        
        # Get problem from database
        problem_data = await firebase_service.get_problem(problem_id)
        
        if not problem_data:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # Double-check user ownership (should match user_id from URL)
        if problem_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert to ProblemResponse object
        problem = ProblemResponse(
            id=problem_data.get('id', ''),
            user_id=problem_data.get('user_id', ''),
            original_filename=problem_data.get('original_filename', ''),
            extracted_text=problem_data.get('extracted_text'),
            math_expressions=problem_data.get('math_expressions', []),
            status=ProblemStatus(problem_data.get('status', 'pending')),
            created_at=problem_data.get('created_at', datetime.now()),
            updated_at=problem_data.get('updated_at', datetime.now())
        )
        
        return problem
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve problem: {str(e)}")


@router.delete("/problems/{user_id}/{problem_id}")
async def delete_problem(
    user_id: str,
    problem_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, str]:
    """
    Delete a specific problem
    
    - **user_id**: ID of the user who owns the problem
    - **problem_id**: ID of the problem to delete
    - Returns confirmation message
    """
    try:
        # Verify user can delete this user_id's problems
        requesting_user_id = user.get('uid')
        if requesting_user_id != user_id:
            raise AuthorizationError("You can only delete your own problems")
        
        # First verify the problem exists and user owns it
        problem_data = await firebase_service.get_problem(problem_id)
        
        if not problem_data:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        if problem_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete from database
        delete_success = await firebase_service.delete_problem(problem_id)
        
        if not delete_success:
            raise HTTPException(status_code=500, detail="Failed to delete problem from database")
        
        # TODO: Delete associated files from storage
        # TODO: Delete associated solutions
        # For now, just delete from database
        
        return {
            "message": f"Problem {problem_id} deleted successfully",
            "problem_id": problem_id
        }
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete problem: {str(e)}")