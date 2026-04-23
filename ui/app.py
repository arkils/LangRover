"""
LangRover Streamlit UI — entry point.

Run:
    streamlit run ui/app.py

On Raspberry Pi (accessible from LAN):
    streamlit run ui/app.py --server.address 0.0.0.0
"""

import sys
import threading
from pathlib import Path

# Ensure repo root is on sys.path so robot modules are importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

st.set_page_config(
    page_title="LangRover",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from streamlit_autorefresh import st_autorefresh  # noqa: E402

from ui.components import (  # noqa: E402
    render_camera_frame,
    render_decision_cycles,
    render_decision_cycle_summary,
    render_decision_trace,
    render_heading,
    render_history,
    render_sensors,
    render_stm_table,
    render_status_bar,
    render_vision,
)
from ui.state import UIState  # noqa: E402
from ui.worker import robot_worker  # noqa: E402


# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

def _init_session() -> None:
    defaults = {
        "ui_state":    None,
        "stop_event":  None,
        "pause_event": None,
        "step_event":  None,
        "worker_thread": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_session()


# ---------------------------------------------------------------------------
# Auto-refresh while the robot is starting, running, or paused
# ---------------------------------------------------------------------------

history, status, error_msg, total_steps = [], "idle", "", 0
if st.session_state.ui_state is not None:
    history, status, error_msg, total_steps = st.session_state.ui_state.snapshot()

if status in ("starting", "running", "paused"):
    st_autorefresh(interval=1000, key="robot_refresh")


# ---------------------------------------------------------------------------
# Sidebar — configuration + controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🤖 LangRover")
    st.divider()

    st.subheader("Configuration")

    decision_mode = st.selectbox(
        "Decision Mode",
        ["hybrid", "rag", "agent"],
        index=0,
        help="hybrid = Agentic RAG | rag = Traditional RAG | agent = pure LLM",
    )
    llm_provider = st.selectbox(
        "LLM Provider",
        ["ollama", "openai"],
        index=0,
    )
    if llm_provider == "ollama":
        ollama_model = st.selectbox(
            "Ollama Model",
            ["qwen2.5:3b", "qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:7b", "llama3.2:3b", "llama3.1:8b"],
            index=0,
        )
    else:
        ollama_model = st.selectbox(
            "OpenAI Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
            index=0,
        )
    sim_steps = st.slider("Simulation Steps", min_value=1, max_value=50, value=10)
    cycle_delay = st.slider("Cycle Delay (s)", min_value=0, max_value=10, value=1)
    stm_cycles = st.slider("STM Cycles (memory)", min_value=1, max_value=10, value=5)

    st.divider()
    st.subheader("Hardware")
    use_real_sensors = st.toggle("Real Sensors", value=False)
    use_real_camera  = st.toggle("Real Camera", value=False)
    use_real_vision  = st.toggle("Real Vision (YOLO)", value=False)
    use_gpio_actions = st.toggle("Real Motors (GPIO)", value=False)

    st.divider()
    st.subheader("Controls")

    ctrl_cols = st.columns(2)
    active_run = status in ("starting", "running", "paused")

    # ── Start ────────────────────────────────────────────────────────────────
    if ctrl_cols[0].button("▶ Start", width="stretch", disabled=active_run):
        # Tear down any previous run
        if st.session_state.stop_event:
            st.session_state.stop_event.set()
            if st.session_state.pause_event:
                st.session_state.pause_event.set()

        ui_state   = UIState()
        ui_state.set_status("starting")
        stop_ev    = threading.Event()
        pause_ev   = threading.Event()
        pause_ev.set()   # start un-paused
        step_ev    = threading.Event()

        config_overrides = {
            "DECISION_MODE":        decision_mode,
            "LLM_PROVIDER":         llm_provider,
            "OLLAMA_MODEL":         ollama_model,
            "SIMULATION_STEPS":     str(sim_steps),
            "CYCLE_DELAY":          str(cycle_delay),
            "SHORT_TERM_MEMORY_CYCLES": str(stm_cycles),
            "USE_REAL_SENSORS":     str(use_real_sensors).lower(),
            "USE_REAL_CAMERA":      str(use_real_camera).lower(),
            "USE_REAL_VISION":      str(use_real_vision).lower(),
            "USE_GPIO_ACTIONS":     str(use_gpio_actions).lower(),
        }

        thread = threading.Thread(
            target=robot_worker,
            args=(ui_state, stop_ev, pause_ev, step_ev, config_overrides),
            daemon=True,
        )
        thread.start()

        st.session_state.ui_state     = ui_state
        st.session_state.stop_event   = stop_ev
        st.session_state.pause_event  = pause_ev
        st.session_state.step_event   = step_ev
        st.session_state.worker_thread = thread
        st.rerun()

    # ── Stop ─────────────────────────────────────────────────────────────────
    if ctrl_cols[1].button("⏹ Stop", width="stretch", disabled=(status not in ("starting", "running", "paused"))):
        st.session_state.stop_event.set()
        st.session_state.pause_event.set()   # unblock thread so it can exit
        st.rerun()

    # ── Pause / Resume ───────────────────────────────────────────────────────
    pause_label = "▶ Resume" if status == "paused" else "⏸ Pause"
    if st.button(pause_label, width="stretch", disabled=(status not in ("running", "paused"))):
        pe = st.session_state.pause_event
        if pe.is_set():
            pe.clear()    # pause
            st.session_state.ui_state.set_status("paused")
        else:
            pe.set()      # resume
            st.session_state.ui_state.set_status("running")
        st.rerun()

    # ── Single Step ──────────────────────────────────────────────────────────
    if st.button("⏭ Step", width="stretch", disabled=(status != "paused")):
        st.session_state.step_event.set()
        st.session_state.pause_event.set()   # allow the one cycle to run
        st.rerun()

    if status == "error" and error_msg:
        st.error(error_msg)


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.header("LangRover — Live Dashboard")
st.divider()

render_status_bar(history, status, total_steps)
st.divider()

# ── Latest cycle data ─────────────────────────────────────────────────────

latest = history[-1] if history else None

top_left, top_mid, top_right = st.columns([2, 2, 1])

with top_left:
    st.subheader("Sensors")
    if latest:
        render_sensors(latest.world_state)
    else:
        st.caption("Waiting for first cycle…")

with top_mid:
    st.subheader("Camera Frame")
    render_camera_frame(latest.frame_path if latest else None)

with top_right:
    st.subheader("Vision")
    if latest:
        render_vision(latest.world_state)
        st.divider()
        render_heading(latest.heading, latest.action)
    else:
        st.caption("Waiting…")

st.divider()

st.subheader("Decision Cycle Summary")
render_decision_cycle_summary(latest)

st.divider()

st.subheader("Decision Trace")
render_decision_trace(latest)

st.divider()

st.subheader("Decision Cycles")
render_decision_cycles(history)

st.divider()

st.subheader("Short-Term Memory (last 5 cycles)")
render_stm_table(history)

st.divider()

st.subheader("Cycle History")
render_history(history)
