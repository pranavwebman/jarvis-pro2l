"""Application entry point for JARVIS AI Workspace (PyQt6)."""

import sys
from PyQt6.QtWidgets import QApplication
from config import Config
from ai import NvidiaNIMClient, MockAIClient
from tools import create_default_registry
from memory import MemoryManager
from brain import Agent
from gui import JarvisWorkspaceApp


def main():
    # 1. Load configuration
    config = Config.from_env()

    # 2. Initialize memory
    memory = MemoryManager(config.db_path)

    # 3. Setup AI Client (NVIDIA NIM or Mock fallback if key missing)
    if config.nvidia_api_key:
        ai_client = NvidiaNIMClient(
            api_key=config.nvidia_api_key,
            base_url=config.nvidia_base_url,
            model=config.nvidia_model,
        )
    else:
        print("[JARVIS] NVIDIA_API_KEY not found in environment. Initializing Mock AI Client.")
        ai_client = MockAIClient()

    # 4. Setup Tool Registry
    tools = create_default_registry()

    # 5. Initialize Agent Brain
    agent = Agent(
        config=config,
        ai_client=ai_client,
        tool_registry=tools,
        memory_manager=memory,
    )

    # 6. Launch PyQt6 GUI Workspace
    app = QApplication(sys.argv)
    window = JarvisWorkspaceApp(agent=agent)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
