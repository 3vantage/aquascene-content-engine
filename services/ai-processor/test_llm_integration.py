#!/usr/bin/env python3
"""
Test script to verify LLM API integrations are working correctly.
This script tests the OpenAI, Anthropic, and Ollama integrations.
"""

import asyncio
import os
from typing import Dict, Any

# Add src to path
import sys
sys.path.append('/Users/kg/aquascene-content-engine/services/ai-processor/src')

from llm_clients.base_client import LLMConfig, ModelType, ContentType
from llm_clients.openai_client import OpenAIClient
from llm_clients.anthropic_client import AnthropicClient
from llm_clients.ollama_client import OllamaClient
from llm_clients.client_manager import LLMClientManager


async def test_openai_client():
    """Test OpenAI client integration"""
    print("Testing OpenAI Client...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found in environment variables")
        return False
    
    try:
        config = LLMConfig(
            model=ModelType.OPENAI_GPT4_MINI,
            api_key=api_key,
            temperature=0.7,
            max_tokens=100
        )
        
        client = OpenAIClient(config)
        
        # Test availability
        is_available = await client.is_available()
        if not is_available:
            print("❌ OpenAI service is not available")
            return False
        
        # Test content generation
        response = await client.generate_content(
            prompt="Write a brief tip about aquascaping lighting for beginners.",
            content_type=ContentType.NEWSLETTER_ARTICLE,
            system_prompt="You are an aquascaping expert providing helpful advice."
        )
        
        print(f"✅ OpenAI Client working successfully")
        print(f"   Model: {response.model_used}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_estimate:.4f}")
        print(f"   Content preview: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Client error: {str(e)}")
        return False


async def test_anthropic_client():
    """Test Anthropic client integration"""
    print("\nTesting Anthropic Client...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Anthropic API key not found in environment variables")
        return False
    
    try:
        config = LLMConfig(
            model=ModelType.CLAUDE_SONNET,
            api_key=api_key,
            temperature=0.7,
            max_tokens=100
        )
        
        client = AnthropicClient(config)
        
        # Test availability
        is_available = await client.is_available()
        if not is_available:
            print("❌ Anthropic service is not available")
            return False
        
        # Test content generation
        response = await client.generate_content(
            prompt="Write a brief tip about aquascaping substrate for beginners.",
            content_type=ContentType.INSTAGRAM_CAPTION,
            system_prompt="You are an aquascaping expert providing helpful advice."
        )
        
        print(f"✅ Anthropic Client working successfully")
        print(f"   Model: {response.model_used}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_estimate:.4f}")
        print(f"   Content preview: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Anthropic Client error: {str(e)}")
        return False


async def test_ollama_client():
    """Test Ollama client integration (local)"""
    print("\nTesting Ollama Client...")
    
    try:
        config = LLMConfig(
            model=ModelType.OLLAMA_LLAMA3,
            base_url="http://localhost:11434",
            temperature=0.7,
            max_tokens=100
        )
        
        client = OllamaClient(config)
        
        # Test availability
        is_available = await client.is_available()
        if not is_available:
            print("❌ Ollama service is not available (make sure Ollama is running locally)")
            return False
        
        # Test content generation
        response = await client.generate_content(
            prompt="Write a brief tip about aquascaping plant placement for beginners.",
            content_type=ContentType.HOW_TO_GUIDE,
            system_prompt="You are an aquascaping expert providing helpful advice."
        )
        
        print(f"✅ Ollama Client working successfully")
        print(f"   Model: {response.model_used}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_estimate:.4f}")
        print(f"   Content preview: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama Client error: {str(e)}")
        return False


async def test_client_manager():
    """Test LLM Client Manager with multiple providers"""
    print("\nTesting LLM Client Manager...")
    
    configs = {}
    
    # Add available configs
    if os.getenv('OPENAI_API_KEY'):
        configs["openai"] = LLMConfig(
            model=ModelType.OPENAI_GPT4_MINI,
            api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.7,
            max_tokens=100
        )
    
    if os.getenv('ANTHROPIC_API_KEY'):
        configs["anthropic"] = LLMConfig(
            model=ModelType.CLAUDE_SONNET,
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            temperature=0.7,
            max_tokens=100
        )
    
    # Try to add Ollama (local)
    configs["ollama"] = LLMConfig(
        model=ModelType.OLLAMA_LLAMA3,
        base_url="http://localhost:11434",
        temperature=0.7,
        max_tokens=100
    )
    
    if not configs:
        print("❌ No API keys found for testing Client Manager")
        return False
    
    try:
        manager = LLMClientManager(configs)
        
        # Test content generation with intelligent routing
        response = await manager.generate_content(
            prompt="Write a brief aquascaping tip about CO2 for planted tanks.",
            content_type=ContentType.NEWSLETTER_ARTICLE,
            system_prompt="You are an aquascaping expert providing helpful advice."
        )
        
        print(f"✅ Client Manager working successfully")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model_used}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_estimate:.4f}")
        print(f"   Content preview: {response.content[:100]}...")
        
        # Get performance stats
        stats = manager.get_performance_stats()
        print(f"   Available clients: {list(stats['health'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Client Manager error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Testing AI Processor LLM Integrations")
    print("=" * 50)
    
    results = {}
    
    # Test individual clients
    results['openai'] = await test_openai_client()
    results['anthropic'] = await test_anthropic_client()
    results['ollama'] = await test_ollama_client()
    
    # Test client manager
    results['client_manager'] = await test_client_manager()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests > 0:
        print("\n🎉 At least some LLM integrations are working!")
        if passed_tests == total_tests:
            print("🚀 All LLM integrations are working perfectly!")
    else:
        print("\n⚠️  No LLM integrations are working. Check your API keys and services.")
        print("\nSetup instructions:")
        print("1. Set OPENAI_API_KEY environment variable for OpenAI")
        print("2. Set ANTHROPIC_API_KEY environment variable for Anthropic")
        print("3. Install and run Ollama locally for local LLM support")


if __name__ == "__main__":
    asyncio.run(main())