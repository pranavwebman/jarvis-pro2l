"""Tests for PyQt6 GUI application initialization and widget rendering."""

import sys
import os
import unittest

# Use offscreen platform plugin for Qt in headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from gui import JarvisWorkspaceApp, ChatPanel, TaskPanel, ToolActivityPanel


class TestGUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize single QApplication instance for headless Qt testing
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_gui_initialization(self):
        window = JarvisWorkspaceApp(agent=None)
        self.assertIsNotNone(window.chat_panel)
        self.assertIsNotNone(window.task_panel)
        self.assertIsNotNone(window.activity_panel)

    def test_chat_append(self):
        chat = ChatPanel()
        chat.append_message("TestSender", "Hello PyQt6")
        content = chat.history_text.toPlainText()
        self.assertIn("TestSender: Hello PyQt6", content)


if __name__ == "__main__":
    unittest.main()
