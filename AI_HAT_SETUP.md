# Raspberry Pi AI HAT+ / AI HAT+ 2 Setup Guide

Complete guide for setting up the Raspberry Pi AI HAT+ or AI HAT+ 2 for local AI model inference on LangRover.

## What is the AI HAT+?

The **Raspberry Pi AI HAT+** and **AI HAT+ 2** are hardware accelerator add-ons for Raspberry Pi 5 that provide edge AI acceleration via Hailo neural processing units (NPUs).

### AI HAT+ Specifications
- **13 TOPS** or **26 TOPS** (Tera Operations Per Second) AI performance
- **Hailo-8L** (13 TOPS) or **Hailo-8** (26 TOPS) AI processor
- Shares Raspberry Pi 5 memory
- Best for: Object detection, robotics, vision workloads
- **Does NOT support LLMs** (uses Pi memory only)

### AI HAT+ 2 Specifications (NEW)
- **40 TOPS** inference performance
- **Hailo-10H** AI processor with **8GB onboard SDRAM**
- **Full LLM and VLM support** (local LLMs up to ~6 billion parameters)
- Includes dedicated heatsink
- Best for: LLMs, VLMs, generative AI, everything AI HAT+ does plus more
- **RECOMMENDED for LangRover with local LLM support**

### Key Differences

| Feature | AI HAT+ | AI HAT+ 2 |
|---------|---------|-----------|
| TOPS Performance | 13-26 | 40 |
| Accelerator Chip | Hailo-8L/8 | Hailo-10H |
| Onboard Memory | None (uses Pi RAM) | 8GB SDRAM |
| LLM Support | ❌ No | ✅ Yes |
| VLM Support | ❌ No | ✅ Yes |
| Max LLM Size | N/A | ~6B parameters |
| Heatsink | Optional | Included, Recommended |

## Why Use AI HAT+/2 for LangRover?

1. **Hardware-Accelerated Inference**: Offload AI workloads from CPU
2. **Local AI Processing**: No cloud dependencies
3. **Low Latency**: Real-time decision-making
4. **Privacy**: All data stays on device
5. **Cost Effective**: No API usage fees
6. **AI HAT+ 2 Bonus**: Run full LLMs like TinyLlama, Phi, Llama locally

---

## Hardware Installation

### Prerequisites

**You will need**:
- Raspberry Pi 5 (running latest Raspberry Pi OS Trixie)
- AI HAT+ or AI HAT+ 2
- Phillips crosshead screwdriver
- GPIO stacking header (included)
- PCIe ribbon cable (included)
- Threaded spacers (included)
- **HIGHLY RECOMMENDED**: Raspberry Pi Active Cooler (fan heatsink)
- **For AI HAT+ 2**: Additional heatsink (included with HAT+ 2)

### Step 0: Update Raspberry Pi OS

Run BEFORE installing HAT:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo rpi-eeprom-update -a
sudo reboot
```

### Step 1: Mount Active Cooler (Recommended)

**ESPECIALLY for AI HAT+ 2 with heavy workloads.**

1. Power OFF Raspberry Pi 5
2. Remove protective paper from thermal pads on cooler
3. Align two white push pins with dedicated heatsink holes on Pi
4. Press cooler down until push pins click
5. Plug fan JST connector into fan socket on Raspberry Pi 5

### Step 2: Mount AI HAT+ 2 Heatsink (if using AI HAT+ 2)

**Skip this step if you have AI HAT+ (not 2).**

1. Remove protective paper from thermal pads on heatsink
2. Align two black push pins to two diagonal heatsink holes on HAT+ 2
3. Evenly press pins down until they click

**⚠️ NOTE**: Don't remove heatsink after installation (can damage push pins)

### Step 3: Mount the AI HAT (Both AI HAT+ and AI HAT+ 2)

1. Power OFF Raspberry Pi 5
2. **Fit the spacers**: Attach four threaded spacers to yellow holes on Pi using four longer screws
3. **Connect GPIO stacking header**: Align and press firmly until fully seated
4. **Disconnect PCIe ribbon cable from HAT**: Slide retaining clips outward, gently pull cable out
5. **Insert PCIe ribbon into Pi**:
   - Slide retaining clips upward on Pi's PCIe connector
   - Insert ribbon cable (metallic contacts face inward toward USB ports)
   - Push retaining clips back in from both sides
6. **Mount the AI HAT**: Align mounting holes with spacers, use four short screws to secure
7. **Connect PCIe ribbon to HAT**:
   - Slide retaining clips outward on HAT's PCIe connector
   - Insert ribbon cable
   - Push retaining clips back in from both sides

### Step 4: Verify Installation

```bash
# Check PCIe device detection
lspci

