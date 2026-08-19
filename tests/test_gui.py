"""Tests for GUI application initialization and headless widget creation."""

import unittest
import tkinter as tk
from gui import JarvisWorkspaceApp, ChatPanel, TaskPanel, ToolActivityPanel


class TestGUI(unittest.TestCase):

    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide main window during headless test
        except Exception:
            self.skipTest("Tkinter display initialization unavailable")

    def tearDown(self):
        if hasattr(self, "root") and self.root:
            self.root.destroy()

    def test_gui_initialization(self):
        app = JarvisWorkspaceApp(self.root, agent=None)
        self.assertIsNotNone(app.chat_panel)
        self.assertIsNotNone(app.task_panel)
        self.assertIsNotNone(app.activity_panel)

    def test_chat_append(self):
        chat = ChatPanel(self.root, send_callback=lambda x: None)
        chat.append_message("Test", "Hello World")
        content = chat.history_text.get("1.0", tk.END)
        self.assertIn("Test: Hello World", content)


if __name__ == "__main__":
    unittest.main()
