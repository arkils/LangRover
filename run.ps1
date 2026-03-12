# LangRover - Quick Run Script for Windows PowerShell
# This script handles the complete startup process:
# 1. Activates the virtual environment
# 2. Checks/starts Ollama service
# 3. Runs the project

param(
    [switch]$NoOllama = $false,  # Skip Ollama checks if set
    [string]$Model = "",          # Override model (e.g., -Model "mistral")
    [switch]$Vision = $false      # Install and enable real YOLO vision
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

# Detect LLM provider from .env or environment
$llmProvider = $env:LLM_PROVIDER
if (-Not $llmProvider -and (Test-Path ".env")) {
    $llmProvider = (Get-Content ".env" | Where-Object { $_ -match "^LLM_PROVIDER\s*=" } | Select-Object -First 1) -replace "^LLM_PROVIDER\s*=\s*", ""
}
if (-Not $llmProvider) { $llmProvider = "ollama" }

Write-Host "LLM Provider: $llmProvider" -ForegroundColor Cyan

# Check Ollama (only when provider is ollama and not skipped)
if ($llmProvider -eq "ollama" -and -Not $NoOllama) {
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
    $modelToUse = if ($Model) { $Model } else { "qwen2.5:0.5b" }
    
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
Write-Host "Step 4: Checking vision dependencies..." -ForegroundColor Yellow
if ($Vision) {
    Write-Host "  Installing YOLO + OpenCV (this may take a moment)..." -ForegroundColor Gray
    pip install -q ultralytics opencv-python
    if ($LASTEXITCODE -eq 0) {
        Write-Host "YOLO + OpenCV installed" -ForegroundColor Green
    } else {
        Write-Host "Failed to install vision dependencies" -ForegroundColor Red
        exit 1
    }
    $env:USE_REAL_VISION = "true"
    Write-Host "Real YOLO vision enabled" -ForegroundColor Green
} else {
    $useRealVision = $env:USE_REAL_VISION
    if (-Not $useRealVision -and (Test-Path ".env")) {
        $useRealVision = (Get-Content ".env" | Where-Object { $_ -match "^USE_REAL_VISION\s*=" } | Select-Object -First 1) -replace "^USE_REAL_VISION\s*=\s*", ""
    }
    if ($useRealVision -eq "true") {
        Write-Host "USE_REAL_VISION=true - verifying ultralytics is installed..." -ForegroundColor Gray
        $check = venv\Scripts\python.exe -c "import ultralytics" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ultralytics not found. Run: .\run.ps1 -Vision  (or pip install ultralytics opencv-python)" -ForegroundColor Yellow
        } else {
            Write-Host "YOLO ready" -ForegroundColor Green
        }
    } else {
        Write-Host "Using mock vision (set USE_REAL_VISION=true in .env or pass -Vision to enable YOLO)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Step 5: Starting LangRover..." -ForegroundColor Yellow
Write-Host ""

if ($Model) {
    $env:OLLAMA_MODEL = $Model
}

python main.py
