# AI HAT+ vs AI HAT+ 2 Comparison Guide

Updated January 2026 - Official Raspberry Pi AI HAT+ Documentation

---

## Quick Comparison Table

| Feature | AI HAT+ | AI HAT+ 2 |
|---------|---------|-----------|
| **Accelerator Chip** | Hailo-8L or Hailo-8 | Hailo-10H |
| **TOPS Performance** | 13 or 26 | **40** ⭐ |
| **Onboard Memory** | None (uses Pi 5 RAM) | **8GB SDRAM** ⭐ |
| **Local LLM Support** | ❌ No | ✅ **Yes** ⭐ |
| **Max LLM Size** | N/A | ~6B parameters |
| **Vision/Detection** | ✅ Yes | ✅ Yes |
| **Heatsink** | Optional | ✅ Included |
| **VLM Support** | ❌ No | ✅ **Yes** ⭐ |
| **Price** | Lower | Higher |
| **Recommended for LangRover** | ❓ Limited | ✅ **YES** |

---

## Detailed Comparison

### Hardware Specifications

#### AI HAT+

**Available Variants:**
- **Hailo-8L**: 13 TOPS, INT8 (similar to older AI Kit)
- **Hailo-8**: 26 TOPS, INT8 (higher performance variant)

**Memory Architecture:**
- Uses **shared Raspberry Pi 5 RAM** (4GB or 8GB)
- Limited by Pi memory constraints
- All inference data goes through Pi memory bus

**Thermal Management:**
- Small footprint
- Optional heatsink (can overheat under continuous load)
- No forced cooling

**Dimensions:**
- ~66mm × 56.5mm
- ~17mm × 17mm Hailo chip

#### AI HAT+ 2

**Single Variant:**
- **Hailo-10H**: 40 TOPS, INT4 (3x faster than Hailo-8L)

**Memory Architecture:**
- **8GB dedicated SDRAM** on-board ⭐
- Independent of Pi memory
- Much faster inference for LLMs
- Supports models up to ~6 billion parameters

