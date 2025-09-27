#!/bin/bash

# Test script for page-by-page PDF upload
# Usage: ./test_pages.sh YOUR_FIREBASE_TOKEN YOUR_USER_ID

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

echo "🚀 Testing ORCCortex API - Page-by-Page Upload..."
echo "================================"

# Test: Upload PDF file with page splitting
echo "📄 Step 1: Uploading PDF file with page splitting (P5_Maths_2023_SA2_acsprimary.pdf)..."

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

# Extract total pages and first problem ID for testing
TOTAL_PAGES=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_pages'])" 2>/dev/null || echo "")
FIRST_PROBLEM_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['problems'][0]['id'])" 2>/dev/null || echo "")

if [ -z "$TOTAL_PAGES" ] || [ -z "$FIRST_PROBLEM_ID" ]; then
    echo "❌ Upload failed!"
    exit 1
fi

echo "✅ Total Pages: $TOTAL_PAGES"
echo "✅ First Problem ID: $FIRST_PROBLEM_ID"

# Wait a bit for processing
echo ""
echo "⏳ Waiting 5 seconds for processing..."
sleep 5

# Test: Check status of first problem
echo ""
echo "🔍 Step 2: Checking status of first problem (page 1)..."

STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/upload/status/$FIRST_PROBLEM_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Status Response:"
echo "$STATUS_RESPONSE" | python3 -m json.tool

echo ""
echo "🎉 Page-by-page upload test completed!"
echo "================================"