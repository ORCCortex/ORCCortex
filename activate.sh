#!/bin/bash

# ORCCortex Development Environment Setup Script

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if uploads directory exists, create if not
if [ ! -d "uploads" ]; then
    mkdir uploads
    echo "Created uploads directory"
fi

echo "Environment activated. Python path: $(which python)"
echo "You can now run the application with: python main.py"
echo "Or start development server with: uvicorn main:app --reload"