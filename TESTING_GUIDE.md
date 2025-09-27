# 🧪 ORCCortex Testing Guide

## Prerequisites ✅
- [x] Server running on http://localhost:8000
- [x] Firebase Authentication configured
- [x] Firestore database initialized

## Step 1: Get Firebase ID Token 🔑

### Option A: Using test_auth.html (Recommended)
1. **Setup Firebase Console:**
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Select your project: `orccortex-543d1`
   - Go to **Authentication** → **Sign-in method**
   - Enable **Email/Password** authentication

2. **Get API Key:**
   - Go to **Project Settings** (gear icon) → **General**
   - Copy your **Web API Key**
   - Edit `test_auth.html` and replace `"YOUR_API_KEY_HERE"` with your key

3. **Open test page:**
   ```bash
   open test_auth.html
   ```
   
4. **Create test user:**
   - Email: `test@example.com`
   - Password: `password123`
   - Click "Create New User"
   - Copy the generated token

### Option B: Using curl (Alternative)
```bash
curl -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "returnSecureToken": true
  }'
```

## Step 2: Test Upload Process 📄

### Upload a PDF
```bash
# Create a simple test file
echo "Math Problems:
1. Solve for x: 2x + 5 = 15
2. Find derivative: f(x) = x^2 + 3x - 2
3. Solve: x^2 - 5x + 6 = 0" > test_math.txt

# Upload (replace YOUR_TOKEN with actual token)
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_math.txt"
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "user_id": "firebase-uid",
  "original_filename": "test_math.txt",
  "status": "processing",
  "created_at": "2025-09-27T...",
  "updated_at": "2025-09-27T..."
}
```

### Check Upload Status
```bash
# Replace PROBLEM_ID with the ID from upload response
curl -X GET "http://localhost:8000/api/v1/upload/status/PROBLEM_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Step 3: View Problems 👀

### Get All User Problems
```bash
# Replace YOUR_USER_ID with your Firebase UID (from token decode)
curl -X GET "http://localhost:8000/api/v1/problems/YOUR_USER_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Specific Problem Details
```bash
curl -X GET "http://localhost:8000/api/v1/problems/YOUR_USER_ID/PROBLEM_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search Problems
```bash
curl -X GET "http://localhost:8000/api/v1/problems/YOUR_USER_ID/search?q=derivative" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get User Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/problems/YOUR_USER_ID/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Step 4: Solve Problems 🧮

### Start Solving a Problem
```bash
curl -X POST "http://localhost:8000/api/v1/solve/PROBLEM_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "id": "solution-uuid",
  "problem_id": "problem-uuid",
  "user_id": "firebase-uid",
  "math_expression": "2x + 5 = 15",
  "status": "solving",
  "created_at": "2025-09-27T...",
  "updated_at": "2025-09-27T..."
}
```

### Check Solution Status
```bash
curl -X GET "http://localhost:8000/api/v1/solve/status/SOLUTION_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get All Solutions for a Problem
```bash
curl -X GET "http://localhost:8000/api/v1/solve/PROBLEM_ID/solutions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Specific Solution Details
```bash
curl -X GET "http://localhost:8000/api/v1/solve/solution/SOLUTION_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Step 5: Using the Python Test Script 🐍

1. **Edit test_api.py:**
   ```python
   TOKEN = "your-actual-firebase-token"
   USER_ID = "your-firebase-user-id"
   ```

2. **Run the test:**
   ```bash
   /Users/thanh/Workspace/ORCCortex/.venv/bin/python test_api.py
   ```

## Complete Workflow Example 🔄

```bash
# 1. Upload PDF
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_math.txt")

PROBLEM_ID=$(echo $UPLOAD_RESPONSE | jq -r '.id')
echo "Problem ID: $PROBLEM_ID"

# 2. Wait for processing and check status
sleep 2
curl -X GET "http://localhost:8000/api/v1/upload/status/$PROBLEM_ID" \
  -H "Authorization: Bearer $TOKEN"

# 3. Solve the problem
SOLVE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/solve/$PROBLEM_ID" \
  -H "Authorization: Bearer $TOKEN")

SOLUTION_ID=$(echo $SOLVE_RESPONSE | jq -r '.id')
echo "Solution ID: $SOLUTION_ID"

# 4. Check solution results
sleep 2
curl -X GET "http://localhost:8000/api/v1/solve/status/$SOLUTION_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting 🔧

### Common Issues:
1. **401 Unauthorized**: Check your Firebase token
2. **403 Forbidden**: User ID mismatch
3. **404 Not Found**: Problem/solution doesn't exist
4. **500 Server Error**: Check server logs

### Check Server Logs:
The server terminal will show detailed logs for debugging.

### Database Verification:
Check Firebase Console → Firestore Database to see stored data.

## Success Indicators ✅

- [ ] Upload returns problem ID
- [ ] Problem appears in user's problem list
- [ ] OCR extracts math expressions
- [ ] Solve creates solution records
- [ ] Solutions show step-by-step results
- [ ] All data persists in Firestore

Ready to test! 🚀