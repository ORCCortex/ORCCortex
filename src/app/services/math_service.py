import sympy
from sympy import symbols, sympify, solve, simplify, expand, factor, diff, integrate
from typing import Dict, Any, List, Optional
import re
from src.app.utils.exceptions import MathSolvingError


class MathService:
    """Math solving service using SymPy"""
    
    def __init__(self):
        # Common mathematical symbols
        self.common_symbols = symbols('x y z a b c n t u v w alpha beta gamma theta phi')
    
    async def solve_expression(self, expression: str) -> Dict[str, Any]:
        """Solve a mathematical expression"""
        try:
            # Clean and prepare the expression
            cleaned_expr = self._clean_expression(expression)
            
            result = {
                "original_expression": expression,
                "cleaned_expression": cleaned_expr,
                "solution_steps": [],
                "final_answer": None,
                "expression_type": "unknown"
            }
            
            # Solve based on expression type
            if "=" in cleaned_expr:
                result.update(await self._solve_equation(None, cleaned_expr))
            else:
                # Parse the expression for non-equations
                try:
                    parsed_expr = sympify(cleaned_expr)
                    result["parsed_expression"] = str(parsed_expr)
                    result["expression_type"] = self._identify_expression_type(parsed_expr)
                    result.update(await self._simplify_expression(parsed_expr))
                except Exception as e:
                    result["solution_steps"] = [f"Could not parse expression: {str(e)}"]
                    result["final_answer"] = "Unable to parse expression"
            
            return result
        except Exception as e:
            raise MathSolvingError(f"Failed to solve expression '{expression}': {str(e)}")
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and normalize mathematical expression"""
        # Remove LaTeX delimiters
        cleaned = re.sub(r'\$+', '', expression)
        
        # Replace common symbols
        replacements = {
            '×': '*',
            '÷': '/',
            '²': '**2',
            '³': '**3',
            '√': 'sqrt',
            'π': 'pi',
            '∞': 'oo',
            '≤': '<=',
            '≥': '>=',
            '≠': '!=',
            '±': '+/-',
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Handle implicit multiplication (e.g., "2x" -> "2*x")
        cleaned = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', cleaned)
        cleaned = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', cleaned)
        
        return cleaned.strip()
    
    def _identify_expression_type(self, expr) -> str:
        """Identify the type of mathematical expression"""
        try:
            if expr.is_polynomial():
                return "polynomial"
            elif expr.has(sympy.sin, sympy.cos, sympy.tan):
                return "trigonometric"
            elif expr.has(sympy.log, sympy.exp):
                return "logarithmic_exponential"
            elif expr.has(sympy.Integral):
                return "integral"
            elif expr.has(sympy.Derivative):
                return "derivative"
            else:
                return "algebraic"
        except:
            return "unknown"
    
    async def _solve_equation(self, expr, cleaned_expr: str) -> Dict[str, Any]:
        """Solve an equation"""
        try:
            # Split equation by = sign
            parts = cleaned_expr.split('=')
            if len(parts) != 2:
                raise ValueError("Invalid equation format")
            
            left = sympify(parts[0].strip())
            right = sympify(parts[1].strip())
            equation = sympy.Eq(left, right)
            
            # Find variables in the equation
            variables = list(equation.free_symbols)
            
            solutions = []
            solution_steps = []
            
            if variables:
                # Solve for each variable
                for var in variables:
                    try:
                        var_solutions = solve(equation, var)
                        if var_solutions:
                            solutions.extend(var_solutions)
                            solution_steps.append(f"Solving for {var}: {var_solutions}")
                    except:
                        solution_steps.append(f"Could not solve for {var}")
            else:
                # Check if it's a valid equation
                if left.equals(right):
                    solution_steps.append("Equation is always true")
                    solutions = ["True for all values"]
                else:
                    solution_steps.append("Equation has no solution")
                    solutions = ["No solution"]
            
            return {
                "solution_steps": solution_steps,
                "final_answer": str(solutions) if solutions else "No solution found",
                "variables": [str(var) for var in variables],
                "solutions": [str(sol) for sol in solutions],
                "expression_type": "equation"
            }
        except Exception as e:
            return {
                "solution_steps": [f"Error solving equation: {str(e)}"],
                "final_answer": "Could not solve equation",
                "error": str(e),
                "expression_type": "equation"
            }
    
    async def _simplify_expression(self, expr) -> Dict[str, Any]:
        """Simplify a mathematical expression"""
        try:
            solution_steps = []
            
            # Try different simplification approaches
            simplified = simplify(expr)
            solution_steps.append(f"Simplified: {simplified}")
            
            expanded = expand(expr)
            if expanded != expr:
                solution_steps.append(f"Expanded: {expanded}")
            
            try:
                factored = factor(expr)
                if factored != expr:
                    solution_steps.append(f"Factored: {factored}")
            except:
                pass
            
            # Try derivative if expression contains variables
            variables = list(expr.free_symbols)
            if variables:
                for var in variables[:2]:  # Limit to 2 variables to avoid complexity
                    try:
                        derivative = diff(expr, var)
                        solution_steps.append(f"Derivative with respect to {var}: {derivative}")
                    except:
                        pass
            
            return {
                "solution_steps": solution_steps,
                "final_answer": str(simplified),
                "simplified_form": str(simplified),
                "variables": [str(var) for var in variables]
            }
        except Exception as e:
            return {
                "solution_steps": [f"Error simplifying expression: {str(e)}"],
                "final_answer": str(expr),
                "error": str(e)
            }
    
    async def solve_multiple_expressions(self, expressions: List[str]) -> List[Dict[str, Any]]:
        """Solve multiple mathematical expressions"""
        results = []
        for expr in expressions:
            try:
                result = await self.solve_expression(expr)
                results.append(result)
            except Exception as e:
                results.append({
                    "original_expression": expr,
                    "error": str(e),
                    "final_answer": "Could not solve"
                })
        return results


# Global math service instance
math_service = MathService()