# Llama 3.2 RAG System Setup Script for Windows
# Run this script in PowerShell as Administrator

Write-Host "🦙 Llama 3.2 RAG System Setup" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  This script should be run as Administrator for best results" -ForegroundColor Yellow
    Write-Host "   Some installations might fail without admin privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if command exists
function Test-Command($command) {
    try {
        Get-Command $command -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Check Python installation
Write-Host "🔍 Checking Python installation..." -ForegroundColor Cyan
if (Test-Command "python") {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found" -ForegroundColor Red
    Write-Host "   Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    Write-Host "   Or use: winget install Python.Python.3" -ForegroundColor Yellow
    exit 1
}

# Check pip
Write-Host "🔍 Checking pip..." -ForegroundColor Cyan
if (Test-Command "pip") {
    Write-Host "✅ pip found" -ForegroundColor Green
} else {
    Write-Host "❌ pip not found" -ForegroundColor Red
    exit 1
}

# Install Ollama
Write-Host "🔍 Checking Ollama installation..." -ForegroundColor Cyan
if (Test-Command "ollama") {
    Write-Host "✅ Ollama already installed" -ForegroundColor Green
} else {
    Write-Host "📥 Installing Ollama..." -ForegroundColor Yellow
    try {
        winget install Ollama.Ollama
        Write-Host "✅ Ollama installed successfully" -ForegroundColor Green
        Write-Host "   Please restart your terminal/PowerShell window" -ForegroundColor Yellow
        Write-Host "   Then run this script again" -ForegroundColor Yellow
        pause
        exit 0
    }
    catch {
        Write-Host "❌ Failed to install Ollama via winget" -ForegroundColor Red
        Write-Host "   Please install manually from https://ollama.ai/" -ForegroundColor Yellow
        exit 1
    }
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

# Start Ollama service
Write-Host "🚀 Starting Ollama service..." -ForegroundColor Cyan
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3

# Pull Llama 3.2 model
Write-Host "🔽 Pulling Llama 3.2 model (this may take a while)..." -ForegroundColor Cyan
try {
    ollama pull llama3.2
    Write-Host "✅ Llama 3.2 model downloaded successfully" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Could not pull Llama 3.2 model automatically" -ForegroundColor Yellow
    Write-Host "   You can pull it manually later: ollama pull llama3.2" -ForegroundColor Yellow
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
Write-Host "1. Command-line interface:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Web interface:" -ForegroundColor White
Write-Host "   streamlit run web_app.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Add your knowledge files to the knowledge_base/ directory" -ForegroundColor White
Write-Host ""

# Ask if user wants to launch the web interface
$launch = Read-Host "Would you like to launch the web interface now? (y/N)"
if ($launch -eq "y" -or $launch -eq "Y") {
    Write-Host "🌐 Launching web interface..." -ForegroundColor Cyan
    streamlit run web_app.py
}
