"""LangChain agent for autonomous robot decision-making."""

from typing import List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import StructuredTool

from actions.base import RobotActions
from brain.prompts import ROBOT_SYSTEM_PROMPT, build_human_prompt
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
    memory=None,
    rag_kb=None,
    short_term_memory=None,
) -> dict:
    """
    Create the robot agent.

    Args:
        robot_actions: Hardware or CLI action implementation.
        skill_registry: Registry of registered robot skills.
        llm_provider: ``"openai"`` or ``"ollama"``.
        ollama_model: Ollama model name; overrides ``OLLAMA_MODEL`` env var.
        memory: Optional ``RobotMemory`` instance (long-term ChromaDB memory).
        rag_kb: Optional ``RAGKnowledgeBase`` instance (Week 4 RAG modes).
        short_term_memory: Optional ``ShortTermMemory`` instance (Week 4,
            rolling in-process buffer of recent cycles).

    Returns:
        Agent dict passed to ``decide_and_act()`` each cycle.
    """
    llm = get_llm(llm_provider, ollama_model=ollama_model)
    return {
        "llm": llm,
        "robot_actions": robot_actions,
        "skill_registry": skill_registry,
        "memory": memory,
        "rag_kb": rag_kb,
        "short_term_memory": short_term_memory,
        "current_heading": 0.0,
    }


# ---------------------------------------------------------------------------
# Decision cycle
# ---------------------------------------------------------------------------

