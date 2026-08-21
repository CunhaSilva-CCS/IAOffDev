from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from .config import settings
from .demo import demo_agent_run
from .ollama_client import OllamaClient, OllamaError
from .tools import TOOL_DEFINITIONS, resolve_workspace, run_tool

SYSTEM_PROMPT = """Você é o IAOffDev, um agente de IA offline especializado em desenvolvimento de software.

Princípios:
- Responda em português do Brasil, de forma clara e prática.
- Priorize código correto, legível e pronto para uso.
- Use as ferramentas disponíveis (list_dir, read_file, write_file, search_code) quando precisar inspecionar ou editar o projeto.
- Antes de alterar arquivos, leia o contexto relevante.
- Explique decisões importantes de forma breve.
- Quando gerar código, use blocos markdown com a linguagem correta.
- Se algo estiver fora do alcance (sem modelo, sem arquivo), diga objetivamente o que falta.

Você opera 100% local via Ollama — sem enviar dados para a nuvem.
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


class DevAgent:
    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    async def run(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        workspace: str | None = None,
        use_tools: bool = True,
    ) -> AsyncIterator[dict[str, Any]]:
        model_name = model or settings.default_model
        root = resolve_workspace(workspace)
        history = [{"role": "system", "content": SYSTEM_PROMPT + f"\nWorkspace atual: {root}"}]
        history.extend(_normalize_messages(messages))

        if not await self.client.health():
            yield {
                "type": "token",
                "content": "_Ollama offline. Usando modo demonstração local (ferramentas de arquivos ativas)._\n\n",
            }
            async for event in demo_agent_run(messages, workspace=str(root)):
                yield event
            return

        tools = TOOL_DEFINITIONS if use_tools else None
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
                # Chamada não-stream para detectar tool calls; tokens finais vão no yield.
                response = await self.client.chat(
                    model=model_name,
                    messages=history,
                    tools=tools,
                    stream=False,
                )
            except (OllamaError, Exception) as exc:  # noqa: BLE001
                # Sem Ollama: modo demonstração com ferramentas locais.
                if rounds == 1:
                    yield {
                        "type": "token",
                        "content": (
                            f"_Ollama indisponível ({exc}). Entrando em modo demonstração local…_\n\n"
                        ),
                    }
                    async for event in demo_agent_run(messages, workspace=str(root)):
                        yield event
                    return
                yield {"type": "error", "content": f"Falha no Ollama: {exc}"}
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
                        try:
                            args = json.loads(raw_args) if raw_args.strip() else {}
                        except json.JSONDecodeError:
                            args = {}
                    else:
                        args = raw_args

                    yield {"type": "tool_start", "name": name, "arguments": args}
                    result = run_tool(name, args, root)
                    yield {"type": "tool_result", "name": name, "content": result[:8000]}

                    history.append(
                        {
                            "role": "tool",
                            "name": name,
                            "content": result[:12000],
                        }
                    )
                continue

            # Resposta final — reenvia em stream para UX fluida
            if content:
                # Já temos o conteúdo completo; emite em chunks simulados
                # para manter o protocolo SSE uniforme no frontend.
                chunk_size = 48
                for i in range(0, len(content), chunk_size):
                    yield {"type": "token", "content": content[i : i + chunk_size]}
            else:
                # Tenta stream real se a resposta veio vazia (raro)
                async for event in self._stream_plain(model_name, history):
                    yield event

            yield {"type": "done", "model": model_name, "workspace": str(root)}
            return

    async def _stream_plain(
        self, model: str, messages: list[dict[str, Any]]
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            async for chunk in self.client.chat_stream(model=model, messages=messages, tools=None):
                part = (chunk.get("message") or {}).get("content") or ""
                if part:
                    yield {"type": "token", "content": part}
                if chunk.get("done"):
                    break
        except Exception as exc:  # noqa: BLE001
            yield {"type": "error", "content": str(exc)}


def ensure_demo_workspace() -> Path:
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
