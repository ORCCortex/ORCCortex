# System Architecture

## Technology Stack

### Backend Framework

- **FastAPI 0.104.1** - Modern Python web framework
- **Uvicorn 0.24.0** - ASGI server
- **Python 3.10+** - Runtime environment

### OCR and Document Processing

- **Tesseract OCR** - Industry-standard OCR engine
- **PyMuPDF 1.23.8** - PDF processing and text extraction
- **pdfminer.six 20221105** - Python PDF mining
- **pytesseract 0.3.10** - Tesseract Python wrapper

### Mathematical Computing

- **SymPy 1.12** - Symbolic mathematics library
- **Advanced regex patterns** - Math expression detection

### Cloud and Authentication

- **Firebase Admin SDK 6.2.0** - Authentication and storage
- **Firebase Auth** - User management
- **Firebase Storage** - Cloud file storage

### Development Tools

- **pytest** - Testing framework
- **black** - Code formatting
- **flake8** - Code linting
- **mypy** - Type checking
- **uv** - Package manager

## Application Structure

```text
ORCCortex/
├── main.py                    # FastAPI entry point
├── src/app/
│   ├── models/                # Data models
│   │   ├── user.py           # User models
│   │   ├── problem.py        # Problem models
│   │   └── solution.py       # Solution models
│   ├── services/              # Business logic
│   │   ├── firebase_service.py
│   │   ├── ocr_service.py
│   │   └── math_service.py
│   ├── routers/               # API endpoints
│   │   ├── upload.py
│   │   ├── problems.py
│   │   └── solve.py
│   └── utils/                 # Utilities
│       ├── config.py
│       └── exceptions.py
├── tests/                     # Test suite
├── uploads/                   # File storage
└── .venv/                    # Virtual environment
```

## Architectural Patterns

### Service Layer Pattern

- **OCR Service**: Handles PDF processing and text extraction
- **Math Service**: Manages symbolic mathematics and equation solving
- **Firebase Service**: Provides authentication and cloud storage

### Repository Pattern

- Models define data structures using Pydantic
- Services encapsulate business logic
- Routers handle HTTP requests and responses

### Async/Await Pattern

- Non-blocking I/O operations
- Background task processing
- Concurrent request handling

## Scalability Considerations

- **Modular Architecture**: Independent service scaling
- **Background Processing**: Async PDF and math operations
- **Cloud Storage**: Firebase for distributed file handling
- **Stateless Design**: Horizontal scaling capability