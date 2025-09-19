@echo off
setlocal ENABLEDELAYEDEXPANSION

ECHO 🤖 Gemini MCP System Setup
ECHO ================================

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO ❌ Python not found
    ECHO    Install Python 3.8+ from https://www.python.org/
    exit /b 1
) ELSE (
    FOR /F "tokens=*" %%i IN ('python --version') DO ECHO ✅ %%i detected
)

REM Check pip
pip --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO ❌ pip not found
    exit /b 1
) ELSE (
    FOR /F "tokens=*" %%i IN ('pip --version') DO ECHO ✅ %%i detected
)

REM Check GOOGLE_API_KEY
IF "%GOOGLE_API_KEY%"=="" (
    ECHO ❌ GOOGLE_API_KEY is not set
    ECHO    Create an API key in Google AI Studio and run:
    ECHO    set GOOGLE_API_KEY=your_key
    exit /b 1
) ELSE (
    ECHO ✅ GOOGLE_API_KEY detected
)

REM Install Python dependencies
ECHO 📦 Installing Python dependencies...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    ECHO ❌ Failed to install Python dependencies
    exit /b 1
) ELSE (
    ECHO ✅ Dependencies installed
)

REM Create directories
IF NOT EXIST data mkdir data
IF NOT EXIST knowledge_base mkdir knowledge_base
ECHO ✅ Project directories ready

ECHO.
ECHO 🎉 Setup completed!
ECHO Next steps:
ECHO   python main.py
ECHO   Add knowledge files to knowledge_base\ if desired

endlocal
