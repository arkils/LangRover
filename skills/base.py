"""Abstract base class and context for robot skills."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from actions.base import RobotActions
from world.state import WorldState


@dataclass
class SkillContext:
    """
    Runtime context passed to a skill when it executes.

    Contains everything the skill needs: the current sensor/vision snapshot
    and the robot action interface.
    """

    world_state: WorldState
    robot_actions: RobotActions


class Skill(ABC):
    """
    Abstract base for a named, reusable robot behaviour (skill).

    A skill is triggered when specific YOLO-detected object classes appear in
    the vision data.  The LLM receives every registered skill as a LangChain
    tool and chooses which one to invoke (or falls back to raw navigation).

    To add a new skill:

    1. Subclass ``Skill`` and implement the four abstract members.
    2. Register an instance with ``SkillRegistry.register()``.

    That's it — no changes to the agent or prompt are needed.

    Example::

        class CatGreetingSkill(Skill):
            @property
            def name(self) -> str:
                return "greet_cat"

            @property
            def description(self) -> str:
                return "Greet a cat with a friendly wiggle"

            @property
            def trigger_objects(self) -> List[str]:
                return ["cat"]

            def execute(self, context: SkillContext) -> str:
                context.robot_actions.turn_left(20)
                context.robot_actions.turn_right(40)
                context.robot_actions.turn_left(20)
                return "Cat greeted"
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique snake_case identifier.

        Used as the LangChain tool name — must be unique across the registry.
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """
        One-sentence description shown to the LLM when it selects tools.

        Be specific: tell the LLM *when* to call this skill and *what* it does.
        """
        ...

    @property
    @abstractmethod
    def trigger_objects(self) -> List[str]:
        """
        YOLO class names that make this skill relevant.

        E.g. ``["cat", "kitten"]``.  Used to hint to the LLM which skills are
        relevant for the current frame (shown in the prompt as "RELEVANT SKILLS").
        The LLM may still call any registered skill — this is just guidance.
        """
        ...

    @abstractmethod
    def execute(self, context: SkillContext) -> str:
        """
        Run the skill behaviour.

        Implementations can call any combination of:
        - ``context.robot_actions.*`` — motion primitives
        - ``print(...)`` — console messages
        - Future: display animations, play sounds, etc.

        Args:
            context: Runtime snapshot of the world and robot action interface.

        Returns:
            A short human-readable string describing what happened (logged to console).
        """
        ...
