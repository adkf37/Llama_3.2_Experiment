#!/usr/bin/env python3
"""
Setup script for Llama 3.2 RAG System
Installs dependencies and sets up the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        # Specify encoding and error handling for subprocess output
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        # Optionally print stdout if needed for debugging, or if the command is expected to produce useful output
        # if result.stdout:
        #     print(result.stdout)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        # Print decoded stderr
        print(f"Error output: {e.stderr}")
        return False
    except Exception as ex: # Catch other potential exceptions like FileNotFoundError
        print(f"❌ An unexpected error occurred while running command '{command}': {ex}")
        return False

def check_gemini_api_key():
    """Ensure a Gemini API key is available."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("✅ GOOGLE_API_KEY detected")
        return True

    print("❌ GOOGLE_API_KEY not set")
    print("   Create an API key in Google AI Studio and export it before running the app.")
    print("   Linux/macOS: export GOOGLE_API_KEY=your_key")
    print("   Windows PowerShell: $Env:GOOGLE_API_KEY=\"your_key\"")
    return False

def main():
    """Main setup function."""
    print("🤖 Gemini MCP System Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found. Make sure you're in the project directory.")
        return False
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("💡 Try upgrading pip: python -m pip install --upgrade pip")
        return False
    
    # Check Gemini API key
    if not check_gemini_api_key():
        return False

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print("✅ Created data directory")
    
    # Create knowledge base directory if it doesn't exist
    kb_dir = Path("knowledge_base")
    if not kb_dir.exists():
        kb_dir.mkdir(exist_ok=True)
        print("✅ Created knowledge_base directory")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Start the system:")
    print("   python main.py")
    print("\n2. Add your own knowledge files to the knowledge_base/ directory")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
