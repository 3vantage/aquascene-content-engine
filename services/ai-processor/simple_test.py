#!/usr/bin/env python3
"""
Simple test for OpenAI and Anthropic API integrations
"""

import asyncio
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional

# Simple test without complex dependencies
@dataclass
class SimpleConfig:
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 100

async def test_openai():
    """Test OpenAI directly"""
    print("Testing OpenAI API...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found")
        return False
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an aquascaping expert."},
                {"role": "user", "content": "Give one simple aquascaping tip for beginners."}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        
        print(f"✅ OpenAI working: {tokens} tokens")
        print(f"   Response: {content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI error: {str(e)}")
        return False

async def test_anthropic():
    """Test Anthropic directly"""
    print("\nTesting Anthropic API...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Anthropic API key not found")
        return False
    
    try:
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=api_key)
        
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{
                "role": "user", 
                "content": "Give one simple aquascaping tip for beginners."
            }],
            system="You are an aquascaping expert.",
            temperature=0.7
        )
        
        content = response.content[0].text if response.content else ""
        tokens = (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
        
        print(f"✅ Anthropic working: {tokens} tokens")
        print(f"   Response: {content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Anthropic error: {str(e)}")
        return False

async def main():
    print("🧪 Testing LLM APIs")
    print("=" * 40)
    
    openai_works = await test_openai()
    anthropic_works = await test_anthropic()
    
    print("\n" + "=" * 40)
    if openai_works or anthropic_works:
        print("🎉 At least one API is working!")
    else:
        print("⚠️ No APIs are working. Check your API keys:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("   export ANTHROPIC_API_KEY='your-key-here'")

if __name__ == "__main__":
    asyncio.run(main())