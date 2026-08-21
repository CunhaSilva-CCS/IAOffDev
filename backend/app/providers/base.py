from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


ProviderKind = Literal["ollama", "openai_compat"]


@dataclass(frozen=True)
class ProviderEndpoint:
    id: str
    name: str
    kind: ProviderKind
    base_url: str
    # Preferência para modelos de código (filtro suave)
    coder_bias: bool = True


@dataclass
class RemoteModel:
    id: str  # provider_id/model_name
    name: str
    provider_id: str
    provider_name: str
    raw_name: str
    size: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStatus:
    id: str
    name: str
    kind: ProviderKind
    base_url: str
    online: bool
    models: list[RemoteModel] = field(default_factory=list)
    error: str | None = None


class ChatProvider(Protocol):
    endpoint: ProviderEndpoint

    async def health(self) -> bool: ...

    async def list_models(self) -> list[RemoteModel]: ...

    async def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]: ...
