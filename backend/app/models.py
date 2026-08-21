from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    workspace: str | None = None
    stream: bool = True
    use_tools: bool = True
    council: bool = False  # consultar todas as IAs offline


class ModelInfo(BaseModel):
    name: str
    id: str | None = None
    provider: str | None = None
    provider_id: str | None = None
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ProviderInfo(BaseModel):
    id: str
    name: str
    kind: str
    base_url: str
    online: bool
    models: list[ModelInfo] = Field(default_factory=list)
    error: str | None = None


class StatusResponse(BaseModel):
    online: bool
    ollama_url: str
    models: list[ModelInfo] = Field(default_factory=list)
    providers: list[ProviderInfo] = Field(default_factory=list)
    default_model: str
    message: str
    council_ready: bool = False


class FileEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int | None = None


class ReadFileRequest(BaseModel):
    path: str
    workspace: str | None = None


class WriteFileRequest(BaseModel):
    path: str
    content: str
    workspace: str | None = None


class SearchRequest(BaseModel):
    query: str
    workspace: str | None = None
    glob: str = "*"
    max_results: int = 40
