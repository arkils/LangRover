# LangRover — Multi-Agent Implementation Plan

This document is the authoritative implementation plan derived from `MULTI_AGENT_PLAN.md`.
It captures all decisions made and provides a precise, phase-by-phase breakdown of what
to build, what to change, and how to verify each phase.

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Memory backend | ChromaDB (persistent) | Survives restarts; built-in embedding |
| Multi-agent execution | Parallel (`asyncio.gather`) | Lower wall-clock time per cycle |
| Agent diversity | Different models per agent | More realistic decision diversity |
| Implementation pace | Strictly incremental | Each phase must pass tests before the next starts |

---

## Architecture Evolution

```
Phase 1 (now):   World → Agent → Action

Phase 2:         World → Agent + Memory (ChromaDB) → Action

Phase 3:         World → ReAct Agent (multi-step reasoning) → Action

Phase 4:         World → Agent [RAG on/off toggle] → Action

Phase 5-6:       World → SafeAgent  ─┐
                        FastAgent   ─┼─ Orchestrator → Final Action
                        Explorer    ─┘

Phase 7:         Same as above + Metrics recorder
```

---

## Current State — Phase 1 ✅ Complete

The core single-agent loop is already implemented. No changes needed for Week 1.

| File | Role |
|---|---|
| `brain/agent.py` | `decide_and_act()` — single LLM call per cycle |
| `brain/prompts.py` | `ROBOT_SYSTEM_PROMPT` |
| `skills/` | Extensible via `Skill` ABC + `SkillRegistry` |
| `world/state.py` | `WorldState`, `VisionData`, `DetectedObject` (Pydantic) |
| `config.py` | All env vars |
| `main.py` | Main loop |
| `models/llm.py` | OpenAI + Ollama providers |

---

## Phase 2 — Memory Layer + Semantic Map (Week 2)

### Goal
Give the agent persistent memory so it learns from past decisions and builds a semantic
map of its environment using YOLO detections.

### Two ChromaDB Collections

**Collection 1 — `decisions`**
Stores past sensor readings and the action taken, so the agent can recall what worked
in similar situations.

Example document:
```
"Front=22cm, Left=80cm, Right=15cm → turned_left 45° → obstacle cleared"
```

**Collection 2 — `observations`** (semantic map)
Stores YOLO detections with estimated heading and distance at time of observation.
Heading is accumulated from turn commands (no encoder needed).
Distance is approximated from the front ultrasonic reading at detection time.

Example document:
```
"sofa(0.89), TV(0.91) | heading=0° | front_dist=60cm | ts=1712345678"
```

The LLM can then infer room type from object co-occurrences (sofa + TV → living room).

### What the Agent Prompt Gains
```
PAST DECISIONS (similar sensor state):
  - Front=22cm → turned left 45° — worked well
  - Front=28cm → stopped, then turned left — success

SEMANTIC MAP (what you have seen):
  - Heading ~0° (North): sofa, TV detected — likely living room
  - Heading ~90° (East): person detected 3 times — hallway/bedroom
```

### New Files

**`brain/memory.py`**
```python
class RobotMemory:
    store_decision(world_state, action, reasoning)
    store_observation(world_state, heading_deg)
    retrieve(world_state, k=3) -> str   # returns formatted context block
```

### Modified Files

| File | Change |
|---|---|
| `requirements.txt` | Add `chromadb` |
| `pyproject.toml` | Add `chromadb` dependency |
| `config.py` | Add `CHROMA_PERSIST_DIR` (default `./chroma_db`), `USE_MEMORY` (default `false`) |
| `brain/prompts.py` | Add `build_human_prompt(world_state, memories=None)` |
| `brain/agent.py` | Retrieve memory before LLM call; store decision + observation after; track `current_heading` |
| `test_full_robot.py` | Add `test_memory_store_retrieve`, `test_semantic_map_observation` |

### Verification
- `USE_MEMORY=false` → prompt contains no memory block
- `USE_MEMORY=true` → after 2+ cycles, prompt contains past decisions and observations
- ChromaDB directory created at `CHROMA_PERSIST_DIR` on disk
- All new tests pass in simulation mode (no hardware, no LLM API calls)

---

## Phase 3 — ReAct Agent Mode (Week 3)

### Goal
Replace the single-invoke LLM call with a multi-step reasoning loop:
**Think → Act → Observe → Think → Act → ...**

### How ReAct Works
Instead of the LLM picking one tool and ending, it reasons out loud across multiple steps:
```
Thought: Front is blocked at 20cm. I need to turn. Let me check which side is clearer.
Action: turn_left
Action Input: {"degrees": 45}
Observation: Turned left 45 degrees
Thought: Now I can assess. Front should be clearer. I'll move forward.
Action: move_forward
Action Input: {"distance_cm": 30}
```