# Should show Hailo device (Myriad or similar)

# Check Hailo firmware
hailortcli fw-control identify
```

Expected output:
```
Identifying board
Control Protocol Version: 2
Firmware Version: 4.x.x
Board Name: Hailo-8L (or Hailo-10H for AI HAT+ 2)
```

---

## Software Setup

### Step 1: Update System

```bash
# Update Raspberry Pi OS
sudo apt update
sudo apt upgrade -y

# Install required dependencies
sudo apt install -y python3-pip python3-venv cmake build-essential
```

### Step 2: Install Hailo SDK

```bash
# Install Hailo runtime, tools, and libraries
sudo apt install -y hailo-all

# Verify Hailo device and firmware
hailortcli fw-control identify

# Check available models
hailortcli model-zoo list
```

### Step 3: Install Python Libraries

```bash
# Activate virtual environment
source venv/bin/activate

# Install Hailo Python runtime
pip install hailort

# Install Hailo Model Zoo (pre-optimized models)
pip install hailo-model-zoo

# Install common AI frameworks
pip install torch torchvision  # PyTorch
pip install tensorflow         # TensorFlow
pip install onnx               # ONNX support
```

---

## Running Models on Hailo

### Option 1: Use Pre-Optimized Models from Hailo Model Zoo

```bash
# List available models
hailortcli model-zoo list

# Download and optimize a model for your HAT
hailortcli model-zoo download --model yolov5s --target-platform hailo8l

# Run inference
hailortcli model-zoo run --model yolov5s --target-platform hailo8l --image input.jpg
```

### Option 2: Vision Models with Picamera2 Integration

Picamera2 automatically uses Hailo for supported models:

```python
from picamera2 import Picamera2
from picamera2.postprocess.controls import ContrastControl
import numpy as np

picam2 = Picamera2()

# Configure for object detection with Hailo acceleration
config = picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)},
    controls={"FrameRate": 30},
)
picam2.start()

# Hailo NPU automatically accelerates vision models
while True:
    frame = picam2.capture_array()
    # Detection happens on Hailo NPU
```

### Option 3: LLMs on AI HAT+ 2 (RECOMMENDED)

**AI HAT+ 2 ONLY** - AI HAT+ does not support LLMs.

#### Best Models for AI HAT+ 2

| Model | Size | Speed on Pi 5 | Quant | Use Case |
|-------|------|--------------|-------|----------|
| **TinyLlama 1.1B** | 1.1B | Fast | Q4_K_M | Real-time decisions |
| **Phi-2 2.7B** | 2.7B | Medium | Q4_K_M | Balanced reasoning |
| **Llama 3.2 1B** | 1B | Fast | Q4_K_M | Modern, efficient |
| **Mistral 7B** | 7B | Slower | Q3_K_M | Complex tasks |
| **Qwen 1.8B** | 1.8B | Fast | Q4_K_M | Multilingual |

#### Using llama.cpp with Hailo

```bash
# Clone and build llama.cpp with Hailo support
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build with Hailo support (if available)
make

# Download a model
cd models
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Run with Hailo (automatic detection)
../main -m tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
        -p "You are an autonomous robot assistant." \
        -n 100 -e
```

#### Using with Ollama (AI HAT+ 2)

```bash
# Install Ollama on Raspberry Pi
curl -fsSL https://ollama.com/install.sh | sh

# Ollama automatically detects and uses Hailo NPU
ollama pull tinyllama

# Run with Hailo (automatic)
ollama run tinyllama
```

#### Using with Transformers (AI HAT+ 2)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load a small quantized model
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load with INT8 quantization (Hailo friendly)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    load_in_8bit=True,
)

# Generate text (Hailo accelerates if model is optimized)
inputs = tokenizer("You are a helpful robot. What should you do?", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0]))
```

### Option 4: ONNX Models with Hailo Optimizer

```bash
# Download ONNX model
wget https://example.com/model.onnx

# Optimize for Hailo
hailortcli quantize --input-model model.onnx \
                    --target-platform hailo10h \
                    --output model-optimized.har

# Use in Python
from hailort import InferenceContext

context = InferenceContext.create_context(model_file="model-optimized.har")
```

