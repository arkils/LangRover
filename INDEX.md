# LangRover - Quick Navigation Guide

## 🚀 Start Here

**New to the project?** Start with one of these:

### For Running the Robot
→ [VISION_QUICKSTART.md](VISION_QUICKSTART.md) - **2-minute quick start**

### For Understanding Vision
→ [VISION_COMPLETE.md](VISION_COMPLETE.md) - **Feature overview and test results**

### For Full Documentation  
→ [README.md](README.md) - **Complete project guide**

### For Vision Technical Details
→ [VISION.md](VISION.md) - **Comprehensive vision system documentation**

---

## 📚 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[VISION_QUICKSTART.md](VISION_QUICKSTART.md)** | Quick start with examples | 5 min |
| **[VISION_COMPLETE.md](VISION_COMPLETE.md)** | Vision feature summary & test results | 5 min |
| **[VISION.md](VISION.md)** | Complete vision system guide | 15 min |
| **[README.md](README.md)** | Full project documentation | 20 min |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | Project completion report | 10 min |
| **[ISOLATION_COMPLETE.md](ISOLATION_COMPLETE.md)** | Virtual environment setup | 10 min |

---

## 🎯 By Use Case

### "I just want to run the robot"
```powershell
.\run.ps1
```
See: [VISION_QUICKSTART.md](VISION_QUICKSTART.md)

### "I want to understand the vision system"
Read in order:
1. [VISION_COMPLETE.md](VISION_COMPLETE.md) - What it does
2. [VISION.md](VISION.md) - How it works
3. [main.py](main.py) - Code walkthrough

### "I want to add a custom skill for a detected object"
1. Subclass `Skill` in [skills/builtin.py](skills/builtin.py)
2. Register it in [main.py](main.py) with `skill_registry.register(YourSkill())`
3. Run — the LLM picks it up automatically