def decide_and_act(agent: dict, world_state: WorldState) -> None:
    """
    Run one decision cycle: read world state → call LLM with tools → execute.

    Three modes selected via ``Config.DECISION_MODE``:

    * ``agent``  — Pure agent reasoning. No retrieval. Single LLM invoke.
    * ``rag``    — Traditional RAG. Rules retrieved from the knowledge base
                   *before* the LLM call and injected into the prompt.
    * ``hybrid`` — Agentic RAG. The knowledge base is exposed as a
                   LangChain tool (``query_knowledge_base``). The LLM decides
                   each cycle whether to call it. If it does, a second invoke
                   is performed with the retrieved rules injected.

    Short-term memory (rolling session buffer) is injected in all modes when
    available. Long-term ChromaDB memory is injected in ``rag`` and ``hybrid``
    modes when ``USE_MEMORY=true``.

    Args:
        agent: Dict from ``create_agent()``.
        world_state: Current sensor + vision snapshot.
    """
    from config import Config
    cfg = Config()
    mode = cfg.DECISION_MODE.lower()

    llm = agent["llm"]
    robot_actions: RobotActions = agent["robot_actions"]
    skill_registry: SkillRegistry = agent["skill_registry"]
    rag_kb = agent.get("rag_kb")
    short_term = agent.get("short_term_memory")

    # ------------------------------------------------------------------
    # 1. Hard safety check — runs BEFORE consulting the LLM
    # ------------------------------------------------------------------
    # Note: people are friendly — robot greets them via greet_person skill.
    # Only obstacle distances trigger hard safety blocks.

    # Pre-LLM hard rules: greet detected people/animals immediately
    detected_names = [obj.name for obj in world_state.vision.objects]
    skill_context_early = SkillContext(world_state=world_state, robot_actions=robot_actions)

    if world_state.vision.people_count > 0 or "person" in detected_names:
        skill = skill_registry.get("greet_person")
        if skill:
            print(f"[HARD RULE] Person detected — executing greet_person")
            skill.execute(skill_context_early)
            return

    if "cat" in detected_names:
        skill = skill_registry.get("greet_cat")
        if skill:
            print(f"[HARD RULE] Cat detected — executing greet_cat")
            skill.execute(skill_context_early)
            return

    if "dog" in detected_names:
        skill = skill_registry.get("greet_dog")
        if skill:
            print(f"[HARD RULE] Dog detected — executing greet_dog")
            skill.execute(skill_context_early)
            return

    # ------------------------------------------------------------------
    # 2. Build core tools (nav + skills) — used in all modes
    # ------------------------------------------------------------------
    skill_context = SkillContext(world_state=world_state, robot_actions=robot_actions)
    nav_tools = _build_navigation_tools(robot_actions)
    skill_tools = skill_registry.to_langchain_tools(skill_context)
    core_tools = nav_tools + skill_tools

    # ------------------------------------------------------------------
    # Short-term memory context (all modes)
    # ------------------------------------------------------------------
    short_term_context: Optional[str] = None
    if short_term is not None:
        short_term_context = short_term.summarise() or None

    # ------------------------------------------------------------------
    # Long-term memory context (rag + hybrid modes)
    # ------------------------------------------------------------------
    long_term_context: Optional[str] = None
    if mode in ("rag", "hybrid"):
        robot_memory = agent.get("memory")
        if robot_memory is not None and cfg.USE_MEMORY:
            try:
                long_term_context = robot_memory.retrieve(world_state) or None
            except Exception:
                pass

    stm_cycles = len(short_term) if short_term is not None else 0
    print(
        f"[BRAIN]   Mode: {mode.upper()} | STM: {stm_cycles} cycles"
        f" | LTM: {'on' if long_term_context else 'off'}"
        f" | RAG KB: {'ready' if rag_kb is not None else 'none'}"
    )

    try:
        # ==================================================================
        # MODE: agent — pure reasoning, no retrieval
        # ==================================================================
        if mode == "agent":
            stm_label = f"{stm_cycles} cycles" if stm_cycles else "empty"
            print(f"[CONTEXT] Source: STM ({stm_label}) | RAG: none | LTM: none")
            human_msg = HumanMessage(
                content=build_human_prompt(
                    world_state, skill_registry,
                    short_term_context=short_term_context,
                )
            )
            messages = [SystemMessage(content=ROBOT_SYSTEM_PROMPT), human_msg]
            tool_list = ", ".join(t.name for t in core_tools)
            print(f"[LLM]     Invoke 1/1 — {len(core_tools)} tools: [{tool_list}]")
            response = llm.bind_tools(core_tools).invoke(messages)
            action = _execute_response(response, core_tools, robot_actions, agent, world_state)
            heading = agent.get("current_heading", 0.0)
            print(f"[RESULT]  Action: {action or 'none'} | Heading: {heading:.0f}°")
            _record_short_term(short_term, world_state, action)
            return

        # ==================================================================
        # MODE: rag — traditional RAG, always retrieve before LLM
        # ==================================================================
        if mode == "rag":
            rag_context: Optional[str] = None
            if rag_kb is not None:
                print("[RAG]     Querying knowledge base...")
                rag_context = rag_kb.retrieve(world_state) or None
                rule_count = rag_context.count("Rule") if rag_context else 0
                print(f"[RAG]     {rule_count} rules matched for current sensor state")
            else:
                print("[RAG]     No RAG KB configured — falling back to sensor-only prompt")
            stm_label = f"{stm_cycles} cycles" if stm_cycles else "empty"
            rag_label = f"{rag_context.count('Rule') if rag_context else 0} rules" if rag_context else "none"
            ltm_label = "on" if long_term_context else "off"
            print(f"[CONTEXT] Source: STM ({stm_label}) | RAG: {rag_label} | LTM: {ltm_label}")
            human_msg = HumanMessage(
                content=build_human_prompt(
                    world_state, skill_registry,
                    memories=long_term_context,
                    rag_context=rag_context,
                    short_term_context=short_term_context,
                )
            )
            messages = [SystemMessage(content=ROBOT_SYSTEM_PROMPT), human_msg]
            tool_list = ", ".join(t.name for t in core_tools)
            print(f"[LLM]     Invoke 1/1 — {len(core_tools)} tools: [{tool_list}]")
            response = llm.bind_tools(core_tools).invoke(messages)
            action = _execute_response(response, core_tools, robot_actions, agent, world_state)
            heading = agent.get("current_heading", 0.0)
            print(f"[RESULT]  Action: {action or 'none'} | Heading: {heading:.0f}°")
            _record_short_term(short_term, world_state, action)
            return

        # ==================================================================
        # MODE: hybrid — Agentic RAG: expose KB as a tool, LLM decides
        # ==================================================================
        if mode == "hybrid":
            # Build the query_knowledge_base tool (closure over rag_kb + world_state)
            rag_context_holder: list[Optional[str]] = [None]

            def query_knowledge_base(reason: str) -> str:  # noqa: D401
                """Consult the navigation knowledge base for rules relevant to
                the current sensor state.  Call this when the situation is
                ambiguous or novel.  Skip it when the path is clear."""
                if rag_kb is None:
                    return "Knowledge base not available."
                result = rag_kb.retrieve(world_state)
                rag_context_holder[0] = result
                return result or "No relevant rules found."

            rag_tool = StructuredTool.from_function(
                query_knowledge_base, name="query_knowledge_base"
            )
            all_tools = core_tools + [rag_tool]

            stm_label = f"{stm_cycles} cycles" if stm_cycles else "empty"
            ltm_label = "on" if long_term_context else "off"
            print(f"[CONTEXT] Source: STM ({stm_label}) | LTM: {ltm_label} | RAG: not injected yet (LLM decides)")

            # -- Invoke 1: LLM sees sensors + all tools incl. query_knowledge_base
            human_msg = HumanMessage(
                content=build_human_prompt(
                    world_state, skill_registry,
                    memories=long_term_context,
                    short_term_context=short_term_context,
                )
            )
            messages = [SystemMessage(content=ROBOT_SYSTEM_PROMPT), human_msg]
            tool_list = ", ".join(t.name for t in all_tools)
            print(f"[LLM]     Invoke 1/2 — {len(all_tools)} tools (incl. query_knowledge_base): [{tool_list}]")
            response1 = llm.bind_tools(all_tools).invoke(messages)

            tool_calls1 = getattr(response1, "tool_calls", None) or []
            kb_calls = [tc for tc in tool_calls1 if tc["name"] == "query_knowledge_base"]
            action_calls = [tc for tc in tool_calls1 if tc["name"] != "query_knowledge_base"]

            if kb_calls:
                # LLM chose to retrieve — execute KB call, then invoke again
                for tc in kb_calls:
                    reason = tc.get("args", {}).get("reason", "(no reason given)")
                    print(f"[RAG]     LLM called query_knowledge_base — reason: '{reason}'")
                    rag_tool.invoke(tc.get("args", {}))

                retrieved = rag_context_holder[0]
                rule_count = retrieved.count("Rule") if retrieved else 0
                print(f"[RAG]     {rule_count} rules retrieved — injecting into Invoke 2")

                # -- Invoke 2: inject retrieved rules, final action decision
                human_msg2 = HumanMessage(
                    content=build_human_prompt(
                        world_state, skill_registry,
                        memories=long_term_context,
                        rag_context=retrieved,
                        short_term_context=short_term_context,
                    )
                )
                messages2 = [SystemMessage(content=ROBOT_SYSTEM_PROMPT), human_msg2]
                tool_list2 = ", ".join(t.name for t in core_tools)
                print(f"[LLM]     Invoke 2/2 — {len(core_tools)} tools (RAG injected): [{tool_list2}]")
                response2 = llm.bind_tools(core_tools).invoke(messages2)
                action = _execute_response(response2, core_tools, robot_actions, agent, world_state)
            else:
                # LLM skipped retrieval and called an action directly
                print("[LLM]     LLM skipped retrieval — acting from Invoke 1 directly")
                tool_map = {t.name: t for t in core_tools}
                action = None
                for tc in action_calls:
                    matched = tool_map.get(tc["name"])
                    if matched:
                        print(f"[ACTION]  >> {tc['name']}({tc.get('args', {})})")
                        matched.invoke(tc.get("args", {}))
                        _update_heading(agent, tc["name"], tc.get("args", {}))
                        _store_memory(agent, world_state, tc["name"])
                        action = tc["name"]
                if not action:
                    # Fallback if LLM returned no tool calls at all
                    content = getattr(response1, "content", "").strip().lower()
                    action = _execute_text_fallback(content, robot_actions)

            heading = agent.get("current_heading", 0.0)
            print(f"[RESULT]  Action: {action or 'none'} | Heading: {heading:.0f}°")
            _record_short_term(short_term, world_state, action)
            return

        # Unknown mode — safe default
        print(f"[WARNING] Unknown DECISION_MODE '{mode}' — stopping")
        robot_actions.stop()

    except Exception as e:
        print(f"[ERROR] Agent error: {e}")
        robot_actions.stop()
        print("[SAFETY] Stopped robot after agent error")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _execute_response(
    response,
    all_tools: List[StructuredTool],
    robot_actions: RobotActions,
    agent: dict,
    world_state: WorldState,
) -> Optional[str]:
    """Execute tool calls from an LLM response, or fall back to text parsing.

    Returns:
        Name of the action executed, or ``None``.
    """
    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        tool_map = {t.name: t for t in all_tools}
        last_action = None
        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("args", {})
            matched = tool_map.get(tool_name)
            if matched:
                print(f"[ACTION]  >> {tool_name}({tool_args})")
                matched.invoke(tool_args)
                _update_heading(agent, tool_name, tool_args)
                _store_memory(agent, world_state, tool_name)
                last_action = tool_name
            else:
                print(f"[WARNING] LLM returned unknown tool '{tool_name}' — skipping")
        return last_action

    # Text fallback
    content = (
        response.content.strip().lower()
        if hasattr(response, "content")
        else str(response).strip().lower()
    )
    print(f"[FALLBACK] No tool_calls — parsing LLM text: '{content[:80]}'")
    action = _execute_text_fallback(content, robot_actions)
    if action:
        _update_heading(agent, action, {})
        _store_memory(agent, world_state, action)
    return action


