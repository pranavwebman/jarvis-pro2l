"""System info tools."""

import platform
import os
from typing import Dict, Any
from tools.base import BaseTool, PermissionLevel, ToolResult


class GetSystemInfoTool(BaseTool):
    name = "system.get_info"
    description = "Retrieves operating system details, platform name, and environment overview."
    permission_level = PermissionLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {}}

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        try:
            info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
                "cwd": os.getcwd(),
            }
            return ToolResult(success=True, data=info)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
