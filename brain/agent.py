"""JARVIS Core Agent Orchestrator."""

from typing import Dict, Any, List, Optional, Callable
from ai.client import BaseAIClient, LLMResponse
from tools.base import ToolRegistry, PermissionLevel, ToolResult
from memory.repository import MemoryManager
from brain.context import ContextManager
from brain.planner import Planner
from config.settings import Config


class Agent:
    """Primary reasoning loop and tool execution engine for JARVIS."""

    def __init__(
        self,
        config: Config,
        ai_client: BaseAIClient,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
        confirmation_handler: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ):
        self.config = config
        self.ai_client = ai_client
        self.tools = tool_registry
        self.memory = memory_manager
        self.context_mgr = ContextManager(memory_manager)
        self.planner = Planner(memory_manager)
        self.confirmation_handler = confirmation_handler
        self.session_id = "default_session"

    def process_user_input(self, user_text: str) -> Dict[str, Any]:
        """Main agent loop processing user message, invoking AI, validating tool calls, and returning execution response."""
        # 1. Record user message in memory
        self.memory.conversations.add_message(self.session_id, "user", user_text)

        # 2. Get recent conversation history
        history = self.memory.conversations.get_messages(self.session_id, limit=10)
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]

        # 3. Assemble prompt context
        tools_schema = self.tools.list_tools()
        system_prompt = self.context_mgr.build_system_prompt(tools_schema)

        # 4. Invoke AI model
        ai_resp: LLMResponse = self.ai_client.generate(
            messages=messages, system_prompt=system_prompt, tools=list(tools_schema.values())
        )

        # 5. Record AI content response
        if ai_resp.content:
            self.memory.conversations.add_message(self.session_id, "assistant", ai_resp.content)

        tool_results = []

        # 6. Process requested tool actions securely
        for tool_call in ai_resp.tool_calls:
            tool_name = tool_call.get("tool")
            args = tool_call.get("arguments", {})

            tool_obj = self.tools.get_tool(tool_name)
            if not tool_obj:
                err_msg = f"Unknown tool: '{tool_name}'"
                self.memory.tool_activity.log_activity(tool_name, args, "ERROR", {"error": err_msg})
                tool_results.append({"tool": tool_name, "success": False, "error": err_msg})
                continue

            # Validate input arguments
            validation = tool_obj.validate(args)
            if not validation.is_valid:
                err_msg = f"Validation failed: {validation.error_message}"
                self.memory.tool_activity.log_activity(tool_name, args, "INVALID_ARGS", {"error": err_msg})
                tool_results.append({"tool": tool_name, "success": False, "error": err_msg})
                continue

            # Check permissions and confirmation requirements
            requires_conf = (
                self.config.require_confirmation
                and tool_obj.permission_level in (PermissionLevel.CONFIRMATION_REQUIRED, PermissionLevel.DANGEROUS)
            )

            if requires_conf:
                confirmed = False
                if self.confirmation_handler:
                    confirmed = self.confirmation_handler(tool_name, args)

                if not confirmed:
                    err_msg = f"User denied execution of tool '{tool_name}'"
                    self.memory.tool_activity.log_activity(tool_name, args, "DENIED", {"error": err_msg})
                    tool_results.append({"tool": tool_name, "success": False, "error": err_msg})
                    continue

            # Execute tool safely
            exec_res: ToolResult = tool_obj.execute(args)
            status = "SUCCESS" if exec_res.success else "FAILURE"
            self.memory.tool_activity.log_activity(tool_name, args, status, exec_res.data or exec_res.error)

            tool_results.append({
                "tool": tool_name,
                "success": exec_res.success,
                "data": exec_res.data,
                "error": exec_res.error,
            })

        return {
            "response": ai_resp.content,
            "tool_calls": ai_resp.tool_calls,
            "tool_results": tool_results,
        }