### Important: No Tool-Calling Required
`create_react_agent` uses a **text-based** Thought/Action/Observation format — it parses
the model's plain text output, runs the tool, and injects the result back as an Observation.
This works with **any model**, including small Ollama models like `qwen2.5:0.5b` that do not
support structured tool calling. ReAct is actually more compatible than the current single-invoke
mode (which falls back to text parsing for non-tool-calling models).

### New Pydantic Model — `AgentDecision` (added to `world/state.py`)
```python
class AgentDecision(BaseModel):
    agent_name: str
    action: str           # final tool name chosen
    tool_args: dict       # arguments passed
    reasoning: str        # full chain-of-thought (empty in single mode)
    confidence: float     # 0.0–1.0
```

### Modified Files

| File | Change |
|---|---|
| `world/state.py` | Add `AgentDecision` Pydantic model |
| `config.py` | Add `AGENT_MODE` env var (`"single"` default \| `"react"`) |
| `brain/prompts.py` | Add `ROBOT_REACT_PROMPT` with Thought/Action/Observation instructions |
| `brain/agent.py` | Branch on `AGENT_MODE`: `"single"` path unchanged; `"react"` uses `create_react_agent` |
| `test_full_robot.py` | Add `test_react_agent` |

### Verification
- `AGENT_MODE=single` → existing behaviour unchanged
- `AGENT_MODE=react` → `AgentDecision.reasoning` is a non-empty string
- ReAct agent produces a valid action within 5 steps
- Test passes without LLM API calls (mock LLM in test)

---

## Phase 4 — RAG Toggle (Week 4)

### Goal
Demonstrate the difference between pure reasoning (no memory) and retrieval-augmented
generation (memory injected into prompt). Verify the toggle works correctly.

### What Changes
No new files. `USE_MEMORY` (added in Phase 2) is the RAG on/off switch:

- `USE_MEMORY=false` → LLM reasons purely from current sensor state
- `USE_MEMORY=true` → LLM receives relevant past decisions + semantic map observations

### Modified Files

| File | Change |
|---|---|
| `test_full_robot.py` | Add `test_rag_toggle` |

### `test_rag_toggle` Logic
1. Run one cycle and store a decision in memory
2. Run another cycle with `USE_MEMORY=false` → capture prompt → assert no memory block
3. Run same cycle with `USE_MEMORY=true` → capture prompt → assert memory block present
4. Assert the two prompts differ

### Verification
- Test passes in simulation mode
- Logged prompt output visibly shows/hides memory block depending on flag

---

## Phase 5 — Multi-Agent System + Orchestrator (Weeks 5–6)

### Goal
Replace the single agent with three specialist agents running **in parallel**, feeding a
`DecisionOrchestrator` that selects the final action.

### Three Agent Personalities

| Agent | Model (env var) | Behaviour |
|---|---|---|
| `SafeAgent` | `SAFE_AGENT_MODEL` | Risk-averse; maximises clearance; stops when uncertain |
| `FastAgent` | `FAST_AGENT_MODEL` | Speed-focused; minimises stops; accepts tighter clearance |
| `ExplorerAgent` | `EXPLORER_AGENT_MODEL` | Curiosity-driven; prefers unvisited headings; avoids repeat actions |

Each agent has its own LLM instance bound to its configured model.

### Orchestrator Strategies (selectable via `ORCHESTRATOR_STRATEGY`)

| Strategy | How it picks the final action |
|---|---|
| `voting` (default) | Majority vote on action name; tie → SafeAgent wins |
| `scoring` | Highest `AgentDecision.confidence` wins |
| `rule_based` | Safety rules applied first; then Fast if clear; else Safe |
| `judge` | A 4th LLM call reviews all three proposals and picks one |

### Execution
All three agents run in parallel using `asyncio.gather`. Wall-clock time ≈ slowest single agent.

### New Files

| File | Purpose |
|---|---|
| `brain/agents/__init__.py` | Package init |
| `brain/agents/base_agent.py` | `BaseRobotAgent(ABC)` — abstract `async decide(world_state) -> AgentDecision` |
| `brain/agents/safe_agent.py` | `SafeAgent(BaseRobotAgent)` |
| `brain/agents/fast_agent.py` | `FastAgent(BaseRobotAgent)` |
| `brain/agents/explorer_agent.py` | `ExplorerAgent(BaseRobotAgent)` — queries semantic map for unvisited headings |
| `brain/orchestrator.py` | `DecisionOrchestrator` — parallel run + strategy |

### Modified Files

