"""Persistent memory for LangRover using ChromaDB.

Two collections:
- ``decisions``: past sensor readings + actions taken (so the LLM can recall
  what worked in similar situations).
- ``observations``: YOLO detections with heading + distance (semantic map).
"""

import time
import uuid

from world.state import WorldState


class RobotMemory:
    """ChromaDB-backed persistent memory with two collections.

    Args:
        persist_dir: Directory where ChromaDB stores its data on disk.
    """

    def __init__(self, persist_dir: str = "./chroma_db") -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._decisions = self._client.get_or_create_collection("decisions")
        self._observations = self._client.get_or_create_collection("observations")

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def store_decision(
        self, world_state: WorldState, action: str, reasoning: str = ""
    ) -> None:
        """Store a completed decision so similar future states can recall it.

        Args:
            world_state: Sensor snapshot at decision time.
            action: Tool name that was executed (e.g. ``"turn_left"``).
            reasoning: Optional free-text explanation appended to the document.
        """
        doc = (
            f"Front={world_state.front_distance_cm:.0f}cm, "
            f"Left={world_state.left_distance_cm:.0f}cm, "
            f"Right={world_state.right_distance_cm:.0f}cm → {action}"
        )
        if reasoning:
            doc += f" — {reasoning}"

        self._decisions.add(
            documents=[doc],
            ids=[str(uuid.uuid4())],
            metadatas=[{"ts": int(time.time()), "action": action}],
        )

    def store_observation(self, world_state: WorldState, heading_deg: float) -> None:
        """Store a YOLO observation in the semantic map.

        Only stored when at least one object is detected.

        Args:
            world_state: Sensor + vision snapshot.
            heading_deg: Current accumulated heading (degrees from start).
        """
        objects = world_state.vision.objects
        if not objects:
            return

        obj_str = ", ".join(
            f"{o.name}({o.confidence:.2f})" for o in objects
        )
        doc = (
            f"{obj_str} | heading={heading_deg:.0f}° | "
            f"front_dist={world_state.front_distance_cm:.0f}cm | "
            f"ts={int(time.time())}"
        )
        self._observations.add(
            documents=[doc],
            ids=[str(uuid.uuid4())],
            metadatas=[{
                "ts": int(time.time()),
                "heading": heading_deg,
                "front_dist": world_state.front_distance_cm,
            }],
        )

    # ------------------------------------------------------------------
    # Read helper
    # ------------------------------------------------------------------

    def retrieve(self, world_state: WorldState, k: int = 3) -> str:
        """Return a formatted context block with past decisions + observations.

        Queries both collections using the current sensor state as the search
        vector and returns the top-*k* results from each, formatted for direct
        injection into the LLM prompt.

        Args:
            world_state: Current sensor snapshot (used as the query).
            k: Maximum number of results to return per collection.

        Returns:
            Multi-line string ready to embed in the human prompt, or an empty
            string when both collections are empty.
        """
        query = (
            f"Front={world_state.front_distance_cm:.0f}cm, "
            f"Left={world_state.left_distance_cm:.0f}cm, "
            f"Right={world_state.right_distance_cm:.0f}cm"
        )
        lines: list[str] = []

        # -- Past decisions --------------------------------------------------
        try:
            count = self._decisions.count()
            if count > 0:
                results = self._decisions.query(
                    query_texts=[query],
                    n_results=min(k, count),
                )
                docs = results.get("documents", [[]])[0]
                if docs:
                    lines.append("PAST DECISIONS (similar sensor state):")
                    for doc in docs:
                        lines.append(f"  - {doc}")
        except Exception:
            pass

        # -- Semantic map observations ----------------------------------------
        try:
            count = self._observations.count()
            if count > 0:
                results = self._observations.query(
                    query_texts=[query],
                    n_results=min(k, count),
                )
                obs_docs = results.get("documents", [[]])[0]
                if obs_docs:
                    lines.append("\nSEMANTIC MAP (what you have seen):")
                    for doc in obs_docs:
                        lines.append(f"  - {doc}")
        except Exception:
            pass

        return "\n".join(lines)
