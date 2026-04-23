"""Streamlit render components for the LangRover UI."""

from typing import List, Optional

import streamlit as st

from ui.state import CycleEvent
from world.state import WorldState


# ---------------------------------------------------------------------------
# Color maps
# ---------------------------------------------------------------------------

_LOG_COLORS = {
    "[CYCLE]":   "#5dade2",
    "[SENSORS]": "#4a9eff",
    "[VISION]":  "#9b59b6",
    "[BRAIN]":   "#e67e22",
    "[CONTEXT]": "#888888",
    "[LLM]":     "#e74c3c",
    "[RAG]":     "#27ae60",
    "[ACTION]":  "#1abc9c",
    "[RESULT]":  "#2ecc71",
    "[WARNING]": "#f39c12",
    "[FALLBACK]":"#d35400",
    "[ERROR]":   "#c0392b",
    "[HARD RULE]":"#ff6b6b",
    "[SKILL]":   "#a29bfe",
}

_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _compass(degrees: float) -> str:
    idx = round(degrees / 45) % 8
    return _COMPASS[idx]


def _sensor_color(cm: float, min_safe: int = 30, warn: int = 60) -> str:
    if cm < min_safe:
        return "#e74c3c"   # red
    if cm < warn:
        return "#f39c12"   # orange
    return "#2ecc71"       # green


def _bar_pct(cm: float, max_cm: float = 400.0) -> float:
    return min(cm / max_cm, 1.0)


def _event_summary(event: CycleEvent) -> dict:
    """Derive a compact decision summary from one cycle's logs."""
    llm_invokes = 0
    rag_used = False
    hard_rule = False
    context_line = ""
    result_line = ""

    for line in event.logs:
        if "[LLM]" in line and "Invoke" in line:
            llm_invokes += 1
        if "[RAG]" in line:
            rag_used = True
        if "[HARD RULE]" in line:
            hard_rule = True
        if "[CONTEXT]" in line and not context_line:
            context_line = line.split("]", 1)[-1].strip()
        if "[RESULT]" in line:
            result_line = line.split("]", 1)[-1].strip()

    path_parts = [event.mode.upper()]
    if hard_rule:
        path_parts.append("hard-rule")
    elif rag_used and llm_invokes:
        path_parts.append("RAG -> LLM")
    elif rag_used:
        path_parts.append("RAG")
    elif llm_invokes:
        path_parts.append("LLM")
    else:
        path_parts.append("no-decision-log")

    return {
        "path": " | ".join(path_parts),
        "llm_invokes": llm_invokes,
        "rag_used": rag_used,
        "hard_rule": hard_rule,
        "context": context_line or "—",
        "result": result_line or "—",
    }


# ---------------------------------------------------------------------------
# Status bar
# ---------------------------------------------------------------------------

def render_status_bar(history: List[CycleEvent], status: str, total: int) -> None:
    """5-column metrics row at the top of the page."""
    cycle = len(history)
    last = history[-1] if history else None
    last_action = last.action or "—" if last else "—"
    heading_str = f"{last.heading:.0f}° ({_compass(last.heading)})" if last else "—"
    mode = last.mode.upper() if last else "—"

    status_emoji = {
        "idle": "⏸ Idle",
        "running": "▶ Running",
        "paused": "⏸ Paused",
        "done": "✅ Done",
        "stopped": "⏹ Stopped",
        "error": "❌ Error",
    }.get(status, status)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Status", status_emoji)
    c2.metric("Cycle", f"{cycle} / {total}" if total else str(cycle))
    c3.metric("Mode", mode)
    c4.metric("Last Action", last_action)
    c5.metric("Heading", heading_str)


# ---------------------------------------------------------------------------
# Sensor bars
# ---------------------------------------------------------------------------

def render_sensors(ws: WorldState) -> None:
    """4 distance sensors as labeled, color-coded progress bars."""
    sensors = [
        ("FRONT", ws.front_distance_cm),
        ("LEFT",  ws.left_distance_cm),
        ("RIGHT", ws.right_distance_cm),
        ("REAR",  ws.rear_distance_cm),
    ]
    col_a, col_b = st.columns(2)
    for i, (label, val) in enumerate(sensors):
        col = col_a if i % 2 == 0 else col_b
        color = _sensor_color(val)
        pct = _bar_pct(val)
        col.markdown(
            f"**{label}** &nbsp; <span style='color:{color}'>{val:.0f} cm</span>",
            unsafe_allow_html=True,
        )
        col.progress(pct)


# ---------------------------------------------------------------------------
# Camera frame
# ---------------------------------------------------------------------------

def render_camera_frame(frame_path: Optional[str]) -> None:
    """Display the most recent camera frame (real or placeholder)."""
    if frame_path:
        try:
            st.image(frame_path, use_container_width=True)
            return
        except Exception:
            pass
    st.info("No frame available yet")


# ---------------------------------------------------------------------------
# Vision panel
# ---------------------------------------------------------------------------

