"""Tools package initializer and default registry setup."""

from tools.base import (
    BaseTool,
    PermissionLevel,
    ValidationResult,
    ToolResult,
    ToolRegistry,
)
from tools.filesystem import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    DeleteFileTool,
)
from tools.system import GetSystemInfoTool


def create_default_registry() -> ToolRegistry:
    """Create registry populated with built-in standard tools."""
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ListDirectoryTool())
    registry.register(DeleteFileTool())
    registry.register(GetSystemInfoTool())
    return registry


__all__ = [
    "BaseTool",
    "PermissionLevel",
    "ValidationResult",
    "ToolResult",
    "ToolRegistry",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirectoryTool",
    "DeleteFileTool",
    "GetSystemInfoTool",
    "create_default_registry",
]
