# Gemini MCP System Setup Script for Windows
# Run this script in PowerShell (Administrator privileges recommended)

Write-Host "🤖 Gemini MCP System Setup" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Check Python installation
Write-Host "🔍 Checking Python installation..." -ForegroundColor Cyan
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found" -ForegroundColor Red
    Write-Host "   Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Check pip
Write-Host "🔍 Checking pip..." -ForegroundColor Cyan
if (Get-Command "pip" -ErrorAction SilentlyContinue) {
    Write-Host "✅ pip found" -ForegroundColor Green
} else {
    Write-Host "❌ pip not found" -ForegroundColor Red
    exit 1
}

# Verify Gemini API key
Write-Host "🔐 Checking for GOOGLE_API_KEY..." -ForegroundColor Cyan
if ($Env:GOOGLE_API_KEY) {
    Write-Host "✅ GOOGLE_API_KEY detected" -ForegroundColor Green
} else {
    Write-Host "❌ GOOGLE_API_KEY is not set" -ForegroundColor Red
    Write-Host "   Create an API key in Google AI Studio and set it before running the app." -ForegroundColor Yellow
    Write-Host "   PowerShell: $Env:GOOGLE_API_KEY=\"your_key\"" -ForegroundColor Yellow
    exit 1
}

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
try {
    pip install -r requirements.txt
    Write-Host "✅ Python dependencies installed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
    Write-Host "   Try: python -m pip install --upgrade pip" -ForegroundColor Yellow
    exit 1
}

# Create directories
Write-Host "📁 Creating project directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "data" | Out-Null
New-Item -ItemType Directory -Force -Path "knowledge_base" -ErrorAction SilentlyContinue | Out-Null
Write-Host "✅ Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run the CLI:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Add knowledge files to knowledge_base/ if desired" -ForegroundColor White
