#!/usr/bin/env python3
"""
Test script for GPT OSS service with actual model inference
"""
import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.app.services.gpt_oss_service import GPTOSSService, LLAMA_CPP_AVAILABLE


async def test_model_loading():
    """Test basic model loading and inference"""
    print("🚀 Testing GPT OSS Service...")
    print(f"📦 llama-cpp-python available: {LLAMA_CPP_AVAILABLE}")
    
    if not LLAMA_CPP_AVAILABLE:
        print("❌ llama-cpp-python not installed. Please install with:")
        print("   pip install llama-cpp-python")
        return False
    
    try:
        # Initialize service
        print("🔧 Initializing GPT OSS service...")
        service = GPTOSSService()
        
        # Test model loading and simple inference
        print("🧪 Running inference test...")
        result = await service.test_inference()
        
        print(f"✅ Test result: {result['success']}")
        print(f"🧠 Model loaded: {result['model_loaded']}")
        
        if result['success']:
            print("📝 Raw response preview:")
            print(result['raw_response'][:200] + "..." if len(result['raw_response']) > 200 else result['raw_response'])
            print("\n🎯 Parsed response:")
            print(f"   Steps: {len(result['parsed_response']['steps'])} steps")
            print(f"   Answer: {result['parsed_response']['answer']}")
            print(f"   Explanation: {result['parsed_response']['explanation'][:100]}...")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Test with a real math problem
        print("\n🔢 Testing with a real math problem...")
        math_problem = """
# Math Problem

Solve for x: 2x + 5 = 13

Show all steps in your solution.
"""
        
        solution = await service.solve_problem(math_problem, page_number=1)
        print("📚 Problem solution:")
        print(f"   Final answer: {solution['final_answer']}")
        print(f"   Number of steps: {len(solution['solution_steps'])}")
        print(f"   Model used: {solution['model_used']}")
        
        # Clean up
        await service.unload_model()
        print("🧹 Model unloaded successfully")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Model file not found: {e}")
        print("   Make sure the GGUF model file exists in the gpt-oss-20b-GGUF directory")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_multiple_problems():
    """Test solving multiple problems"""
    print("\n🔢 Testing multiple problem solving...")
    
    try:
        service = GPTOSSService()
        
        problems = [
            {
                "markdown_content": "What is the area of a rectangle with length 8 and width 5?",
                "page_number": 1
            },
            {
                "markdown_content": "Solve: 3x - 7 = 14",
                "page_number": 2
            }
        ]
        
        results = await service.solve_multiple_problems(problems)
        
        print(f"✅ Solved {len(results)} problems:")
        for i, result in enumerate(results, 1):
            if 'error' not in result:
                print(f"   Problem {i}: {result['final_answer']}")
            else:
                print(f"   Problem {i}: Error - {result['error']}")
        
        await service.unload_model()
        return True
        
    except Exception as e:
        print(f"❌ Multiple problems test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 60)
    print("GPT OSS SERVICE TEST")
    print("=" * 60)
    
    # Test basic functionality
    basic_test_passed = await test_model_loading()
    
    if basic_test_passed:
        # Test multiple problems
        await test_multiple_problems()
        print("\n✅ All tests completed!")
    else:
        print("\n❌ Basic test failed. Please check the setup.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())