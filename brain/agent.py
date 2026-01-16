"""LangChain agent for autonomous robot decision-making."""

from typing import Any

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage

from actions.base import RobotActions
from brain.prompts import ROBOT_SYSTEM_PROMPT
from models.llm import get_llm
from world.state import WorldState


def create_agent(robot_actions: RobotActions, llm_provider: str = "ollama") -> dict:
    """
    Create a simple agent for autonomous robot control.

    Uses the LLM to decide actions based on sensor input.

    Args:
        robot_actions: Implementation of RobotActions interface.
        llm_provider: LLM provider to use ("openai" or "ollama").

    Returns:
        Dictionary containing the llm and robot_actions for use in decide_and_act.
    """
    llm = get_llm(llm_provider)

    return {
        "llm": llm,
        "robot_actions": robot_actions,
    }


def decide_and_act(
    agent: dict,
    world_state: WorldState,
) -> None:
    """
    Get decision from LLM and execute one action based on sensors and vision.

    Args:
        agent: Dictionary containing llm and robot_actions.
        world_state: Current state of the world (sensors + vision).
    """
    llm = agent["llm"]
    robot_actions = agent["robot_actions"]

    # Build detailed sensor report
    vision_report = ""
    if world_state.vision.objects:
        object_list = ", ".join([
            f"{obj.name}({obj.confidence:.0%} confidence at position {obj.x:.1f},{obj.y:.1f})"
            for obj in world_state.vision.objects
        ])
        vision_report += f"\n- Detected objects: {object_list}"

    if world_state.vision.people_count > 0:
        vision_report += f"\n- PEOPLE DETECTED: {world_state.vision.people_count} person(s)"

    if world_state.vision.motion_detected:
        vision_report += "\n- Motion detected in environment"

    # Format world state for the LLM
    sensor_input = f"""Current robot state:
DISTANCE SENSORS:
- Front: {world_state.front_distance_cm} cm
- Left: {world_state.left_distance_cm} cm
- Right: {world_state.right_distance_cm} cm
- Target visible: {world_state.target_visible}

VISION SENSORS:{vision_report if vision_report else " No objects detected"}

{ROBOT_SYSTEM_PROMPT}

Based on the current sensor and vision data, decide ONE of the following actions:
1. Move forward (specify distance 10-50 cm)
2. Turn left (specify degrees 30-90)
3. Stop

Respond with ONLY the action and parameter, nothing else. Format: "ACTION: value"
Example: "ACTION: move_forward 30" or "ACTION: turn_left 45" or "ACTION: stop"

Your decision:"""

    try:
        # Get LLM decision
        print(f"[SENSORS] {world_state}")
        print(f"[AGENT] Consulting...")
        
        response = llm.invoke(sensor_input)
        decision = response.content.strip().lower() if hasattr(response, 'content') else str(response).lower()
        
        print(f"[DECISION] {decision}")

        # SAFETY: If people detected, always stop
        if world_state.vision.people_count > 0:
            print("[SAFETY] People detected! Stopping immediately.")
            robot_actions.stop()
            print(f"[EXECUTED] STOP (people safety protocol)")
            return

        # Parse and execute action
        if "move_forward" in decision:
            try:
                distance = int(''.join(filter(str.isdigit, decision.split("move_forward")[-1])).split()[0] or "30")
                distance = min(max(distance, 10), 100)  # Clamp between 10-100 cm
                robot_actions.move_forward(distance)
                print(f"[EXECUTED] move_forward {distance} cm")
            except:
                robot_actions.move_forward(30)
                print(f"[EXECUTED] move_forward 30 cm (default)")

        elif "turn_left" in decision:
            try:
                degrees = int(''.join(filter(str.isdigit, decision.split("turn_left")[-1])).split()[0] or "45")
                degrees = min(max(degrees, 15), 90)  # Clamp between 15-90 degrees
                robot_actions.turn_left(degrees)
                print(f"[EXECUTED] turn_left {degrees} degrees")
            except:
                robot_actions.turn_left(45)
                print(f"[EXECUTED] turn_left 45 degrees (default)")

        elif "stop" in decision:
            robot_actions.stop()
            print(f"[EXECUTED] stop")

        else:
            # Default: move forward
            robot_actions.move_forward(30)
            print(f"[EXECUTED] move_forward 30 cm (default fallback)")

    except Exception as e:
        print(f"[ERROR] Agent error: {e}")
        robot_actions.stop()
        print(f"[SAFETY] Stopped robot")
