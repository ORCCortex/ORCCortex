# Configuration

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase service account JSON file | `""` | Yes |
| `FIREBASE_STORAGE_BUCKET` | Firebase Storage bucket name | `""` | Yes |
| `DEBUG` | Enable debug mode for development | `False` | No |
| `MAX_FILE_SIZE` | Maximum upload file size in bytes | `10485760` (10MB) | No |
| `UPLOAD_DIR` | Local directory for temporary file storage | `"uploads"` | No |
| `TESSERACT_CMD` | Path to Tesseract OCR executable | `"tesseract"` | No |

## Settings Class

```python
class Settings:
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    
    # Application Configuration
    APP_NAME: str = "ORCCortex"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf"]
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    
    # OCR Configuration
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
```

## Firebase Setup

### Prerequisites

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Authentication and Storage in your Firebase project
3. Create a service account and download the credentials JSON file
4. Set up Firebase Storage bucket

### Configuration Steps

1. **Download Service Account Key**:
   - Go to Project Settings → Service Accounts
   - Generate new private key
   - Download the JSON file

2. **Set Environment Variables**:
   ```bash
   export FIREBASE_CREDENTIALS_PATH="/path/to/your/firebase-credentials.json"
   export FIREBASE_STORAGE_BUCKET="your-bucket-name.appspot.com"
   ```

3. **Enable Firebase Services**:
   - Authentication: Enable Email/Password provider
   - Storage: Set up security rules for file access

## Development Configuration

### Local Development

Create a `.env` file in the project root:

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_STORAGE_BUCKET=orccortex-dev.appspot.com

# Application Configuration
DEBUG=True
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads

# OCR Configuration (optional)
TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

### Production Configuration

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/app/config/firebase-credentials.json
FIREBASE_STORAGE_BUCKET=orccortex-prod.appspot.com

# Application Configuration
DEBUG=False
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/app/uploads

# OCR Configuration
TESSERACT_CMD=/usr/bin/tesseract
```

## System Dependencies

### macOS Installation

```bash
# Install Tesseract OCR
brew install tesseract

# Install Poppler (for PDF processing)
brew install poppler
```

### Ubuntu/Debian Installation

```bash
# Install Tesseract OCR
sudo apt-get update
sudo apt-get install tesseract-ocr

# Install Poppler utils
sudo apt-get install poppler-utils
```

## Security Configuration

### CORS Settings

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### File Upload Security

- File type validation (PDF only)
- File size limits (10MB maximum)
- Temporary file cleanup after processing
- Secure Firebase Storage integration

## Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```