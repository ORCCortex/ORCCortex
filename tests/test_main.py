"""
Test configuration and basic functionality
"""
import pytest


def test_imports():
    """Test that all main modules can be imported"""
    from main import app
    assert app is not None
    
    from app import models, services, routers
    assert models is not None
    assert services is not None
    assert routers is not None


def test_math_service():
    """Test math service functionality"""
    import asyncio
    from app.services.math_service import math_service
    
    async def run_test():
        result = await math_service.solve_expression("2 + 2")
        assert result is not None
        assert "final_answer" in result
        return result
    
    result = asyncio.run(run_test())
    assert result["final_answer"] == "4"


def test_ocr_service_import():
    """Test OCR service can be imported"""
    from app.services.ocr_service import ocr_service
    assert ocr_service is not None


def test_firebase_service_import():
    """Test Firebase service can be imported"""
    from app.services.firebase_service import firebase_service
    assert firebase_service is not None