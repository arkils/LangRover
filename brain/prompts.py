"""System prompts for the robot agent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from skills.registry import SkillRegistry
    from world.state import WorldState

ROBOT_SYSTEM_PROMPT = """You are LangRover, an autonomous robot navigating an environment using sensors and a camera.

Your Role:
- Explore the environment intelligently
- Interact with detected objects and people using the appropriate skill
- React intelligently to detected objects using skills or navigation
- Execute exactly ONE tool call per decision cycle

Available tool categories:
1. Navigation primitives: move_forward, turn_left, turn_right, stop
2. Skills: named behaviours triggered by specific detected objects (e.g. greet_person, greet_cat, greet_dog)

Safety Rules (non-negotiable):
1. NEVER call move_forward if front_distance_cm < 30 cm
2. NEVER turn toward a side whose distance < 25 cm
3. When uncertain: call stop

Interaction Rules:
- When people_count > 0 or 'person' is detected: call greet_person
- After greeting, resume normal navigation

Navigation Strategy:
- front clear (>= 30 cm): move_forward
- front blocked, more space left: turn_left
- front blocked, more space right: turn_right
- all sides blocked: stop

Skill Strategy:
- Check RELEVANT SKILLS in the prompt — these match the current detected objects
- Prefer skills over raw navigation when a known object is detected

You MUST call exactly one tool. Do not reply with plain text.

Knowledge Base Tool (Agentic RAG — hybrid mode only):
- query_knowledge_base: Call this when the situation is ambiguous or novel and
  you want to consult stored navigation rules.  Skip it when the situation is
  clear (e.g. an obvious obstacle or a well-known object in front of you).
"""


def build_human_prompt(
    world_state: "WorldState",
    skill_registry: "SkillRegistry",
    memories: Optional[str] = None,
    rag_context: Optional[str] = None,
    short_term_context: Optional[str] = None,
) -> str:
    """Build the human-turn message for the LLM.

    Args:
        world_state: Current sensor + vision snapshot.
        skill_registry: Registry used to surface relevant skill hints.
        memories: Optional long-term memory context block from
            ``RobotMemory.retrieve()``.  Injected verbatim when provided.
        rag_context: Optional retrieved rules from ``RAGKnowledgeBase.retrieve()``
            (Traditional RAG mode).  Injected as a distinct section.
        short_term_context: Optional rolling session buffer summary from
            ``ShortTermMemory.summarise()``.  Injected as a distinct section.

    Returns:
        Formatted multi-line string ready to send as a ``HumanMessage``.
    """
    v = world_state.vision

    # Vision section
    if v.objects or v.people_count or v.motion_detected:
        vision_lines = []
        for obj in v.objects:
            vision_lines.append(
                f"  - {obj.name} ({obj.confidence:.0%} confidence, "
                f"pos {obj.x:.2f},{obj.y:.2f})"
            )
        if v.people_count:
            vision_lines.append(
                f"  - PEOPLE DETECTED: {v.people_count} person(s) — use greet_person"
            )
        if v.motion_detected:
            vision_lines.append("  - Motion detected")
        vision_section = "\n" + "\n".join(vision_lines)
    else:
        vision_section = " No objects detected"

    # Compute explicit recommended action based on sensor data and detections
    detected_names = [obj.name for obj in v.objects]

    # Person/cat/dog — greet takes priority
    if v.people_count > 0 or "person" in detected_names:
        recommendation = "RECOMMENDED ACTION: call greet_person — a person is detected."
    elif "cat" in detected_names:
        recommendation = "RECOMMENDED ACTION: call greet_cat — a cat is detected."
    elif "dog" in detected_names:
        recommendation = "RECOMMENDED ACTION: call greet_dog — a dog is detected."
    else:
        front = world_state.front_distance_cm
        left = world_state.left_distance_cm
        right = world_state.right_distance_cm
        if front >= 30:
            recommendation = f"RECOMMENDED ACTION: call move_forward — front is clear ({front:.0f} cm)."
        elif left >= right and left >= 25:
            recommendation = f"RECOMMENDED ACTION: call turn_left — left has more space ({left:.0f} cm vs right {right:.0f} cm)."
        elif right >= 25:
            recommendation = f"RECOMMENDED ACTION: call turn_right — right has more space ({right:.0f} cm)."
        else:
            recommendation = "RECOMMENDED ACTION: call stop — all directions blocked."

    triggered = skill_registry.get_triggered_skills(detected_names)
    skill_hint = ""
    if triggered:
        names = ", ".join(s.name for s in triggered)
        skill_hint = f"\nRELEVANT SKILLS for detected objects: {names}\n"

    # Memory context block (long-term — ChromaDB across runs)
    memory_section = ""
    if memories and memories.strip():
        memory_section = f"\n{memories.strip()}\n"

    # RAG context block (Traditional RAG — pre-retrieved rules)
    rag_section = ""
    if rag_context and rag_context.strip():
        rag_section = f"\n{rag_context.strip()}\n"

    # Short-term memory block (this session, rolling buffer)
    short_term_section = ""
    if short_term_context and short_term_context.strip():
        short_term_section = f"\n{short_term_context.strip()}\n"

    return (
        f"Current robot state:\n\n"
        f"DISTANCE SENSORS:\n"
        f"  Front: {world_state.front_distance_cm} cm\n"
        f"  Left:  {world_state.left_distance_cm} cm\n"
        f"  Right: {world_state.right_distance_cm} cm\n"
        f"  Rear:  {world_state.rear_distance_cm} cm\n"
        f"  Target visible: {world_state.target_visible}\n\n"
        f"VISION:{vision_section}\n"
        f"{skill_hint}"
        f"{short_term_section}"
        f"{memory_section}"
        f"{rag_section}\n"
        f"Choose the best tool to call."
    )