### "I want to deploy on Raspberry Pi"
1. Read: [VISION.md](VISION.md#raspberry-pi-setup-real-vision-with-pi-camera-3)
2. Install: `pip install picamera2 ultralytics opencv-python`
3. Run: `export USE_REAL_CAMERA=true; export USE_REAL_VISION=true; python main.py`

### "I want to customize the robot"
1. Understand: [README.md](README.md#extending-to-real-hardware)
2. Implement: Custom `RobotActions` or `VisionDetector`
3. Integrate: Update config and main.py

### "I want to see the latest test results"
→ [VISION_COMPLETE.md](VISION_COMPLETE.md#test-results) - Latest run shows all 10 cycles passed

---

## 🔧 Key Files Reference

### Brain (Decision Making)
- **[brain/agent.py](brain/agent.py)** - LLM tool calling agent with skill + nav tools
- **[brain/prompts.py](brain/prompts.py)** - System prompts with vision & skill rules

### Skills (Object-Triggered Behaviours)
- **[skills/base.py](skills/base.py)** - `Skill` ABC + `SkillContext`
- **[skills/registry.py](skills/registry.py)** - `SkillRegistry` (register, lookup, LangChain tools)
- **[skills/builtin.py](skills/builtin.py)** - `CatGreetingSkill`, `DogGreetingSkill`, `PersonSafetySkill`

### Vision (Computer Vision)
- **[vision/camera.py](vision/camera.py)** - Pi Camera 3 & Mock camera
- **[vision/detector.py](vision/detector.py)** - Vision detector interface  
- **[vision/vision.py](vision/vision.py)** - YOLO & Mock detectors

### World (Sensors & State)
- **[world/state.py](world/state.py)** - WorldState with vision data
- **[world/simulator.py](world/simulator.py)** - Simulated sensor data

### Control
- **[main.py](main.py)** - Main control loop
- **[config.py](config.py)** - Configuration

### Scripts
- **[run.ps1](run.ps1)** / **[run.sh](run.sh)** - Smart startup
- **[setup.ps1](setup.ps1)** / **[setup.sh](setup.sh)** - Initial setup

---

## ✅ Feature Checklist

### Core Features
- ✅ Autonomous decision-making with LangChain
- ✅ Local Ollama integration (gemma3:270m)
- ✅ Distance sensor simulation (3-axis)
- ✅ Target detection
- ✅ Virtual environment isolation

### Vision Features
- ✅ Object detection (YOLO / mock)
- ✅ Person detection
- ✅ Face detection
- ✅ Motion detection
- ✅ Pi Camera 3 support
- ✅ YOLO real detection
- ✅ Mock vision for testing
- ✅ Safety protocol (person → stop)

### Skill System
- ✅ `Skill` ABC — extensible interface
- ✅ `SkillRegistry` — register skills, expose as LangChain tools
- ✅ Built-in: `greet_cat`, `greet_dog`, `person_safety_stop`
- ✅ YOLO detections trigger relevant skills automatically
- ✅ LLM picks skill tools via `bind_tools()` (real tool calling)

### Deployment
- ✅ Windows support (PowerShell)
- ✅ Linux/macOS support (Bash)
- ✅ Laptop testing (mock mode)
- ✅ Raspberry Pi deployment (real mode)
- ✅ Cloud LLM support (OpenAI)
- ✅ Local LLM support (Ollama)

---

## 🎓 Learning Path

**Beginner** (Want to just run it)
1. [VISION_QUICKSTART.md](VISION_QUICKSTART.md)
2. Run: `.\run.ps1`
3. Watch the output

**Intermediate** (Want to understand it)
1. [VISION_COMPLETE.md](VISION_COMPLETE.md)
2. [README.md](README.md)
3. Read: [main.py](main.py) + [brain/agent.py](brain/agent.py)

**Advanced** (Want to customize it)
1. All above documentation
2. [VISION.md](VISION.md) - Complete technical guide
3. Source code in order:
   - [config.py](config.py)
   - [world/state.py](world/state.py)
   - [world/simulator.py](world/simulator.py)
   - [vision/](vision/) - Vision module
   - [brain/agent.py](brain/agent.py)
   - [main.py](main.py)

---

## 🔗 Quick Links

### Documentation
- [Full README](README.md)
- [Vision Complete Guide](VISION.md)
- [Quick Start](VISION_QUICKSTART.md)
- [Project Status](PROJECT_STATUS.md)

### Scripts
- Run: `.\run.ps1` (Windows) or `./run.sh` (Linux/macOS)
- Setup: `.\setup.ps1` (Windows) or `./setup.sh` (Linux/macOS)

### Code Entry Points
- **Main loop**: [main.py](main.py)
- **Agent logic**: [brain/agent.py](brain/agent.py)
- **Vision system**: [vision/vision.py](vision/vision.py)

---

## ❓ FAQ

**Q: Do I need hardware to run this?**
A: No! Mock vision runs on any laptop. Hardware (Pi Camera 3) is optional.

**Q: Can I use a different LLM?**
A: Yes! Set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`. See [README.md](README.md#configuration).

**Q: How do I customize the robot?**
A: Edit [brain/prompts.py](brain/prompts.py) for behavior or implement custom `RobotActions`.

**Q: What if people are detected?**
A: Robot stops immediately - it's a safety protocol you can't disable easily. See [brain/agent.py](brain/agent.py).

**Q: Can I run on Raspberry Pi?**
A: Yes! Install packages and enable real mode. See [VISION.md](VISION.md#raspberry-pi-setup-real-vision-with-pi-camera-3).

**Q: Where are all the dependencies?**
A: In `./venv/` only - completely isolated. See [ISOLATION_COMPLETE.md](ISOLATION_COMPLETE.md).

---

## 📈 Project Status

**Latest Test**: ✅ All 10 decision cycles passed
**Vision Mode**: Mock (laptop compatible)
**LLM**: gemma3:270m via Ollama
**Safety**: People detection → immediate stop ✓

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for complete details.

---

**Choose your starting point above and dive in! 🚀**
