"""Tests for Agent brain, context manager, and tool security execution loop."""

import os
import tempfile
import unittest
from config import Config
from ai import MockAIClient, LLMResponse
from tools import create_default_registry
from memory import MemoryManager
from brain import Agent, ContextManager, Planner


class TestBrain(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "brain_test.db")
        self.config = Config(require_confirmation=True)
        self.tools = create_default_registry()
        self.memory = MemoryManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_agent_read_only_tool_execution(self):
        # Setup mock client returning a system info tool request
        mock_resp = LLMResponse(
            content="Checking system status...",
            tool_calls=[{"tool": "system.get_info", "arguments": {}}],
            raw_response={},
        )
        ai_client = MockAIClient(predefined_responses=[mock_resp])

        agent = Agent(self.config, ai_client, self.tools, self.memory)
        result = agent.process_user_input("What is the system info?")

        self.assertEqual(result["response"], "Checking system status...")
        self.assertEqual(len(result["tool_results"]), 1)
        self.assertTrue(result["tool_results"][0]["success"])
        self.assertIn("system", result["tool_results"][0]["data"])

    def test_agent_confirmation_required_denied(self):
        test_file = os.path.join(self.temp_dir.name, "write_test.txt")
        mock_resp = LLMResponse(
            content="Writing file...",
            tool_calls=[{
                "tool": "filesystem.write_file",
                "arguments": {"path": test_file, "content": "Hello"},
            }],
            raw_response={},
        )
        ai_client = MockAIClient(predefined_responses=[mock_resp])

        # Confirmation handler returning False (denied)
        def deny_handler(tool_name, args):
            return False

        agent = Agent(self.config, ai_client, self.tools, self.memory, confirmation_handler=deny_handler)
        result = agent.process_user_input("Write file")

        self.assertEqual(len(result["tool_results"]), 1)
        self.assertFalse(result["tool_results"][0]["success"])
        self.assertIn("User denied execution", result["tool_results"][0]["error"])
        self.assertFalse(os.path.exists(test_file))

    def test_agent_confirmation_required_approved(self):
        test_file = os.path.join(self.temp_dir.name, "write_test_appr.txt")
        mock_resp = LLMResponse(
            content="Writing file...",
            tool_calls=[{
                "tool": "filesystem.write_file",
                "arguments": {"path": test_file, "content": "Hello Approved"},
            }],
            raw_response={},
        )
        ai_client = MockAIClient(predefined_responses=[mock_resp])

        # Confirmation handler returning True (approved)
        def approve_handler(tool_name, args):
            return True

        agent = Agent(self.config, ai_client, self.tools, self.memory, confirmation_handler=approve_handler)
        result = agent.process_user_input("Write file")

        self.assertEqual(len(result["tool_results"]), 1)
        self.assertTrue(result["tool_results"][0]["success"])
        self.assertTrue(os.path.exists(test_file))

    def test_planner_creates_and_fetches_tasks(self):
        planner = Planner(self.memory)
        task_ids = planner.create_plan("Build Feature", ["Design schema", "Implement core"])
        self.assertEqual(len(task_ids), 2)

        summary = planner.get_plan_summary()
        self.assertEqual(len(summary), 2)
        self.assertEqual(summary[0]["title"], "Step 1: Design schema")


if __name__ == "__main__":
    unittest.main()
