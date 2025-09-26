# API Specifications

## Base Configuration

- **Base URL**: `http://localhost:8000`
- **API Version**: `/api/v1`
- **Authentication**: Firebase JWT Bearer tokens
- **Documentation**: Swagger UI at `/docs`, ReDoc at `/redoc`

## Endpoints

### System Endpoints

```http
GET /                    # Root endpoint with API info
GET /health             # Health check endpoint
GET /docs               # Interactive API documentation (Swagger UI)
GET /redoc              # Alternative API documentation (ReDoc)
```

### Upload Management

```http
POST /api/v1/upload                        # Upload PDF file for processing
GET  /api/v1/upload/status/{problem_id}    # Check processing status
```

### Problem Management

```http
GET    /api/v1/problems/{user_id}                    # Get user's problems
GET    /api/v1/problems/{user_id}/{problem_id}       # Get specific problem details
DELETE /api/v1/problems/{user_id}/{problem_id}       # Delete a problem
```

### Math Solving

```http
POST /api/v1/solve/{problem_id}               # Solve math problems from PDF
POST /api/v1/solve/expression                 # Solve single math expression
GET  /api/v1/solve/{problem_id}/solutions     # Get problem solutions
GET  /api/v1/solve/solution/{solution_id}     # Get solution details
```

## Authentication

All API endpoints require Firebase JWT Bearer token authentication:

```http
Authorization: Bearer <firebase_jwt_token>
```

## Request/Response Examples

### Upload PDF

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "file=@math_problems.pdf"
```

**Response:**
```json
{
  "problem_id": "uuid-string",
  "status": "pending",
  "message": "PDF uploaded successfully and queued for processing"
}
```

### Solve Expression

```bash
curl -X POST "http://localhost:8000/api/v1/solve/expression" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expression": "2x + 5 = 15"}'
```

**Response:**
```json
{
  "solution_id": "uuid-string",
  "original_expression": "2x + 5 = 15",
  "final_answer": "x = 5",
  "solution_steps": {
    "step1": "2x + 5 = 15",
    "step2": "2x = 15 - 5",
    "step3": "2x = 10",
    "step4": "x = 5"
  },
  "status": "completed"
}
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Error Response Format

```json
{
  "detail": "Error message",
  "type": "ErrorType",
  "status_code": 400
}
```

## Rate Limiting

- Maximum file size: 10MB
- Supported file types: PDF only
- Authentication required for all endpoints
- Background processing for heavy operations