---

## Integration with LangRover

### Configuration for Your HAT

Update `config.py` to specify which HAT you have:

```python
# config.py

# Hailo AI HAT+ settings
LLM_PROVIDER = "hailo"  # or "ollama" or "openai"

# AI HAT+ (no LLM support)
HAILO_DEVICE = "hailo8l"  # or "hailo8" for 26-TOPS variant

# AI HAT+ 2 (full LLM support)
HAILO_DEVICE = "hailo10h"  # Recommended for LLM support

# LLM configuration for AI HAT+ 2
HAILO_MODEL_PATH = "/home/pi/models/tinyllama-1.1b.Q4_K_M.gguf"
HAILO_CONTEXT_LENGTH = 1024
HAILO_MAX_TOKENS = 100
HAILO_TEMPERATURE = 0.7

# Alternative: Use Ollama with Hailo
# LLM_PROVIDER = "ollama"
# OLLAMA_MODEL = "tinyllama"
```

### Update `models/llm.py` for Hailo Support

```python
def create_llm(config):
    """Create LLM instance based on configuration."""
    provider = config.LLM_PROVIDER.lower()
    
    if provider == "hailo":
        # For AI HAT+ 2 with local LLM support
        from langchain_community.llms import LlamaCpp
        
        return LlamaCpp(
            model_path=config.HAILO_MODEL_PATH,
            n_ctx=config.HAILO_CONTEXT_LENGTH,
            n_batch=512,
            n_gpu_layers=0,  # Hailo handles acceleration
            temperature=config.HAILO_TEMPERATURE,
            max_tokens=config.HAILO_MAX_TOKENS,
            verbose=False,
        )
    
    elif provider == "ollama":
        from langchain_community.llms import Ollama
        
        return Ollama(
            model=config.OLLAMA_MODEL,
            base_url="http://localhost:11434",
        )
    
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model_name="gpt-4",
            api_key=config.OPENAI_API_KEY,
        )
```

---

## Model Recommendations for Robot Use

### Object Detection (All HAT Models)

Works on **AI HAT+** and **AI HAT+ 2**:

```python
# YOLOv5 object detection with Hailo
from hailort import InferenceContext
import numpy as np

# Load optimized YOLO model
context = InferenceContext.create_context(
    model_file="/path/to/yolov5s-hailo.har"
)

# Run inference on camera frame
def detect_objects(frame):
    results = context.infer([frame])
    return results

# Detect people with safety protocol
detections = detect_objects(camera_frame)
if any(d["class"] == "person" for d in detections):
    robot.stop()  # Safety!
```

### LLM Support (AI HAT+ 2 ONLY)

| Model | Size | Speed | Best For | Notes |
|-------|------|-------|----------|-------|
| **TinyLlama 1.1B** | 1.1B | 25-40 tok/s | Real-time decisions | Very fast |
| **Phi-2 2.7B** | 2.7B | 15-25 tok/s | Better reasoning | Balanced |
| **Llama 3.2 1B** | 1B | 25-35 tok/s | Modern arch | Efficient |
| **Mistral 7B** | 7B | 5-10 tok/s | Complex tasks | Slow but capable |
| **Qwen 1.8B** | 1.8B | 20-30 tok/s | Multilingual | Good variety |

### Download & Test Models

```bash
# Create models directory
mkdir -p ~/models && cd ~/models

# Download GGUF models from Hugging Face
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Test with llama.cpp
~/llama.cpp/main -m tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
                 -p "What is the robot's next action?" -n 50

# Benchmark token generation speed
time ~/llama.cpp/main -m tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
                      -p "Test prompt." -n 100 > /dev/null
```

### Quantization Explained

For **AI HAT+ 2** LLM inference:
- **Q2_K**: Ultra-fast, lower quality (experimental)
- **Q3_K_M**: Fast, acceptable quality
- **Q4_K_M**: **RECOMMENDED** - Best balance
- **Q5_K_M**: Better quality, slower
- **Q6_K**: High quality, quite slow
- **Q8_0**: Full precision (uses more VRAM)

---

## Performance Tuning

### Thermal Management (Important for AI HAT+ 2)

**AI HAT+ 2** requires active cooling:

```bash
# Check Hailo temperature
watch -n 1 'hailortcli fw-control identify | grep -i temp'

# Monitor Pi temperature
watch -n 1 'vcgencmd measure_temp'

# Both should stay below 80°C under load
```

