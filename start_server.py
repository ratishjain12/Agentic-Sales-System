#!/usr/bin/env python3
"""
Sales Agent Server Startup Script
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI dependencies found")
        return True
    except ImportError:
        print("❌ FastAPI dependencies not found")
        print("Installing server dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "server/requirements.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "GMAIL_CREDENTIALS_FILE",
        "GMAIL_SENDER_EMAIL",
        "CEREBRAS_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file:")
        print("GMAIL_CREDENTIALS_FILE=credentials/oauth2_credentials.json")
        print("GMAIL_SENDER_EMAIL=your-email@gmail.com")
        print("CEREBRAS_API_KEY=your_cerebras_api_key")
        return False
    
    print("✅ Environment variables configured")
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Sales Agent API Server...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Server will start but some features may not work")
        input("Press Enter to continue anyway, or Ctrl+C to exit...")
    
    print("\n🌐 Server Information:")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    print("   - Root: http://localhost:8000/")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server
        os.system("python server/run.py")
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = start_server()
    sys.exit(0 if success else 1)
