#!/usr/bin/env python3
"""
Quick test script to verify AI processor service can start up correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all major components can be imported"""
    print("Testing imports...")
    
    try:
        from llm_clients.base_client import BaseLLMClient, ContentType, ModelType
        print("✅ Base client imports successful")
        
        from llm_clients.client_manager import LLMClientManager
        print("✅ Client manager import successful")
        
        from knowledge.aquascaping_kb import AquascapingKnowledgeBase
        print("✅ Knowledge base import successful")
        
        from validators.quality_validator import QualityValidator
        print("✅ Quality validator import successful")
        
        from generators.content_orchestrator import ContentOrchestrator
        print("✅ Content orchestrator import successful")
        
        from config.settings import Settings, get_settings
        print("✅ Settings import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without API keys"""
    print("\nTesting basic functionality...")
    
    try:
        # Test knowledge base initialization
        kb = AquascapingKnowledgeBase()
        stats = kb.get_stats()
        print(f"✅ Knowledge base initialized with {stats['total_plants']} plants")
        
        # Test content types enum
        content_types = list(ContentType)
        print(f"✅ Content types available: {len(content_types)}")
        
        # Test model types enum  
        model_types = list(ModelType)
        print(f"✅ Model types available: {len(model_types)}")
        
        # Test settings
        settings = get_settings()
        print(f"✅ Settings loaded for environment: {settings.environment}")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

def test_service_structure():
    """Test that service directory structure is correct"""
    print("\nTesting service structure...")
    
    required_dirs = [
        'src/llm_clients',
        'src/generators', 
        'src/validators',
        'src/knowledge',
        'src/optimizers',
        'src/templates',
        'src/batch',
        'src/monitoring',
        'src/config'
    ]
    
    base_path = os.path.dirname(__file__)
    all_exist = True
    
    for required_dir in required_dirs:
        dir_path = os.path.join(base_path, required_dir)
        if os.path.exists(dir_path):
            print(f"✅ {required_dir} exists")
        else:
            print(f"❌ {required_dir} missing")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    print("🤖 AI Content Processor Service Test")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    if test_service_structure():
        tests_passed += 1
        
    if test_imports():
        tests_passed += 1
        
    if test_basic_functionality():
        tests_passed += 1
    
    print("\n" + "=" * 40)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Service is ready for deployment.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the output above.")
        sys.exit(1)