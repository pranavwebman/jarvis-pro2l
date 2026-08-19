"""PyQt6 Workspace GUI for JARVIS with responsive background worker threading."""

import sys
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QLabel,
    QGroupBox,
)


class AgentWorker(QThread):
    """Background thread worker to execute Agent processing without freezing the UI."""

    finished = pyqtSignal(dict)
    confirmation_requested = pyqtSignal(str, dict)

    def __init__(self, agent, user_text: str):
        super().__init__()
        self.agent = agent
        self.user_text = user_text
        self.confirmation_response: Optional[bool] = None

    def run(self):
        # Attach custom confirmation handler if agent is set
        if self.agent:
            self.agent.confirmation_handler = self._handle_confirmation

        result = self.agent.process_user_input(self.user_text) if self.agent else {}
        self.finished.emit(result)

    def _handle_confirmation(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        self.confirmation_response = None
        self.confirmation_requested.emit(tool_name, arguments)

        # Wait for main thread signal response
        while self.confirmation_response is None:
            self.msleep(100)
        return self.confirmation_response


class ChatPanel(QWidget):
    """Panel for conversation history and user input."""

    send_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)

        input_layout = QHBoxLayout()
        self.input_entry = QLineEdit()
        self.input_entry.setPlaceholderText("Type your message or instruction for JARVIS...")
        self.input_entry.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_entry)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

    def _on_send(self):
        text = self.input_entry.text().strip()
        if text:
            self.append_message("User", text)
            self.input_entry.clear()
            self.send_message.emit(text)

    def append_message(self, sender: str, message: str):
        self.history_text.append(f"<b>{sender}:</b> {message}<br>")

    def set_inputs_enabled(self, enabled: bool):
        self.input_entry.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)


class TaskPanel(QWidget):
    """Panel displaying active project tasks and multi-step plans."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("Active Tasks & Planning")
        group_layout = QVBoxLayout(group)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Status", "Task Description"])
        self.tree.setColumnWidth(0, 100)
        group_layout.addWidget(self.tree)

        layout.addWidget(group)

    def update_tasks(self, tasks: List[Dict[str, Any]]):
        self.tree.clear()
        for t in tasks:
            item = QTreeWidgetItem([t.get("status", "pending").upper(), t.get("title", "")])
            self.tree.addTopLevelItem(item)


class ToolActivityPanel(QWidget):
    """Panel displaying log of requested tool operations and validation results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("Tool Execution Activity Log")
        group_layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        group_layout.addWidget(self.log_text)

        layout.addWidget(group)

    def log_activity(self, tool_name: str, status: str, details: str):
        color = "green" if status == "SUCCESS" else "red"
        self.log_text.append(
            f"<b>[{status}]</b> {tool_name}<br>&nbsp;&nbsp;<font color='{color}'>Details: {details}</font><br>"
        )


class JarvisWorkspaceApp(QMainWindow):
    """Main PyQt6 Window for JARVIS AI Workspace."""

    def __init__(self, agent=None):
        super().__init__()
        self.agent = agent
        self.worker: Optional[AgentWorker] = None

        self.setWindowTitle("JARVIS - Personal AI Workspace (Windows 10)")
        self.resize(1100, 750)

        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Chat
        self.chat_panel = ChatPanel()
        self.chat_panel.send_message.connect(self.on_user_send)
        splitter.addWidget(self.chat_panel)

        # Right splitter: Tasks & Activity Log
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.task_panel = TaskPanel()
        self.activity_panel = ToolActivityPanel()

        right_splitter.addWidget(self.task_panel)
        right_splitter.addWidget(self.activity_panel)

        splitter.addWidget(right_splitter)
        splitter.setSizes([600, 500])

        main_layout.addWidget(splitter)

    def on_user_send(self, text: str):
        if not self.agent:
            self.chat_panel.append_message("System", "Agent core not connected.")
            return

        self.chat_panel.set_inputs_enabled(False)
        self.chat_panel.append_message("System", "<i>JARVIS is thinking...</i>")

        # Launch background worker thread so GUI stays 100% responsive
        self.worker = AgentWorker(self.agent, text)
        self.worker.finished.connect(self.on_agent_finished)
        self.worker.confirmation_requested.connect(self.on_confirmation_requested)
        self.worker.start()

    def on_confirmation_requested(self, tool_name: str, arguments: Dict[str, Any]):
        msg = f"JARVIS requests permission to execute tool:\n\nTool: {tool_name}\nArguments: {arguments}\n\nAllow execution?"
        reply = QMessageBox.question(
            self,
            "JARVIS Permission Request",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if self.worker:
            self.worker.confirmation_response = (reply == QMessageBox.StandardButton.Yes)

    def on_agent_finished(self, result: Dict[str, Any]):
        self.chat_panel.set_inputs_enabled(True)

        resp = result.get("response", "")
        if resp:
            self.chat_panel.append_message("JARVIS", resp)

        for t_res in result.get("tool_results", []):
            tool_name = t_res.get("tool", "unknown")
            success = t_res.get("success", False)
            status = "SUCCESS" if success else "DENIED/ERROR"
            details = t_res.get("data") or t_res.get("error")
            self.activity_panel.log_activity(tool_name, status, str(details))

        if self.agent and self.agent.planner:
            tasks = self.agent.planner.get_plan_summary()
            self.task_panel.update_tasks(tasks)
