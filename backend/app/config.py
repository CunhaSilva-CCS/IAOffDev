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
    # Consulta paralela em todas as IAs offline
    council_max_models: int = 6
    council_timeout_seconds: float = 90.0
    # JSON opcional: [{"id":"meu","name":"Meu LLM","kind":"openai_compat","base_url":"http://127.0.0.1:9999/v1"}]
    extra_providers_json: str = "[]"


settings = Settings()
