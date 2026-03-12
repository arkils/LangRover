---
description: "Use when you want to understand how LangRover works end-to-end, trace a single decision cycle, explore the architecture, or find out where to add something new."
argument-hint: "Optional: a specific part to focus on (e.g. 'vision pipeline', 'how skills are selected', 'simulation vs real hardware')"
agent: "agent"
---

Explain how LangRover works, tracing a complete decision cycle from start to finish.

Cover these steps in order:

1. **Entry point** — what `main.py` initialises (Config, SkillRegistry, RobotActions, agent) and how the main loop runs
2. **World state** — how `read_world_state()` in `world/simulator.py` builds a `WorldState`: sensor branch (real `SensorArray` vs. random floats) and vision branch (real YOLO via `vision/vision.py` + `vision/camera.py` vs. `MockVisionDetector`)
3. **Safety pre-checks** — which hard-coded rules run in `brain/agent.py` *before* the LLM is consulted (`people_count > 0` → instant stop; `front_distance_cm < 30` → block move_forward)
4. **LLM decision** — how `decide_and_act()` builds the prompt (`brain/prompts.py` `ROBOT_SYSTEM_PROMPT`), binds tools via `llm.bind_tools(nav_tools + skill_tools)`, and calls `llm.invoke([SystemMessage, HumanMessage])` — emphasise this is a **single invoke call, not a ReAct loop**
5. **Tool dispatch** — how the tool call result is parsed: real `tool_calls` on the response vs. the keyword text-parse fallback
6. **Navigation tools** — the four `StructuredTool` closures (move_forward, turn_left, turn_right, stop) built in `_build_navigation_tools()`, each delegating to `RobotActions`
7. **Skills dispatch** — how `SkillRegistry` turns each `Skill` into a LangChain tool; how `trigger_objects` is used to surface relevant skills in the prompt; how `execute(SkillContext)` runs
8. **Actions layer** — `CLIRobotActions` (simulation: prints to console) vs. `GPIORobotActions` (real hardware: calls `MotorController` → `ESP32Serial` JSON commands over USB)
9. **Simulation vs. real-hardware switch points** — list every env var that flips a layer (`USE_GPIO_ACTIONS`, `USE_REAL_SENSORS`, `USE_REAL_VISION`) and which file reads it

After the trace, add a short section: **"Where to add things"**
- New skill → `skills/` subclass + `main.py` registration
- New navigation primitive → `actions/base.py` ABC + both concrete impls
- New LLM provider → `models/llm.py` `get_llm()` + `config.py` env vars
- New sensor type → `hardware/sensors.py` + `world/simulator.py` `read_world_state()`

Reference actual file paths throughout (e.g. `brain/agent.py`, `world/simulator.py`).
If the user specified a focus area in their message, go deeper on that part.
