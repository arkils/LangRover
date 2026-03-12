# LangRover Setup Script for Windows PowerShell
# This script sets up the project with an isolated virtual environment
# and manages the Ollama service for the qwen2.5:0.5b model

Write-Host "================================" -ForegroundColor Cyan
Write-Host "LangRover - Complete Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create virtual environment
Write-Host "Step 1: Creating virtual environment..." -ForegroundColor Yellow
if (-Not (Test-Path "venv")) {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created in ./venv" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Step 2: Activate virtual environment
Write-Host "`nStep 2: Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Step 3: Upgrade pip
Write-Host "`nStep 3: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip 2>&1 | Out-Null
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Step 4: Install dependencies in venv ONLY (not global)
Write-Host "`nStep 4: Installing project dependencies (venv only)..." -ForegroundColor Yellow
pip install -q -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed in ./venv ONLY" -ForegroundColor Green
    Write-Host "  (NOT installed globally)" -ForegroundColor Gray
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 5: Check Ollama installation
Write-Host "`nStep 5: Checking Ollama installation..." -ForegroundColor Yellow
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($null -eq $ollama) {
    Write-Host "⚠ Ollama not found in PATH" -ForegroundColor Yellow
    Write-Host "  Install from: https://ollama.ai" -ForegroundColor Gray
} else {
    Write-Host "✓ Ollama is installed" -ForegroundColor Green
    
    # Step 6: Check if qwen2.5:0.5b model is available
    Write-Host "`nStep 6: Checking for qwen2.5:0.5b model..." -ForegroundColor Yellow
    $models = ollama list 2>&1
    if ($models -match "qwen2.5:0.5b") {
        Write-Host "✓ qwen2.5:0.5b model is available" -ForegroundColor Green
    } else {
        Write-Host "⚠ qwen2.5:0.5b model not found locally" -ForegroundColor Yellow
        Write-Host "  Pulling model (this may take a few minutes)..." -ForegroundColor Gray
        ollama pull qwen2.5:0.5b
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ qwen2.5:0.5b model pulled successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to pull qwen2.5:0.5b model" -ForegroundColor Red
        }
    }
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  LLM Provider: Ollama (default)" -ForegroundColor Gray
Write-Host "  Model: qwen2.5:0.5b" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start Ollama service (in separate terminal):"
Write-Host "   ollama serve" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run the robot simulation:"
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Virtual environment is active. All dependencies are installed in ./venv only." -ForegroundColor Green
