# LangRover - Quick Run Script for Windows PowerShell
# This script handles the complete startup process:
# 1. Activates the virtual environment
# 2. Checks/starts Ollama service
# 3. Runs the project

param(
    [switch]$NoOllama = $false,  # Skip Ollama checks if set
    [string]$Model = ""           # Override model (e.g., -Model "mistral")
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "LangRover - Startup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-Not (Test-Path "venv")) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "  Run: .\setup.ps1" -ForegroundColor Gray
    exit 1
}

# Activate virtual environment
Write-Host "Step 1: Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "Virtual environment activated" -ForegroundColor Green

# Check Ollama (if not skipped)
if (-Not $NoOllama) {
    Write-Host ""
    Write-Host "Step 2: Checking Ollama service..." -ForegroundColor Yellow
    
    # Check if Ollama is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Ollama is running at localhost:11434" -ForegroundColor Green
    } catch {
        Write-Host "Ollama is not running" -ForegroundColor Yellow
        
        # Try to start Ollama
        Write-Host "  Attempting to start Ollama service..." -ForegroundColor Gray
        $ollama = Get-Command ollama -ErrorAction SilentlyContinue
        
        if ($null -eq $ollama) {
            Write-Host "Ollama not found in PATH" -ForegroundColor Red
            Write-Host "  Install from: https://ollama.ai" -ForegroundColor Gray
            exit 1
        }
        
        # Start Ollama in a new PowerShell window
        Write-Host "  Starting 'ollama serve' in new window..." -ForegroundColor Gray
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve"
        
        # Wait for Ollama to start
        Write-Host "  Waiting 5 seconds for Ollama to start..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
        
        # Verify connection
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
            Write-Host "Ollama started successfully" -ForegroundColor Green
        } catch {
            Write-Host "Could not connect to Ollama after startup" -ForegroundColor Red
            Write-Host "  Please manually run 'ollama serve' in a separate terminal" -ForegroundColor Gray
            exit 1
        }
    }
    
    # Check model availability
    Write-Host ""
    Write-Host "Step 3: Checking model availability..." -ForegroundColor Yellow
    $models = ollama list 2>&1
    $modelToUse = if ($Model) { $Model } else { "gemma3:270m" }
    
    if ($models -match [regex]::Escape($modelToUse)) {
        Write-Host "Model '$modelToUse' is available" -ForegroundColor Green
    } else {
        Write-Host "Model '$modelToUse' not found locally" -ForegroundColor Yellow
        Write-Host "  Pulling model (this may take a few minutes)..." -ForegroundColor Gray
        ollama pull $modelToUse
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Model '$modelToUse' pulled successfully" -ForegroundColor Green
        } else {
            Write-Host "Failed to pull model '$modelToUse'" -ForegroundColor Red
            exit 1
        }
    }
}

# Run the project
Write-Host ""
Write-Host "Step 4: Starting LangRover..." -ForegroundColor Yellow
Write-Host ""

if ($Model) {
    $env:OLLAMA_MODEL = $Model
}

python main.py
