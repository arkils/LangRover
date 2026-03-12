#!/bin/bash
# LangRover - Quick Run Script for Linux/macOS
# This script handles the complete startup process:
# 1. Activates the virtual environment
# 2. Checks/starts Ollama service
# 3. Runs the project

NO_OLLAMA=false
MODEL=""
VISION=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-ollama)
            NO_OLLAMA=true
            shift
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --vision)
            VISION=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo "================================"
echo "LangRover - Startup"
echo "================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "✗ Virtual environment not found!"
    echo "  Run: ./setup.sh"
    exit 1
fi

# Activate virtual environment
echo "Step 1: Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Check Ollama (if not skipped)
if [ "$NO_OLLAMA" = false ]; then
    echo ""
    echo "Step 2: Checking Ollama service..."
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is running at localhost:11434"
    else
        echo "⚠ Ollama is not running"
        
        # Check if Ollama is installed
        if ! command -v ollama &> /dev/null; then
            echo "✗ Ollama not found in PATH"
            echo "  Install from: https://ollama.ai"
            exit 1
        fi
        
        # Start Ollama in the background
        echo "  Starting 'ollama serve' in background..."
        ollama serve > /tmp/ollama.log 2>&1 &
        
        # Wait for Ollama to start
        echo "  Waiting 5 seconds for Ollama to start..."
        sleep 5
        
        # Verify connection
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✓ Ollama started successfully"
        else
            echo "✗ Could not connect to Ollama after startup"
            echo "  Please manually run 'ollama serve' in a separate terminal"
            exit 1
        fi
    fi
    
    # Check model availability
    echo ""
    echo "Step 3: Checking model availability..."
    MODEL_TO_USE=${MODEL:-"qwen2.5:0.5b"}
    
    if ollama list 2>&1 | grep -q "^${MODEL_TO_USE}"; then
        echo "✓ Model '$MODEL_TO_USE' is available"
    else
        echo "⚠ Model '$MODEL_TO_USE' not found locally"
        echo "  Pulling model (this may take a few minutes)..."
        ollama pull "$MODEL_TO_USE"
        if [ $? -eq 0 ]; then
            echo "✓ Model '$MODEL_TO_USE' pulled successfully"
        else
            echo "✗ Failed to pull model '$MODEL_TO_USE'"
            exit 1
        fi
    fi
fi

# Vision dependencies
echo ""
echo "Step 4: Checking vision dependencies..."
if [ "$VISION" = true ]; then
    echo "  Installing YOLO + OpenCV (this may take a moment)..."
    pip install -q ultralytics opencv-python
    if [ $? -eq 0 ]; then
        echo "✓ YOLO + OpenCV installed"
    else
        echo "✗ Failed to install vision dependencies"
        exit 1
    fi
    export USE_REAL_VISION=true
    echo "✓ Real YOLO vision enabled"
else
    USE_REAL_VISION_VAL=${USE_REAL_VISION:-$(grep -m1 '^USE_REAL_VISION=' .env 2>/dev/null | cut -d= -f2)}
    if [ "$USE_REAL_VISION_VAL" = "true" ]; then
        echo "  USE_REAL_VISION=true — verifying ultralytics is installed..."
        if ! python -c "import ultralytics" 2>/dev/null; then
            echo "⚠ ultralytics not found. Run: ./run.sh --vision  (or pip install ultralytics opencv-python)"
        else
            echo "✓ YOLO ready"
        fi
    else
        echo "  Using mock vision (pass --vision or set USE_REAL_VISION=true in .env to enable YOLO)"
    fi
fi

# Run the project
echo ""
echo "Step 5: Starting LangRover..."
echo ""

if [ -n "$MODEL" ]; then
    export OLLAMA_MODEL=$MODEL
fi

python main.py
