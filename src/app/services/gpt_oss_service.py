import asyncio
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from src.app.utils.config import settings
from src.app.utils.exceptions import MathSolvingError

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python not available. Install with: pip install llama-cpp-python")


class GPTOSSService:
    """GPT OSS service for solving math problems using local GGUF model"""

    def __init__(self):
        self.model_path = Path(settings.GPT_OSS_MODEL_PATH)
        self.llama_model = None
        self._model_lock = asyncio.Lock()

        # Check if model exists
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"GPT OSS model not found at {self.model_path}")
        
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError(
                "llama-cpp-python is required for GPT OSS inference. "
                "Install with: pip install llama-cpp-python"
            )

    async def _load_model(self):
        """Load the GGUF model if not already loaded"""
        if self.llama_model is None:
            async with self._model_lock:
                if self.llama_model is None:  # Double-check after acquiring lock
                    try:
                        logging.info(f"Loading GPT OSS model from {self.model_path}")
                        # Load model with optimized parameters for math problems
                        self.llama_model = Llama(
                            model_path=str(self.model_path),
                            n_ctx=settings.GPT_OSS_N_CTX,  # Context length
                            n_threads=settings.GPT_OSS_N_THREADS,  # Number of threads
                            n_gpu_layers=settings.GPT_OSS_N_GPU_LAYERS,  # GPU layers (0 for CPU)
                            verbose=False
                        )
                        logging.info("GPT OSS model loaded successfully")
                    except Exception as e:
                        logging.error(f"Failed to load GPT OSS model: {str(e)}")
                        raise MathSolvingError(f"Failed to load model: {str(e)}")

    def _get_generation_params(self) -> Dict[str, Any]:
        """Get optimized parameters for math problem solving"""
        return {
            "max_tokens": settings.GPT_OSS_MAX_TOKENS,
            "temperature": settings.GPT_OSS_TEMPERATURE,  # Low temperature for consistent math
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "stop": ["Human:", "User:", "\n\n\n"],  # Stop sequences
        }

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
        Generate response using the loaded GGUF model
        """
        try:
            # Ensure model is loaded
            await self._load_model()
            
            # Get generation parameters
            gen_params = self._get_generation_params()
            
            logging.info("Generating response with GPT OSS model")
            
            # Run inference in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._run_inference,
                prompt,
                gen_params
            )
            
            logging.info("Response generated successfully")
            return response

        except Exception as e:
            logging.error(f"Failed to generate response: {str(e)}")
            raise MathSolvingError(f"Failed to generate response: {str(e)}")

    def _run_inference(self, prompt: str, gen_params: Dict[str, Any]) -> str:
        """Run the actual model inference (synchronous)"""
        try:
            if self.llama_model is None:
                raise MathSolvingError("Model not loaded")
                
            # Generate response
            output = self.llama_model(
                prompt,
                **gen_params
            )
            
            # Extract the generated text
            if isinstance(output, dict) and 'choices' in output:
                response_text = output['choices'][0]['text']
            else:
                response_text = str(output)
            
            return response_text.strip()
            
        except Exception as e:
            raise MathSolvingError(f"Inference failed: {str(e)}")



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

    async def unload_model(self):
        """Unload the model to free memory"""
        async with self._model_lock:
            if self.llama_model is not None:
                del self.llama_model
                self.llama_model = None
                logging.info("GPT OSS model unloaded")

    async def test_inference(self, test_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Test the model with a simple math problem"""
        if test_prompt is None:
            test_prompt = """You are an expert mathematics tutor. Solve this simple problem.

Problem:
What is 2 + 3 × 4?

Please provide your response in JSON format:
{
    "steps": ["Step 1: Apply order of operations", "Step 2: Calculate 3 × 4 = 12", "Step 3: Add 2 + 12 = 14"],
    "answer": "14",
    "explanation": "Following PEMDAS, multiplication comes before addition"
}

Response:"""
        
        try:
            response = await self._generate_response(test_prompt)
            parsed = self._parse_response(response)
            
            return {
                "success": True,
                "model_loaded": self.llama_model is not None,
                "raw_response": response,
                "parsed_response": parsed,
                "message": "Model test completed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "model_loaded": self.llama_model is not None,
                "error": str(e),
                "message": "Model test failed"
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
