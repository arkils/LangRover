"""Background worker thread: runs the robot control loop and feeds UIState."""

import io
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from ui.state import CycleEvent, UIState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEMP_DIR = Path(__file__).parent / "temp"
_PLACEHOLDER_PATH = _TEMP_DIR / "no_frame.jpg"


def _ensure_temp_dir() -> None:
    _TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _make_placeholder() -> Path:
    """Create a grey 640×360 placeholder JPEG and return its path."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (640, 360), color=(60, 60, 60))
        draw = ImageDraw.Draw(img)
        text_lines = ["Simulation Mode", "No camera feed"]
        y = 150
        for line in text_lines:
            # Basic centering without truetype fonts
            bbox = draw.textbbox((0, 0), line)
            w = bbox[2] - bbox[0]
            draw.text(((640 - w) // 2, y), line, fill=(180, 180, 180))
            y += 28
        _ensure_temp_dir()
        img.save(str(_PLACEHOLDER_PATH), "JPEG")
    except Exception:
        # If PIL fails (not installed yet), write an empty file as fallback
        _ensure_temp_dir()
        _PLACEHOLDER_PATH.touch()
    return _PLACEHOLDER_PATH


def _save_frame(raw_frame, step: int) -> Optional[str]:
    """
    Persist a camera frame as a JPEG and return its absolute path.

    - numpy array  → PIL Image.fromarray → save JPEG
    - None (mock)  → copy/use placeholder
    """
    _ensure_temp_dir()
    dest = _TEMP_DIR / f"frame_{step:04d}.jpg"

    if raw_frame is not None:
        try:
            import numpy as np
            from PIL import Image
            if isinstance(raw_frame, np.ndarray):
                Image.fromarray(raw_frame).save(str(dest), "JPEG")
                return str(dest)
        except Exception:
            pass

    # Fallback: use / create placeholder
    placeholder = _PLACEHOLDER_PATH if _PLACEHOLDER_PATH.exists() else _make_placeholder()
    import shutil
    shutil.copy2(str(placeholder), str(dest))
    return str(dest)


def _parse_action(log_lines: list[str]) -> Optional[str]:
    """Extract the last action name from captured log lines."""
    for line in reversed(log_lines):
        if "[ACTION]" in line and ">>" in line:
            # e.g. "[ACTION]  >> move_forward(30 cm)"
            after = line.split(">>", 1)[-1].strip()
            return after.split("(")[0].strip()
    return None


def _format_cycle_prelude(step: int, decision_mode: str, world_state) -> list[str]:
    """Create explicit per-cycle logs before agent reasoning starts."""
    object_parts = [f"{obj.name}({obj.confidence:.0%})" for obj in world_state.vision.objects]
    blocked = " [!!BLOCKED]" if world_state.front_distance_cm < 30 else ""
    return [
        f"[CYCLE]   Step {step} | Mode: {decision_mode.upper()}",
        (
            f"[SENSORS] Front: {world_state.front_distance_cm:.0f}cm{blocked} | "
            f"Left: {world_state.left_distance_cm:.0f}cm | "
            f"Right: {world_state.right_distance_cm:.0f}cm | "
            f"Rear: {world_state.rear_distance_cm:.0f}cm"
        ),
        (
            f"[VISION]  {', '.join(object_parts) if object_parts else 'no objects detected'}"
            f" | People: {world_state.vision.people_count}"
            f" | Motion: {'yes' if world_state.vision.motion_detected else 'no'}"
        ),
    ]


# ---------------------------------------------------------------------------
# Worker entry point
# ---------------------------------------------------------------------------

def robot_worker(
    ui_state: UIState,
    stop_event: threading.Event,
    pause_event: threading.Event,
    step_event: threading.Event,
    config_overrides: dict,
) -> None:
    """
    Robot control loop intended to run in a daemon ``threading.Thread``.

    Args:
        ui_state:        Shared state consumed by the Streamlit UI.
        stop_event:      Set externally to terminate the loop.
        pause_event:     Cleared externally to pause; set to resume.
        step_event:      Set externally to fire a single cycle while paused.
        config_overrides: ``os.environ`` key/value overrides applied before
                          ``Config`` is instantiated.
    """
    # Load .env first so project defaults are available, then apply sidebar
    # overrides on top (load_dotenv won't overwrite already-set env vars, so
    # we load it before applying our overrides).
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        pass

    # Apply sidebar overrides — these win over .env values
    for k, v in config_overrides.items():
        os.environ[k] = str(v)

    # Force simulation mode — UI worker never touches real hardware
    os.environ["USE_GPIO_ACTIONS"] = "false"
    os.environ["USE_REAL_SENSORS"] = "false"
    os.environ["USE_REAL_CAMERA"] = "false"
    os.environ["USE_REAL_VISION"] = "false"

    # Read all config values directly from os.environ so we always get the
    # current values — Config dataclass defaults are frozen at first import.
    llm_provider   = os.environ.get("LLM_PROVIDER", "ollama")
    ollama_model   = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")
    decision_mode  = os.environ.get("DECISION_MODE", "hybrid")
    total_steps    = int(os.environ.get("SIMULATION_STEPS", "10"))
    stm_cycles     = int(os.environ.get("SHORT_TERM_MEMORY_CYCLES", "5"))
    rag_dir        = os.environ.get("RAG_KNOWLEDGE_DIR", "./chroma_rag")

    try:
        from actions.cli_actions import CLIRobotActions
        from brain.agent import create_agent, decide_and_act
        from brain.memory import ShortTermMemory
        from skills.builtin import CatGreetingSkill, DogGreetingSkill, PersonGreetingSkill
        from skills.registry import SkillRegistry
        from world.simulator import read_world_state

        ui_state.set_total(total_steps)
        ui_state.set_status("starting")

        skill_registry = SkillRegistry()
        for skill in (PersonGreetingSkill(), CatGreetingSkill(), DogGreetingSkill()):
            try:
                skill_registry.register(skill)
            except ValueError:
                pass  # already registered

        robot_actions = CLIRobotActions()
        short_term = ShortTermMemory(max_cycles=stm_cycles)

        # Optional RAG knowledge base
        rag_kb = None
        if decision_mode in ("rag", "hybrid"):
            try:
                from brain.memory import RAGKnowledgeBase
                rag_kb = RAGKnowledgeBase(persist_dir=rag_dir)
            except Exception:
                pass

        agent = create_agent(
            robot_actions=robot_actions,
            skill_registry=skill_registry,
            llm_provider=llm_provider,
            ollama_model=ollama_model,
            short_term_memory=short_term,
            rag_kb=rag_kb,
        )

        # Build placeholder once at startup
        _make_placeholder()
        ui_state.set_status("running")

        for step in range(1, total_steps + 1):
            if stop_event.is_set():
                break

            # Block here if paused (unless a one-shot step was requested)
            one_shot = False
            if not pause_event.is_set():
                # Wait until resumed or a step is requested
                while not pause_event.is_set() and not step_event.is_set() and not stop_event.is_set():
                    time.sleep(0.05)
                if stop_event.is_set():
                    break
                if step_event.is_set():
                    one_shot = True
                    step_event.clear()
                    pause_event.set()  # temporarily set so decide_and_act can run

            # Capture frame + world state
            raw_frame_container: list = []
            world_state = read_world_state(frame_out=raw_frame_container)
            raw_frame = raw_frame_container[0] if raw_frame_container else None
            frame_path = _save_frame(raw_frame, step)

            # Capture stdout from decide_and_act
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                decide_and_act(agent, world_state)
            finally:
                sys.stdout = old_stdout

            log_lines = _format_cycle_prelude(step, decision_mode, world_state)
            log_lines.extend(buf.getvalue().splitlines())

            # Record in short-term memory
            if short_term is not None:
                short_term.record(world_state, _parse_action(log_lines) or "unknown")

            heading = agent.get("current_heading", 0.0)
            event = CycleEvent(
                step=step,
                timestamp=datetime.now().strftime("%H:%M:%S"),
                world_state=world_state,
                heading=heading,
                logs=log_lines,
                action=_parse_action(log_lines),
                mode=decision_mode,
                frame_path=frame_path,
            )
            ui_state.append(event)

            # After one-shot: re-pause by clearing pause_event
            if one_shot:
                pause_event.clear()

            # Interruptible delay
            delay = float(config_overrides.get("CYCLE_DELAY", os.environ.get("DECISION_CYCLE_DELAY", "1")))
            elapsed = 0.0
            chunk = 0.05
            while elapsed < delay and not stop_event.is_set():
                time.sleep(chunk)
                elapsed += chunk

        if stop_event.is_set():
            ui_state.set_status("stopped")
        else:
            ui_state.set_status("done")

    except Exception as exc:
        import traceback
        ui_state.set_status("error", f"{exc}\n{traceback.format_exc()}")
