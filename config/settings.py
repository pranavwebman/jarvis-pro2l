"""Configuration management for JARVIS."""

import os
from dataclasses import dataclass
from typing import Optional


def load_dotenv(env_path: str = ".env") -> None:
    """Load environment variables from a .env file into os.environ if present."""
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass


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
    def from_env(cls, env_path: str = ".env") -> "Config":
        """Load configuration from environment variables (loading .env if exists)."""
        load_dotenv(env_path)
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
