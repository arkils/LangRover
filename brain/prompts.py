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
"""


def build_human_prompt(
    world_state: "WorldState",
    skill_registry: "SkillRegistry",
    memories: Optional[str] = None,
) -> str:
    """Build the human-turn message for the LLM.

    Args:
        world_state: Current sensor + vision snapshot.
        skill_registry: Registry used to surface relevant skill hints.
        memories: Optional pre-formatted memory context block from
            ``RobotMemory.retrieve()``.  Injected verbatim when provided.

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

    # Relevant skill hints
    detected_names = [obj.name for obj in v.objects]
    triggered = skill_registry.get_triggered_skills(detected_names)
    skill_hint = ""
    if triggered:
        names = ", ".join(s.name for s in triggered)
        skill_hint = f"\nRELEVANT SKILLS for detected objects: {names}\n"

    # Memory context block (Phase 2)
    memory_section = ""
    if memories and memories.strip():
        memory_section = f"\n{memories.strip()}\n"

    return (
        f"Current robot state:\n\n"
        f"DISTANCE SENSORS:\n"
        f"  Front: {world_state.front_distance_cm} cm\n"
        f"  Left:  {world_state.left_distance_cm} cm\n"
        f"  Right: {world_state.right_distance_cm} cm\n"
        f"  Target visible: {world_state.target_visible}\n\n"
        f"VISION:{vision_section}\n"
        f"{skill_hint}"
        f"{memory_section}\n"
        f"Choose the best tool to call."
    )