| File | Change |
|---|---|
| `config.py` | Add `ORCHESTRATOR_STRATEGY`, `SAFE_AGENT_MODEL`, `FAST_AGENT_MODEL`, `EXPLORER_AGENT_MODEL` |
| `main.py` | Replace `decide_and_act()` call with `asyncio.run(orchestrator.run(world_state))`; keep single-agent path as fallback |
| `test_full_robot.py` | Add `test_multi_agent_parallel`, `test_orchestrator_voting` |

### Verification
- All three agents return an `AgentDecision` per cycle
- Orchestrator returns exactly one `AgentDecision`
- Parallel execution completes without race conditions
- Single-agent path still works when orchestrator is disabled

---

## Phase 6 — Prompt Engineering (Week 7)

### Goal
Tune each agent's system prompt to produce visibly distinct decision patterns.

### Prompt Design

**`SAFE_AGENT_PROMPT`**
- Refuses `move_forward` unless all three distances > 40cm
- Treats any object at < 50cm as a hazard
- Defaults to `stop` when uncertain

**`FAST_AGENT_PROMPT`**
- Prefers `move_forward` as long as front > 30cm
- Minimises turns; only turns when truly blocked
- Never stops unless forced by safety rules

**`EXPLORER_AGENT_PROMPT`**
- Checks semantic map (from Phase 2) for least-visited heading
- Penalises repeating the same action twice in a row
- Prefers directions where fewer objects have been observed

### Modified Files

| File | Change |
|---|---|
| `brain/prompts.py` | Add `SAFE_AGENT_PROMPT`, `FAST_AGENT_PROMPT`, `EXPLORER_AGENT_PROMPT` |
| `brain/agents/safe_agent.py` | Wire `SAFE_AGENT_PROMPT` |
| `brain/agents/fast_agent.py` | Wire `FAST_AGENT_PROMPT` |
| `brain/agents/explorer_agent.py` | Wire `EXPLORER_AGENT_PROMPT` |

### Verification
- Simulation run of 20 cycles shows distinct action distributions across the three agents
- SafeAgent `stop` rate > FastAgent `stop` rate
- ExplorerAgent does not repeat `turn_left` or `turn_right` consecutively

---

## Phase 7 — Evaluation Metrics (Week 8)

### Goal
Measure and log system performance so decisions can be compared and optimised over time.

### Metrics Tracked per Cycle

| Metric | Description |
|---|---|
| Action distribution | Count of each tool called (move_forward, turn_left, etc.) |
| Agent agreement rate | % of cycles where all 3 agents chose the same action |
| Avg decision time (ms) | Wall-clock time from world state read to action executed |
| Total cycles | Running count |
| Safety overrides | Count of hard safety blocks (front < 30cm) |

### New Files

**`brain/metrics.py`**
```python
class DecisionMetrics:
    record_cycle(world_state, agent_decisions: list[AgentDecision],
                 final_action: AgentDecision, elapsed_ms: float)
    get_summary() -> dict
    # If METRICS_LOG_FILE set, appends each cycle as a JSON line
```

### Modified Files

| File | Change |
|---|---|
| `config.py` | Add `METRICS_LOG_FILE` (default `""`, disabled) |
| `main.py` | Instantiate `DecisionMetrics`; call `record_cycle()` each loop; print summary on exit |
| `test_full_robot.py` | Add `test_metrics_recording` |

### Verification
- Summary printed to stdout on exit with correct cycle count
- If `METRICS_LOG_FILE` set, file contains one JSON line per cycle
- Agent agreement rate is 0–100% (no invalid values)

---

## File Change Summary

| File | Phase |
|---|---|
| `brain/memory.py` *(new)* | 2 |
| `brain/agents/__init__.py` *(new)* | 5 |
| `brain/agents/base_agent.py` *(new)* | 5 |
| `brain/agents/safe_agent.py` *(new)* | 5 |
| `brain/agents/fast_agent.py` *(new)* | 5 |
| `brain/agents/explorer_agent.py` *(new)* | 5 |
| `brain/orchestrator.py` *(new)* | 5 |
| `brain/metrics.py` *(new)* | 7 |
| `world/state.py` | 3 |
| `brain/agent.py` | 2, 3 |
| `brain/prompts.py` | 2, 3, 6 |
| `config.py` | 2, 3, 5, 7 |
| `main.py` | 5, 7 |
| `requirements.txt` | 2 |
| `pyproject.toml` | 2 |
| `test_full_robot.py` | 2, 3, 4, 5, 7 |

---

## Scope Boundaries

**In scope:**
- Simulation mode only — all phases must pass tests without real hardware or LLM API calls
- Backward compatibility — single-agent path must remain the default and keep working

**Out of scope:**
- Hailo AI HAT LLM provider (separate concern)
- Web UI / dashboard
- Cloud deployment
- Wheel encoders / true odometry (semantic map uses heading accumulation instead)
