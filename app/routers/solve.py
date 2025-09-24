from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
from datetime import datetime
import uuid

from app.models.solution import Solution, SolutionResponse, SolutionCreate, SolutionStatus
from app.services.firebase_service import firebase_service
from app.services.math_service import math_service
from app.utils.exceptions import create_http_exception, AuthorizationError, ValidationError

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
        
        # In a real application, you would update the database here
        print(f"Solved problem {solution_id}: {result.get('final_answer', 'No solution')}")
        
    except Exception as e:
        print(f"Error solving problem {solution_id}: {str(e)}")


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
        
        # In a real application, you would:
        # 1. Retrieve the problem from database
        # 2. Verify user owns the problem
        # 3. Extract math expressions from the problem
        
        # For now, use mock data
        mock_math_expressions = ["2x + 5 = 15", "x^2 - 4 = 0"]
        
        if not mock_math_expressions:
            raise ValidationError("No math expressions found in the problem")
        
        # Create solutions for each math expression
        solutions = []
        for expr in mock_math_expressions:
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
            
            # Start background solving
            background_tasks.add_task(
                solve_math_problem_background,
                solution_id,
                problem_id,
                user_id,
                expr
            )
            
            solution.status = SolutionStatus.SOLVING
            solution.updated_at = datetime.now()
            
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
        
        # In a real application, you would query the database here
        # For now, return mock data
        mock_solutions = [
            SolutionResponse(
                id="solution-1",
                problem_id=problem_id,
                user_id=user_id,
                math_expression="2x + 5 = 15",
                solution_steps={
                    "steps": [
                        "Subtract 5 from both sides: 2x = 10",
                        "Divide both sides by 2: x = 5"
                    ]
                },
                final_answer="x = 5",
                status=SolutionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            SolutionResponse(
                id="solution-2",
                problem_id=problem_id,
                user_id=user_id,
                math_expression="x^2 - 4 = 0",
                solution_steps={
                    "steps": [
                        "Add 4 to both sides: x^2 = 4",
                        "Take square root: x = ±2"
                    ]
                },
                final_answer="x = 2 or x = -2",
                status=SolutionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        return mock_solutions
        
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
        
        # In a real application, you would query the database here
        # For now, return mock data
        mock_solution = SolutionResponse(
            id=solution_id,
            problem_id="mock-problem-id",
            user_id=user_id,
            math_expression="x^2 + 2x - 8 = 0",
            solution_steps={
                "original_expression": "x^2 + 2x - 8 = 0",
                "expression_type": "quadratic",
                "steps": [
                    "Identify coefficients: a=1, b=2, c=-8",
                    "Apply quadratic formula: x = (-b ± √(b²-4ac)) / 2a",
                    "Calculate discriminant: Δ = 4 + 32 = 36",
                    "x = (-2 ± 6) / 2",
                    "Solutions: x = 2 or x = -4"
                ]
            },
            final_answer="x = 2 or x = -4",
            status=SolutionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return mock_solution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve solution: {str(e)}")