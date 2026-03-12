# Raspberry Pi 5 Setup Guide — LangRover

From a blank SD card to a running robot, step by step.

---

## What You Need

- Raspberry Pi 5 (4 GB or 8 GB)
- MicroSD card (32 GB minimum, 64 GB recommended, Class 10 / A2)
- MicroSD card reader (USB adapter or built-in)
- A laptop or desktop to flash the card
- USB-C power supply (official Pi 5 supply, 5 V / 5 A)
- HDMI cable + monitor (first boot only; SSH after that)
- USB keyboard (first boot only)

---

## Step 1 — Flash the OS

### Download Raspberry Pi Imager

Go to **https://www.raspberrypi.com/software/** and install Raspberry Pi Imager for your OS (Windows / macOS / Linux).

### Flash the SD card

1. Insert the SD card into your reader.
2. Open Raspberry Pi Imager.
3. Click **Choose Device** → select **Raspberry Pi 5**.
4. Click **Choose OS** → **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)**.
   > Lite = no desktop. Smaller, faster, more RAM free for the LLM.
5. Click **Choose Storage** → select your SD card.
6. Click the **gear icon (⚙)** (or Next → Edit Settings) and configure:
   - **Hostname**: `langrover` (or anything you like)
   - **Username / Password**: set a strong password
   - **Wi-Fi**: enter your SSID + password (saves plugging in a cable for first boot)
   - **Enable SSH**: check **Allow public-key authentication** or **Use password authentication**
   - **Locale / timezone**: set yours
7. Click **Save** → **Write** → confirm the warning.

Wait for the write + verify to complete (~3–5 minutes), then eject the card.

---

## Step 2 — First Boot

1. Insert the SD card into the Pi.
2. Connect the Pi to your monitor and keyboard.
3. Plug in power (USB-C).
4. Wait ~60 seconds for first-boot setup to finish.
5. Log in with the username/password you set.

### Find the Pi's IP address

```bash
hostname -I
```

> After this you can SSH from your laptop and unplug the monitor:
> ```bash
> ssh pi@langrover.local
> # or
> ssh pi@<IP address>
> ```

---

## Step 3 — System Update

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Step 4 — Install Basic Tools

```bash
sudo apt install -y \
    git \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    curl \
    wget \
    nano \
    htop
```

Verify Python version (must be 3.10+):

```bash
python3 --version
```

---

## Step 5 — Enable the Camera

```bash
sudo raspi-config
```

Navigate: **Interface Options → Camera → Enable** → Finish → reboot when prompted.

After reboot, test the camera is detected:

```bash
libcamera-hello --list-cameras
```

You should see `imx708` listed (that's the Camera Module 3 sensor). If not, check the CSI ribbon cable is firmly seated.

---

## Step 6 — Install picamera2

`picamera2` depends on compiled libcamera bindings that only work as a system package — **do not use pip for this one**.

```bash
sudo apt install -y python3-picamera2
```

Quick test:

```bash
python3 -c "from picamera2 import Picamera2; c = Picamera2(); print('Camera OK'); c.close()"
```

---

## Step 7 — Clone the Repo

```bash
cd ~
git clone https://github.com/<your-username>/LangRover.git
cd LangRover
```

---

## Step 8 — Create the Virtual Environment

Because `picamera2` is installed system-wide (via apt), the venv needs `--system-site-packages` so it can see it.

```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
```

Install the Python dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 9 — Install Ollama

Ollama runs the LLM locally on the Pi.

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify Ollama is running:

```bash
ollama list
```

Pull the default model (small enough to run on Pi 5 with 4 GB RAM):

```bash
ollama pull qwen2.5:0.5b
```

> If you have 8 GB RAM you can try a larger model:
> ```bash
> ollama pull qwen2.5:1.5b
> ```
> Update `OLLAMA_MODEL` in your `.env` file accordingly.

---

## Step 10 — Install Vision Libraries

YOLO and OpenCV are fine to install via pip:

```bash
pip install ultralytics opencv-python
```

This downloads the YOLOv8 weights on first run (~6 MB for nano).

---

## Step 11 — Configure Environment

Create a `.env` file in the project root:

```bash
nano .env
```

Paste and save:

```env
# LLM
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:0.5b

# Enable real hardware
USE_GPIO_ACTIONS=true
USE_REAL_SENSORS=true
USE_REAL_CAMERA=true
USE_REAL_VISION=true

# ESP32 serial port — check with: ls /dev/ttyACM*
ESP32_SERIAL_PORT=/dev/ttyACM0

# Motor speed (0–100%)
DEFAULT_MOTOR_SPEED=70
```

---

## Step 12 — Run the Robot

```bash
source venv/bin/activate
python main.py
```

You should see:

```
[CAMERA] Pi Camera Module 3 initialized (1280×720 RGB888, autofocus)
[VISION] YOLO model loaded successfully
Checking Ollama connection at http://localhost:11434...
[OK] Connected to Ollama
[OK] Using model: qwen2.5:0.5b
[SENSORS] Front: 120cm | Left: 80cm | Right: 200cm | ...
[AGENT] Consulting LLM | tools: [move_forward, stop, turn_left, turn_right, greet_person, ...]
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `libcamera-hello` shows no cameras | Check CSI ribbon cable; run `sudo raspi-config` and re-enable camera |
| `from picamera2 import Picamera2` fails | `sudo apt install python3-picamera2`; make sure venv was created with `--system-site-packages` |
| `ollama: command not found` | Re-run the install script; check `~/.local/bin` is in `$PATH` |
| `ConnectionError: Ollama is not running` | `ollama serve` in a separate terminal, or enable the systemd service: `sudo systemctl enable --now ollama` |
| ESP32 not found on `/dev/ttyACM0` | Run `ls /dev/ttyACM*` and update `ESP32_SERIAL_PORT` in `.env` |
| Permission denied on serial port | `sudo usermod -aG dialout $USER` then log out and back in |
| YOLO `No such file or directory` on first run | Normal — weights download automatically on first inference |

---

## Quick Reference

```bash
# Activate venv
source ~/LangRover/venv/bin/activate

# Run robot
cd ~/LangRover && python main.py

# Run tests (simulation mode, no hardware needed)
python test_full_robot.py

# Update code
git pull && pip install -r requirements.txt

# Check Ollama models
ollama list

# Pull a different model
ollama pull qwen2.5:1.5b
```

---

For wiring the motors and sensors see [HARDWARE_SETUP.md](HARDWARE_SETUP.md).  
For the full project architecture see [ARCHITECTURE.md](ARCHITECTURE.md).
