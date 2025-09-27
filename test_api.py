#!/usr/bin/env python3
"""
Test script for ORCCortex API endpoints
Run this after getting your Firebase ID token
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "YOUR_FIREBASE_ID_TOKEN_HERE"  # Replace with actual token
USER_ID = "YOUR_USER_ID_HERE"  # Replace with your Firebase user ID

def test_upload_pdf():
    """Test PDF upload endpoint"""
    print("🔄 Testing PDF upload...")
    
    # Create a simple text file to simulate PDF upload
    test_content = b"Sample math problems:\n1. Solve for x: 2x + 5 = 15\n2. Find derivative of f(x) = x^2 + 3x - 2"
    
    with open("test_problem.txt", "wb") as f:
        f.write(test_content)
    
    files = {"file": ("test_problem.pdf", open("test_problem.txt", "rb"), "application/pdf")}
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            problem_id = response.json().get("id")
            print(f"✅ Upload successful! Problem ID: {problem_id}")
            return problem_id
        else:
            print("❌ Upload failed!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        files["file"][1].close()
        os.remove("test_problem.txt")

def test_get_problems(user_id):
    """Test get user problems endpoint"""
    print("🔄 Testing get problems...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/problems/{user_id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            problems = response.json()
            print(f"✅ Found {len(problems)} problems")
            return problems
        else:
            print("❌ Failed to get problems!")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_upload_status(problem_id):
    """Test upload status endpoint"""
    print(f"🔄 Testing upload status for {problem_id}...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/upload/status/{problem_id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            status = response.json().get("status")
            print(f"✅ Problem status: {status}")
            return status
        else:
            print("❌ Failed to get status!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_solve_problem(problem_id):
    """Test solve problem endpoint"""
    print(f"🔄 Testing solve problem {problem_id}...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.post(f"{BASE_URL}/solve/{problem_id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            solution_id = response.json().get("id")
            print(f"✅ Solve started! Solution ID: {solution_id}")
            return solution_id
        else:
            print("❌ Failed to solve problem!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_solutions(problem_id):
    """Test get problem solutions endpoint"""
    print(f"🔄 Testing get solutions for {problem_id}...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/solve/{problem_id}/solutions", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            solutions = response.json()
            print(f"✅ Found {len(solutions)} solutions")
            return solutions
        else:
            print("❌ Failed to get solutions!")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    """Run all tests"""
    print("🚀 Starting ORCCortex API Tests")
    print("=" * 50)
    
    if TOKEN == "YOUR_FIREBASE_ID_TOKEN_HERE":
        print("❌ Please set your Firebase ID token in the script!")
        return
    
    if USER_ID == "YOUR_USER_ID_HERE":
        print("❌ Please set your Firebase user ID in the script!")
        return
    
    # Test 1: Upload PDF
    problem_id = test_upload_pdf()
    if not problem_id:
        return
    
    print("\n" + "=" * 50)
    
    # Test 2: Get problems
    problems = test_get_problems(USER_ID)
    
    print("\n" + "=" * 50)
    
    # Test 3: Check upload status
    status = test_upload_status(problem_id)
    
    print("\n" + "=" * 50)
    
    # Test 4: Solve problem
    solution_id = test_solve_problem(problem_id)
    
    print("\n" + "=" * 50)
    
    # Test 5: Get solutions
    solutions = test_get_solutions(problem_id)
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()