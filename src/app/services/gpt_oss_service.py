import asyncio
import json
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
from src.app.utils.config import settings
from src.app.utils.exceptions import MathSolvingError


class GPTOSSService:
    """GPT OSS service for solving math problems using local GGUF model"""
    
    def __init__(self):
        self.model_path = Path("/Users/thanh/Workspace/ORCCortex/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf")
        self.llama_cpp_path = None  # Will be set when needed
        
        # Check if model exists
        if not self.model_path.exists():
            raise FileNotFoundError(f"GPT OSS model not found at {self.model_path}")
    
    async def solve_problem(self, markdown_content: str, page_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Solve math problem from markdown content using GPT OSS
        
        Args:
            markdown_content: The markdown content of the problem
            page_number: Optional page number for context
            
        Returns:
            Dictionary with solution steps and final answer
        """
        try:
            # Create a prompt for the math problem solving
            prompt = self._create_solving_prompt(markdown_content, page_number)
            
            # Generate response using the local model
            response = await self._generate_response(prompt)
            
            # Parse the response
            result = self._parse_response(response)
            
            return {
                "original_content": markdown_content,
                "page_number": page_number,
                "solution_steps": result.get("steps", []),
                "final_answer": result.get("answer", "No solution found"),
                "explanation": result.get("explanation", ""),
                "model_used": "gpt-oss-20b",
                "raw_response": response
            }
        except Exception as e:
            raise MathSolvingError(f"Failed to solve problem: {str(e)}")
    
    def _create_solving_prompt(self, markdown_content: str, page_number: Optional[int] = None) -> str:
        """Create a prompt for solving the math problem"""
        page_info = f" (Page {page_number})" if page_number else ""
        
        prompt = f"""You are an expert mathematics tutor. Analyze the following problem{page_info} and provide a complete solution.

Problem:
{markdown_content}

Please provide your response in the following JSON format:
{{
    "steps": [
        "Step 1: [Describe what you're doing]",
        "Step 2: [Show the calculation]",
        "Step 3: [Continue with solution]"
    ],
    "answer": "[Final numerical or algebraic answer]",
    "explanation": "[Brief explanation of the solution method]"
}}

Make sure to:
1. Break down the solution into clear, logical steps
2. Show all calculations
3. Explain your reasoning
4. Provide the final answer clearly
5. Use proper mathematical notation where needed

Response:"""
        
        return prompt
    
    async def _generate_response(self, prompt: str) -> str:
        """
        Generate response using llama.cpp with the GGUF model
        
        Note: This is a simplified implementation. In production, you might want to use
        a more robust solution like llama-cpp-python or a dedicated inference server.
        """
        try:
            # For now, we'll use a subprocess call to llama.cpp
            # In production, consider using llama-cpp-python for better integration
            
            # Create a temporary file for the prompt
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Basic llama.cpp command
            # Note: You'll need to have llama.cpp built and available
            cmd = [
                "llama.cpp",  # Adjust path as needed
                "-m", str(self.model_path),
                "-f", prompt_file,
                "-n", "2048",  # Max tokens
                "-t", "4",     # Threads
                "--temp", "0.1",  # Low temperature for consistent math
                "--top-p", "0.9",
                "--repeat-penalty", "1.1"
            ]
            
            # For now, return a mock response since llama.cpp setup varies
            # In production, uncomment the subprocess call below
            
            # result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # if result.returncode != 0:
            #     raise Exception(f"llama.cpp failed: {result.stderr}")
            # response = result.stdout
            
            # Mock response for demonstration
            response = self._get_mock_response(prompt)
            
            # Clean up temp file
            Path(prompt_file).unlink(missing_ok=True)
            
            return response
            
        except Exception as e:
            raise MathSolvingError(f"Failed to generate response: {str(e)}")
    
    def _get_mock_response(self, prompt: str) -> str:
        """
        Mock response for testing purposes
        Replace this with actual model inference in production
        """
        return """{
    "steps": [
        "Step 1: Identify the mathematical problem from the given content",
        "Step 2: Apply appropriate mathematical principles and formulas",
        "Step 3: Perform the necessary calculations",
        "Step 4: Verify the solution and present the final answer"
    ],
    "answer": "Solution will be provided based on the specific problem",
    "explanation": "The solution approach depends on the type of mathematical problem presented in the content."
}"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from the model"""
        try:
            # Try to extract JSON from the response
            import re
            
            # Look for JSON-like content
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Fallback: parse as plain text
                return {
                    "steps": [response.strip()],
                    "answer": "Unable to parse structured response",
                    "explanation": "The model provided an unstructured response"
                }
        except json.JSONDecodeError:
            # Fallback: treat as plain text
            lines = response.strip().split('\n')
            return {
                "steps": lines,
                "answer": lines[-1] if lines else "No response",
                "explanation": "Response was not in expected JSON format"
            }
        except Exception as e:
            return {
                "steps": [f"Error parsing response: {str(e)}"],
                "answer": "Parsing failed",
                "explanation": "Unable to parse model response"
            }
    
    async def solve_multiple_problems(self, problems_data: list) -> list:
        """Solve multiple problems from different pages"""
        results = []
        for problem_data in problems_data:
            try:
                result = await self.solve_problem(
                    problem_data.get("markdown_content", ""),
                    problem_data.get("page_number")
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "error": str(e),
                    "page_number": problem_data.get("page_number"),
                    "final_answer": "Error solving problem"
                })
        return results


# Global GPT OSS service instance
gpt_oss_service = GPTOSSService()