**Thermal Management:**
- **Heatsink included and required** ⭐
- 15mm × 15mm Hailo chip
- 14.5mm × 10mm SDRAM
- Push-pin attachment (don't remove after installation)
- Requires Raspberry Pi Active Cooler on Pi 5

**Dimensions:**
- ~66mm × 56.5mm (same physical size)
- 3.2mm high without heatsink
- 14mm high with push pins and heatsink
- Heatsink: 42.5mm × 64mm

---

## AI HAT+ (No LLM Support)

### Best Use Cases

✅ **Vision/Detection Tasks:**
- Object detection (YOLO, SSD, MobileNet)
- People detection and counting
- Face recognition
- Pose estimation
- Image classification
- Real-time video processing

✅ **Robotics Applications:**
- Obstacle detection and avoidance
- Visual navigation
- Environmental monitoring
- Safety-critical vision tasks

### Limitations

❌ **No LLM Support**
- Cannot run TinyLlama, Phi, Llama, Mistral locally
- Requires cloud API for language processing
- Dependent on network connectivity
- Higher latency for AI decisions

❌ **Memory-Constrained**
- Shares Pi 5's RAM (limited to 8GB max)
- Less memory for complex models
- Can cause memory pressure with large models

### Typical Workflow

```
Camera → Detection (Hailo) → Decision (Cloud API) → Motor Control
         (Fast, local)       (Slow, remote)
```

**Performance:**
- Object detection: 30-60 FPS
- LLM inference: ❌ Not available
- Decision latency: 100-500ms+ (includes cloud API)

### Configuration for LangRover

```bash
# For AI HAT+ (vision only)
export HAILO_DEVICE=hailo8l        # or hailo8 for 26 TOPS
export LLM_PROVIDER=openai         # Use cloud LLM
export USE_REAL_VISION=true
python main.py
```

---

## AI HAT+ 2 (RECOMMENDED - Full AI Autonomy)

### Key Innovations ⭐

1. **40 TOPS Performance**: 3× faster than Hailo-8L
2. **8GB Onboard SDRAM**: Dedicated AI memory
3. **LLM Support**: Run models locally without cloud
4. **VLM Support**: Vision-Language Models
5. **True Edge AI**: Fully autonomous, no internet needed

### Best Use Cases

✅ **Everything AI HAT+ does:**
- Object detection and vision processing
- Real-time video analysis
- All detection tasks

✅ **NEW - Language Processing:**
- Run TinyLlama (1.1B) locally
- Run Phi-2 (2.7B) locally
- Run Llama 3.2 (1B) locally
- Chat with documents
- Natural language planning
- Contextual reasoning

✅ **Perfect for Fully Autonomous Robots:**
- No cloud dependency
- Fast decision-making (local LLM)
- Privacy-preserving
- Works offline
- Low latency

### Advantages Over AI HAT+

| Aspect | Gain |
|--------|------|
| **Speed** | 3× faster (40 vs 13 TOPS) |
| **Memory** | 8GB dedicated (vs shared Pi RAM) |
| **LLM Support** | ✅ (vs ❌) |
| **Autonomy** | Fully local (vs cloud-dependent) |
| **Latency** | Instant decisions (vs API calls) |
| **Reliability** | Works offline (vs needs internet) |

### Typical Workflow

```
Camera → Detection (Hailo) → Local LLM → Motor Control
         (40 TOPS)          (instant)
         All local, no internet needed!
```

**Performance:**
- Object detection: 60+ FPS
- LLM inference (TinyLlama): 30-40 tokens/sec
- Decision latency: <100ms (pure local)
- Full autonomy: ✅ Yes

### Configuration for LangRover

```bash
# For AI HAT+ 2 (RECOMMENDED)
export HAILO_DEVICE=hailo10h
export LLM_PROVIDER=hailo
export HAILO_MODEL_PATH=/home/pi/models/tinyllama-1.1b.Q4_K_M.gguf
export USE_REAL_VISION=true
python main.py

# Robot is now fully autonomous! No cloud needed.
```

### Thermal Requirements

⚠️ **AI HAT+ 2 runs hot and requires cooling:**

1. **Raspberry Pi Active Cooler** (required)
   - Install on Pi 5 before AI HAT+ 2
   - Fan heatsink
   - ~$20-30

2. **AI HAT+ 2 Heatsink** (included, required)
   - Install on top of AI HAT+ 2
   - Two push pins (diagonal corners)
   - Don't remove after installation

3. **Good Airflow**
   - Ensure robot has ventilation
   - Don't cover with chassis entirely
   - Monitor temperatures during development

**Temperature Management:**
```bash
# Check Pi temperature
vcgencmd measure_temp

# Check Hailo temperature
hailortcli fw-control identify | grep -i temperature

# Both should stay below 80°C
# Throttling occurs above 85°C
```

---

## Model Support Comparison

### AI HAT+ (Vision Models Only)

| Category | Support |
|----------|---------|
| **YOLO** (detection) | ✅ All versions |
| **SSD** (detection) | ✅ Optimized |
| **MobileNet** (classification) | ✅ Efficient |
| **PoseNet** (pose) | ✅ Available |
| **TinyLlama** | ❌ No |
| **Phi-2** | ❌ No |
| **Llama** | ❌ No |
| **Vision-Language** (CLIP, LLaVA) | ❌ No |

### AI HAT+ 2 (Vision + LLM)

| Category | Support |
|----------|---------|
| **YOLO** (detection) | ✅ All versions |
| **SSD** (detection) | ✅ Optimized |
| **MobileNet** (classification) | ✅ Efficient |
| **PoseNet** (pose) | ✅ Available |
| **TinyLlama 1.1B** | ✅ **YES** ⭐ |
| **Phi-2 2.7B** | ✅ **YES** ⭐ |
| **Llama 3.2 1B** | ✅ **YES** ⭐ |
| **Mistral 7B** | ✅ **YES** ⭐ |
| **Vision-Language** (CLIP, LLaVA) | ✅ **YES** ⭐ |
| **Custom quantized models** | ✅ Up to 6B params |

---

## Real-World Performance

### Vision Detection (Both HATs)

**Object Detection Speed** (on Pi 5):
- YOLOv5n: 60+ FPS
- YOLOv5s: 30-40 FPS
- YOLOv5m: 15-20 FPS

### AI HAT+ 2 LLM Performance

**Token Generation Speed** (on Pi 5 + 8GB):

| Model | Size | Quantization | Tokens/sec | Use Case |
|-------|------|--------------|-----------|----------|
| **TinyLlama 1.1B** | 1.1B | Q4_K_M | **30-40** | Real-time decisions ⭐ |
| **Phi-2 2.7B** | 2.7B | Q4_K_M | **15-25** | Better reasoning |
| **Llama 3.2 1B** | 1B | Q4_K_M | **30-35** | Modern architecture |
| **Mistral 7B** | 7B | Q3_K_M | **5-10** | Complex tasks |

**Energy Efficiency:**
- TinyLlama Q4: ~0.1W per token
- AI HAT+ 2: Uses <10W total with cooling
- Pi 5: ~5-10W total

---

## Which Should You Choose for LangRover?

### Choose AI HAT+ if:
- ❌ You don't need LLM capabilities
- ✅ Vision detection is your primary need
- ✅ You have reliable internet connectivity
- ✅ You're OK using cloud AI (OpenAI, Anthropic)
- ✅ You have budget constraints

### Choose AI HAT+ 2 if:
- ✅ **You want full autonomy** (recommended!)
- ✅ You need local LLM processing
- ✅ You want low-latency decisions (<100ms)
- ✅ You need offline operation
- ✅ You prioritize privacy (no cloud)
- ✅ You want "true edge AI"

---

## Installation Requirements Comparison

### AI HAT+

**Physical**:
- GPIO stacking header (included)
- PCIe ribbon cable (included)
- 4 spacers + 8 screws (included)
- Optional heatsink

**Software**:
```bash
sudo apt install hailo-all
hailortcli fw-control identify
```

**Time**: ~30 minutes

### AI HAT+ 2

**Physical** (more involved):
- GPIO stacking header (included)
- PCIe ribbon cable (included)
- 4 spacers + 8 screws (included)
- **Heatsink assembly** (included, required)
- Requires Pi Active Cooler + AI HAT+ 2 heatsink

**Software** (same):
```bash
sudo apt install hailo-all
hailortcli fw-control identify
```

**Extra Steps**:
1. Install Active Cooler on Pi 5
2. Install AI HAT+ 2 heatsink (two push pins)
3. Mount both to Pi 5

**Time**: ~45 minutes (more complex assembly)

---

## Cost Analysis

**Approximate Pricing** (Jan 2026):

| Item | Cost |
|------|------|
| Raspberry Pi 5 (8GB) | $80-100 |
| **AI HAT+** (13 TOPS) | $60-80 |
| **AI HAT+ 2** (40 TOPS) | $120-150 |
| Active Cooler | $20-30 |
| **Difference** | **+$40-70** |

**ROI Analysis:**
- If using OpenAI API: ~$0.01-0.10 per decision
- AI HAT+ 2 LLM: Free after purchase
- Payback: ~500-1000 robot decisions

---

## Recommendations for LangRover

### Recommended Configuration ⭐

**For Full Autonomy:**
```
✅ Raspberry Pi 5 (8GB)
✅ AI HAT+ 2 (40 TOPS + 8GB SDRAM)
✅ Raspberry Pi Active Cooler
✅ Pi Camera 3
✅ 4× Ultrasonic sensors
✅ 2× TB6612FNG motor drivers
✅ TinyLlama 1.1B Q4_K_M local model
```

**Result:**
- Fully autonomous (no internet needed)
- Fast decisions (<100ms)
- Privacy-preserving
- Cost-effective after initial investment

### Alternative (Cloud-Dependent)

```
✅ Raspberry Pi 5 (4GB)
✅ AI HAT+ (13 TOPS)
✅ Pi Camera 3
✅ Cloud LLM (OpenAI, Anthropic, etc.)
```

**Trade-offs:**
- Requires internet connection
- Higher API costs
- Slower decisions (network latency)
- Less privacy
- Less autonomous

---

## Transition Path

If you start with **AI HAT+** and want to upgrade:

1. Purchase **AI HAT+ 2**
2. Update `HAILO_DEVICE` in config:
   ```python
   HAILO_DEVICE = "hailo10h"  # Changed from hailo8l
   ```
3. Download local LLM:
   ```bash
   ollama pull tinyllama
   ```
4. Set `LLM_PROVIDER = "hailo"`
5. Done! Same hardware interface, more powerful

---

## Summary

| Aspect | AI HAT+ | AI HAT+ 2 |
|--------|---------|-----------|
| **Best For** | Vision tasks | Full autonomy ⭐ |
| **Local LLM** | ❌ No | ✅ Yes |
| **Internet** | Required | Optional |
| **Latency** | Medium | Low ⭐ |
| **Privacy** | Low | High ⭐ |
| **Cost** | Lower | Higher |
| **Complexity** | Simple | Moderate |
| **For LangRover** | Possible | **Highly Recommended** ⭐ |

---

**Final Recommendation for LangRover:** 🤖⭐

**Choose AI HAT+ 2** for:
- True autonomous operation
- Fast, intelligent decisions
- No internet dependency
- Maximum robot independence

**Choose AI HAT+** if:
- You prioritize lower cost
- Vision is your primary need
- You have reliable internet
- You're OK with cloud AI delays

---

## Additional Resources

- [Official Raspberry Pi AI HAT+ Documentation](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html)
- [Hailo Model Explorer](https://hailo.ai/products/hailo-software/model-explorer/)
- [Ollama for Raspberry Pi](https://ollama.com)
- [LangRover AI_HAT_SETUP.md](AI_HAT_SETUP.md) - Complete setup guide
- [LangRover HARDWARE_SETUP.md](HARDWARE_SETUP.md) - Hardware assembly

