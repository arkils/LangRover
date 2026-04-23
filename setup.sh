#!/bin/bash
# LangRover Setup Script for Linux/macOS
# This script sets up the project with an isolated virtual environment

echo "================================"
echo "LangRover - Project Setup"
echo "================================"
echo ""

# Step 1: Install Raspberry Pi system dependencies
IS_PI=false
if [ -f /etc/rpi-issue ] || grep -qi "raspberry" /proc/device-tree/model 2>/dev/null; then
    IS_PI=true
fi

if [ "$IS_PI" = true ]; then
    echo "Step 1: Installing Raspberry Pi system dependencies..."
    sudo apt-get install -y \
        libcap-dev \
        python3-libcamera \
        python3-picamera2 \
        python3-kms++
    if [ $? -eq 0 ]; then
        echo "✓ System dependencies installed"
    else
        echo "✗ Failed to install system dependencies (run: sudo apt-get update first)"
        exit 1
    fi

    # Install Ollama if not already installed
    if ! command -v ollama &> /dev/null; then
        echo ""
        echo "  Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        if [ $? -eq 0 ]; then
            echo "✓ Ollama installed"
        else
            echo "✗ Failed to install Ollama"
            exit 1
        fi
    else
        echo "✓ Ollama already installed"
    fi
else
    echo "Step 1: Skipping Pi system dependencies (not a Raspberry Pi)"
fi
echo ""

# Step 2: Create virtual environment
echo "Step 2: Creating virtual environment..."
# On Raspberry Pi, use --system-site-packages so libcamera/picamera2 (apt packages) are accessible.
VENV_FLAGS=""
if [ "$IS_PI" = true ]; then
    echo "  (Raspberry Pi detected — using --system-site-packages for libcamera/picamera2 support)"
    VENV_FLAGS="--system-site-packages"
fi
if [ ! -d "venv" ]; then
    python3 -m venv venv $VENV_FLAGS
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created in ./venv"
    else
        echo "✗ Failed to create virtual environment"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists"
fi

# Step 3: Activate virtual environment
echo ""
echo "Step 3: Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Step 4: Upgrade pip
echo ""
echo "Step 4: Upgrading pip..."
python -m pip install --upgrade pip
echo "✓ pip upgraded"

# Step 5: Install dependencies in venv ONLY (not global)
echo ""
echo "Step 5: Installing project dependencies (venv only)..."
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed in ./venv ONLY"
    echo "  (NOT installed globally)"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Step 6: Pre-download YOLO model weights (Pi only — saves time on first robot run)
if [ "$IS_PI" = true ]; then
    echo ""
    echo "Step 6: Pre-downloading YOLO model weights..."
    python -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); print('✓ YOLOv8n weights ready')" 2>&1 | grep -E '✓|ERROR|error' || true
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Copy and edit the environment file:"
echo "   cp .env.example .env   # or edit .env directly"
echo ""
echo "2. Set your OpenAI API key (only if using OpenAI):"
echo "   export OPENAI_API_KEY='sk-...'"
echo ""
echo "3. Run the robot:"
echo "   source venv/bin/activate && python main.py"
echo ""
echo "Virtual environment is active. All dependencies are installed in ./venv only."
