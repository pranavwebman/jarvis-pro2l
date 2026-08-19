"""Configuration management for JARVIS."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration settings."""

    # NVIDIA NIM settings
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.1-70b-instruct"

    # Application paths
    db_path: str = "jarvis_memory.db"
    workspace_dir: str = "."

    # Safety settings
    require_confirmation: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            nvidia_api_key=os.getenv("NVIDIA_API_KEY", ""),
            nvidia_base_url=os.getenv(
                "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
            ),
            nvidia_model=os.getenv(
                "NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"
            ),
            db_path=os.getenv("JARVIS_DB_PATH", "jarvis_memory.db"),
            workspace_dir=os.getenv("JARVIS_WORKSPACE", "."),
            require_confirmation=os.getenv("JARVIS_REQUIRE_CONFIRMATION", "true").lower()
            in ("true", "1", "yes"),
        )
