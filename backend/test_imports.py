#!/usr/bin/env python3
"""
Quick import test to verify all services can be imported correctly.
This is useful for CI/CD pipeline testing.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_storage_imports():
    """Test storage service imports."""
    try:
        from services.storage.services.file_processor import FileProcessor
        from services.storage.services.vector_store import VectorStore
        print("✅ Storage service imports successful")
        return True
    except ImportError as e:
        print(f"❌ Storage service import failed: {e}")
        return False

def test_retriever_imports():
    """Test retriever service imports."""
    try:
        from services.retriever.services.hybrid_retriever import HybridRetriever
        print("✅ Retriever service imports successful")
        return True
    except ImportError as e:
        print(f"❌ Retriever service import failed: {e}")
        return False

def test_gateway_imports():
    """Test gateway service imports."""
    try:
        from services.gateway.services.orchestrator import RAGOrchestrator
        print("✅ Gateway service imports successful")
        return True
    except ImportError as e:
        print(f"❌ Gateway service import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    try:
        from services.storage.services.file_processor import FileProcessor
        
        processor = FileProcessor()
        test_text = "This is a test document with some content to test the chunking functionality."
        chunks = processor.chunk_text(test_text, chunk_size=30, overlap=5)
        
        if len(chunks) > 0:
            print(f"✅ Text chunking test passed: {len(chunks)} chunks created")
            return True
        else:
            print("❌ Text chunking test failed: no chunks created")
            return False
            
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all import and basic functionality tests."""
    print("🔍 Testing service imports and basic functionality...")
    
    tests = [
        test_storage_imports,
        test_retriever_imports,
        test_gateway_imports,
        test_basic_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())