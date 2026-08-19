"""Modular GUI Workspace views for JARVIS using Python Tkinter."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Optional, Callable, Dict, Any, List


class ChatPanel(ttk.Frame):
    """Panel for user conversation and AI responses."""

    def __init__(self, parent, send_callback: Callable[[str], None]):
        super().__init__(parent)
        self.send_callback = send_callback
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Message History
        self.history_text = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, state="disabled", width=60, height=20
        )
        self.history_text.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Input box
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(self, textvariable=self.input_var)
        self.input_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.input_entry.bind("<Return>", lambda e: self._on_send())

        # Send Button
        self.send_btn = ttk.Button(self, text="Send", command=self._on_send)
        self.send_btn.grid(row=1, column=1, padx=5, pady=5)

    def _on_send(self):
        text = self.input_var.get().strip()
        if text:
            self.append_message("User", text)
            self.input_var.set("")
            self.send_callback(text)

    def append_message(self, sender: str, message: str):
        self.history_text.config(state="normal")
        self.history_text.insert(tk.END, f"{sender}: {message}\n\n")
        self.history_text.see(tk.END)
        self.history_text.config(state="disabled")


class TaskPanel(ttk.Frame):
    """Panel displaying active project tasks and multi-step plan steps."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        lbl = ttk.Label(self, text="Current Tasks & Planning", font=("Helvetica", 10, "bold"))
        lbl.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.tree = ttk.Treeview(self, columns=("status", "title"), show="headings")
        self.tree.heading("status", text="Status")
        self.tree.heading("title", text="Task Description")
        self.tree.column("status", width=80)
        self.tree.column("title", width=300)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def update_tasks(self, tasks: List[Dict[str, Any]]):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for t in tasks:
            self.tree.insert("", "end", values=(t.get("status", "pending"), t.get("title", "")))


class ToolActivityPanel(ttk.Frame):
    """Panel displaying tool actions, validation status, and results."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        lbl = ttk.Label(self, text="Tool Activity Log", font=("Helvetica", 10, "bold"))
        lbl.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, state="disabled", width=40, height=10
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def log_activity(self, tool_name: str, status: str, details: str):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{status}] {tool_name}\n  Details: {details}\n\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")


class JarvisWorkspaceApp:
    """Main Application Window for JARVIS Workspace."""

    def __init__(self, root: tk.Tk, agent=None):
        self.root = root
        self.agent = agent
        self.root.title("JARVIS - AI Personal Workspace (Windows 10)")
        self.root.geometry("1024x700")

        if self.agent:
            self.agent.confirmation_handler = self.request_confirmation

        self._build_workspace()

    def _build_workspace(self):
        # Configure main window grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # PanedWindow splitting Chat (left) and Workspace Tools/Tasks (right)
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.grid(row=0, column=0, sticky="nsew")

        # Left: Chat
        self.chat_panel = ChatPanel(self.main_paned, send_callback=self.on_user_send)
        self.main_paned.add(self.chat_panel, weight=3)

        # Right: Task & Activity Split
        self.right_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.task_panel = TaskPanel(self.right_paned)
        self.activity_panel = ToolActivityPanel(self.right_paned)

        self.right_paned.add(self.task_panel, weight=2)
        self.right_paned.add(self.activity_panel, weight=2)
        self.main_paned.add(self.right_paned, weight=2)

    def request_confirmation(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Prompt user dialog for confirming dangerous or modifying tool actions."""
        msg = f"JARVIS requests permission to execute tool:\n\nTool: {tool_name}\nArguments: {arguments}\n\nAllow execution?"
        return messagebox.askyesno("JARVIS Permission Request", msg)

    def on_user_send(self, text: str):
        if not self.agent:
            self.chat_panel.append_message("System", "Agent core not connected.")
            return

        # Process input via Agent
        result = self.agent.process_user_input(text)

        if result.get("response"):
            self.chat_panel.append_message("JARVIS", result["response"])

        for t_res in result.get("tool_results", []):
            tool_name = t_res.get("tool", "unknown")
            success = t_res.get("success", False)
            status = "SUCCESS" if success else "DENIED/ERROR"
            details = t_res.get("data") or t_res.get("error")
            self.activity_panel.log_activity(tool_name, status, str(details))

        # Update tasks
        if self.agent.planner:
            tasks = self.agent.planner.get_plan_summary()
            self.task_panel.update_tasks(tasks)
