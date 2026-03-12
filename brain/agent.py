"""LangChain agent for autonomous robot decision-making."""

from typing import List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import StructuredTool

from actions.base import RobotActions
from brain.prompts import ROBOT_SYSTEM_PROMPT
from models.llm import get_llm
from skills.base import SkillContext
from skills.registry import SkillRegistry
from world.state import WorldState


# ---------------------------------------------------------------------------
# Navigation tool factory
# ---------------------------------------------------------------------------

def _build_navigation_tools(robot_actions: RobotActions) -> List[StructuredTool]:
    """
    Build LangChain tools for the four navigation primitives.

    Each tool is a closure over ``robot_actions`` so the LLM can call them
    without any extra context.
    """

    def move_forward(distance_cm: int) -> str:
        """Move the robot forward. distance_cm must be between 10 and 100."""
        distance_cm = max(10, min(100, distance_cm))
        robot_actions.move_forward(distance_cm)
        return f"Moved forward {distance_cm} cm"

    def turn_left(degrees: int) -> str:
        """Turn the robot left (counter-clockwise). degrees must be between 15 and 90."""
        degrees = max(15, min(90, degrees))
        robot_actions.turn_left(degrees)
        return f"Turned left {degrees} degrees"

    def turn_right(degrees: int) -> str:
        """Turn the robot right (clockwise). degrees must be between 15 and 90."""
        degrees = max(15, min(90, degrees))
        robot_actions.turn_right(degrees)
        return f"Turned right {degrees} degrees"

    def stop() -> str:
        """Stop all robot movement immediately. Use when blocked, uncertain, or when a person is nearby."""
        robot_actions.stop()
        return "Robot stopped"

    return [
        StructuredTool.from_function(move_forward, name="move_forward"),
        StructuredTool.from_function(turn_left, name="turn_left"),
        StructuredTool.from_function(turn_right, name="turn_right"),
        StructuredTool.from_function(stop, name="stop"),
    ]


# ---------------------------------------------------------------------------
# Agent lifecycle
# ---------------------------------------------------------------------------

def create_agent(
    robot_actions: RobotActions,
    skill_registry: SkillRegistry,
    llm_provider: str = "ollama",
    ollama_model: str | None = None,
) -> dict:
    """
    Create the robot agent.

    Args:
        robot_actions: Hardware or CLI action implementation.
        skill_registry: Registry of registered robot skills.
        llm_provider: ``"openai"`` or ``"ollama"``.
        ollama_model: Ollama model name; overrides ``OLLAMA_MODEL`` env var.

    Returns:
        Agent dict passed to ``decide_and_act()`` each cycle.
    """
    llm = get_llm(llm_provider, ollama_model=ollama_model)
    return {
        "llm": llm,
        "robot_actions": robot_actions,
        "skill_registry": skill_registry,
    }


# ---------------------------------------------------------------------------
# Decision cycle
# ---------------------------------------------------------------------------

