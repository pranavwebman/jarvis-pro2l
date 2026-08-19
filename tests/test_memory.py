"""Tests for SQLite database initialization and memory repositories."""

import os
import tempfile
import unittest
from memory import MemoryManager


class TestMemory(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_memory.db")
        self.memory = MemoryManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_conversations(self):
        self.memory.conversations.add_message("session_1", "user", "Hello JARVIS")
        self.memory.conversations.add_message("session_1", "assistant", "Hello User")

        msgs = self.memory.conversations.get_messages("session_1")
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[0]["content"], "Hello JARVIS")
        self.assertEqual(msgs[1]["role"], "assistant")

    def test_projects_and_tasks(self):
        proj_id = self.memory.projects.create_project("JARVIS-V2", "/tmp/jarvis", "AI workspace")
        projects = self.memory.projects.list_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "JARVIS-V2")

        task_id = self.memory.tasks.add_task("Build GUI", project_id=proj_id, description="Tkinter workspace")
        tasks = self.memory.tasks.get_tasks_for_project(proj_id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["status"], "pending")

        self.memory.tasks.update_task_status(task_id, "completed")
        tasks_updated = self.memory.tasks.get_tasks_for_project(proj_id)
        self.assertEqual(tasks_updated[0]["status"], "completed")

    def test_tool_activity_log(self):
        self.memory.tool_activity.log_activity("filesystem.read_file", {"path": "a.txt"}, "SUCCESS", {"content": "ok"})
        logs = self.memory.tool_activity.get_recent_activity(10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["tool_name"], "filesystem.read_file")
        self.assertEqual(logs[0]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
