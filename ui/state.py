"""Shared state between the robot worker thread and the Streamlit UI."""

import threading
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from world.state import WorldState


@dataclass
class CycleEvent:
    """Snapshot of one complete decision cycle."""

    step: int
    timestamp: str
    world_state: WorldState
    heading: float
    logs: List[str]           # raw stdout lines captured from decide_and_act
    action: Optional[str]     # last action name parsed from "[ACTION]  >>" line
    mode: str
    frame_path: Optional[str] = None  # absolute path to the saved JPEG for this cycle


class UIState:
    """Thread-safe shared state consumed by the Streamlit UI."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.history: List[CycleEvent] = []
        self.status: str = "idle"   # idle | starting | running | paused | done | stopped | error
        self.error_msg: str = ""
        self.total_steps: int = 0

    # ------------------------------------------------------------------
    # Mutators (always hold the lock)
    # ------------------------------------------------------------------

    def append(self, event: CycleEvent) -> None:
        with self._lock:
            self.history.append(event)

    def set_status(self, status: str, error_msg: str = "") -> None:
        with self._lock:
            self.status = status
            self.error_msg = error_msg

    def set_total(self, total: int) -> None:
        with self._lock:
            self.total_steps = total

    def reset(self) -> None:
        with self._lock:
            self.history = []
            self.status = "idle"
            self.error_msg = ""
            self.total_steps = 0

    # ------------------------------------------------------------------
    # Read-only snapshot — returns copies so the UI works without holding
    # the lock for the entire render pass
    # ------------------------------------------------------------------

    def snapshot(self) -> Tuple[List[CycleEvent], str, str, int]:
        """Return (history_copy, status, error_msg, total_steps)."""
        with self._lock:
            return list(self.history), self.status, self.error_msg, self.total_steps
