from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from .config import settings
from .demo import demo_agent_run
from .providers.clients import ProviderError
from .providers.registry import (
    discover_providers,
    flatten_models,
    pick_council_models,
    resolve_model_ref,
)
from .tools import TOOL_DEFINITIONS, resolve_workspace, run_tool


def ensure_demo_workspace():
    """Cria um workspace de demonstração se o padrão não existir com conteúdo."""
    root = settings.workspace_root
    root.mkdir(parents=True, exist_ok=True)
    demo = root / "demo-app"
    if not demo.exists():
        demo.mkdir(parents=True, exist_ok=True)
        (demo / "README.md").write_text(
            "# Demo App\n\nProjeto de exemplo para o IAOffDev.\n",
            encoding="utf-8",
        )
        (demo / "main.py").write_text(
            'def greet(name: str) -> str:\n    return f"Olá, {name}!"\n\n\nif __name__ == "__main__":\n    print(greet("mundo"))\n',
            encoding="utf-8",
        )
    return root


SYSTEM_PROMPT = """Você é o IAOffDev, um agente de IA offline especializado em desenvolvimento de software.

Princípios:
- Responda em português do Brasil, de forma clara e prática.
- Priorize código correto, legível e pronto para uso.
- Use as ferramentas disponíveis (list_dir, read_file, write_file, search_code) quando precisar inspecionar ou editar o projeto.
- Antes de alterar arquivos, leia o contexto relevante.
- Explique decisões importantes de forma breve.
- Quando gerar código, use blocos markdown com a linguagem correta.
- Se algo estiver fora do alcance (sem modelo, sem arquivo), diga objetivamente o que falta.

Você opera 100% local — consulta IAs offline na máquina (Ollama, LM Studio, LocalAI, etc.), sem nuvem.
"""

COUNCIL_SYNTH_PROMPT = """Você é o orquestrador do IAOffDev. Várias IAs offline responderam à mesma pergunta de desenvolvimento.

Sua tarefa:
1. Compare as respostas.
2. Produza UMA resposta final prática em português, com o melhor código/abordagem.
3. Se houver divergências importantes, cite-as brevemente.
4. Não invente APIs que nenhuma resposta usou sem necessidade.
5. Prefira soluções corretas, simples e testáveis.
"""


def _normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for message in messages:
        item: dict[str, Any] = {
            "role": message["role"],
            "content": message.get("content") or "",
        }
        if message.get("name"):
            item["name"] = message["name"]
        if message.get("tool_call_id"):
            item["tool_call_id"] = message["tool_call_id"]
        if message.get("tool_calls"):
            item["tool_calls"] = message["tool_calls"]
        normalized.append(item)
    return normalized


def _chunk_tokens(content: str, size: int = 48) -> list[str]:
    return [content[i : i + size] for i in range(0, len(content), size)] or [""]


