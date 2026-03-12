"""Built-in robot skills shipped with LangRover.

Add new skills here or create them in your own module and register them with
``SkillRegistry.register()`` in ``main.py``.

Each class follows the ``Skill`` interface from ``skills.base``:
- ``name``            — unique LangChain tool name
- ``description``     — shown to the LLM so it knows when to call this skill
- ``trigger_objects`` — YOLO class names that make this skill relevant
- ``execute(ctx)``    — the actual behaviour (motion + console + future outputs)
"""

from typing import List

from skills.base import Skill, SkillContext


# ---------------------------------------------------------------------------
# Animal greetings
# ---------------------------------------------------------------------------

class CatGreetingSkill(Skill):
    """
    Perform a friendly wiggle greeting when a cat is detected.

    Sequence:  turn left 20° → turn right 40° → turn left 20° (back to centre)
    This imitates a friendly tail-wag / swivel.
    """

    @property
    def name(self) -> str:
        return "greet_cat"

    @property
    def description(self) -> str:
        return (
            "Perform a friendly greeting when a cat is detected in the camera. "
            "The robot does a small left-right wiggle and prints a hello message. "
            "Use this skill when 'cat' appears in the detected objects."
        )

    @property
    def trigger_objects(self) -> List[str]:
        return ["cat"]

    def execute(self, context: SkillContext) -> str:
        actions = context.robot_actions
        print("[SKILL] Hello, cat! =^.^=")
        actions.turn_left(20)
        actions.turn_right(40)
        actions.turn_left(20)
        return "Cat greeted with a friendly wiggle"


class DogGreetingSkill(Skill):
    """
    Perform a friendly bow greeting when a dog is detected.

    Sequence:  nudge forward 10 cm → stop  (imitates a bow)
    """

    @property
    def name(self) -> str:
        return "greet_dog"

    @property
    def description(self) -> str:
        return (
            "Perform a friendly greeting bow when a dog is detected in the camera. "
            "The robot nudges forward as a bow gesture and prints a hello message. "
            "Use this skill when 'dog' appears in the detected objects."
        )

    @property
    def trigger_objects(self) -> List[str]:
        return ["dog"]

    def execute(self, context: SkillContext) -> str:
        actions = context.robot_actions
        print("[SKILL] Hello, dog! Woof! >v<")
        actions.move_forward(10)
        actions.stop()
        return "Dog greeted with a bow"


# ---------------------------------------------------------------------------
# People greeting
# ---------------------------------------------------------------------------

class PersonGreetingSkill(Skill):
    """
    Perform a greeting interaction when a person is detected.

    Sequence: stop → wiggle left/right → continue
    """

    @property
    def name(self) -> str:
        return "greet_person"

    @property
    def description(self) -> str:
        return (
            "Perform a greeting interaction when a person is detected. "
            "Use this skill when 'person' appears in detected objects or people_count > 0."
        )

    @property
    def trigger_objects(self) -> List[str]:
        return ["person"]

    def execute(self, context: SkillContext) -> str:
        actions = context.robot_actions
        print("[SKILL] Hello there! =^_^=")
        actions.stop()
        actions.turn_left(20)
        actions.turn_right(40)
        actions.turn_left(20)
        return "Person greeted with a friendly wiggle"


# ---------------------------------------------------------------------------
# Convenience: pre-built default registry
# ---------------------------------------------------------------------------

def get_default_skills() -> List[Skill]:
    """Return the default set of built-in skills to register at startup."""
    return [
        PersonGreetingSkill(),
        CatGreetingSkill(),
        DogGreetingSkill(),
    ]