**Recommendations**:
- Always use **Active Cooler on Pi 5** (included in mounting kit)
- Always use **AI HAT+ 2 heatsink** (included with HAT+ 2)
- Ensure good airflow around robot
- Monitor temperatures during development

### Optimize for Speed (Real-time Inference)

```bash
# CPU governor for performance
sudo apt install cpufrequtils
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable CPU throttling (for testing only)
sudo cpufreq-set -g performance

# Increase swap for model loading
sudo dphys-swapfile swapoff
echo "CONF_SWAPSIZE=4096" | sudo tee /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Optimize for Power (Battery Operation)

```bash
# Use smaller quantization
# Q3_K_M instead of Q5_K_M
# Reduce context length
# Limit max tokens per generation

# Power-efficient CPU governor
echo "powersave" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Benchmark Your Setup

```bash
# benchmark_hailo.py
import time
from langchain_community.llms import LlamaCpp

model = LlamaCpp(
    model_path="/home/pi/models/tinyllama-1.1b.Q4_K_M.gguf",
    n_ctx=1024,
    temperature=0.7,
    max_tokens=100,
)

prompts = [
    "What object is in front of the robot?",
    "Should the robot move forward or turn?",
    "Describe the environment.",
]

print("Benchmarking LLM on AI HAT+ 2...")
print("-" * 60)

for prompt in prompts:
    start = time.time()
    response = model(prompt)
    elapsed = time.time() - start
    
    tokens = len(response.split())
    token_rate = tokens / elapsed
    
    print(f"Prompt: {prompt}")
    print(f"Tokens: {tokens} | Time: {elapsed:.2f}s | Rate: {token_rate:.1f} tok/s")
    print(f"Response: {response[:100]}...")
    print("-" * 60)

# Expected speeds on Pi 5 + AI HAT+ 2
# TinyLlama 1.1B Q4: 30-40 tok/s
# Phi-2 2.7B Q4: 15-25 tok/s
```

---

## Alternative: Run Ollama with Hailo

Ollama simplifies model management and automatically uses Hailo when available:

```bash
# Install Ollama on Raspberry Pi OS
curl -fsSL https://ollama.com/install.sh | sh

# Ollama automatically detects Hailo NPU
# Pull a model
ollama pull tinyllama      # 1.1B model
ollama pull phi            # 2.7B model
ollama pull neural-chat    # 7B model

# Run Ollama server (listens on port 11434)
ollama serve
```

**In another terminal**:

```bash
# Chat with model (auto-uses Hailo)
ollama run tinyllama

# Or use REST API from LangRover
curl http://localhost:11434/api/generate \
  -d '{"model":"tinyllama","prompt":"What should the robot do?"}'
```

**Integration with LangRover**:

```python
# config.py
LLM_PROVIDER = "ollama"
OLLAMA_MODEL = "tinyllama"
OLLAMA_BASE_URL = "http://localhost:11434"

# models/llm.py
from langchain_community.llms import Ollama

def create_llm(config):
    return Ollama(
        model=config.OLLAMA_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0.7,
    )
```

---

## Troubleshooting

### HAT Not Detected

```bash
# Check PCIe device
lspci | grep Hailo

# If nothing shows, verify:
# 1. HAT is firmly seated
# 2. GPIO stacking header is inserted
# 3. PCIe ribbon cable is fully inserted (both ends)
# 4. Retaining clips are pushed in on both ends
# 5. Pi is fully powered (check red LED)

# Reboot after reseating
sudo reboot

# Check Hailo detection again
hailortcli fw-control identify
```

### Hailo SDK Installation Issues

```bash
# Reinstall Hailo packages
sudo apt remove -y hailo-all
sudo apt install -y hailo-all

# Install specific Python package
pip install --upgrade hailort

# Check if SDK is working
python3 -c "import hailort; print(hailort.__version__)"
```

### Model Loading Fails (AI HAT+ 2)

```bash
# Verify model file exists and is readable
ls -lh ~/models/*.gguf
file ~/models/tinyllama-1.1b.Q4_K_M.gguf

# Check available memory
free -h

# If out of memory:
# - Use smaller model (TinyLlama vs Phi-2)
# - Reduce context length (1024 vs 2048)
# - Reduce quantization (Q3 vs Q4)
```

### Slow Inference

```bash
# Verify Hailo is being used
hailortcli fw-control identify

# Check CPU usage during inference
top -b -n 1 | head -20

# Low GPU/Hailo utilization means CPU bottleneck
# Solutions:
# - Use simpler model
# - Reduce batch size
# - Profile with Python cProfile
```

