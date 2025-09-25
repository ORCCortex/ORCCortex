from fastapi import HTTPException
from typing import Optional


class ORCCortexException(Exception):
    """Base exception for ORCCortex application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(ORCCortexException):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationError(ORCCortexException):
    """Authorization related errors"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class ValidationError(ORCCortexException):
    """Validation related errors"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, 400)


class FileProcessingError(ORCCortexException):
    """File processing related errors"""
    def __init__(self, message: str = "File processing failed"):
        super().__init__(message, 422)


class OCRError(ORCCortexException):
    """OCR processing related errors"""
    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(message, 422)


class MathSolvingError(ORCCortexException):
    """Math solving related errors"""
    def __init__(self, message: str = "Math solving failed"):
        super().__init__(message, 422)


def create_http_exception(exc: ORCCortexException) -> HTTPException:
    """Convert ORCCortexException to HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message
    )