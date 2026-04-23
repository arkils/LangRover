"""Main entry point for LangRover autonomous robot."""

import time
import sys
import os

# Fix encoding for Windows console
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

from dotenv import load_dotenv
load_dotenv()  # loads .env from the project root before Config reads env vars

from config import Config
from brain.agent import create_agent, decide_and_act
from skills import SkillRegistry, get_default_skills
from world.simulator import read_world_state


def main() -> None:
    """Run the LangRover autonomous robot loop."""
    # Load configuration
    config = Config()

    print("=" * 60)
    print("[ROBOT] LangRover - Autonomous Robot Framework")
    print("=" * 60)
    print(f"LLM Provider: {config.LLM_PROVIDER}")
    print(f"Hardware Mode: {'GPIO (Real)' if config.USE_GPIO_ACTIONS else 'CLI (Simulation)'}")
    print(f"Sensors: {'Real Ultrasonic' if config.USE_REAL_SENSORS else 'Simulated'}")
    print(f"Vision: {'Real YOLO' if config.USE_REAL_VISION else 'Mock'}")
    print(f"Simulation Steps: {config.SIMULATION_STEPS}")
    print("=" * 60)
    print()

    # Build skill registry with default built-in skills.
    # Register additional skills here before create_agent() is called.
    skill_registry = SkillRegistry()
    for skill in get_default_skills():
        skill_registry.register(skill)
    print()

    # Initialize robot actions (GPIO or CLI)
    if config.USE_GPIO_ACTIONS:
        try:
            from actions.gpio_actions import GPIORobotActions
            robot_actions = GPIORobotActions(default_speed=config.DEFAULT_MOTOR_SPEED)
            print("[ACTIONS] Using GPIO hardware control")
        except Exception as e:
            print(f"[WARNING] GPIO actions failed: {e}")
            print("[ACTIONS] Falling back to CLI simulation")
            from actions.cli_actions import CLIRobotActions
            robot_actions = CLIRobotActions()
    else:
        from actions.cli_actions import CLIRobotActions
        robot_actions = CLIRobotActions()
        print("[ACTIONS] Using CLI simulation")

    # Initialise memory (long-term ChromaDB) — only if USE_MEMORY=true
    robot_memory = None
    if config.USE_MEMORY:
        from brain.memory import RobotMemory
        robot_memory = RobotMemory(persist_dir=config.CHROMA_PERSIST_DIR)
        print(f"[MEMORY] Long-term ChromaDB enabled — persisting to {config.CHROMA_PERSIST_DIR}")
    else:
        print("[MEMORY] Long-term memory disabled (set USE_MEMORY=true to enable)")

    # Initialise short-term memory (Week 4 — always on, in-process deque)
    from brain.memory import ShortTermMemory
    short_term_memory = ShortTermMemory(max_cycles=config.SHORT_TERM_MEMORY_CYCLES)
    print(f"[MEMORY] Short-term memory enabled — rolling window: {config.SHORT_TERM_MEMORY_CYCLES} cycles")

    # Initialise RAG knowledge base (Week 4 — rag and hybrid modes)
    rag_kb = None
    mode = config.DECISION_MODE.lower()
    print(f"[AGENT] Decision mode: {mode.upper()}")
    if mode in ("rag", "hybrid"):
        from brain.rag import RAGKnowledgeBase
        rag_kb = RAGKnowledgeBase(persist_dir=config.RAG_KNOWLEDGE_DIR)
        rag_kb.populate_defaults()

    # Create agent
    agent = create_agent(
        robot_actions,
        skill_registry,
        llm_provider=config.LLM_PROVIDER,
        ollama_model=config.OLLAMA_MODEL,
        memory=robot_memory,
        rag_kb=rag_kb,
        short_term_memory=short_term_memory,
    )

    # Main control loop
    try:
        for step in range(1, config.SIMULATION_STEPS + 1):
            print(f"\n--- Decision Cycle {step} ---")

            # Read current world state (real sensors or simulated)
            world_state = read_world_state()
            front_flag = " [!!BLOCKED]" if world_state.front_distance_cm < config.MIN_SAFE_DISTANCE_CM else ""
            print(
                f"[SENSORS] Front: {world_state.front_distance_cm:.0f}cm{front_flag}"
                f" | Left: {world_state.left_distance_cm:.0f}cm"
                f" | Right: {world_state.right_distance_cm:.0f}cm"
                f" | Rear: {world_state.rear_distance_cm:.0f}cm"
            )
            _obj_parts = [f"{o.name}({o.confidence:.0%})" for o in world_state.vision.objects]
            if world_state.vision.people_count > 0:
                _obj_parts.append(f"{world_state.vision.people_count} person(s)")
            if world_state.vision.motion_detected:
                _obj_parts.append("motion")
            print(f"[VISION]  {', '.join(_obj_parts) if _obj_parts else 'no objects detected'}")

            # Get agent decision and execute action
            decide_and_act(agent, world_state)

            # Wait before next cycle
            if step < config.SIMULATION_STEPS:
                time.sleep(config.DECISION_CYCLE_DELAY_SECONDS)

        print("\n" + "=" * 60)
        print("[SUCCESS] Simulation complete")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        robot_actions.stop()
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        robot_actions.stop()
        raise
    finally:
        # Cleanup GPIO resources if using hardware
        if config.USE_GPIO_ACTIONS and hasattr(robot_actions, 'cleanup'):
            robot_actions.cleanup()


if __name__ == "__main__":
    main()
