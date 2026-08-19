"""AI provider interface, NVIDIA NIM client, response parser, and mock LLM client."""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Structured response from LLM call."""

    content: str
    tool_calls: List[Dict[str, Any]]
    raw_response: Dict[str, Any]


class BaseAIClient:
    """Base interface for AI client providers."""

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        raise NotImplementedError


class MockAIClient(BaseAIClient):
    """Mock AI Client for offline development and testing."""

    def __init__(self, predefined_responses: Optional[List[LLMResponse]] = None):
        self.predefined_responses = predefined_responses or []
        self.call_count = 0

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if self.call_count < len(self.predefined_responses):
            response = self.predefined_responses[self.call_count]
            self.call_count += 1
            return response

        # Default fallback response
        user_msg = messages[-1]["content"] if messages else ""
        return LLMResponse(
            content=f"Mock response for: {user_msg}",
            tool_calls=[],
            raw_response={"mock": True},
        )


class NvidiaNIMClient(BaseAIClient):
    """NVIDIA NIM API Client using standard library urllib with robust error handling."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model: str = "meta/llama-3.1-70b-instruct",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content="[NVIDIA API Key not provided. Please set NVIDIA_API_KEY in your .env file or environment variables.]",
                tool_calls=[],
                raw_response={"error": "missing_api_key"},
            )

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.2,
            "max_tokens": 2048,
        }

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data.get("choices", [{}])[0].get("message", {})
                content = choice.get("content", "")
                tool_calls = parse_tool_calls_from_text(content)
                return LLMResponse(
                    content=content,
                    tool_calls=tool_calls,
                    raw_response=data,
                )
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            err_msg = f"NVIDIA NIM API HTTP Error {e.code}: {e.reason}.\nDetails: {error_body}"
            return LLMResponse(
                content=f"[NVIDIA NIM API Error]: {err_msg}",
                tool_calls=[],
                raw_response={"error": err_msg, "code": e.code},
            )
        except urllib.error.URLError as e:
            err_msg = f"NVIDIA NIM Connection Error: {e.reason}"
            return LLMResponse(
                content=f"[NVIDIA NIM Network Error]: {err_msg}",
                tool_calls=[],
                raw_response={"error": err_msg},
            )
        except Exception as e:
            err_msg = f"Unexpected Error: {str(e)}"
            return LLMResponse(
                content=f"[NVIDIA NIM Error]: {err_msg}",
                tool_calls=[],
                raw_response={"error": err_msg},
            )


def parse_tool_calls_from_text(text: str) -> List[Dict[str, Any]]:
    """Parses structured JSON tool call blocks from LLM content text."""
    tool_calls = []
    if not text:
        return tool_calls

    lines = text.split("\n")
    in_json = False
    json_buf = []

    for line in lines:
        if line.strip().startswith("```json") or line.strip() == "```":
            if in_json:
                in_json = False
                try:
                    parsed = json.loads("\n".join(json_buf))
                    if isinstance(parsed, dict) and "tool" in parsed:
                        tool_calls.append(parsed)
                    elif isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict) and "tool" in item:
                                tool_calls.append(item)
                except Exception:
                    pass
                json_buf = []
            else:
                in_json = True
                json_buf = []
            continue

        if in_json:
            json_buf.append(line)

    if not tool_calls and "tool" in text:
        try:
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                parsed = json.loads(text[start_idx : end_idx + 1])
                if isinstance(parsed, dict) and "tool" in parsed:
                    tool_calls.append(parsed)
        except Exception:
            pass

    return tool_calls
