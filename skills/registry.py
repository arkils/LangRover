"""Skill registry: maps detected objects to executable robot skills."""

from typing import Dict, List

from langchain_core.tools import StructuredTool

from skills.base import Skill, SkillContext


class SkillRegistry:
    """
    Central registry for robot skills.

    Register skills once at startup.  Each decision cycle the agent:

    1. Calls ``to_langchain_tools(context)`` to get all skills as LangChain
       tools (bound to the current world-state snapshot).
    2. Passes them to ``llm.bind_tools(nav_tools + skill_tools)`` so the LLM
       can choose any of them.
    3. Optionally calls ``get_triggered_skills(objects)`` to surface relevant
       skills as a hint in the prompt.

    Usage::

        registry = SkillRegistry()
        registry.register(CatGreetingSkill())
        registry.register(DogGreetingSkill())
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, skill: Skill) -> None:
        """
        Register a skill.

        Args:
            skill: A concrete ``Skill`` instance.

        Raises:
            ValueError: If a skill with the same name is already registered.
        """
        if skill.name in self._skills:
            raise ValueError(
                f"Skill '{skill.name}' is already registered. "
                "Use a unique name for each skill."
            )
        self._skills[skill.name] = skill
        print(f"[SKILLS] Registered: {skill.name}")

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get_all(self) -> List[Skill]:
        """Return all registered skills."""
        return list(self._skills.values())

    def get_triggered_skills(self, detected_object_names: List[str]) -> List[Skill]:
        """
        Return skills whose ``trigger_objects`` overlap with detected class names.

        Used to build the "RELEVANT SKILLS" hint shown to the LLM.

        Args:
            detected_object_names: YOLO class names detected in the current frame.

        Returns:
            Skills that match at least one of the detected object names.
        """
        detected = {n.lower() for n in detected_object_names}
        return [
            skill for skill in self._skills.values()
            if any(trigger.lower() in detected for trigger in skill.trigger_objects)
        ]

    # ------------------------------------------------------------------
    # LangChain tool conversion
    # ------------------------------------------------------------------

    def to_langchain_tools(self, context: SkillContext) -> List[StructuredTool]:
        """
        Convert all registered skills into LangChain ``StructuredTool`` instances.

        Each skill becomes a tool whose input schema is ``{"reason": string}``.
        The LLM is expected to fill ``reason`` with a short explanation of why it
        chose this skill — this surfaces in logs for debugging.

        Args:
            context: SkillContext bound to the current decision cycle.

        Returns:
            One ``StructuredTool`` per registered skill.
        """
        tools: List[StructuredTool] = []
        for skill in self._skills.values():
            tools.append(_make_skill_tool(skill, context))
        return tools


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _make_skill_tool(skill: Skill, context: SkillContext) -> StructuredTool:
    """Wrap a single Skill as a LangChain StructuredTool."""

    # Capture skill and context in a closure so the tool is self-contained.
    _skill = skill
    _ctx = context

    def _execute(reason: str = "") -> str:
        """Execute the skill (reason is optional LLM explanation)."""
        if reason:
            print(f"[SKILL] {_skill.name} — reason: {reason}")
        result = _skill.execute(_ctx)
        print(f"[SKILL] {_skill.name} complete: {result}")
        return result

    return StructuredTool.from_function(
        func=_execute,
        name=_skill.name,
        description=_skill.description,
    )
