"""Repositories for memory operations."""

import json
from typing import List, Dict, Any, Optional
from memory.db import DatabaseManager


class ConversationsRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_message(self, session_id: str, role: str, content: str) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
            conn.commit()
            return cursor.lastrowid

    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM conversations WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


class ProjectsRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_project(self, name: str, path: str, description: str = "") -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, path, description) VALUES (?, ?, ?)",
                (name, path, description),
            )
            conn.commit()
            return cursor.lastrowid

    def list_projects(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None


class TasksRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_task(self, title: str, project_id: Optional[int] = None, description: str = "") -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (project_id, title, description, status) VALUES (?, ?, ?, 'pending')",
                (project_id, title, description),
            )
            conn.commit()
            return cursor.lastrowid

    def update_task_status(self, task_id: int, status: str) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
            conn.commit()

    def get_tasks_for_project(self, project_id: Optional[int]) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if project_id is not None:
                cursor.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY id ASC", (project_id,))
            else:
                cursor.execute("SELECT * FROM tasks WHERE project_id IS NULL ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]


class ToolActivityRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def log_activity(self, tool_name: str, arguments: Dict[str, Any], status: str, result: Optional[Any] = None) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tool_activity (tool_name, arguments, status, result) VALUES (?, ?, ?, ?)",
                (tool_name, json.dumps(arguments), status, json.dumps(result) if result is not None else None),
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_activity ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]


class MemoryManager:
    """Unified access point for all memory repositories."""

    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.db_manager = DatabaseManager(db_path)
        self.conversations = ConversationsRepository(self.db_manager)
        self.projects = ProjectsRepository(self.db_manager)
        self.tasks = TasksRepository(self.db_manager)
        self.tool_activity = ToolActivityRepository(self.db_manager)
