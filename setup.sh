#!/bin/bash
# LangRover Setup Script for Linux/macOS
# This script sets up the project with an isolated virtual environment

echo "================================"
echo "LangRover - Project Setup"
echo "================================"
echo ""

# Step 1: Create virtual environment
echo "Step 1: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created in ./venv"
    else
        echo "✗ Failed to create virtual environment"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists"
fi

# Step 2: Activate virtual environment
echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Step 3: Upgrade pip
echo ""
echo "Step 3: Upgrading pip..."
python -m pip install --upgrade pip
echo "✓ pip upgraded"

# Step 4: Install dependencies in venv ONLY (not global)
echo ""
echo "Step 4: Installing project dependencies (venv only)..."
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed in ./venv ONLY"
    echo "  (NOT installed globally)"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Set your OpenAI API key:"
echo "   export OPENAI_API_KEY='sk-...'"
echo ""
echo "2. Run the robot simulation:"
echo "   python main.py"
echo ""
echo "Virtual environment is active. All dependencies are installed in ./venv only."
