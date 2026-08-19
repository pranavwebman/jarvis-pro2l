"""Tests for config and AI modules."""

import os
import tempfile
import unittest
from config.settings import Config, load_dotenv
from ai.client import MockAIClient, LLMResponse, parse_tool_calls_from_text, NvidiaNIMClient


class TestConfigAndAI(unittest.TestCase):

    def test_config_defaults_and_from_env(self):
        cfg = Config.from_env()
        self.assertEqual(cfg.db_path, "jarvis_memory.db")
        self.assertTrue(cfg.require_confirmation)

        os.environ["NVIDIA_API_KEY"] = "test_key_123"
        cfg2 = Config.from_env()
        self.assertEqual(cfg2.nvidia_api_key, "test_key_123")

    def test_load_dotenv(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write("TEST_ENV_KEY=test_env_val\nNVIDIA_API_KEY=key_from_dotenv\n")
            temp_path = tf.name

        try:
            if "TEST_ENV_KEY" in os.environ:
                del os.environ["TEST_ENV_KEY"]
            if "NVIDIA_API_KEY" in os.environ:
                del os.environ["NVIDIA_API_KEY"]

            cfg = Config.from_env(env_path=temp_path)
            self.assertEqual(os.getenv("TEST_ENV_KEY"), "test_env_val")
            self.assertEqual(cfg.nvidia_api_key, "key_from_dotenv")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_mock_ai_client(self):
        mock_resp = LLMResponse(
            content="Hello",
            tool_calls=[{"tool": "filesystem.read_file", "arguments": {"path": "a.txt"}}],
            raw_response={},
        )
        client = MockAIClient(predefined_responses=[mock_resp])

        res = client.generate([{"role": "user", "content": "Hi"}])
        self.assertEqual(res.content, "Hello")
        self.assertEqual(len(res.tool_calls), 1)

        res_fallback = client.generate([{"role": "user", "content": "Next"}])
        self.assertIn("Mock response for: Next", res_fallback.content)

    def test_parse_tool_calls(self):
        text = '''
I will read the file.
```json
{
    "tool": "filesystem.read_file",
    "arguments": {
        "path": "test.txt"
    }
}
```
'''
        calls = parse_tool_calls_from_text(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["tool"], "filesystem.read_file")
        self.assertEqual(calls[0]["arguments"]["path"], "test.txt")

    def test_nvidia_nim_client_no_key(self):
        client = NvidiaNIMClient(api_key="")
        resp = client.generate([{"role": "user", "content": "test"}])
        self.assertIn("API Key not provided", resp.content)


if __name__ == "__main__":
    unittest.main()
