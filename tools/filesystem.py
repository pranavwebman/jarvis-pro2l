"""Filesystem tools with path safety and validation."""

import os
from typing import Dict, Any
from tools.base import BaseTool, PermissionLevel, ValidationResult, ToolResult


class ReadFileTool(BaseTool):
    name = "filesystem.read_file"
    description = "Reads the content of a file at the specified path."
    permission_level = PermissionLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative or absolute path to file"}
        },
        "required": ["path"],
    }

    def validate(self, arguments: Dict[str, Any]) -> ValidationResult:
        if "path" not in arguments or not isinstance(arguments["path"], str):
            return ValidationResult(is_valid=False, error_message="Argument 'path' must be a string.")
        path = arguments["path"]
        if not os.path.exists(path):
            return ValidationResult(is_valid=False, error_message=f"File not found: {path}")
        if not os.path.isfile(path):
            return ValidationResult(is_valid=False, error_message=f"Path is not a file: {path}")
        return ValidationResult(is_valid=True)

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        path = arguments["path"]
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return ToolResult(success=True, data={"path": path, "content": content})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(BaseTool):
    name = "filesystem.write_file"
    description = "Writes or overwrites content to a file at the specified path."
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file path"},
            "content": {"type": "string", "description": "Text content to write"},
        },
        "required": ["path", "content"],
    }

    def validate(self, arguments: Dict[str, Any]) -> ValidationResult:
        if "path" not in arguments or not isinstance(arguments["path"], str):
            return ValidationResult(is_valid=False, error_message="Argument 'path' must be a string.")
        if "content" not in arguments or not isinstance(arguments["content"], str):
            return ValidationResult(is_valid=False, error_message="Argument 'content' must be a string.")
        return ValidationResult(is_valid=True)

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        path = arguments["path"]
        content = arguments["content"]
        try:
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(
                success=True,
                data={"path": path, "bytes_written": len(content.encode("utf-8"))},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListDirectoryTool(BaseTool):
    name = "filesystem.list_directory"
    description = "Lists files and subdirectories within a specified directory."
    permission_level = PermissionLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (defaults to '.')"}
        },
    }

    def validate(self, arguments: Dict[str, Any]) -> ValidationResult:
        path = arguments.get("path", ".")
        if not isinstance(path, str):
            return ValidationResult(is_valid=False, error_message="Argument 'path' must be a string.")
        if not os.path.exists(path):
            return ValidationResult(is_valid=False, error_message=f"Directory not found: {path}")
        if not os.path.isdir(path):
            return ValidationResult(is_valid=False, error_message=f"Path is not a directory: {path}")
        return ValidationResult(is_valid=True)

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        path = arguments.get("path", ".")
        try:
            entries = os.listdir(path)
            items = []
            for entry in entries:
                full_path = os.path.join(path, entry)
                is_dir = os.path.isdir(full_path)
                items.append({
                    "name": entry,
                    "is_directory": is_dir,
                    "size": os.path.getsize(full_path) if not is_dir else 0,
                })
            return ToolResult(success=True, data={"path": path, "items": items})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeleteFileTool(BaseTool):
    name = "filesystem.delete_file"
    description = "Deletes a specified file. Destructive operation."
    permission_level = PermissionLevel.DANGEROUS
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to delete"}
        },
        "required": ["path"],
    }

    def validate(self, arguments: Dict[str, Any]) -> ValidationResult:
        if "path" not in arguments or not isinstance(arguments["path"], str):
            return ValidationResult(is_valid=False, error_message="Argument 'path' must be a string.")
        path = arguments["path"]
        if not os.path.exists(path):
            return ValidationResult(is_valid=False, error_message=f"File not found: {path}")
        return ValidationResult(is_valid=True)

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        path = arguments["path"]
        try:
            os.remove(path)
            return ToolResult(success=True, data={"path": path, "status": "deleted"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
