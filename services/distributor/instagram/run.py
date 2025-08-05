#!/usr/bin/env python3
"""
Instagram Automation System - Startup Script
Simple script to start the Instagram automation system with proper error handling.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from instagram_automation import InstagramAutomationSystem


def setup_directories():
    """Create necessary directories"""
    directories = [
        "config",
        "data",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)


def check_configuration():
    """Check if configuration file exists"""
    config_file = Path("config/config.yaml")
    example_file = Path("config/config.example.yaml")
    
    if not config_file.exists():
        if example_file.exists():
            print("❌ Configuration file not found!")
            print("📝 Please copy config/config.example.yaml to config/config.yaml")
            print("🔧 Then update it with your Instagram API credentials")
            return False
        else:
            print("❌ No configuration files found!")
            print("🚀 Run: python instagram_automation.py --create-config")
            return False
    
    return True


def check_environment_variables():
    """Check for required environment variables"""
    required_vars = [
        "INSTAGRAM_ACCESS_TOKEN",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("🔧 These can be set in your configuration file instead")
        return True  # Not critical if in config file
    
    return True


async def main():
    """Main startup function"""
    
    print("🌱 Starting Instagram Automation System for AquaScene...")
    print("=" * 60)
    
    # Setup directories
    setup_directories()
    
    # Check configuration
    if not check_configuration():
        sys.exit(1)
    
    # Check environment variables
    check_environment_variables()
    
    # Initialize and start system
    system = InstagramAutomationSystem()
    
    try:
        # Initialize system
        print("🔧 Initializing system components...")
        if not system.initialize():
            print("❌ Failed to initialize system")
            sys.exit(1)
        
        print("✅ System initialized successfully")
        print("🚀 Starting automation system...")
        print("📊 Monitor logs in instagram_automation.log")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start the system
        await system.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        logging.exception("System startup error")
        sys.exit(1)
    finally:
        print("👋 Instagram Automation System stopped")


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)