def _record_short_term(
    short_term, world_state: WorldState, action: Optional[str]
) -> None:
    """Record the completed cycle in short-term memory when available."""
    if short_term is not None and action is not None:
        try:
            short_term.record(world_state, action)
        except Exception:
            pass


def _execute_text_fallback(decision: str, robot_actions: RobotActions) -> None:
    """Parse a plain-text LLM response and execute the best matching action.

    Returns:
        The name of the action that was executed, or ``None`` if nothing ran.
    """

    def _extract_int(text: str, default: int) -> int:
        digits = "".join(c for c in text if c.isdigit())
        return int(digits[:4]) if digits else default

    if "move_forward" in decision:
        distance = max(10, min(100, _extract_int(decision.split("move_forward")[-1], 30)))
        robot_actions.move_forward(distance)
        print(f"[ACTION]  >> move_forward(distance_cm={distance}) [text fallback]")
        return "move_forward"
    elif "turn_right" in decision:
        degrees = max(15, min(90, _extract_int(decision.split("turn_right")[-1], 45)))
        robot_actions.turn_right(degrees)
        print(f"[ACTION]  >> turn_right(degrees={degrees}) [text fallback]")
        return "turn_right"
    elif "turn_left" in decision:
        degrees = max(15, min(90, _extract_int(decision.split("turn_left")[-1], 45)))
        robot_actions.turn_left(degrees)
        print(f"[ACTION]  >> turn_left(degrees={degrees}) [text fallback]")
        return "turn_left"
    elif "stop" in decision:
        robot_actions.stop()
        print("[ACTION]  >> stop() [text fallback]")
        return "stop"
    else:
        robot_actions.move_forward(30)
        print("[ACTION]  >> move_forward(distance_cm=30) [default fallback]")
        return "move_forward"


