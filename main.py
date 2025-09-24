from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime

from app.routers import upload, problems, solve
from app.utils.config import settings
from app.utils.exceptions import ORCCortexException, create_http_exception

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="OCR Math Solver - Extract and solve mathematical problems from PDF documents",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ORCCortexException)
async def orccortex_exception_handler(request, exc: ORCCortexException):
    """Handle custom ORCCortex exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": type(exc).__name__}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to ORCCortex - OCR Math Solver API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# Include routers
app.include_router(
    upload.router,
    prefix=settings.API_V1_STR,
    tags=["upload"]
)

app.include_router(
    problems.router,
    prefix=settings.API_V1_STR,
    tags=["problems"]
)

app.include_router(
    solve.router,
    prefix=settings.API_V1_STR,
    tags=["solve"]
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"Upload directory: {settings.UPLOAD_DIR}")
    
    # Initialize services (Firebase, etc.)
    print("Initializing services...")
    
    if settings.DEBUG:
        print("Running in DEBUG mode")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown"""
    print(f"Shutting down {settings.APP_NAME}")


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )