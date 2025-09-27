# GPT OSS Model Setup Guide

## Overview
This guide explains how to set up the GPT OSS model for the restructured ORCCortex system.

## Current Status
The system is configured to use the GPT OSS 20B model located at:
- **Model Path**: `gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf`
- **Model Size**: ~20B parameters
- **Format**: GGUF (optimized for llama.cpp)

## Setup Options

### Option 1: llama-cpp-python (Recommended)
Install the Python binding for llama.cpp:

```bash
# Install llama-cpp-python
pip install llama-cpp-python

# For GPU acceleration (optional)
pip install llama-cpp-python[metal]  # macOS Metal
# or
pip install llama-cpp-python[cuda]   # NVIDIA CUDA
```

Update `gpt_oss_service.py` to use llama-cpp-python:

```python
from llama_cpp import Llama

class GPTOSSService:
    def __init__(self):
        self.model = Llama(
            model_path="/Users/thanh/Workspace/ORCCortex/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf",
            n_ctx=2048,  # Context window
            n_threads=4,  # CPU threads
            verbose=False
        )
    
    async def _generate_response(self, prompt: str) -> str:
        output = self.model(
            prompt,
            max_tokens=2048,
            temperature=0.1,
            top_p=0.9,
            echo=False
        )
        return output['choices'][0]['text']
```

### Option 2: llama.cpp Binary
Download and compile llama.cpp:

```bash
# Clone repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build
make

# Copy binary to your PATH or update the service to use full path
```

### Option 3: Development Mode (Current)
The current implementation uses mock responses for development. This allows testing the API structure without requiring the full model setup.

## Memory Requirements

### Minimum Requirements
- **RAM**: 16GB+ (for 20B model)
- **Storage**: 15GB+ free space
- **CPU**: Multi-core processor recommended

### Recommended for Production
- **RAM**: 32GB+
- **GPU**: 8GB+ VRAM (for GPU acceleration)
- **Storage**: SSD for model loading speed

## Configuration

### Environment Variables
Add to your `.env` file:

```env
# GPT OSS Configuration
GPT_OSS_MODEL_PATH=/Users/thanh/Workspace/ORCCortex/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf
GPT_OSS_MAX_TOKENS=2048
GPT_OSS_TEMPERATURE=0.1
GPT_OSS_THREADS=4
```

### Model Parameters
- **Temperature**: 0.1 (low for consistent math solutions)
- **Max Tokens**: 2048 (sufficient for detailed solutions)
- **Top-p**: 0.9 (good balance for mathematical reasoning)

## Testing the Setup

### 1. Basic Model Test
```bash
# Test if model loads
python -c "
from src.app.services.gpt_oss_service import gpt_oss_service
print('GPT OSS service initialized successfully')
"
```

### 2. API Test
```bash
# Test the solve endpoint
curl -X POST "http://localhost:8000/api/v1/solve/expression" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"expression": "What is 2 + 2?"}'
```

### 3. Upload and Solve Test
```bash
# Upload a PDF
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf"

# Get problem ID from response, then solve
curl -X POST "http://localhost:8000/api/v1/solve/{problem_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Performance Optimization

### CPU Optimization
- Increase `n_threads` based on your CPU cores
- Use `-O3` compilation flags for llama.cpp
- Consider CPU-specific optimizations (AVX2, AVX512)

### GPU Acceleration
- Use Metal on macOS: `pip install llama-cpp-python[metal]`
- Use CUDA on Linux/Windows: `pip install llama-cpp-python[cuda]`
- Monitor VRAM usage during inference

### Memory Management
- Use `mlock=True` to keep model in RAM
- Consider model quantization for lower memory usage
- Monitor system memory during operation

## Troubleshooting

### Common Issues

#### "Model file not found"
- Verify the model path in `gpt_oss_service.py`
- Check file permissions
- Ensure the GGUF file is not corrupted

#### "Out of memory"
- Reduce `n_ctx` (context window size)
- Use a smaller quantized model
- Add more RAM or enable swap

#### "Slow inference"
- Enable GPU acceleration
- Increase CPU threads
- Use SSD storage for model file

### Debug Mode
Enable verbose logging in the service:

```python
self.model = Llama(
    model_path=self.model_path,
    verbose=True  # Enable debug output
)
```

## Production Deployment

### Docker Setup
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -g++ make

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy model and application
COPY gpt-oss-20b-GGUF/ /app/models/
COPY src/ /app/src/
COPY main.py /app/

# Set environment variables
ENV GPT_OSS_MODEL_PATH=/app/models/gpt-oss-20b-MXFP4.gguf

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Scaling Considerations
- Use multiple worker processes
- Implement model loading balancing
- Consider caching for frequent problems
- Monitor resource usage

## Alternative Models

If the 20B model is too large, consider:

- **7B models**: Require less memory (~8GB RAM)
- **13B models**: Good balance of performance and resource usage
- **Quantized versions**: 4-bit or 8-bit quantization for lower memory

## Next Steps

1. Choose your setup option (llama-cpp-python recommended)
2. Install dependencies
3. Test the configuration
4. Monitor performance in development
5. Optimize for your hardware
6. Deploy to production

The system will automatically fall back to mock responses if the model isn't available, so you can develop and test the API structure while setting up the model infrastructure.