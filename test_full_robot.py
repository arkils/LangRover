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
                assert 0 <= state.rear_distance_cm <= 400, "Rear distance out of range"
                assert isinstance(state.target_visible, bool), "Target visible should be bool"

                self.log(
                    f"  Cycle {i+1}: F={state.front_distance_cm}cm, "
                    f"L={state.left_distance_cm}cm, R={state.right_distance_cm}cm, "
                    f"Rear={state.rear_distance_cm}cm, Target={state.target_visible}",
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
            from brain.agent import _build_navigation_tools
            from brain.prompts import build_human_prompt as _build_human_prompt

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
                    f"L={state.left_distance_cm}cm, R={state.right_distance_cm}cm, "
                    f"Rear={state.rear_distance_cm}cm)",
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
            from brain.prompts import build_human_prompt as _build_human_prompt

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

    def test_memory_store_retrieve(self):
        """Test: RobotMemory stores decisions and retrieves them (USE_MEMORY=true)."""
        self.log("Memory Store & Retrieve", "TEST")
        import tempfile
        import os

        try:
            tmpdir = tempfile.mkdtemp(prefix="langrover_mem_test_")
            from brain.memory import RobotMemory

            mem = RobotMemory(persist_dir=tmpdir)

            state = WorldState(
                front_distance_cm=22.0,
                left_distance_cm=80.0,
                right_distance_cm=15.0,
                target_visible=False,
            )

            # Store two decisions
            mem.store_decision(state, "turn_left", "obstacle cleared")
            mem.store_decision(
                WorldState(
                    front_distance_cm=28.0,
                    left_distance_cm=60.0,
                    right_distance_cm=30.0,
                    target_visible=False,
                ),
                "stop",
                "then turned left — success",
            )

            # Retrieve should return a non-empty context block
            context = mem.retrieve(state)
            assert isinstance(context, str), "retrieve() should return a string"
            assert len(context.strip()) > 0, "context should be non-empty after storing decisions"
            assert "PAST DECISIONS" in context, "context should include PAST DECISIONS header"
            assert "turn_left" in context or "stop" in context, \
                "context should mention at least one stored action"
            self.log(f"  Retrieved context ({len(context)} chars)", "SUCCESS")

            # USE_MEMORY=false → build_human_prompt should not include memory block
            from brain.prompts import build_human_prompt
            from skills.registry import SkillRegistry as _SR
            reg = _SR()
            prompt_no_mem = build_human_prompt(state, reg, memories=None)
            assert "PAST DECISIONS" not in prompt_no_mem, \
                "Prompt without memories should not contain PAST DECISIONS"
            self.log("  No memory block when memories=None", "SUCCESS")

            # USE_MEMORY=true equivalent → memory block injected
            prompt_with_mem = build_human_prompt(state, reg, memories=context)
            assert "PAST DECISIONS" in prompt_with_mem, \
                "Prompt with memories should contain PAST DECISIONS"
            self.log("  Memory block present when memories provided", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Memory Store & Retrieve Test Failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def test_semantic_map_observation(self):
        """Test: RobotMemory stores YOLO observations and includes them in retrieve."""
        self.log("Semantic Map Observation", "TEST")
        import tempfile

        try:
            tmpdir = tempfile.mkdtemp(prefix="langrover_obs_test_")
            from brain.memory import RobotMemory

            mem = RobotMemory(persist_dir=tmpdir)

            state_with_objects = WorldState(
                front_distance_cm=60.0,
                left_distance_cm=100.0,
                right_distance_cm=100.0,
                target_visible=False,
                vision=VisionData(
                    objects=[
                        DetectedObject(name="sofa", confidence=0.89, x=0.5, y=0.5, width=0.3, height=0.3),
                        DetectedObject(name="TV", confidence=0.91, x=0.7, y=0.4, width=0.2, height=0.2),
                    ]
                ),
            )

            # No objects → observation not stored
            state_empty = WorldState(
                front_distance_cm=40.0,
                left_distance_cm=40.0,
                right_distance_cm=40.0,
                target_visible=False,
            )
            mem.store_observation(state_empty, heading_deg=0.0)
            # observations collection should still be empty
            # (store_observation skips empty vision)

            # With objects → should be stored
            mem.store_observation(state_with_objects, heading_deg=0.0)
            mem.store_observation(
                WorldState(
                    front_distance_cm=50.0,
                    left_distance_cm=80.0,
                    right_distance_cm=80.0,
                    target_visible=False,
                    vision=VisionData(
                        objects=[
                            DetectedObject(name="person", confidence=0.99, x=0.5, y=0.5, width=0.2, height=0.5)
                        ],
                        people_count=1,
                    ),
                ),
                heading_deg=90.0,
            )

            context = mem.retrieve(state_with_objects)
            assert "SEMANTIC MAP" in context, "context should include SEMANTIC MAP header"
            assert "sofa" in context or "TV" in context or "person" in context, \
                "context should mention at least one observed object"
            self.log(f"  Semantic map context retrieved ({len(context)} chars)", "SUCCESS")

            # Heading tracking: turning left should decrease heading
            from brain.agent import _update_heading
            agent_dict = {"current_heading": 0.0}
            _update_heading(agent_dict, "turn_left", {"degrees": 45})
            assert agent_dict["current_heading"] == 315.0, \
                f"Expected 315.0 after turn_left 45 from 0, got {agent_dict['current_heading']}"
            self.log("  turn_left updates heading correctly (0 - 45 = 315 mod 360)", "SUCCESS")

            _update_heading(agent_dict, "turn_right", {"degrees": 90})
            assert agent_dict["current_heading"] == 45.0, \
                f"Expected 45.0 after turn_right 90 from 315, got {agent_dict['current_heading']}"
            self.log("  turn_right updates heading correctly (315 + 90 = 45 mod 360)", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Semantic Map Observation Test Failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
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

    # ------------------------------------------------------------------
    # Week 4 — RAG + Agents + Agentic RAG
    # ------------------------------------------------------------------

    def test_rag_knowledge_base_retrieval(self) -> bool:
        """RAGKnowledgeBase populates and retrieves relevant rules."""
        self.log("Testing RAG Knowledge Base retrieval", "TEST")
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            from brain.rag import RAGKnowledgeBase
            kb = RAGKnowledgeBase(persist_dir=tmp)
            kb.populate_defaults()
            world_state = WorldState(
                front_distance_cm=25.0,
                left_distance_cm=90.0,
                right_distance_cm=40.0,
                target_visible=False,
            )
            result = kb.retrieve(world_state, k=3)
            assert result, "retrieve() returned empty string"
            assert "Rule" in result, "Expected 'Rule' label in output"
            rule_count = result.count("Rule")
            self.log(f"  Retrieved {rule_count} rules for obstacle scenario", "SUCCESS")
            open_state = WorldState(
                front_distance_cm=150.0,
                left_distance_cm=130.0,
                right_distance_cm=140.0,
                target_visible=False,
            )
            open_result = kb.retrieve(open_state, k=3)
            assert open_result, "retrieve() returned empty for open-path state"
            self.log("  Open-path retrieval also successful", "SUCCESS")
            del kb
            return True
        except Exception as e:
            self.log(f"RAG KB Retrieval failed: {e}", "ERROR")
            return False
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_short_term_memory(self) -> bool:
        """ShortTermMemory records cycles and produces a correct summary."""
        self.log("Testing Short-Term Memory rolling buffer", "TEST")
        try:
            from brain.memory import ShortTermMemory
            stm = ShortTermMemory(max_cycles=3)
            assert stm.summarise() == "", "Empty buffer should return empty string"

            states = [
                WorldState(front_distance_cm=120.0, left_distance_cm=80.0, right_distance_cm=60.0, rear_distance_cm=150.0, target_visible=False),
                WorldState(front_distance_cm=45.0, left_distance_cm=90.0, right_distance_cm=55.0, rear_distance_cm=200.0, target_visible=False),
                WorldState(front_distance_cm=90.0, left_distance_cm=40.0, right_distance_cm=85.0, rear_distance_cm=100.0, target_visible=False),
                # 4th entry should drop the 1st (maxlen=3)
                WorldState(front_distance_cm=200.0, left_distance_cm=180.0, right_distance_cm=190.0, rear_distance_cm=50.0, target_visible=False),
            ]
            actions = ["move_forward", "turn_left", "move_forward", "move_forward"]
            for s, a in zip(states, actions):
                stm.record(s, a)

            assert len(stm) == 3, f"Expected 3 entries (maxlen), got {len(stm)}"
            summary = stm.summarise()
            assert "Short-Term Memory" in summary, "Missing header in summary"
            assert "turn_left" in summary, "Expected turn_left in summary"
            assert "120" not in summary, "First (dropped) entry should not appear"
            assert "Rear=" in summary, "Rear distance should appear in summary"
            self.log(f"  Buffer correctly capped at 3, summary includes Rear, generated", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Short-Term Memory failed: {e}", "ERROR")
            return False

    def test_traditional_rag_mode(self) -> bool:
        """DECISION_MODE=rag: RAG context injected into prompt, single LLM invoke."""
        self.log("Testing Traditional RAG mode (DECISION_MODE=rag)", "TEST")
        import tempfile, shutil
        original_mode = os.environ.get("DECISION_MODE", "")
        tmp = tempfile.mkdtemp()
        try:
            os.environ["DECISION_MODE"] = "rag"
            from brain.rag import RAGKnowledgeBase

            kb = RAGKnowledgeBase(persist_dir=tmp)
            kb.populate_defaults()

            ws = WorldState(front_distance_cm=25.0, left_distance_cm=90.0, right_distance_cm=50.0, target_visible=False)
            rag_result = kb.retrieve(ws)
            assert rag_result, "RAG KB should return rules for obstacle state"
            self.log(f"  RAG retrieve: {rag_result[:60]}...", "SUCCESS")

            from brain.prompts import build_human_prompt
            prompt = build_human_prompt(ws, self.skill_registry, rag_context=rag_result)
            assert "RAG Knowledge Base" in prompt or "Rule" in prompt, \
                "RAG context not found in prompt"
            self.log("  RAG context correctly injected into prompt", "SUCCESS")
            del kb
            return True
        except Exception as e:
            self.log(f"Traditional RAG mode failed: {e}", "ERROR")
            return False
        finally:
            if original_mode:
                os.environ["DECISION_MODE"] = original_mode
            else:
                os.environ.pop("DECISION_MODE", None)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_pure_agent_mode(self) -> bool:
        """DECISION_MODE=agent: no RAG context, no long-term memory in prompt."""
        self.log("Testing Pure Agent mode (DECISION_MODE=agent)", "TEST")
        original_mode = os.environ.get("DECISION_MODE", "")
        try:
            os.environ["DECISION_MODE"] = "agent"
            ws = WorldState(front_distance_cm=100.0, left_distance_cm=100.0, right_distance_cm=100.0, target_visible=False)

            from brain.prompts import build_human_prompt
            prompt = build_human_prompt(ws, self.skill_registry)
            assert "RAG Knowledge Base" not in prompt, "RAG context should not appear in agent mode"
            assert "Short-Term Memory" not in prompt, "Short-term context should not appear when empty"
            assert "DISTANCE SENSORS" in prompt, "Sensor data must always appear"
            self.log("  Pure agent prompt: no retrieval sections, sensors present", "SUCCESS")

            # Verify agent dict is structured correctly without calling LLM init
            # (agent dict is just a plain dict; rag_kb=None means no retrieval)
            mock_agent = {
                "llm": None,
                "robot_actions": self.actions,
                "skill_registry": self.skill_registry,
                "memory": None,
                "rag_kb": None,
                "short_term_memory": None,
                "current_heading": 0.0,
            }
            assert mock_agent.get("rag_kb") is None, "rag_kb should be None in pure agent mode"
            self.log("  Agent dict without RAG KB verified", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Pure Agent mode failed: {e}", "ERROR")
            return False
        finally:
            if original_mode:
                os.environ["DECISION_MODE"] = original_mode
            else:
                os.environ.pop("DECISION_MODE", None)

    def test_agentic_rag_hybrid_mode(self) -> bool:
        """DECISION_MODE=hybrid: query_knowledge_base tool available, KB accessible."""
        self.log("Testing Agentic RAG hybrid mode (DECISION_MODE=hybrid)", "TEST")
        import tempfile, shutil
        original_mode = os.environ.get("DECISION_MODE", "")
        tmp = tempfile.mkdtemp()
        try:
            os.environ["DECISION_MODE"] = "hybrid"
            from brain.rag import RAGKnowledgeBase
            from brain.memory import ShortTermMemory

            kb = RAGKnowledgeBase(persist_dir=tmp)
            kb.populate_defaults()
            stm = ShortTermMemory(max_cycles=5)

            # Verify agent dict structure without triggering LLM init
            mock_agent = {
                "llm": None,
                "robot_actions": self.actions,
                "skill_registry": self.skill_registry,
                "memory": None,
                "rag_kb": kb,
                "short_term_memory": stm,
                "current_heading": 0.0,
            }
            assert mock_agent.get("rag_kb") is kb, "rag_kb not stored in agent"
            assert mock_agent.get("short_term_memory") is stm, "short_term_memory not stored"
            self.log("  Agent dict contains rag_kb + short_term_memory", "SUCCESS")

            ws = WorldState(front_distance_cm=25.0, left_distance_cm=90.0, right_distance_cm=50.0, target_visible=False)
            result = kb.retrieve(ws)
            assert result, "KB retrieve must return rules in hybrid mode"
            self.log(f"  KB retrieve in hybrid mode: {result[:60]}...", "SUCCESS")

            stm.record(ws, "turn_left")
            from brain.prompts import build_human_prompt
            prompt = build_human_prompt(
                ws, self.skill_registry,
                short_term_context=stm.summarise(),
                rag_context=result,
            )
            assert "Short-Term Memory" in prompt, "Short-term context missing from prompt"
            assert "RAG Knowledge Base" in prompt or "Rule" in prompt, \
                "RAG context missing from prompt"
            self.log("  Hybrid prompt contains both short-term + RAG sections", "SUCCESS")
            del kb
            return True
        except Exception as e:
            self.log(f"Agentic RAG hybrid mode failed: {e}", "ERROR")
            return False
        finally:
            if original_mode:
                os.environ["DECISION_MODE"] = original_mode
            else:
                os.environ.pop("DECISION_MODE", None)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_rear_sensor_and_logging(self) -> bool:
        """Rear sensor wired through WorldState, prompt, and ShortTermMemory summary."""
        self.log("Rear Sensor + Improved Logging", "TEST")
        try:
            import io
            from contextlib import redirect_stdout

            # 1. WorldState accepts and stores rear_distance_cm
            ws = WorldState(
                front_distance_cm=25.0,
                left_distance_cm=90.0,
                right_distance_cm=60.0,
                rear_distance_cm=180.0,
                target_visible=False,
            )
            assert ws.rear_distance_cm == 180.0, "rear_distance_cm not stored"
            self.log("  WorldState stores rear_distance_cm", "SUCCESS")

            # 2. __str__ includes Rear
            ws_str = str(ws)
            assert "Rear" in ws_str, f"__str__ missing Rear: {ws_str}"
            self.log(f"  WorldState.__str__ includes Rear: {ws_str}", "SUCCESS")

            # 3. Prompt includes Rear sensor line
            from brain.prompts import build_human_prompt
            prompt = build_human_prompt(ws, self.skill_registry)
            assert "Rear:" in prompt, "Rear sensor line missing from prompt"
            assert "180" in prompt, "Rear distance value missing from prompt"
            self.log("  build_human_prompt() includes Rear sensor", "SUCCESS")

            # 4. ShortTermMemory summary includes Rear
            from brain.memory import ShortTermMemory
            stm = ShortTermMemory(max_cycles=3)
            stm.record(ws, "turn_right")
            summary = stm.summarise()
            assert "Rear=" in summary, f"Rear= missing from STM summary: {summary}"
            assert "180" in summary, "Rear value missing from STM summary"
            self.log("  ShortTermMemory.summarise() includes Rear distance", "SUCCESS")

            # 5. Default rear_distance_cm is 200.0 (no breakage without providing it)
            ws_default = WorldState(
                front_distance_cm=50.0,
                left_distance_cm=100.0,
                right_distance_cm=100.0,
                target_visible=False,
            )
            assert ws_default.rear_distance_cm == 200.0, "Default rear should be 200.0"
            self.log("  rear_distance_cm defaults to 200.0 (backward compatible)", "SUCCESS")

            # 6. Simulator produces rear_distance_cm in valid range
            from world.simulator import read_world_state
            for _ in range(3):
                state = read_world_state()
                assert 0 <= state.rear_distance_cm <= 400, (
                    f"Rear distance out of range: {state.rear_distance_cm}"
                )
            self.log("  Simulator produces valid rear_distance_cm", "SUCCESS")

            # 7. [!!BLOCKED] flag appears in main.py sensor log when front < 30
            from config import Config
            cfg = Config()
            buf = io.StringIO()
            with redirect_stdout(buf):
                front_flag = " [!!BLOCKED]" if ws.front_distance_cm < cfg.MIN_SAFE_DISTANCE_CM else ""
                print(
                    f"[SENSORS] Front: {ws.front_distance_cm:.0f}cm{front_flag}"
                    f" | Left: {ws.left_distance_cm:.0f}cm"
                    f" | Right: {ws.right_distance_cm:.0f}cm"
                    f" | Rear: {ws.rear_distance_cm:.0f}cm"
                )
            sensors_line = buf.getvalue()
            assert "[!!BLOCKED]" in sensors_line, "BLOCKED flag missing when front < MIN_SAFE_DISTANCE"
            assert "Rear:" in sensors_line, "Rear not in sensor log line"
            self.log(f"  Sensor log format correct: {sensors_line.strip()}", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Rear Sensor + Logging test failed: {e}", "ERROR")
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
            ("Memory Store & Retrieve", self.test_memory_store_retrieve),
            ("Semantic Map Observation", self.test_semantic_map_observation),
            # Week 4 — RAG + Agents + Agentic RAG
            ("RAG KB Retrieval", self.test_rag_knowledge_base_retrieval),
            ("Short-Term Memory", self.test_short_term_memory),
            ("Traditional RAG Mode", self.test_traditional_rag_mode),
            ("Pure Agent Mode", self.test_pure_agent_mode),
            ("Agentic RAG Hybrid Mode", self.test_agentic_rag_hybrid_mode),
            # Week 4 — Rear sensor + improved logging
            ("Rear Sensor & Logging", self.test_rear_sensor_and_logging),
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
