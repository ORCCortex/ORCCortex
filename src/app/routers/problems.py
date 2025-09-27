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
        
        # Delete associated solutions first
        try:
            solutions_data = await firebase_service.get_problem_solutions(problem_id)
            for solution in solutions_data:
                solution_id = solution.get('id')
                if solution_id:
                    await firebase_service.delete_solution(solution_id)
            print(f"Deleted {len(solutions_data)} associated solutions")
        except Exception as e:
            print(f"Warning: Failed to delete some solutions: {str(e)}")
        
        # Delete associated files from storage
        try:
            file_path = problem_data.get('file_path')
            if file_path and file_path.startswith('problems/'):
                # It's a Firebase storage path
                await firebase_service.delete_file(file_path)
                print(f"Deleted file from storage: {file_path}")
        except Exception as e:
            print(f"Warning: Failed to delete file from storage: {str(e)}")
        
        # Delete from database
        delete_success = await firebase_service.delete_problem(problem_id)
        
        if not delete_success:
            raise HTTPException(status_code=500, detail="Failed to delete problem from database")
        
        return {
            "message": f"Problem {problem_id} and associated data deleted successfully",
            "problem_id": problem_id
        }
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete problem: {str(e)}")


@router.get("/problems/{user_id}/stats")
async def get_user_problem_stats(
    user_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Get statistics about user's problems
    
    - **user_id**: ID of the user whose stats to retrieve
    - Returns problem statistics (counts by status, recent activity, etc.)
    """
    try:
        # Verify user can access this user_id's stats
        requesting_user_id = user.get('uid')
        if requesting_user_id != user_id:
            raise AuthorizationError("You can only access your own statistics")
        
        # Get all problems for the user (no pagination for stats)
        all_problems = await firebase_service.get_user_problems(
            user_id=user_id,
            status=None,
            limit=1000,  # Large limit to get all problems
            offset=0
        )
        
        # Calculate statistics
        stats = {
            "total_problems": len(all_problems),
            "status_counts": {
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            },
            "recent_problems": 0,  # Problems from last 7 days
            "total_math_expressions": 0
        }
        
        # Count by status and calculate other metrics
        from datetime import timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        for problem in all_problems:
            status = problem.get('status', 'pending')
            if status in stats["status_counts"]:
                stats["status_counts"][status] += 1
            
            # Count recent problems
            created_at = problem.get('created_at')
            if created_at and isinstance(created_at, datetime) and created_at > seven_days_ago:
                stats["recent_problems"] += 1
            
            # Count math expressions
            math_expressions = problem.get('math_expressions', [])
            stats["total_math_expressions"] += len(math_expressions)
        
        return stats
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@router.patch("/problems/{user_id}/{problem_id}")
async def update_problem_status(
    user_id: str,
    problem_id: str,
    update_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Update problem information (mainly for manual status changes)
    
    - **user_id**: ID of the user who owns the problem
    - **problem_id**: ID of the problem to update
    - **update_data**: Data to update (status, extracted_text, math_expressions)
    - Returns confirmation message
    """
    try:
        # Verify user can update this user_id's problems
        requesting_user_id = user.get('uid')
        if requesting_user_id != user_id:
            raise AuthorizationError("You can only update your own problems")
        
        # First verify the problem exists and user owns it
        problem_data = await firebase_service.get_problem(problem_id)
        
        if not problem_data:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        if problem_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Filter allowed update fields
        allowed_fields = ['status', 'extracted_text', 'math_expressions']
        filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_update:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update in database
        update_success = await firebase_service.update_problem(problem_id, filtered_update)
        
        if not update_success:
            raise HTTPException(status_code=500, detail="Failed to update problem in database")
        
        return {
            "message": f"Problem {problem_id} updated successfully",
            "problem_id": problem_id,
            "updated_fields": list(filtered_update.keys())
        }
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update problem: {str(e)}")


@router.get("/problems/{user_id}/search")
async def search_user_problems(
    user_id: str,
    q: str = Query(..., description="Search query for problem content"),
    user: Dict[str, Any] = Depends(verify_user),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
) -> List[ProblemResponse]:
    """
    Search user's problems by content (filename, extracted text, math expressions)
    
    - **user_id**: ID of the user whose problems to search
    - **q**: Search query string
    - **limit**: Maximum number of results to return
    - Returns list of matching problems
    """
    try:
        # Verify user can search this user_id's problems
        requesting_user_id = user.get('uid')
        if requesting_user_id != user_id:
            raise AuthorizationError("You can only search your own problems")
        
        # Get all problems for the user (we'll filter client-side since Firestore full-text search is limited)
        all_problems = await firebase_service.get_user_problems(
            user_id=user_id,
            status=None,
            limit=1000,  # Get all problems for searching
            offset=0
        )
        
        # Filter problems based on search query
        search_query = q.lower().strip()
        matching_problems = []
        
        for problem_data in all_problems:
            # Search in filename
            filename = problem_data.get('original_filename', '').lower()
            
            # Search in extracted text
            extracted_text = problem_data.get('extracted_text', '').lower()
            
            # Search in math expressions
            math_expressions = problem_data.get('math_expressions', [])
            expressions_text = ' '.join(math_expressions).lower()
            
            # Check if search query matches any of the fields
            if (search_query in filename or 
                search_query in extracted_text or 
                search_query in expressions_text):
                
                matching_problems.append(ProblemResponse(
                    id=problem_data.get('id', ''),
                    user_id=problem_data.get('user_id', ''),
                    original_filename=problem_data.get('original_filename', ''),
                    extracted_text=problem_data.get('extracted_text'),
                    math_expressions=problem_data.get('math_expressions', []),
                    status=ProblemStatus(problem_data.get('status', 'pending')),
                    created_at=problem_data.get('created_at', datetime.now()),
                    updated_at=problem_data.get('updated_at', datetime.now())
                ))
                
                # Limit results
                if len(matching_problems) >= limit:
                    break
        
        return matching_problems
        
    except AuthorizationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search problems: {str(e)}")