from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
from datetime import datetime
import uuid

from src.app.models.solution import Solution, SolutionResponse, SolutionCreate, SolutionStatus
from src.app.services.firebase_service import firebase_service
from src.app.services.math_service import math_service
from src.app.utils.exceptions import create_http_exception, AuthorizationError, ValidationError

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


async def solve_math_problem_background(solution_id: str, problem_id: str, user_id: str, math_expression: str):
    """Background task to solve math problem"""
    try:
        # Solve the math expression
        result = await math_service.solve_expression(math_expression)
        
        # Update solution with results in database
        update_data = {
            'solution_steps': result.get('steps', {}),
            'final_answer': result.get('final_answer', 'No solution'),
            'status': SolutionStatus.COMPLETED.value
        }
        
        try:
            await firebase_service.update_solution(solution_id, update_data)
            print(f"Successfully solved problem {solution_id}: {result.get('final_answer', 'No solution')}")
        except Exception as db_error:
            print(f"Database update failed for solution {solution_id}: {str(db_error)}")
            # Update status to failed if database update fails
            try:
                await firebase_service.update_solution(solution_id, {
                    'status': SolutionStatus.FAILED.value,
                    'error_message': f"Database update failed: {str(db_error)}"
                })
            except Exception:
                pass  # If this fails too, we can't do much more
        
    except Exception as e:
        print(f"Error solving problem {solution_id}: {str(e)}")
        # Update status to failed in database
        try:
            await firebase_service.update_solution(solution_id, {
                'status': SolutionStatus.FAILED.value,
                'error_message': str(e)
            })
        except Exception:
            pass  # If database update fails, we can't do much more


