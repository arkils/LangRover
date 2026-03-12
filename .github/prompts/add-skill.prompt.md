---
description: "Use when adding a new robot skill — a named behaviour triggered when specific objects are detected by the camera (e.g. greet a bird, inspect a bottle, alert on a backpack)."
argument-hint: "Describe the skill: name, what YOLO objects trigger it, what the robot should do"
agent: "agent"
---

Create a new LangRover robot skill based on the user's description.

Follow these steps exactly:

## 1. Understand the skill
From the user's message identify:
- **Skill name** — snake_case, unique, used as the LangChain tool name (e.g. `greet_bird`)
- **Trigger objects** — list of YOLO class label strings that make this skill relevant (e.g. `["bird"]`). Common YOLO labels: person, cat, dog, horse, bird, car, bottle, chair, laptop, backpack, cell phone, book.
- **Behaviour** — what sequence of `RobotActions` calls and print statements should happen
- **Return message** — short string returned from `execute()` describing what happened

## 2. Create the skill class
Add the new skill to `skills/builtin.py` (or a new file in `skills/` if it's clearly a separate domain).

Follow this exact pattern from the existing skills:

```python
class MyNewSkill(Skill):
    """One-line summary of what this skill does."""

    @property
    def name(self) -> str:
        return "skill_name"          # snake_case, unique

    @property
    def description(self) -> str:
        return (
            "What this skill does and when the LLM should call it. "
            "Be specific: 'Use this skill when X appears in detected objects.'"
        )

    @property
    def trigger_objects(self) -> List[str]:
        return ["yolo_class_name"]   # must match YOLO label strings exactly

    def execute(self, context: SkillContext) -> str:
        actions = context.robot_actions
        print("[SKILL] message here")
        # Use: actions.move_forward(cm), actions.turn_left(deg),
        #      actions.turn_right(deg), actions.stop()
        # Access sensor data: context.world_state.front_distance_cm etc.
        # Access vision data: context.world_state.vision_data.objects
        return "Short description of what was done"
```

## 3. Register the skill in main.py
In `main.py`, find the skill registration block and add:
```python
skill_registry.register(MyNewSkill())
```

If the skill was added to `skills/builtin.py`, also export it from `skills/__init__.py` if appropriate, or use `get_default_skills()` to include it automatically by adding it to the list in `builtin.py`.

## 4. Suggest a test case
Show a short code snippet or describe how to verify the skill works:
- Set `USE_REAL_VISION=false` (mock mode)
- Manually inject a `DetectedObject` with the trigger class name into a mock `VisionData`
- Call `skill.execute(SkillContext(world_state=..., robot_actions=CLIRobotActions()))` directly
- Check the return string and printed output

## Important rules
- Do NOT modify `skills/base.py` — the `Skill` ABC is stable
- Do NOT modify `brain/agent.py` or `brain/prompts.py` — skills are auto-registered as tools
- Safety: if the skill moves the robot, check `context.world_state.front_distance_cm` before calling `move_forward`
- The `description` property is shown directly to the LLM — make it unambiguous about when to invoke this skill
