# Development Guide

## Quick Start

### Prerequisites

- Python 3.10 or higher
- uv package manager
- Tesseract OCR
- Firebase account

### Installation

```bash
# Clone the repository
git clone https://github.com/ORCCortex/ORCCortex.git
cd ORCCortex

# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# Install system dependencies (macOS)
brew install tesseract poppler

# Configure environment
cp .env.example .env
# Edit .env with your Firebase credentials

# Run the application
uvicorn main:app --reload
```

### Verification

```bash
# Check project status
./project_status.sh

# Run tests
pytest tests/ -v

# Access API documentation
open http://localhost:8000/docs
```

## Development Workflow

### Code Quality Standards

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy src/

# Run all quality checks
black . && flake8 . && mypy src/
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py -v
```

### Environment Management

```bash
# Activate environment
source .venv/bin/activate

# Install new package
uv pip install package-name

# Update requirements
uv pip freeze > requirements.txt

# Deactivate environment
deactivate
```

## Development Structure

### Adding New Features

1. **Define Models** in `src/app/models/`
2. **Implement Services** in `src/app/services/`
3. **Create API Endpoints** in `src/app/routers/`
4. **Write Tests** in `tests/`
5. **Update Documentation**

### Service Development

```python
# Example service structure
class NewService:
    def __init__(self):
        # Initialize service
        pass
    
    async def process_data(self, data: str) -> dict:
        # Implement business logic
        return {"result": "processed"}

# Register service instance
new_service = NewService()
```

### Router Development

```python
from fastapi import APIRouter, Depends
from src.app.services.new_service import new_service

router = APIRouter()

@router.post("/new-endpoint")
async def create_item(data: dict):
    result = await new_service.process_data(data)
    return result
```

## Testing Strategy

### Test Structure

```text
tests/
├── test_main.py              # Application tests
├── test_services/            # Service layer tests
│   ├── test_ocr_service.py
│   ├── test_math_service.py
│   └── test_firebase_service.py
├── test_routers/             # API endpoint tests
│   ├── test_upload.py
│   ├── test_problems.py
│   └── test_solve.py
└── test_models/              # Data model tests
    ├── test_problem.py
    └── test_solution.py
```

### Writing Tests

```python
import pytest
from src.app.services.math_service import math_service

@pytest.mark.asyncio
async def test_solve_expression():
    result = await math_service.solve_expression("2 + 2")
    assert result["final_answer"] == "4"
    assert result["status"] == "completed"

def test_model_validation():
    from src.app.models.problem import Problem
    problem = Problem(
        id="test-id",
        user_id="user-123",
        original_filename="test.pdf",
        file_path="/tmp/test.pdf",
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert problem.id == "test-id"
```

## Debugging

### Local Development

```bash
# Run with debug mode
DEBUG=True uvicorn main:app --reload --log-level debug

# Use Python debugger
import pdb; pdb.set_trace()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

async def process_file(file_path: str):
    logger.info(f"Processing file: {file_path}")
    try:
        # Process file
        result = await ocr_service.extract_text(file_path)
        logger.info(f"Extracted {len(result)} characters")
        return result
    except Exception as e:
        logger.error(f"Failed to process file: {e}")
        raise
```

## Performance Optimization

### Async Operations

- Use `async/await` for I/O operations
- Implement background tasks for heavy processing
- Utilize connection pooling for database operations

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(input_data: str) -> str:
    # Expensive operation
    return processed_result
```

### Monitoring

- Use application metrics
- Monitor API response times
- Track error rates and patterns
- Monitor resource usage

## Deployment

### Docker Setup

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Firebase credentials secured
- [ ] CORS settings configured for production
- [ ] Logging configured appropriately
- [ ] Error tracking enabled
- [ ] Health checks implemented
- [ ] SSL/TLS enabled
- [ ] Rate limiting configured