def render_vision(ws: WorldState) -> None:
    """Detected objects with confidence bars + people / motion warnings."""
    if ws.vision.people_count > 0:
        st.warning(f"👤 {ws.vision.people_count} person(s) detected")
    if ws.vision.motion_detected:
        st.warning("🚨 Motion detected")

    if ws.vision.objects:
        st.markdown("**Detected objects**")
        for obj in ws.vision.objects:
            st.progress(obj.confidence, text=f"{obj.name} ({obj.confidence:.0%})")
    else:
        st.caption("No objects detected")


# ---------------------------------------------------------------------------
# Heading
# ---------------------------------------------------------------------------

def render_heading(heading: float, action: Optional[str]) -> None:
    """Current heading metric + compass direction."""
    st.metric("Heading", f"{heading:.0f}°", delta=_compass(heading))
    if action:
        st.caption(f"Last action: **{action}**")


# ---------------------------------------------------------------------------
# Decision trace
# ---------------------------------------------------------------------------

def _colorize_line(line: str) -> str:
    """Wrap a log line in a colored span based on its prefix tag."""
    for tag, color in _LOG_COLORS.items():
        if tag in line:
            bold = tag in ("[ACTION]", "[RESULT]", "[HARD RULE]")
            style = f"color:{color}; {'font-weight:bold;' if bold else ''}"
            escaped = line.replace("<", "&lt;").replace(">", "&gt;")
            return f'<span style="{style}">{escaped}</span>'
    escaped = line.replace("<", "&lt;").replace(">", "&gt;")
    return f'<span style="color:#cccccc">{escaped}</span>'


def render_decision_trace(event: Optional[CycleEvent]) -> None:
    """Monospace dark div showing all captured log lines for this cycle."""
    if event is None:
        st.caption("No cycle data yet")
        return
    lines_html = "<br>".join(_colorize_line(l) for l in event.logs)
    st.markdown(
        f"""
        <div style="
            background:#1e1e1e;
            border:1px solid #333;
            border-radius:6px;
            padding:12px 16px;
            font-family:monospace;
            font-size:12px;
            line-height:1.6;
            max-height:260px;
            overflow-y:auto;
        ">{lines_html}</div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_cycle_summary(event: Optional[CycleEvent]) -> None:
    """Compact per-cycle explanation of the decision path."""
    if event is None:
        st.caption("No cycle data yet")
        return

    summary = _event_summary(event)
    c1, c2, c3 = st.columns(3)
    c1.metric("Decision Path", summary["path"])
    c2.metric("LLM Invokes", str(summary["llm_invokes"]))
    c3.metric("RAG Consulted", "Yes" if summary["rag_used"] else "No")

    st.caption(f"Context: {summary['context']}")
    st.caption(f"Result: {summary['result']}")


def render_decision_cycles(history: List[CycleEvent]) -> None:
    """Table showing how each cycle was decided so modes are easy to compare."""
    if not history:
        st.caption("No cycles recorded yet")
        return

    import pandas as pd

    rows = []
    for ev in reversed(history):
        summary = _event_summary(ev)
        rows.append({
            "Cycle": ev.step,
            "Time": ev.timestamp,
            "Mode": ev.mode.upper(),
            "Path": summary["path"],
            "RAG": "Yes" if summary["rag_used"] else "No",
            "LLM": summary["llm_invokes"],
            "Action": ev.action or "—",
            "Context": summary["context"],
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Short-term memory table
# ---------------------------------------------------------------------------

def render_stm_table(history: List[CycleEvent]) -> None:
    """Dataframe showing the last 5 cycles: F/L/R/Rear/Action/Heading."""
    if not history:
        st.caption("No cycles recorded yet")
        return

    import pandas as pd

    rows = []
    for ev in history[-5:]:
        ws = ev.world_state
        rows.append({
            "Cycle": ev.step,
            "Time":  ev.timestamp,
            "Front":  f"{ws.front_distance_cm:.0f}",
            "Left":   f"{ws.left_distance_cm:.0f}",
            "Right":  f"{ws.right_distance_cm:.0f}",
            "Rear":   f"{ws.rear_distance_cm:.0f}",
            "Action": ev.action or "—",
            "Heading":f"{ev.heading:.0f}°",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Cycle history expanders
# ---------------------------------------------------------------------------

def render_history(history: List[CycleEvent]) -> None:
    """One expander per completed cycle (newest first)."""
    if not history:
        return
    for ev in reversed(history):
        ws = ev.world_state
        summary = _event_summary(ev)
        label = (
            f"Cycle {ev.step} — {ev.timestamp} | "
            f"{ev.mode.upper()} | "
            f"F:{ws.front_distance_cm:.0f} L:{ws.left_distance_cm:.0f} "
            f"R:{ws.right_distance_cm:.0f} Re:{ws.rear_distance_cm:.0f} | "
            f"{summary['path']} | {ev.action or '—'}"
        )
        with st.expander(label, expanded=False):
            c1, c2 = st.columns([1, 2])
            with c1:
                render_camera_frame(ev.frame_path)
                render_sensors(ws)
            with c2:
                render_decision_cycle_summary(ev)
                render_decision_trace(ev)
