#!/bin/bash

# ORCCortex Project Summary Script

echo "======================================="
echo "        ORCCortex Project Status"
echo "======================================="
echo ""

# Check virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "❌ Virtual environment not active"
    echo "   Run: source .venv/bin/activate"
fi
echo ""

# Check Python and packages
echo "🐍 Python version: $(python --version 2>&1)"
echo "📦 Package manager: uv $(uv --version 2>&1 | cut -d' ' -f2)"
echo ""

# Check key dependencies
echo "🔍 Key Dependencies Check:"
python -c "
try:
    import fastapi; print('✅ FastAPI:', fastapi.__version__)
except ImportError: print('❌ FastAPI not installed')

try:
    import firebase_admin; print('✅ Firebase Admin SDK installed')
except ImportError: print('❌ Firebase Admin SDK not installed')

try:
    import sympy; print('✅ SymPy:', sympy.__version__)
except ImportError: print('❌ SymPy not installed')

try:
    import fitz; print('✅ PyMuPDF available')
except ImportError: print('❌ PyMuPDF not installed')

try:
    import pytesseract; print('✅ pytesseract available')
except ImportError: print('❌ pytesseract not installed')
"
echo ""

# Check system dependencies
echo "🔧 System Dependencies:"
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract OCR: $(tesseract --version 2>&1 | head -1)"
else
    echo "❌ Tesseract OCR not found"
fi
echo ""

# Project structure
echo "📁 Project Structure:"
echo "   • FastAPI backend with modular architecture"
echo "   • Application code in src/app/ directory"
echo "   • OCR service (PDF text extraction)"
echo "   • Math solving service (SymPy integration)"
echo "   • Firebase integration (Auth + Storage)"
echo "   • RESTful API with authentication"
echo ""

# Check if uploads directory exists
if [ -d "uploads" ]; then
    echo "✅ Uploads directory exists"
else
    echo "❌ Uploads directory missing"
    mkdir uploads
    echo "   Created uploads directory"
fi
echo ""

# Application test
echo "🚀 Application Import Test:"
if python -c "from main import app; print('✅ Application imports successfully')" 2>/dev/null; then
    echo "✅ Main application can be imported"
else
    echo "❌ Application import failed"
fi

if python -c "from src.app.services.math_service import math_service; print('✅ Services import successfully')" 2>/dev/null; then
    echo "✅ Services can be imported from src/app"
else
    echo "❌ Services import failed from src/app"
fi
echo ""

echo "📋 Quick Start Commands:"
echo "   • Start development server: uvicorn main:app --reload"
echo "   • Run tests: pytest"
echo "   • API documentation: http://localhost:8000/docs"
echo "   • Format code: black ."
echo "   • Lint code: flake8 ."
echo ""

echo "🎯 Next Steps:"
echo "   1. Configure Firebase credentials in .env"
echo "   2. Test OCR functionality with sample PDFs"
echo "   3. Set up authentication endpoints"
echo "   4. Deploy to production environment"
echo ""
echo "======================================="