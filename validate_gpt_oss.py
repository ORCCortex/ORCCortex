#!/usr/bin/env python3
"""
Simple validation script for GPT OSS service configuration
This script validates the setup without requiring llama-cpp-python installation
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def validate_model_file():
    """Validate that the GGUF model file exists"""
    model_path = Path("/Users/thanh/Workspace/ORCCortex/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf")
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ Model file found: {model_path}")
        print(f"📊 Model size: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ Model file not found: {model_path}")
        print("   Please ensure the GGUF model is downloaded to the correct location")
        return False

def validate_service_import():
    """Validate that the service can be imported"""
    try:
        from src.app.services.gpt_oss_service import LLAMA_CPP_AVAILABLE
        print(f"✅ Service imports successfully")
        print(f"📦 llama-cpp-python available: {LLAMA_CPP_AVAILABLE}")
        
        if not LLAMA_CPP_AVAILABLE:
            print("⚠️  Install llama-cpp-python to enable inference:")
            print("   pip3 install llama-cpp-python")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def validate_config():
    """Validate configuration settings"""
    try:
        from src.app.utils.config import settings
        print("✅ Configuration loaded successfully")
        print(f"🎯 Model path: {settings.GPT_OSS_MODEL_PATH}")
        print(f"🧠 Context length: {settings.GPT_OSS_N_CTX}")
        print(f"🔥 Temperature: {settings.GPT_OSS_TEMPERATURE}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Main validation function"""
    print("=" * 60)
    print("GPT OSS SERVICE VALIDATION")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Check model file
    print("\n1. Validating model file...")
    if not validate_model_file():
        all_checks_passed = False
    
    # Check service import
    print("\n2. Validating service import...")
    if not validate_service_import():
        all_checks_passed = False
    
    # Check configuration
    print("\n3. Validating configuration...")
    if not validate_config():
        all_checks_passed = False
    
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ All validation checks passed!")
        print("🚀 The GPT OSS service is ready for use")
        print("\nNext steps:")
        print("1. Install llama-cpp-python: pip3 install llama-cpp-python")
        print("2. Run the test script: python3 test_gpt_oss.py")
    else:
        print("❌ Some validation checks failed")
        print("Please fix the issues above before using the service")
    print("=" * 60)

if __name__ == "__main__":
    main()