class DevAgent:
    async def run(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        workspace: str | None = None,
        use_tools: bool = True,
        council: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        root = resolve_workspace(workspace)
        providers = await discover_providers()
        models = flatten_models(providers)
        online_providers = [p for p in providers if p.online]

        if not online_providers:
            yield {
                "type": "token",
                "content": (
                    "_Nenhuma IA offline detectada (Ollama, LM Studio, LocalAI…). "
                    "Usando modo demonstração local._\n\n"
                ),
            }
            async for event in demo_agent_run(messages, workspace=str(root)):
                yield event
            return

        if council:
            async for event in self._run_council(messages, root=str(root), models=models):
                yield event
            return

        model_ref = model or (
            next((m.id for m in models if "coder" in m.name.lower()), None)
            or (models[0].id if models else settings.default_model)
        )
        resolved = resolve_model_ref(model_ref, models)
        if not resolved:
            yield {"type": "error", "content": f"Modelo não encontrado: {model_ref}"}
            return
        provider, raw_model = resolved

        history = [{"role": "system", "content": SYSTEM_PROMPT + f"\nWorkspace atual: {root}"}]
        history.extend(_normalize_messages(messages))
        tools = TOOL_DEFINITIONS if use_tools and provider.endpoint.kind == "ollama" else None
        rounds = 0

        while True:
            rounds += 1
            if rounds > settings.max_tool_rounds:
                yield {
                    "type": "error",
                    "content": "Limite de rodadas de ferramentas atingido. Reformule o pedido.",
                }
                return

            try:
                response = await provider.chat(
                    model=raw_model,
                    messages=history,
                    tools=tools,
                    stream=False,
                )
            except (ProviderError, Exception) as exc:  # noqa: BLE001
                if rounds == 1:
                    yield {
                        "type": "token",
                        "content": f"_Falha em {provider.endpoint.name}: {exc}. Tentando demonstração…_\n\n",
                    }
                    async for event in demo_agent_run(messages, workspace=str(root)):
                        yield event
                    return
                yield {"type": "error", "content": f"Falha no provedor: {exc}"}
                return

            message = response.get("message") or {}
            tool_calls = message.get("tool_calls") or []
            content = message.get("content") or ""

            if tool_calls:
                history.append(message)
                yield {
                    "type": "assistant_partial",
                    "content": content,
                    "tool_calls": tool_calls,
                }
                for call in tool_calls:
                    function = call.get("function") or {}
                    name = function.get("name") or "unknown"
                    raw_args = function.get("arguments") or {}
                    if isinstance(raw_args, str):
                        import json

                        try:
                            args = json.loads(raw_args) if raw_args.strip() else {}
                        except json.JSONDecodeError:
                            args = {}
                    else:
                        args = raw_args

                    yield {"type": "tool_start", "name": name, "arguments": args}
                    result = run_tool(name, args, root)
                    yield {"type": "tool_result", "name": name, "content": result[:8000]}
                    history.append({"role": "tool", "name": name, "content": result[:12000]})
                continue

            for part in _chunk_tokens(content):
                if part:
                    yield {"type": "token", "content": part}
            yield {
                "type": "done",
                "model": model_ref,
                "workspace": str(root),
                "providers": [p.id for p in online_providers],
            }
            return

    async def _run_council(
        self,
        messages: list[dict[str, Any]],
        *,
        root: str,
        models: list[Any],
    ) -> AsyncIterator[dict[str, Any]]:
        selected = pick_council_models(models)
        if not selected:
            yield {"type": "error", "content": "Nenhum modelo disponível para consulta coletiva."}
            return

        last_user = next(
            (m.get("content") for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        yield {
            "type": "council_start",
            "content": f"Consultando {len(selected)} IA(s) offline em paralelo…",
            "models": [m.id for m in selected],
        }

        ask_messages = [
            {
                "role": "system",
                "content": (
                    SYSTEM_PROMPT
                    + f"\nWorkspace atual: {root}\n"
                    "Responda de forma direta à pergunta do usuário. "
                    "Se precisar de arquivos, descreva o que faria (nesta rodada não há tools)."
                ),
            },
            {"role": "user", "content": last_user or ""},
        ]

        async def query_one(remote_model: Any) -> dict[str, Any]:
            provider, raw = resolve_model_ref(remote_model.id, models) or (None, None)
            if not provider or not raw:
                return {
                    "model": remote_model.id,
                    "provider": remote_model.provider_name,
                    "ok": False,
                    "content": "Provedor indisponível",
                }
            try:
                response = await asyncio.wait_for(
                    provider.chat(model=raw, messages=ask_messages, tools=None, stream=False),
                    timeout=settings.council_timeout_seconds,
                )
                content = ((response.get("message") or {}).get("content") or "").strip()
                return {
                    "model": remote_model.id,
                    "provider": remote_model.provider_name,
                    "ok": bool(content),
                    "content": content or "(resposta vazia)",
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "model": remote_model.id,
                    "provider": remote_model.provider_name,
                    "ok": False,
                    "content": f"Erro: {exc}",
                }

        tasks = [asyncio.create_task(query_one(m)) for m in selected]
        answers: list[dict[str, Any]] = []
        for task in asyncio.as_completed(tasks):
            result = await task
            answers.append(result)
            yield {
                "type": "council_result",
                "name": result["model"],
                "content": result["content"][:6000],
                "ok": result["ok"],
                "provider": result.get("provider"),
            }

        ok_answers = [a for a in answers if a.get("ok")]
        if not ok_answers:
            yield {
                "type": "error",
                "content": "Nenhuma IA offline retornou resposta útil. Verifique Ollama/LM Studio/LocalAI.",
            }
            return

        # Síntese com o primeiro modelo coder disponível
        synth_model = pick_council_models(models, max_models=1)[0]
        resolved = resolve_model_ref(synth_model.id, models)
        digest_parts = []
        for answer in ok_answers:
            digest_parts.append(
                f"### {answer['provider']} · `{answer['model']}`\n{answer['content'][:3500]}\n"
            )
        synth_messages = [
            {"role": "system", "content": COUNCIL_SYNTH_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Pergunta original:\n{last_user}\n\n"
                    f"Respostas das IAs:\n\n" + "\n---\n".join(digest_parts)
                ),
            },
        ]

        yield {
            "type": "token",
            "content": "\n\n---\n\n**Síntese do IAOffDev** (combinando todas as IAs):\n\n",
        }

        if resolved:
            provider, raw = resolved
            try:
                response = await provider.chat(
                    model=raw,
                    messages=synth_messages,
                    tools=None,
                    stream=False,
                )
                content = ((response.get("message") or {}).get("content") or "").strip()
                for part in _chunk_tokens(content):
                    if part:
                        yield {"type": "token", "content": part}
            except Exception as exc:  # noqa: BLE001
                # Fallback: junta as melhores respostas
                yield {
                    "type": "token",
                    "content": (
                        f"_Síntese automática falhou ({exc}). Segue consolidado manual:_\n\n"
                        + "\n\n".join(
                            f"**{a['model']}**\n{a['content'][:2000]}" for a in ok_answers[:3]
                        )
                    ),
                }
        else:
            yield {
                "type": "token",
                "content": "\n\n".join(
                    f"**{a['model']}**\n{a['content'][:2000]}" for a in ok_answers[:3]
                ),
            }

        yield {
            "type": "done",
            "model": "council",
            "workspace": root,
            "models": [a["model"] for a in ok_answers],
        }
