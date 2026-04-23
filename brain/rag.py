"""RAG Knowledge Base for LangRover.

Stores static navigation rules that the agent can retrieve at runtime.
Used to demonstrate the difference between:
- Traditional RAG  (DECISION_MODE=rag):  always retrieved before LLM call
- Agentic RAG      (DECISION_MODE=hybrid): exposed as a LangChain tool the
  LLM decides to call or skip each cycle
"""

import uuid

from world.state import WorldState


# ---------------------------------------------------------------------------
# Default navigation rules
# ---------------------------------------------------------------------------

_DEFAULT_RULES: list[str] = [
    # Obstacle avoidance
    "When front distance < 30cm, never move forward. Turn to the side with more space.",
    "When front < 30cm and left > right, turn left to avoid obstacle.",
    "When front < 30cm and right > left, turn right to avoid obstacle.",
    "When front < 30cm and left < 25cm and right < 25cm, stop immediately — fully blocked.",
    "When left distance < 25cm, do not turn left — risk of collision.",
    "When right distance < 25cm, do not turn right — risk of collision.",
    # Open path
    "When front > 80cm and left > 50cm and right > 50cm, move forward confidently.",
    "When front > 50cm, prefer moving forward over turning unless a target is visible.",
    "When all sensors > 100cm, increase forward distance to 40cm for efficiency.",
    # Object detection reactions
    "When a person is detected, stop and call the greet_person skill. Do not move toward them.",
    "When a cat is detected, call the greet_cat skill for a friendly tail-wag motion.",
    "When a dog is detected, call the greet_dog skill for a gentle bow motion.",
    "When an unknown object is detected at confidence < 0.5, treat as no detection.",
    # General navigation
    "Prefer the direction with the greatest sensor distance when choosing to turn.",
    "After turning, always check sensor readings before moving forward again.",
]


class RAGKnowledgeBase:
    """ChromaDB-backed static knowledge base of navigation rules.

    Rules are pre-populated once and then retrieved at runtime via
    semantic similarity against the current world state.

    Args:
        persist_dir: Directory where ChromaDB stores its data on disk.
    """

    def __init__(self, persist_dir: str = "./chroma_rag") -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._rules = self._client.get_or_create_collection("navigation_rules")

    def populate_defaults(self) -> None:
        """Populate the knowledge base with default navigation rules.

        Only runs when the collection is empty — safe to call on every
        startup without creating duplicates.
        """
        if self._rules.count() > 0:
            return

        self._rules.add(
            documents=_DEFAULT_RULES,
            ids=[str(uuid.uuid4()) for _ in _DEFAULT_RULES],
        )
        print(f"[RAG KB] Populated {len(_DEFAULT_RULES)} navigation rules.")

    def retrieve(self, world_state: WorldState, k: int = 3) -> str:
        """Retrieve the most relevant navigation rules for the current state.

        Builds a natural-language query from sensor readings and detected
        objects, then performs a semantic similarity search.

        Args:
            world_state: Current sensor + vision snapshot.
            k: Maximum number of rules to return.

        Returns:
            Formatted multi-line string ready to inject into the LLM prompt,
            or an empty string if the knowledge base is empty.
        """
        count = self._rules.count()
        if count == 0:
            return ""

        # Build query from current sensor state + detected objects
        objects_str = ""
        if world_state.vision.objects:
            names = [o.name for o in world_state.vision.objects]
            objects_str = f" Objects detected: {', '.join(names)}."

        query = (
            f"Front={world_state.front_distance_cm:.0f}cm, "
            f"Left={world_state.left_distance_cm:.0f}cm, "
            f"Right={world_state.right_distance_cm:.0f}cm.{objects_str}"
        )

        results = self._rules.query(
            query_texts=[query],
            n_results=min(k, count),
        )

        docs: list[str] = results.get("documents", [[]])[0]
        if not docs:
            return ""

        lines = ["[RAG Knowledge Base — Retrieved Rules]"]
        for i, doc in enumerate(docs, 1):
            lines.append(f"  Rule {i}: {doc}")
        return "\n".join(lines)