# ---------------------------------------------------------------------------
# Memory helpers (Phase 2)
# ---------------------------------------------------------------------------

def _update_heading(agent: dict, tool_name: str, tool_args: dict) -> None:
    """Update the accumulated heading estimate after a turn action.

    Args:
        agent: Agent dict (mutated in place).
        tool_name: The tool that was just executed.
        tool_args: Arguments passed to the tool (may contain ``degrees``).
    """
    degrees = float(tool_args.get("degrees", 45))
    if tool_name == "turn_left":
        agent["current_heading"] = (agent.get("current_heading", 0.0) - degrees) % 360
    elif tool_name == "turn_right":
        agent["current_heading"] = (agent.get("current_heading", 0.0) + degrees) % 360


def _store_memory(agent: dict, world_state: WorldState, action: str) -> None:
    """Persist a decision and any current YOLO observations to memory.

    Args:
        agent: Agent dict (must have ``"memory"`` and ``"current_heading"``).
        world_state: Current sensor snapshot.
        action: Tool name that was just executed.
    """
    robot_memory = agent.get("memory")
    if robot_memory is None:
        return
    try:
        from config import Config
        if not Config().USE_MEMORY:
            return
    except Exception:
        return

    heading = agent.get("current_heading", 0.0)
    try:
        robot_memory.store_decision(world_state, action)
        robot_memory.store_observation(world_state, heading)
    except Exception as exc:
        print(f"[MEMORY] store failed: {exc}")




