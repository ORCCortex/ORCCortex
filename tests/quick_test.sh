#!/bin/bash

# Quick test script for ORCCortex API
# Usage: ./quick_test.sh YOUR_FIREBASE_TOKEN YOUR_USER_ID

set -e

TOKEN="$1"
USER_ID="$2"

if [ -z "$TOKEN" ] || [ -z "$USER_ID" ]; then
    echo "Usage: $0 <firebase_token> <user_id>"
    echo ""
    echo "Example:"
    echo "  $0 'eyJhbGci...' 'abc123def456'"
    echo ""
    echo "Get your token from: http://localhost:8000/test_auth.html"
    exit 1
fi

BASE_URL="http://localhost:8000/api/v1"

echo "🚀 Testing ORCCortex API..."
echo "================================"

# Test 1: Upload existing PDF file
echo "📄 Step 1: Uploading PDF file (P5_Maths_2023_SA2_acsprimary.pdf)..."

# Check if PDF file exists
if [ ! -f "P5_Maths_2023_SA2_acsprimary.pdf" ]; then
    echo "❌ PDF file 'P5_Maths_2023_SA2_acsprimary.pdf' not found!"
    exit 1
fi

UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@P5_Maths_2023_SA2_acsprimary.pdf")

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool

PROBLEM_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$PROBLEM_ID" ]; then
    echo "❌ Upload failed!"
    exit 1
fi

echo "✅ Problem ID: $PROBLEM_ID"
echo ""

# Test 2: Check upload status
echo "🔍 Step 2: Checking upload status..."
sleep 2  # Wait for processing

curl -s -X GET "$BASE_URL/upload/status/$PROBLEM_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""

# Test 3: Get user problems
echo "📋 Step 3: Getting user problems..."
curl -s -X GET "$BASE_URL/problems/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""

# Test 4: Solve the problem
echo "🧮 Step 4: Starting problem solving..."
SOLVE_RESPONSE=$(curl -s -X POST "$BASE_URL/solve/$PROBLEM_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Solve Response:"
echo "$SOLVE_RESPONSE" | python3 -m json.tool

SOLUTION_ID=$(echo "$SOLVE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -n "$SOLUTION_ID" ]; then
    echo "✅ Solution ID: $SOLUTION_ID"
    echo ""
    
    # Test 5: Check solution status
    echo "🔍 Step 5: Checking solution status..."
    sleep 2  # Wait for solving
    
    curl -s -X GET "$BASE_URL/solve/status/$SOLUTION_ID" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
    
    echo ""
    
    # Test 6: Get all solutions for the problem
    echo "📊 Step 6: Getting all solutions..."
    curl -s -X GET "$BASE_URL/solve/$PROBLEM_ID/solutions" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
fi

echo ""

# Test 7: Get user statistics
echo "📈 Step 7: Getting user statistics..."
curl -s -X GET "$BASE_URL/problems/$USER_ID/stats" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""

# Test 8: Search problems
echo "🔍 Step 8: Searching problems..."
curl -s -X GET "$BASE_URL/problems/$USER_ID/search?q=derivative" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "🎉 All tests completed!"
echo "================================"