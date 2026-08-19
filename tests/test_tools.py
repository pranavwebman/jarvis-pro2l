"""Tests for tool protocol, validation, and permissions."""

import os
import tempfile
import unittest
from tools import (
    create_default_registry,
    PermissionLevel,
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    DeleteFileTool,
    GetSystemInfoTool,
)


class TestTools(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry = create_default_registry()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registry(self):
        tools = self.registry.list_tools()
        self.assertIn("filesystem.read_file", tools)
        self.assertIn("filesystem.write_file", tools)
        self.assertIn("system.get_info", tools)

    def test_filesystem_lifecycle(self):
        test_file = os.path.join(self.temp_dir.name, "sample.txt")
        write_tool = self.registry.get_tool("filesystem.write_file")
        read_tool = self.registry.get_tool("filesystem.read_file")
        list_tool = self.registry.get_tool("filesystem.list_directory")
        delete_tool = self.registry.get_tool("filesystem.delete_file")

        # 1. Write file
        val = write_tool.validate({"path": test_file, "content": "JARVIS test"})
        self.assertTrue(val.is_valid)
        res = write_tool.execute({"path": test_file, "content": "JARVIS test"})
        self.assertTrue(res.success)

        # 2. Read file
        val = read_tool.validate({"path": test_file})
        self.assertTrue(val.is_valid)
        res = read_tool.execute({"path": test_file})
        self.assertTrue(res.success)
        self.assertEqual(res.data["content"], "JARVIS test")

        # 3. List directory
        val = list_tool.validate({"path": self.temp_dir.name})
        self.assertTrue(val.is_valid)
        res = list_tool.execute({"path": self.temp_dir.name})
        self.assertTrue(res.success)
        filenames = [item["name"] for item in res.data["items"]]
        self.assertIn("sample.txt", filenames)

        # 4. Delete file
        val = delete_tool.validate({"path": test_file})
        self.assertTrue(val.is_valid)
        res = delete_tool.execute({"path": test_file})
        self.assertTrue(res.success)
        self.assertFalse(os.path.exists(test_file))

    def test_invalid_path_validation(self):
        read_tool = ReadFileTool()
        val = read_tool.validate({"path": "/path/does/not/exist/foo.txt"})
        self.assertFalse(val.is_valid)
        self.assertIn("File not found", val.error_message)

    def test_permission_levels(self):
        self.assertEqual(
            ReadFileTool().permission_level, PermissionLevel.READ_ONLY
        )
        self.assertEqual(
            WriteFileTool().permission_level, PermissionLevel.CONFIRMATION_REQUIRED
        )
        self.assertEqual(
            DeleteFileTool().permission_level, PermissionLevel.DANGEROUS
        )


if __name__ == "__main__":
    unittest.main()
