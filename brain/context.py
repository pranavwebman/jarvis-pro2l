"""Context Manager for assembling prompt context."""

from typing import Dict, Any, List, Optional
from memory.repository import MemoryManager


class ContextManager:
    """Assembles prompt context from active project, memory, and environment."""

    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.active_project_id: Optional[int] = None

    def set_active_project(self, project_id: Optional[int]) -> None:
        self.active_project_id = project_id

    def build_system_prompt(self, available_tools_schema: Dict[str, Any]) -> str:
        prompt = [
            "You are JARVIS, a personal AI workspace assistant running on Windows 10.",
            "You help users with conversational interaction, project planning, code generation, file management, and system tasks.",
            "CRITICAL SAFETY RULE: You must ONLY request tool execution using valid JSON format.",
            "Tools MUST be specified as a JSON code block in the following format:",
            "```json",
            '{\n  "tool": "tool_name",\n  "arguments": {\n    "param1": "value1"\n  }\n}',
            "```",
            "Available Tools Schema:",
        ]

        for name, tool_info in available_tools_schema.items():
            prompt.append(
                f"- {name} (Permission: {tool_info['permission_level']}): {tool_info['description']}"
            )

        if self.active_project_id is not None:
            tasks = self.memory.tasks.get_tasks_for_project(self.active_project_id)
            prompt.append("\nActive Project Tasks:")
            for t in tasks:
                prompt.append(f"- [{t['status'].upper()}] Task #{t['id']}: {t['title']}")

        return "\n".join(prompt)
