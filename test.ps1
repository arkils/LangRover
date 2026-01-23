# LangRover - Test Full Robot System
# This script runs the comprehensive test suite
# Dependencies are installed in venv only

Write-Host "================================" -ForegroundColor Cyan
Write-Host "LangRover - Full System Test" -ForegroundColor Cyan
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

# Install dependencies in venv only
Write-Host ""
Write-Host "Step 2: Installing dependencies in venv..." -ForegroundColor Yellow
& ".\venv\Scripts\pip.exe" install -q -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully in venv" -ForegroundColor Green
} else {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Run the test
Write-Host ""
Write-Host "Step 3: Running comprehensive robot system test..." -ForegroundColor Yellow
Write-Host ""

python test_full_robot.py
$testExitCode = $LASTEXITCODE

Write-Host ""
if ($testExitCode -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Tests failed" -ForegroundColor Red
}

exit $testExitCode
