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
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_ollama():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed")
            return True
        else:
            print("❌ Ollama not found")
            return False
    except:
        print("❌ Ollama not found")
        return False

def main():
    """Main setup function."""
    print("🦙 Llama 3.2 RAG System Setup")
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
    
    # Check Ollama installation
    if not check_ollama():
        print("\n📥 Ollama not found. Please install it:")
        print("   Windows: winget install Ollama.Ollama")
        print("   Or download from: https://ollama.ai/")
        print("   After installation, restart your terminal")
        return False
    
    # Check if Ollama is running
    try:
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is running")
        else:
            print("⚠️  Ollama may not be running. Try: ollama serve")
    except:
        print("⚠️  Could not check Ollama status")
    
    # Try to pull Llama 3.2 model
    print("\n🔄 Attempting to pull Llama 3.2 model...")
    model_name = "llama3.2"
    
    if run_command(f"ollama pull {model_name}", f"Pulling {model_name} model"):
        print(f"✅ {model_name} model is ready")
    else:
        print(f"⚠️  Could not pull {model_name} model automatically")
        print(f"   You can pull it manually later: ollama pull {model_name}")
    
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
    print("\n2. Or start the web interface:")
    print("   streamlit run web_app.py")
    print("\n3. Add your own knowledge files to the knowledge_base/ directory")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
