from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IAOFFDEV_", env_file=".env", extra="ignore")

    ollama_base_url: str = "http://127.0.0.1:11434"
    default_model: str = "qwen2.5-coder:7b"
    workspace_root: Path = Path.home() / "projects"
    max_file_bytes: int = 200_000
    max_tool_rounds: int = 8
    host: str = "127.0.0.1"
    port: int = 8765


settings = Settings()
