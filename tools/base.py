"""Base classes and schemas for the JARVIS Tool Protocol."""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class PermissionLevel(Enum):
    """Permission levels for tools."""

    READ_ONLY = "READ_ONLY"  # Safe operations like reading files, listing directory
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"  # Actions modifying files or system state
    DANGEROUS = "DANGEROUS"  # Destructive operations like file deletion or command execution


@dataclass
class ValidationResult:
    """Result of tool argument validation."""

    is_valid: bool
    error_message: Optional[str] = None


@dataclass
class ToolResult:
    """Standard response returned by tool execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None


class BaseTool:
    """Base class for all tools executable by JARVIS."""

    name: str = ""
    description: str = ""
    permission_level: PermissionLevel = PermissionLevel.READ_ONLY
    parameters_schema: Dict[str, Any] = field(default_factory=dict)

    def validate(self, arguments: Dict[str, Any]) -> ValidationResult:
        """Validate input arguments against tool schema."""
        return ValidationResult(is_valid=True)

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """Execute tool action safely."""
        raise NotImplementedError

    def to_schema_dict(self) -> Dict[str, Any]:
        """Convert tool descriptor into schema format suitable for LLM context."""
        return {
            "name": self.name,
            "description": self.description,
            "permission_level": self.permission_level.value,
            "parameters": self.parameters_schema,
        }


class ToolRegistry:
    """Central registry for managing tools and validation."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Any]:
        """List schemas of all registered tools."""
        return {name: tool.to_schema_dict() for name, tool in self._tools.items()}
