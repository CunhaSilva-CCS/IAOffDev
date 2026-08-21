from __future__ import annotations

from typing import Any

import httpx

from .base import ChatProvider, ProviderEndpoint, RemoteModel


class ProviderError(Exception):
    pass


class OllamaProvider:
    def __init__(self, endpoint: ProviderEndpoint) -> None:
        self.endpoint = endpoint
        self.timeout = httpx.Timeout(connect=1.5, read=300.0, write=30.0, pool=5.0)

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.endpoint.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[RemoteModel]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.endpoint.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
        models: list[RemoteModel] = []
        for item in data.get("models", []):
            raw = item.get("name") or ""
            if not raw:
                continue
            models.append(
                RemoteModel(
                    id=f"{self.endpoint.id}/{raw}",
                    name=raw,
                    provider_id=self.endpoint.id,
                    provider_name=self.endpoint.name,
                    raw_name=raw,
                    size=item.get("size"),
                    details=item.get("details") or {},
                )
            )
        return models

    async def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.endpoint.base_url}/api/chat", json=payload)
            if response.status_code >= 400:
                raise ProviderError(response.text)
            return response.json()


class OpenAICompatProvider:
    """LM Studio, LocalAI, llama.cpp, Jan, GPT4All, Oobabooga, etc."""

    def __init__(self, endpoint: ProviderEndpoint) -> None:
        self.endpoint = endpoint
        self.timeout = httpx.Timeout(connect=1.5, read=300.0, write=30.0, pool=5.0)
        self.base = endpoint.base_url.rstrip("/")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base}/models")
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[RemoteModel]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base}/models")
            response.raise_for_status()
            data = response.json()
        items = data.get("data") if isinstance(data, dict) else data
        models: list[RemoteModel] = []
        if not isinstance(items, list):
            return models
        for item in items:
            if isinstance(item, str):
                raw = item
            else:
                raw = item.get("id") or item.get("name") or ""
            if not raw:
                continue
            models.append(
                RemoteModel(
                    id=f"{self.endpoint.id}/{raw}",
                    name=raw,
                    provider_id=self.endpoint.id,
                    provider_name=self.endpoint.name,
                    raw_name=raw,
                    details=item if isinstance(item, dict) else {},
                )
            )
        return models

    async def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        # OpenAI chat completions — tools são opcionais e nem todos suportam
        clean_messages = []
        for message in messages:
            role = message.get("role")
            if role not in {"system", "user", "assistant"}:
                continue
            clean_messages.append({"role": role, "content": message.get("content") or ""})

        payload: dict[str, Any] = {
            "model": model,
            "messages": clean_messages,
            "stream": False,
            "temperature": 0.2,
        }
        if tools:
            # Converte tools estilo Ollama/OpenAI function calling se o backend aceitar
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base}/chat/completions", json=payload)
            if response.status_code >= 400:
                # Retry sem tools — muitos servidores locais não suportam
                if tools:
                    payload.pop("tools", None)
                    response = await client.post(f"{self.base}/chat/completions", json=payload)
                if response.status_code >= 400:
                    raise ProviderError(response.text)
            data = response.json()

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls")
        result: dict[str, Any] = {"message": {"role": "assistant", "content": content}}
        if tool_calls:
            result["message"]["tool_calls"] = tool_calls
        return result


def build_provider(endpoint: ProviderEndpoint) -> ChatProvider:
    if endpoint.kind == "ollama":
        return OllamaProvider(endpoint)
    return OpenAICompatProvider(endpoint)
