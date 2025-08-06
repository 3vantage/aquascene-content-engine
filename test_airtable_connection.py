#!/usr/bin/env python3
"""
Test script to verify Airtable connection and credentials
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test if environment variables are properly set"""
    print("🔍 Testing Environment Configuration")
    print("-" * 40)
    
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    print(f"AIRTABLE_API_KEY: {'✅ Set' if api_key and api_key != 'your-airtable-api-key-here' else '❌ Not set or placeholder'}")
    print(f"AIRTABLE_BASE_ID: {'✅ Set' if base_id and base_id != 'your-airtable-base-id-here' else '❌ Not set or placeholder'}")
    
    if api_key and api_key != 'your-airtable-api-key-here':
        print(f"API Key (preview): {api_key[:8]}...")
    
    if base_id and base_id != 'your-airtable-base-id-here':
        print(f"Base ID: {base_id}")
    
    return api_key, base_id

def test_pyairtable_import():
    """Test if pyairtable can be imported"""
    print("\n🔍 Testing pyairtable Import")
    print("-" * 30)
    
    try:
        from pyairtable import Api
        print("✅ pyairtable imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import pyairtable: {e}")
        print("Install with: pip install pyairtable")
        return False

def test_connection(api_key, base_id):
    """Test actual connection to Airtable"""
    if not api_key or api_key == 'your-airtable-api-key-here':
        print("\n⚠️ Skipping connection test - API key not configured")
        return False
    
    if not base_id or base_id == 'your-airtable-base-id-here':
        print("\n⚠️ Skipping connection test - Base ID not configured")
        return False
    
    print("\n🔍 Testing Airtable Connection")
    print("-" * 32)
    
    try:
        from pyairtable import Api
        
        api = Api(api_key)
        base = api.base(base_id)
        
        # Try to get base schema
        schema = base.schema()
        print(f"✅ Connected successfully!")
        print(f"📋 Found {len(schema.tables)} tables in base")
        
        # List table names
        if schema.tables:
            print("📄 Tables:")
            for i, table in enumerate(schema.tables[:5], 1):  # Show first 5
                print(f"   {i}. {table.name}")
            if len(schema.tables) > 5:
                print(f"   ... and {len(schema.tables) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        
        # Provide helpful error messages
        if "Invalid API key" in str(e) or "INVALID_API_KEY" in str(e):
            print("\n💡 Tips for API Key:")
            print("   - Get your API key from: https://airtable.com/create/tokens")
            print("   - Make sure the token has access to your base")
            print("   - API keys should start with 'pat' (Personal Access Token)")
        
        if "NOT_FOUND" in str(e) or "Base not found" in str(e):
            print("\n💡 Tips for Base ID:")
            print("   - Find your base ID in the Airtable API docs for your base")
            print("   - Base IDs typically start with 'app'")
            print("   - Make sure the base exists and you have access to it")
        
        return False

def main():
    """Main test function"""
    print("AquaScene Content Engine - Airtable Connection Test")
    print("=" * 53)
    
    # Test environment
    api_key, base_id = test_environment()
    
    # Test pyairtable import
    if not test_pyairtable_import():
        return 1
    
    # Test connection
    if not test_connection(api_key, base_id):
        print("\n❌ Connection test failed")
        print("\n📋 Next steps:")
        print("   1. Set your actual AIRTABLE_API_KEY in the .env file")
        print("   2. Set your actual AIRTABLE_BASE_ID in the .env file")
        print("   3. Run this test again to verify connection")
        print("   4. Then run the full schema analysis")
        return 1
    
    print("\n✅ All tests passed! Ready to run schema analysis.")
    print("Run: python airtable_schema_analysis.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())