### Out of Memory / Swap Issues

```bash
# Check current memory
free -h

# Increase swap
sudo dphys-swapfile swapoff
echo "CONF_SWAPSIZE=4096" | sudo tee /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Monitor during operation
watch -n 1 free -h
```

### AI HAT+ 2 Overheating

```bash
# Monitor temperature
vcgencmd measure_temp
watch -n 1 'hailortcli fw-control identify | grep -i temperature'

# If temp > 80°C:
# 1. Ensure Active Cooler is installed on Pi 5
# 2. Ensure AI HAT+ 2 heatsink is installed
# 3. Check thermal pads are in contact (no gaps)
# 4. Improve airflow around robot
# 5. Reduce workload (smaller model, fewer requests)
```

---

## Production Configuration

### Recommended Settings for LangRover

**For AI HAT+ (Vision Only)**:
```python
# config.py for Pi 5 + AI HAT+ (13 TOPS)
LLM_PROVIDER = "openai"  # Use cloud API for LLMs
HAILO_DEVICE = "hailo8l"
```

**For AI HAT+ 2 (Vision + LLM)**:
```python
# config.py for Pi 5 + AI HAT+ 2 (40 TOPS + 8GB SDRAM)
LLM_PROVIDER = "hailo"  # Run local LLM
HAILO_DEVICE = "hailo10h"
HAILO_MODEL_PATH = "/home/pi/models/tinyllama-1.1b.Q4_K_M.gguf"
HAILO_CONTEXT_LENGTH = 1024      # Balanced for speed
HAILO_MAX_TOKENS = 100           # Short robot decisions
HAILO_TEMPERATURE = 0.7          # Balanced creativity
USE_REAL_CAMERA = True           # Use Pi Camera
USE_REAL_SENSORS = True          # Use ultrasonic sensors
USE_GPIO_ACTIONS = True          # Real motor control
```

### Auto-Start on Boot

```bash
# Create systemd service
sudo nano /etc/systemd/system/langrover.service
```

```ini
[Unit]
Description=LangRover Autonomous Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/LangRover
Environment="LLM_PROVIDER=hailo"
Environment="USE_GPIO_ACTIONS=true"
Environment="USE_REAL_SENSORS=true"
Environment="USE_REAL_CAMERA=true"
ExecStart=/home/pi/LangRover/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable langrover
sudo systemctl start langrover

# Check status
sudo systemctl status langrover

# View logs
sudo journalctl -u langrover -f
```

## Summary

### AI HAT+ (13 or 26 TOPS)
✅ Vision inference and object detection
✅ Real-time edge processing
✅ Robotics and automation
❌ No LLM support (requires shared Pi memory)

### AI HAT+ 2 (40 TOPS, Recommended)
✅ Everything AI HAT+ does
✅ **Local LLM support** (up to ~6B parameters)
✅ VLM (Vision-Language Model) support
✅ **8GB onboard SDRAM** (dedicated for AI)
✅ Fully autonomous operation without cloud
⚠️ Requires active thermal management (heatsink included)

---

## Quick Start Commands

### Hardware Setup
```bash
# Step 1: Physical installation
# See Hardware Installation section above

# Step 2: Update system
sudo apt update && sudo apt full-upgrade -y

# Step 3: Install Hailo SDK
sudo apt install -y hailo-all

# Step 4: Verify installation
hailortcli fw-control identify
```

### For AI HAT+ 2 (Local LLM)
```bash
# Step 5: Install tools
pip install hailort hailo-model-zoo ollama

# Step 6: Download model
ollama pull tinyllama

# Step 7: Start Ollama
ollama serve

# Step 8: Run robot
export LLM_PROVIDER=hailo
python main.py
```

### For AI HAT+ (Vision Only)
```bash
# Use cloud LLM or local Ollama
export LLM_PROVIDER=openai  # or "ollama"
python main.py
```

---

## Resources

- [Official Raspberry Pi AI HAT+ Docs](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html)
- [Hailo Developer Zone](https://hailo.ai/developer-zone/)
- [Hailo Model Zoo](https://hailo.ai/products/hailo-software/model-explorer/)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [Ollama Raspberry Pi](https://ollama.com)

---

**Status**: Fully compatible with LangRover hardware integration!  
**Updated**: January 2026 (includes AI HAT+ 2)
