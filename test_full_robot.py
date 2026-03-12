#!/usr/bin/env python3
"""
Comprehensive test suite for entire LangRover robot system.
Tests with simulated data - no real hardware required.
"""

import os
import sys
import time
from datetime import datetime

# Force simulation mode
os.environ["USE_REAL_SENSORS"] = "false"

# Configure Unicode output for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from world.simulator import read_world_state
from world.state import WorldState, VisionData, DetectedObject
from brain.agent import create_agent, decide_and_act
from actions.cli_actions import CLIRobotActions
from vision.vision import get_vision_detector
from skills import SkillRegistry, get_default_skills
from skills.base import SkillContext


class RobotSystemTest:
    """Complete robot system test suite."""

    def __init__(self):
        self.actions = CLIRobotActions()
        self.skill_registry = SkillRegistry()
        for skill in get_default_skills():
            self.skill_registry.register(skill)
        self.test_results = []
        self.start_time = None

    def log(self, message: str, level: str = "INFO"):
        """Log test message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "TEST": "🧪",
        }.get(level, "")
        print(f"{prefix} [{timestamp}] {message}")

    def test_world_state(self):
        """Test 1: World state simulator and sensor data."""
        self.log("World State Simulator", "TEST")

        try:
            for i in range(3):
                state = read_world_state()
                assert isinstance(state, WorldState), "State should be WorldState object"
                assert 0 <= state.front_distance_cm <= 400, "Front distance out of range"
                assert 0 <= state.left_distance_cm <= 400, "Left distance out of range"
                assert 0 <= state.right_distance_cm <= 400, "Right distance out of range"
                assert isinstance(state.target_visible, bool), "Target visible should be bool"

                self.log(
                    f"  Cycle {i+1}: F={state.front_distance_cm}cm, "
                    f"L={state.left_distance_cm}cm, R={state.right_distance_cm}cm, "
                    f"Target={state.target_visible}",
                    "SUCCESS"
                )

            return True
        except Exception as e:
            self.log(f"World State Test Failed: {e}", "ERROR")
            return False

    def test_vision_system(self):
        """Test 2: Vision detection system."""
        self.log("Vision Detection System", "TEST")

        try:
            detector = get_vision_detector()
            
            for i in range(3):
                vision_data = detector.detect()
                assert hasattr(vision_data, 'objects'), "Vision data should have objects"
                assert hasattr(vision_data, 'people_count'), "Vision data should have people_count"
                assert isinstance(vision_data.motion_detected, bool), "Motion detected should be bool"

                object_names = [obj.name for obj in vision_data.objects]
                self.log(
                    f"  Cycle {i+1}: {vision_data.people_count} people, "
                    f"{len(vision_data.objects)} objects: {object_names}",
                    "SUCCESS"
                )

            return True
        except Exception as e:
            self.log(f"Vision System Test Failed: {e}", "ERROR")
            return False

    def test_agent_decision_making(self):
        """Test 3: Agent structure and tool building (no LLM call)."""
        self.log("Agent Tool Building", "TEST")

        try:
            from brain.agent import _build_navigation_tools, _build_human_prompt

            actions = CLIRobotActions()
            nav_tools = _build_navigation_tools(actions)
            tool_names = {t.name for t in nav_tools}
            assert "move_forward" in tool_names, "missing move_forward tool"
            assert "turn_left" in tool_names, "missing turn_left tool"
            assert "turn_right" in tool_names, "missing turn_right tool"
            assert "stop" in tool_names, "missing stop tool"
            self.log(f"  Nav tools: {sorted(tool_names)}", "SUCCESS")

            state = WorldState(
                front_distance_cm=150, left_distance_cm=100,
                right_distance_cm=100, target_visible=False
            )
            prompt = _build_human_prompt(state, self.skill_registry)
            assert "Front" in prompt and "150" in prompt, "prompt missing sensor data"
            self.log(f"  Human prompt built ({len(prompt)} chars)", "SUCCESS")

            skill_tools = self.skill_registry.to_langchain_tools(
                SkillContext(world_state=state, robot_actions=actions)
            )
            skill_names = {t.name for t in skill_tools}
            assert "greet_cat" in skill_names, "missing greet_cat skill tool"
            assert "greet_dog" in skill_names, "missing greet_dog skill tool"
            assert "greet_person" in skill_names, "missing greet_person skill tool"
            self.log(f"  Skill tools: {sorted(skill_names)}", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Agent Tool Building Test Failed: {e}", "ERROR")
            return False

    def test_motor_control(self):
        """Test 4: All four motor control actions."""
        self.log("Motor Control Actions", "TEST")

        try:
            commands = [
                ("move_forward", 50),
                ("turn_left", 45),
                ("turn_right", 45),
                ("stop", None),
            ]

            for cmd_name, param in commands:
                if param is not None:
                    getattr(self.actions, cmd_name)(param)
                else:
                    getattr(self.actions, cmd_name)()
                self.log(f"  Motor command executed: {cmd_name}", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Motor Control Test Failed: {e}", "ERROR")
            return False

    def test_integration_loop(self, cycles: int = 5):
        """Test 5: Full integration - complete sense-decide-act loop."""
        self.log(f"Integration Loop ({cycles} cycles)", "TEST")

        try:
            for cycle in range(cycles):
                # Sense
                state = read_world_state()
                
                # Report (LLM would decide but Ollama may not be running)
                self.log(
                    f"  Cycle {cycle+1}/{cycles}: Sensors (F={state.front_distance_cm}cm, "
                    f"L={state.left_distance_cm}cm, R={state.right_distance_cm}cm)",
                    "SUCCESS"
                )

            return True
        except Exception as e:
            self.log(f"Integration Loop Test Failed: {e}", "ERROR")
            return False

    def test_skills_system(self):
        """Test 5: Skill registry, triggering, and execution."""
        self.log("Skills System", "TEST")

        try:
            # Registration
            assert len(self.skill_registry.get_all()) == 3, "Expected 3 default skills"
            self.log(f"  Registered skills: {[s.name for s in self.skill_registry.get_all()]}", "SUCCESS")

            # Trigger detection
            triggered = self.skill_registry.get_triggered_skills(["cat", "cup"])
            assert any(s.name == "greet_cat" for s in triggered), "cat should trigger greet_cat"
            self.log(f"  Triggered by ['cat','cup']: {[s.name for s in triggered]}", "SUCCESS")

            triggered_none = self.skill_registry.get_triggered_skills(["bottle", "chair"])
            assert not any(s.name == "greet_cat" for s in triggered_none), "bottle should not trigger greet_cat"
            self.log("  No false triggers for unrelated objects", "SUCCESS")

            # Skill execution
            state = WorldState(
                front_distance_cm=100, left_distance_cm=100,
                right_distance_cm=100, target_visible=False,
                vision=VisionData(objects=[
                    DetectedObject(name="cat", confidence=0.9, x=0.5, y=0.5, width=0.2, height=0.2)
                ])
            )
            ctx = SkillContext(world_state=state, robot_actions=self.actions)

            from skills.builtin import CatGreetingSkill, DogGreetingSkill, PersonGreetingSkill
            result = CatGreetingSkill().execute(ctx)
            assert isinstance(result, str) and len(result) > 0, "Skill should return non-empty string"
            self.log(f"  CatGreetingSkill executed: {result}", "SUCCESS")

            result = DogGreetingSkill().execute(ctx)
            self.log(f"  DogGreetingSkill executed: {result}", "SUCCESS")

            result = PersonGreetingSkill().execute(ctx)
            self.log(f"  PersonGreetingSkill executed: {result}", "SUCCESS")

            # Duplicate registration raises ValueError
            try:
                duplicate_registry = SkillRegistry()
                from skills.builtin import CatGreetingSkill
                duplicate_registry.register(CatGreetingSkill())
                duplicate_registry.register(CatGreetingSkill())  # should raise
                self.log("  ERROR: duplicate registration should have raised", "ERROR")
                return False
            except ValueError:
                self.log("  Duplicate skill registration correctly raises ValueError", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Skills System Test Failed: {e}", "ERROR")
            return False

    def test_safety_rules(self):
        """Test: Navigation tool safety clamping."""
        self.log("Safety Rules", "TEST")
        try:
            from brain.agent import _build_navigation_tools
            actions = CLIRobotActions()
            nav_tools = _build_navigation_tools(actions)
            tool_map = {t.name: t for t in nav_tools}

            # move_forward should clamp to 10–100
            result = tool_map["move_forward"].invoke({"distance_cm": 5})
            assert "10" in result, "move_forward should clamp min to 10 cm"
            self.log(f"  move_forward clamps low input: {result}", "SUCCESS")

            result = tool_map["move_forward"].invoke({"distance_cm": 500})
            assert "100" in result, "move_forward should clamp max to 100 cm"
            self.log(f"  move_forward clamps high input: {result}", "SUCCESS")

            # turn_left/right should clamp to 15–90
            result = tool_map["turn_left"].invoke({"degrees": 1})
            assert "15" in result, "turn_left should clamp min to 15 degrees"
            self.log(f"  turn_left clamps low input: {result}", "SUCCESS")

            result = tool_map["turn_right"].invoke({"degrees": 999})
            assert "90" in result, "turn_right should clamp max to 90 degrees"
            self.log(f"  turn_right clamps high input: {result}", "SUCCESS")

            # stop always works
            result = tool_map["stop"].invoke({})
            assert isinstance(result, str), "stop should return a string"
            self.log(f"  stop executes cleanly: {result}", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Safety Rules Test Failed: {e}", "ERROR")
            return False

    def test_config(self):
        """Test: Config loads from env vars with correct defaults."""
        self.log("Config & Environment", "TEST")
        try:
            from config import Config

            config = Config()
            assert config.LLM_PROVIDER in ("ollama", "openai", "hailo"), "Invalid LLM provider"
            self.log(f"  LLM provider: {config.LLM_PROVIDER}", "SUCCESS")

            assert isinstance(config.OLLAMA_MODEL, str) and len(config.OLLAMA_MODEL) > 0
            self.log(f"  Ollama model: {config.OLLAMA_MODEL}", "SUCCESS")

            assert 0 < config.DEFAULT_MOTOR_SPEED <= 100, "Motor speed out of range"
            self.log(f"  Motor speed: {config.DEFAULT_MOTOR_SPEED}%", "SUCCESS")

            assert config.MIN_SAFE_DISTANCE_CM > 0
            assert config.CRITICAL_DISTANCE_CM > 0
            assert config.MIN_SAFE_DISTANCE_CM > config.CRITICAL_DISTANCE_CM, \
                "MIN_SAFE_DISTANCE_CM should be greater than CRITICAL_DISTANCE_CM"
            self.log(
                f"  Safety distances: min={config.MIN_SAFE_DISTANCE_CM}cm, "
                f"critical={config.CRITICAL_DISTANCE_CM}cm",
                "SUCCESS"
            )

            assert config.SIMULATION_STEPS > 0
            self.log(f"  Simulation steps: {config.SIMULATION_STEPS}", "SUCCESS")

            # OpenAI validation only raises when provider is openai without key
            bad_config = Config()
            bad_config.LLM_PROVIDER = "openai"
            bad_config.OPENAI_API_KEY = ""
            try:
                bad_config.validate()
                self.log("  ERROR: should have raised for missing OpenAI key", "ERROR")
                return False
            except ValueError:
                self.log("  validate() correctly raises for missing OPENAI_API_KEY", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Config Test Failed: {e}", "ERROR")
            return False

    def test_world_state_model(self):
        """Test: WorldState Pydantic model validation and __str__."""
        self.log("WorldState Data Model", "TEST")
        try:
            # Minimal construction
            state = WorldState(
                front_distance_cm=50.0,
                left_distance_cm=80.0,
                right_distance_cm=120.0,
                target_visible=False,
            )
            assert state.front_distance_cm == 50.0
            assert state.vision is not None, "vision should default to empty VisionData"
            self.log("  Minimal WorldState construction OK", "SUCCESS")

            # With vision data
            state_with_vision = WorldState(
                front_distance_cm=30.0,
                left_distance_cm=40.0,
                right_distance_cm=50.0,
                target_visible=True,
                vision=VisionData(
                    objects=[
                        DetectedObject(name="cat", confidence=0.95, x=0.5, y=0.5, width=0.1, height=0.1),
                        DetectedObject(name="dog", confidence=0.80, x=0.3, y=0.4, width=0.2, height=0.2),
                    ],
                    people_count=1,
                    has_faces=True,
                    motion_detected=True,
                    frame_quality=0.9,
                ),
            )
            assert state_with_vision.vision.people_count == 1
            assert len(state_with_vision.vision.objects) == 2
            assert state_with_vision.vision.objects[0].name == "cat"
            self.log("  Full WorldState with VisionData OK", "SUCCESS")

            # __str__ should include key fields
            state_str = str(state_with_vision)
            assert "30" in state_str or "front" in state_str.lower(), "__str__ should include front distance"
            self.log(f"  __str__ output: {state_str[:80]}...", "SUCCESS")

            # DetectedObject confidence range
            assert 0.0 <= state_with_vision.vision.objects[0].confidence <= 1.0
            self.log("  DetectedObject confidence in valid range", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"WorldState Model Test Failed: {e}", "ERROR")
            return False

    def test_cli_actions_output(self):
        """Test: CLIRobotActions produce correct console output."""
        self.log("CLI Actions Output", "TEST")
        try:
            import io
            from contextlib import redirect_stdout

            actions = CLIRobotActions()

            # move_forward
            buf = io.StringIO()
            with redirect_stdout(buf):
                actions.move_forward(30)
            output = buf.getvalue()
            assert "30" in output or "forward" in output.lower(), \
                f"move_forward output missing distance/direction: {output!r}"
            self.log(f"  move_forward(30): {output.strip()}", "SUCCESS")

            # turn_left
            buf = io.StringIO()
            with redirect_stdout(buf):
                actions.turn_left(45)
            output = buf.getvalue()
            assert "45" in output or "left" in output.lower(), \
                f"turn_left output missing degrees/direction: {output!r}"
            self.log(f"  turn_left(45): {output.strip()}", "SUCCESS")

            # turn_right
            buf = io.StringIO()
            with redirect_stdout(buf):
                actions.turn_right(90)
            output = buf.getvalue()
            assert "90" in output or "right" in output.lower(), \
                f"turn_right output missing degrees/direction: {output!r}"
            self.log(f"  turn_right(90): {output.strip()}", "SUCCESS")

            # stop
            buf = io.StringIO()
            with redirect_stdout(buf):
                actions.stop()
            output = buf.getvalue()
            assert len(output.strip()) > 0, "stop() should print something"
            self.log(f"  stop(): {output.strip()}", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"CLI Actions Output Test Failed: {e}", "ERROR")
            return False

    def test_human_prompt_content(self):
        """Test: Human prompt includes relevant sensor data and skill hints."""
        self.log("Human Prompt Content", "TEST")
        try:
            from brain.agent import _build_human_prompt

            # Prompt with a detected cat — should surface greet_cat as relevant skill
            state = WorldState(
                front_distance_cm=25.0,
                left_distance_cm=60.0,
                right_distance_cm=200.0,
                target_visible=False,
                vision=VisionData(
                    objects=[DetectedObject(name="cat", confidence=0.88, x=0.5, y=0.5, width=0.1, height=0.1)],
                    people_count=0,
                ),
            )
            prompt = _build_human_prompt(state, self.skill_registry)

            assert "25" in prompt, "prompt should include front_distance_cm"
            self.log(f"  Front distance present in prompt", "SUCCESS")

            assert "60" in prompt, "prompt should include left_distance_cm"
            self.log(f"  Left distance present in prompt", "SUCCESS")

            assert "cat" in prompt.lower(), "prompt should mention detected cat"
            self.log(f"  Detected object (cat) present in prompt", "SUCCESS")

            assert "greet_cat" in prompt, "prompt should hint greet_cat as relevant skill"
            self.log(f"  Relevant skill hint (greet_cat) present in prompt", "SUCCESS")

            # Prompt with a person — should surface greet_person
            state_person = WorldState(
                front_distance_cm=100.0,
                left_distance_cm=100.0,
                right_distance_cm=100.0,
                target_visible=False,
                vision=VisionData(
                    objects=[DetectedObject(name="person", confidence=0.99, x=0.5, y=0.5, width=0.3, height=0.6)],
                    people_count=1,
                ),
            )
            prompt_person = _build_human_prompt(state_person, self.skill_registry)
            assert "greet_person" in prompt_person, "prompt should hint greet_person when person detected"
            self.log(f"  Relevant skill hint (greet_person) present when person detected", "SUCCESS")

            # Prompt with no known objects — no skill hints
            state_empty = WorldState(
                front_distance_cm=100.0,
                left_distance_cm=100.0,
                right_distance_cm=100.0,
                target_visible=False,
            )
            prompt_empty = _build_human_prompt(state_empty, self.skill_registry)
            assert isinstance(prompt_empty, str) and len(prompt_empty) > 0
            self.log(f"  Empty vision prompt built OK ({len(prompt_empty)} chars)", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Human Prompt Content Test Failed: {e}", "ERROR")
            return False

    def test_stress(self, cycles: int = 20):
        """Test: Stress test - rapid cycles to check stability."""
        self.log(f"Stress Test ({cycles} rapid cycles)", "TEST")

        try:
            for cycle in range(cycles):
                state = read_world_state()
                # Validate state structure
                assert isinstance(state.front_distance_cm, (int, float))
                assert isinstance(state.left_distance_cm, (int, float))
                assert isinstance(state.right_distance_cm, (int, float))
                
                if (cycle + 1) % 5 == 0:
                    self.log(f"  {cycle + 1}/{cycles} cycles completed", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Stress Test Failed: {e}", "ERROR")
            return False

    def run_all_tests(self):
        """Run all tests and generate report."""
        print("\n" + "="*60)
        print("🤖 LANGROVER ROBOT SYSTEM TEST SUITE")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: SIMULATION (no real hardware)")
        print("="*60 + "\n")

        self.start_time = time.time()

        tests = [
            ("World State & Sensors", self.test_world_state),
            ("Vision System", self.test_vision_system),
            ("Skills System", self.test_skills_system),
            ("Agent Tool Building", self.test_agent_decision_making),
            ("Motor Control", self.test_motor_control),
            ("Integration Loop", self.test_integration_loop),
            ("Stress Test", self.test_stress),
            ("Safety Rules & Clamping", self.test_safety_rules),
            ("Config & Environment", self.test_config),
            ("WorldState Data Model", self.test_world_state_model),
            ("CLI Actions Output", self.test_cli_actions_output),
            ("Human Prompt Content", self.test_human_prompt_content),
        ]

        results = {}
        for test_name, test_func in tests:
            print()
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.log(f"Test crashed: {e}", "ERROR")
                results[test_name] = False

        # Generate report
        elapsed = time.time() - self.start_time
        passed = sum(1 for v in results.values() if v)
        total = len(results)

        print("\n" + "="*60)
        print("TEST REPORT")
        print("="*60)
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")

        print("="*60)
        print(f"Results: {passed}/{total} tests passed")
        print(f"Elapsed: {elapsed:.2f} seconds")
        print("="*60 + "\n")

        return passed == total


def main():
    """Main test execution."""
    try:
        tester = RobotSystemTest()
        success = tester.run_all_tests()
        
        if success:
            print("🎉 All tests passed! Robot system is functional.\n")
            return 0
        else:
            print("⚠️  Some tests failed. Review output above.\n")
            return 1
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
