# Data Models

## Problem Model

Represents a PDF document uploaded for mathematical problem extraction and solving.

```python
class Problem(BaseModel):
    id: str                                    # Unique problem identifier
    user_id: str                              # User who uploaded the problem
    original_filename: str                     # Original PDF filename
    file_path: str                            # Storage path for uploaded file
    extracted_text: Optional[str] = None       # Extracted text from PDF
    math_expressions: Optional[List[str]] = None  # Identified math expressions
    status: ProblemStatus                      # Processing status
    created_at: datetime                       # Creation timestamp
    updated_at: datetime                       # Last update timestamp
```

### Problem Status Enum

```python
class ProblemStatus(str, Enum):
    PENDING = "pending"        # Uploaded, waiting for processing
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"    # Processing finished successfully
    FAILED = "failed"         # Processing failed with errors
```

## Solution Model

Represents a solved mathematical expression with step-by-step solution.

```python
class Solution(BaseModel):
    id: str                                      # Unique solution identifier
    problem_id: str                             # Associated problem ID
    user_id: str                                # User who owns the solution
    math_expression: str                         # Original math expression
    solution_steps: Optional[Dict[str, Any]] = None  # Step-by-step solution
    final_answer: Optional[str] = None           # Final computed answer
    status: SolutionStatus                       # Solution status
    error_message: Optional[str] = None          # Error details if failed
    created_at: datetime                         # Creation timestamp
    updated_at: datetime                         # Last update timestamp
```

### Solution Status Enum

```python
class SolutionStatus(str, Enum):
    PENDING = "pending"      # Queued for solving
    SOLVING = "solving"      # Currently being solved
    COMPLETED = "completed"  # Successfully solved
    FAILED = "failed"       # Solving failed
```

## User Model

Represents authenticated users in the system.

```python
class User(BaseModel):
    id: str                                    # Firebase user ID
    email: str                                 # User email address
    display_name: Optional[str] = None         # User display name
    created_at: datetime                       # Account creation date
    last_login: Optional[datetime] = None      # Last login timestamp
```

## Request/Response Models

### Problem Creation

```python
class ProblemCreate(BaseModel):
    user_id: str
    original_filename: str
```

### Problem Response

```python
class ProblemResponse(BaseModel):
    id: str
    user_id: str
    original_filename: str
    extracted_text: Optional[str] = None
    math_expressions: Optional[List[str]] = None
    status: ProblemStatus
    created_at: datetime
    updated_at: datetime
```

### Solution Creation

```python
class SolutionCreate(BaseModel):
    problem_id: str
    user_id: str
    math_expression: str
```

### Solution Response

```python
class SolutionResponse(BaseModel):
    id: str
    problem_id: str
    user_id: str
    math_expression: str
    solution_steps: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None
    status: SolutionStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

## Data Relationships

- **User** (1) → **Problem** (Many): Users can have multiple problems
- **Problem** (1) → **Solution** (Many): Each problem can have multiple math expressions to solve
- **User** (1) → **Solution** (Many): Users own all solutions derived from their problems

## Validation Rules

- **File Size**: Maximum 10MB for PDF uploads
- **File Type**: Only PDF files are accepted
- **Math Expressions**: Must be valid mathematical notation
- **User Access**: Users can only access their own problems and solutions
- **Status Transitions**: Must follow valid state machine patterns