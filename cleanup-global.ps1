# LangRover - Cleanup Global Python Packages
# This script removes LangChain and related packages from global Python
# Ensures ALL dependencies are isolated to the project's venv/ only

Write-Host "================================" -ForegroundColor Cyan
Write-Host "LangRover - Global Cleanup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# List of packages to remove from global Python
$packagesToRemove = @(
    "langchain",
    "langchain-openai",
    "langchain-community",
    "langchain-core",
    "langchain-text-splitters",
    "pydantic",
    "python-dotenv",
    "openai",
    "tiktoken",
    "aiohttp",
    "dataclasses-json",
    "sqlalchemy",
    "langsmith"
)

Write-Host "This will remove the following packages from GLOBAL Python:" -ForegroundColor Yellow
$packagesToRemove | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
Write-Host ""

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "yes") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Uninstalling from global Python..." -ForegroundColor Yellow

foreach ($package in $packagesToRemove) {
    Write-Host "  Removing $package..." -ForegroundColor Gray
    python -m pip uninstall -y $package 2>&1 | Out-Null
}

Write-Host ""
Write-Host "Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Virtual environment has ALL dependencies:"
Write-Host "   .\venv\Scripts\python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. To verify global Python is clean:"
Write-Host "   python -m pip list | findstr /i langchain" -ForegroundColor Gray
Write-Host ""
Write-Host "All LangChain libraries are now ONLY in ./venv/" -ForegroundColor Green