@router.post("/solve/{problem_id}", response_model=SolutionResponse)
async def solve_problem(
    problem_id: str,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(verify_user)
) -> SolutionResponse:
    """
    Solve math problems from a specific problem
    
    - **problem_id**: ID of the problem to solve
    - Returns solution information with processing status
    """
    try:
        user_id = user.get('uid', 'anonymous')
        
        # 1. Retrieve the problem from database
        problem_data = await firebase_service.get_problem(problem_id)
        
        if not problem_data:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # 2. Verify user owns the problem
        if problem_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 3. Extract math expressions from the problem
        math_expressions = problem_data.get('math_expressions', [])
        
        if not math_expressions:
            raise ValidationError("No math expressions found in the problem")
        
        # Create solutions for each math expression
        solutions = []
        for expr in math_expressions:
            solution_id = str(uuid.uuid4())
            
            solution = Solution(
                id=solution_id,
                problem_id=problem_id,
                user_id=user_id,
                math_expression=expr,
                status=SolutionStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save solution to database
            try:
                await firebase_service.save_solution({
                    'id': solution.id,
                    'problem_id': solution.problem_id,
                    'user_id': solution.user_id,
                    'math_expression': solution.math_expression,
                    'status': solution.status.value,
                    'created_at': solution.created_at,
                    'updated_at': solution.updated_at
                })
            except Exception as e:
                print(f"Database save warning for solution {solution_id}: {str(e)}")
                # Continue without database save for now
            
            # Start background solving
            background_tasks.add_task(
                solve_math_problem_background,
                solution_id,
                problem_id,
                user_id,
                expr
            )
            
            # Update status to solving
            solution.status = SolutionStatus.SOLVING
            solution.updated_at = datetime.now()
            
            # Update status in database
            try:
                await firebase_service.update_solution(solution_id, {
                    'status': solution.status.value,
                    'updated_at': solution.updated_at
                })
            except Exception as e:
                print(f"Database update warning for solution {solution_id}: {str(e)}")
            
            solutions.append(solution)
        
        # Return the first solution (or you could return all)
        if solutions:
            first_solution = solutions[0]
            return SolutionResponse(
                id=first_solution.id,
                problem_id=first_solution.problem_id,
                user_id=first_solution.user_id,
                math_expression=first_solution.math_expression,
                status=first_solution.status,
                created_at=first_solution.created_at,
                updated_at=first_solution.updated_at
            )
        else:
            raise ValidationError("No solutions could be created")
        
    except ValidationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solving failed: {str(e)}")


@router.post("/solve/expression", response_model=Dict[str, Any])
async def solve_expression(
    expression_data: Dict[str, str],
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Solve a single math expression directly
    
    - **expression**: Mathematical expression to solve
    - Returns solution steps and final answer
    """
    try:
        expression = expression_data.get('expression', '').strip()
        if not expression:
            raise ValidationError("No expression provided")
        
        # Solve the expression
        result = await math_service.solve_expression(expression)
        
        return {
            "expression": expression,
            "result": result,
            "solved_at": datetime.now().isoformat()
        }
        
    except ValidationError as e:
        raise create_http_exception(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Expression solving failed: {str(e)}")


@router.get("/solve/{problem_id}/solutions", response_model=List[SolutionResponse])
async def get_problem_solutions(
    problem_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> List[SolutionResponse]:
    """
    Get all solutions for a specific problem
    
    - **problem_id**: ID of the problem
    - Returns list of solutions
    """
    try:
        user_id = user.get('uid', 'anonymous')
        
        # First verify the problem exists and user owns it
        problem_data = await firebase_service.get_problem(problem_id)
        
        if not problem_data:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        if problem_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all solutions for this problem from database
        solutions_data = await firebase_service.get_problem_solutions(problem_id)
        
        # Convert to SolutionResponse objects
        solutions = []
        for solution_data in solutions_data:
            solutions.append(SolutionResponse(
                id=solution_data.get('id', ''),
                problem_id=solution_data.get('problem_id', ''),
                user_id=solution_data.get('user_id', ''),
                math_expression=solution_data.get('math_expression', ''),
                solution_steps=solution_data.get('solution_steps'),
                final_answer=solution_data.get('final_answer'),
                status=SolutionStatus(solution_data.get('status', 'pending')),
                error_message=solution_data.get('error_message'),
                created_at=solution_data.get('created_at', datetime.now()),
                updated_at=solution_data.get('updated_at', datetime.now())
            ))
        
        return solutions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve solutions: {str(e)}")


@router.get("/solve/solution/{solution_id}", response_model=SolutionResponse)
async def get_solution_details(
    solution_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> SolutionResponse:
    """
    Get detailed information about a specific solution
    
    - **solution_id**: ID of the solution to retrieve
    - Returns detailed solution information
    """
    try:
        user_id = user.get('uid', 'anonymous')
        
        # Get solution from database
        solution_data = await firebase_service.get_solution(solution_id)
        
        if not solution_data:
            raise HTTPException(status_code=404, detail="Solution not found")
        
        # Verify user owns this solution
        if solution_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert to SolutionResponse object
        solution = SolutionResponse(
            id=solution_data.get('id', ''),
            problem_id=solution_data.get('problem_id', ''),
            user_id=solution_data.get('user_id', ''),
            math_expression=solution_data.get('math_expression', ''),
            solution_steps=solution_data.get('solution_steps'),
            final_answer=solution_data.get('final_answer'),
            status=SolutionStatus(solution_data.get('status', 'pending')),
            error_message=solution_data.get('error_message'),
            created_at=solution_data.get('created_at', datetime.now()),
            updated_at=solution_data.get('updated_at', datetime.now())
        )
        
        return solution
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve solution: {str(e)}")


@router.get("/solve/status/{solution_id}")
async def get_solution_status(
    solution_id: str,
    user: Dict[str, Any] = Depends(verify_user)
) -> Dict[str, Any]:
    """
    Get the status of a solution processing
    
    - **solution_id**: ID of the solution to check
    - Returns solution status and results if available
    """
    try:
        user_id = user.get('uid', 'anonymous')
        
        # Get solution from database
        solution_data = await firebase_service.get_solution(solution_id)
        
        if not solution_data:
            raise HTTPException(status_code=404, detail="Solution not found")
        
        # Verify user owns this solution
        if solution_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "solution_id": solution_id,
            "problem_id": solution_data.get('problem_id'),
            "math_expression": solution_data.get('math_expression'),
            "status": solution_data.get('status', 'unknown'),
            "message": f"Solution is {solution_data.get('status', 'unknown')}",
            "solution_steps": solution_data.get('solution_steps'),
            "final_answer": solution_data.get('final_answer'),
            "error_message": solution_data.get('error_message'),
            "created_at": solution_data.get('created_at'),
            "updated_at": solution_data.get('updated_at')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")