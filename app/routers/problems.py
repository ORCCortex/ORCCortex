from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.problem import ProblemResponse, ProblemStatus
from app.services.firebase_service import firebase_service
from app.utils.exceptions import create_http_exception, AuthorizationError

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
        
        # In a real application, you would query the database here
        # For now, return mock data
        mock_problems = [
            ProblemResponse(
                id="problem-1",
                user_id=user_id,
                original_filename="math_homework.pdf",
                extracted_text="Solve for x: 2x + 5 = 15",
                math_expressions=["2x + 5 = 15"],
                status=ProblemStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            ProblemResponse(
                id="problem-2",
                user_id=user_id,
                original_filename="calculus_problems.pdf",
                extracted_text="Find the derivative of f(x) = x^2 + 3x - 2",
                math_expressions=["f(x) = x^2 + 3x - 2", "f'(x) = ?"],
                status=ProblemStatus.PROCESSING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # Apply status filter if provided
        if status:
            mock_problems = [p for p in mock_problems if p.status == status]
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated_problems = mock_problems[start_idx:end_idx]
        
        return paginated_problems
        
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
        
        # In a real application, you would query the database here
        # For now, return mock data
        mock_problem = ProblemResponse(
            id=problem_id,
            user_id=user_id,
            original_filename="sample_problem.pdf",
            extracted_text="Solve the quadratic equation: x^2 - 5x + 6 = 0",
            math_expressions=["x^2 - 5x + 6 = 0"],
            status=ProblemStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return mock_problem
        
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
        
        # In a real application, you would:
        # 1. Delete from database
        # 2. Delete associated files from storage
        # 3. Delete associated solutions
        
        return {
            "message": f"Problem {problem_id} deleted successfully",
            "problem_id": problem_id
        }
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete problem: {str(e)}")