def decide_and_act(agent: dict, world_state: WorldState) -> None:
    """
    Run one decision cycle: read world state → call LLM with tools → execute.

    Flow:
    1. Hard safety check (people detected → stop, no LLM call).
    2. Build navigation tools + all registered skill tools.
    3. Bind tools to the LLM (``llm.bind_tools``).
    4. Send system prompt + world state snapshot as a HumanMessage.
    5. If the LLM returns tool_calls → execute each one in order.
    6. If the LLM returns plain text (models without tool-calling support)
       → fall back to text-based parsing.

    Args:
        agent: Dict from ``create_agent()``.
        world_state: Current sensor + vision snapshot.
    """
    llm = agent["llm"]
    robot_actions: RobotActions = agent["robot_actions"]
    skill_registry: SkillRegistry = agent["skill_registry"]

    # ------------------------------------------------------------------
    # 1. Hard safety check — runs BEFORE consulting the LLM
    # ------------------------------------------------------------------
    # Note: people are friendly — robot greets them via greet_person skill.
    # Only obstacle distances trigger hard safety blocks.

    # ------------------------------------------------------------------
    # 2. Build tools
    # ------------------------------------------------------------------
    skill_context = SkillContext(world_state=world_state, robot_actions=robot_actions)
    nav_tools = _build_navigation_tools(robot_actions)
    skill_tools = skill_registry.to_langchain_tools(skill_context)
    all_tools = nav_tools + skill_tools

    # ------------------------------------------------------------------
    # 3. Build messages
    # ------------------------------------------------------------------
    human_msg = HumanMessage(content=_build_human_prompt(world_state, skill_registry))
    messages = [SystemMessage(content=ROBOT_SYSTEM_PROMPT), human_msg]

    print(f"[SENSORS] {world_state}")
    tool_names = ", ".join(t.name for t in all_tools)
    print(f"[AGENT] Consulting LLM | tools: [{tool_names}]")

    # ------------------------------------------------------------------
    # 4. Invoke LLM with bound tools
    # ------------------------------------------------------------------
    try:
        llm_with_tools = llm.bind_tools(all_tools)
        response = llm_with_tools.invoke(messages)

        # ------------------------------------------------------------------
        # 5. Execute tool calls (preferred path)
        # ------------------------------------------------------------------
        tool_calls = getattr(response, "tool_calls", None)
        if tool_calls:
            tool_map = {t.name: t for t in all_tools}
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                matched = tool_map.get(tool_name)
                if matched:
                    print(f"[TOOL] {tool_name}({tool_args})")
                    matched.invoke(tool_args)
                else:
                    print(f"[WARNING] LLM called unknown tool '{tool_name}' — ignoring")
            return

        # ------------------------------------------------------------------
        # 6. Text fallback (models without native tool-calling support)
        # ------------------------------------------------------------------
        content = (
            response.content.strip().lower()
            if hasattr(response, "content")
            else str(response).strip().lower()
        )
        print(f"[FALLBACK] No tool calls received — parsing text: {content[:80]}")
        _execute_text_fallback(content, robot_actions)

    except Exception as e:
        print(f"[ERROR] Agent error: {e}")
        robot_actions.stop()
        print("[SAFETY] Stopped robot after agent error")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_human_prompt(world_state: WorldState, skill_registry: SkillRegistry) -> str:
    """Format the current world state into a human message for the LLM."""
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

    return (
        f"Current robot state:\n\n"
        f"DISTANCE SENSORS:\n"
        f"  Front: {world_state.front_distance_cm} cm\n"
        f"  Left:  {world_state.left_distance_cm} cm\n"
        f"  Right: {world_state.right_distance_cm} cm\n"
        f"  Target visible: {world_state.target_visible}\n\n"
        f"VISION:{vision_section}\n"
        f"{skill_hint}\n"
        f"Choose the best tool to call."
    )


def _execute_text_fallback(decision: str, robot_actions: RobotActions) -> None:
    """Parse a plain-text LLM response and execute the best matching action."""

    def _extract_int(text: str, default: int) -> int:
        digits = "".join(c for c in text if c.isdigit())
        return int(digits[:4]) if digits else default

    if "move_forward" in decision:
        distance = max(10, min(100, _extract_int(decision.split("move_forward")[-1], 30)))
        robot_actions.move_forward(distance)
        print(f"[EXECUTED] move_forward {distance} cm")
    elif "turn_right" in decision:
        degrees = max(15, min(90, _extract_int(decision.split("turn_right")[-1], 45)))
        robot_actions.turn_right(degrees)
        print(f"[EXECUTED] turn_right {degrees} degrees")
    elif "turn_left" in decision:
        degrees = max(15, min(90, _extract_int(decision.split("turn_left")[-1], 45)))
        robot_actions.turn_left(degrees)
        print(f"[EXECUTED] turn_left {degrees} degrees")
    elif "stop" in decision:
        robot_actions.stop()
        print("[EXECUTED] stop")
    else:
        robot_actions.move_forward(30)
        print("[EXECUTED] move_forward 30 cm (default fallback)")



