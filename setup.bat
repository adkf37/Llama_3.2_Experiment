@echo off
echo 🦙 Llama 3.2 RAG System - Setup Batch File
echo ==========================================

echo.
echo 🔍 Checking if Ollama is installed...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama not found
    echo.
    echo 📥 Please install Ollama manually:
    echo    1. Download from https://ollama.ai/
    echo    2. Or use: winget install Ollama.Ollama
    echo    3. Restart your terminal after installation
    echo    4. Run this script again
    pause
    exit /b 1
) else (
    echo ✅ Ollama is installed
)

echo.
echo 🚀 Starting Ollama service...
start /B ollama serve
timeout /t 3 /nobreak >nul

echo.
echo 🔽 Pulling Llama 3.2 model (this may take several minutes)...
ollama pull llama3.2
if %errorlevel% equ 0 (
    echo ✅ Llama 3.2 model downloaded successfully
) else (
    echo ⚠️ Could not pull Llama 3.2 model automatically
    echo    You can try again later with: ollama pull llama3.2
)

echo.
echo 📁 Creating directories...
if not exist "data" mkdir data
if not exist "knowledge_base" mkdir knowledge_base
echo ✅ Directories created

echo.
echo 🎉 Setup completed!
echo.
echo Next steps:
echo 1. Command-line interface: python main.py
echo 2. Web interface: streamlit run web_app.py
echo.
echo Press any key to launch the web interface...
pause >nul
streamlit run web_app.py
