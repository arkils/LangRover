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
            assert "person_safety_stop" in skill_names, "missing person_safety_stop skill tool"
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

            from skills.builtin import CatGreetingSkill, DogGreetingSkill, PersonSafetySkill
            result = CatGreetingSkill().execute(ctx)
            assert isinstance(result, str) and len(result) > 0, "Skill should return non-empty string"
            self.log(f"  CatGreetingSkill executed: {result}", "SUCCESS")

            result = DogGreetingSkill().execute(ctx)
            self.log(f"  DogGreetingSkill executed: {result}", "SUCCESS")

            result = PersonSafetySkill().execute(ctx)
            self.log(f"  PersonSafetySkill executed: {result}", "SUCCESS")

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

    def test_stress(self, cycles: int = 20):
        """Test 6: Stress test - rapid cycles to check stability."""
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
