from __future__ import annotations

import json
import os
from typing import Any

from ..config import settings
from .base import ProviderEndpoint, ProviderStatus, RemoteModel
from .clients import build_provider

# Backends locais comuns para desenvolvimento de software offline
DEFAULT_ENDPOINTS: list[ProviderEndpoint] = [
    ProviderEndpoint("ollama", "Ollama", "ollama", "http://127.0.0.1:11434"),
    ProviderEndpoint("lmstudio", "LM Studio", "openai_compat", "http://127.0.0.1:1234/v1"),
    ProviderEndpoint("localai", "LocalAI", "openai_compat", "http://127.0.0.1:8080/v1"),
    ProviderEndpoint("llamacpp", "llama.cpp", "openai_compat", "http://127.0.0.1:8081/v1"),
    ProviderEndpoint("jan", "Jan", "openai_compat", "http://127.0.0.1:1337/v1"),
    ProviderEndpoint("gpt4all", "GPT4All", "openai_compat", "http://127.0.0.1:4891/v1"),
    ProviderEndpoint("oobabooga", "Oobabooga", "openai_compat", "http://127.0.0.1:5000/v1"),
    ProviderEndpoint("tabbyapi", "TabbyAPI", "openai_compat", "http://127.0.0.1:5001/v1"),
]


CODER_HINTS = (
    "coder",
    "code",
    "devstral",
    "deepseek",
    "qwen2.5-coder",
    "qwen3-coder",
    "starcoder",
    "codellama",
    "wizardcoder",
    "phind",
    "granite-code",
    "codestral",
)


def _extra_endpoints() -> list[ProviderEndpoint]:
    raw = os.environ.get("IAOFFDEV_EXTRA_PROVIDERS") or settings.extra_providers_json
    if not raw or raw == "[]":
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    endpoints: list[ProviderEndpoint] = []
    for item in data:
        try:
            endpoints.append(
                ProviderEndpoint(
                    id=str(item["id"]),
                    name=str(item.get("name") or item["id"]),
                    kind=item.get("kind") or "openai_compat",
                    base_url=str(item["base_url"]).rstrip("/"),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return endpoints


def all_endpoints() -> list[ProviderEndpoint]:
    # Ollama URL configurável tem prioridade
    endpoints = [
        ProviderEndpoint("ollama", "Ollama", "ollama", settings.ollama_base_url.rstrip("/")),
        *[e for e in DEFAULT_ENDPOINTS if e.id != "ollama"],
        *_extra_endpoints(),
    ]
    # Dedup por id
    seen: set[str] = set()
    unique: list[ProviderEndpoint] = []
    for endpoint in endpoints:
        if endpoint.id in seen:
            continue
        seen.add(endpoint.id)
        unique.append(endpoint)
    return unique


async def discover_providers() -> list[ProviderStatus]:
    results: list[ProviderStatus] = []
    for endpoint in all_endpoints():
        provider = build_provider(endpoint)
        try:
            online = await provider.health()
            models: list[RemoteModel] = []
            error = None
            if online:
                try:
                    models = await provider.list_models()
                except Exception as exc:  # noqa: BLE001
                    error = str(exc)
                    online = False
            results.append(
                ProviderStatus(
                    id=endpoint.id,
                    name=endpoint.name,
                    kind=endpoint.kind,
                    base_url=endpoint.base_url,
                    online=online,
                    models=models,
                    error=error,
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                ProviderStatus(
                    id=endpoint.id,
                    name=endpoint.name,
                    kind=endpoint.kind,
                    base_url=endpoint.base_url,
                    online=False,
                    error=str(exc),
                )
            )
    return results


def flatten_models(providers: list[ProviderStatus]) -> list[RemoteModel]:
    models: list[RemoteModel] = []
    for provider in providers:
        if provider.online:
            models.extend(provider.models)
    return models


def is_coder_model(name: str) -> bool:
    lower = name.lower()
    return any(hint in lower for hint in CODER_HINTS)


def pick_council_models(
    models: list[RemoteModel],
    *,
    max_models: int | None = None,
) -> list[RemoteModel]:
    """Escolhe modelos para consulta em paralelo (prioriza coder)."""
    limit = max_models or settings.council_max_models
    coder = [m for m in models if is_coder_model(m.name)]
    others = [m for m in models if not is_coder_model(m.name)]
    # Um modelo por provider primeiro (diversidade), depois completa
    selected: list[RemoteModel] = []
    seen_providers: set[str] = set()
    for pool in (coder, others):
        for model in pool:
            if model.provider_id in seen_providers:
                continue
            selected.append(model)
            seen_providers.add(model.provider_id)
            if len(selected) >= limit:
                return selected
    for pool in (coder, others):
        for model in pool:
            if any(s.id == model.id for s in selected):
                continue
            selected.append(model)
            if len(selected) >= limit:
                return selected
    return selected


def resolve_model_ref(model_ref: str | None, models: list[RemoteModel]) -> tuple[Any, str] | None:
    """Retorna (provider, raw_model_name) a partir de 'provider/model' ou nome simples."""
    if not model_ref:
        return None
    if "/" in model_ref:
        provider_id, raw = model_ref.split("/", 1)
        for model in models:
            if model.provider_id == provider_id and model.raw_name == raw:
                endpoint = next(e for e in all_endpoints() if e.id == provider_id)
                return build_provider(endpoint), raw
        # Provider conhecido mesmo sem discovery prévia
        endpoint = next((e for e in all_endpoints() if e.id == provider_id), None)
        if endpoint:
            return build_provider(endpoint), raw
        return None
    # Nome simples: procura em qualquer provider
    for model in models:
        if model.raw_name == model_ref or model.name == model_ref:
            endpoint = next(e for e in all_endpoints() if e.id == model.provider_id)
            return build_provider(endpoint), model.raw_name
    # Fallback Ollama
    endpoint = next(e for e in all_endpoints() if e.id == "ollama")
    return build_provider(endpoint), model_ref
