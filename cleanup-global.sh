#!/bin/bash
# LangRover - Cleanup Global Python Packages
# This script removes LangChain and related packages from global Python
# Ensures ALL dependencies are isolated to the project's venv/ only

echo "================================"
echo "LangRover - Global Cleanup"
echo "================================"
echo ""

# List of packages to remove from global Python
PACKAGES=(
    "langchain"
    "langchain-openai"
    "langchain-community"
    "langchain-core"
    "langchain-text-splitters"
    "pydantic"
    "python-dotenv"
    "openai"
    "tiktoken"
    "aiohttp"
    "dataclasses-json"
    "sqlalchemy"
    "langsmith"
)

echo "This will remove the following packages from GLOBAL Python:"
for package in "${PACKAGES[@]}"; do
    echo "  - $package"
done
echo ""

read -p "Continue? (y/n) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Uninstalling from global Python..."

for package in "${PACKAGES[@]}"; do
    echo "  Removing $package..."
    pip uninstall -y "$package" 2>&1 > /dev/null
done

echo ""
echo "Cleanup complete!"
echo ""
echo "Next steps:"
echo "1. Virtual environment has ALL dependencies:"
echo "   ./venv/bin/python main.py"
echo ""
echo "2. To verify global Python is clean:"
echo "   python -m pip list | grep langchain"
echo ""
echo "All LangChain libraries are now ONLY in ./venv/"
