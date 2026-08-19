"""Planner for decomposing user requests into tasks."""

from typing import List, Dict, Any, Optional
from memory.repository import MemoryManager


class Planner:
    """Manages multi-step task decomposition and plan tracking."""

    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    def create_plan(self, title: str, steps: List[str], project_id: Optional[int] = None) -> List[int]:
        """Creates a set of tasks representing plan steps."""
        task_ids = []
        for idx, step_desc in enumerate(steps, start=1):
            task_title = f"Step {idx}: {step_desc}"
            t_id = self.memory.tasks.add_task(
                title=task_title, project_id=project_id, description=step_desc
            )
            task_ids.append(t_id)
        return task_ids

    def get_plan_summary(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns plan tasks for the given project."""
        return self.memory.tasks.get_tasks_for_project(project_id)
