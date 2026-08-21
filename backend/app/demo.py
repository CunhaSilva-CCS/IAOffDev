from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from .tools import resolve_workspace, run_tool


DEMO_HELP = """Sou o **IAOffDev** em modo demonstração (Ollama offline).

Posso ainda listar e ler arquivos do workspace com as ferramentas locais.
Para respostas inteligentes, inicie o Ollama e baixe um modelo:

```bash
ollama serve
ollama pull qwen2.5-coder:7b
```

Depois recarregue a página.
"""


async def demo_agent_run(
    messages: list[dict[str, Any]],
    *,
    workspace: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Fallback offline sem LLM: responde a pedidos simples de listagem/leitura."""
    root = resolve_workspace(workspace)
    last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    lower = (last_user or "").lower()

    yield {
        "type": "tool_start",
        "name": "list_dir",
        "arguments": {"path": "."},
    }
    listing = run_tool("list_dir", {"path": "."}, root)
    yield {"type": "tool_result", "name": "list_dir", "content": listing[:4000]}

    if any(k in lower for k in ("leia", "read", "main.py", "arquivo")):
        target = "demo-app/main.py"
        yield {"type": "tool_start", "name": "read_file", "arguments": {"path": target}}
        content = run_tool("read_file", {"path": target}, root)
        yield {"type": "tool_result", "name": "read_file", "content": content[:4000]}
        reply = (
            f"{DEMO_HELP}\n\nLi `{target}`:\n\n```python\n{content}\n```\n\n"
            "Quando o Ollama estiver online, posso refatorar, testar e expandir este código."
        )
    elif any(k in lower for k in ("crie", "criar", "escreva", "write", "endpoint")):
        path = "demo-app/hello_offline.py"
        code = 'def hello() -> str:\n    return "IAOffDev offline"\n'
        yield {
            "type": "tool_start",
            "name": "write_file",
            "arguments": {"path": path, "content": code},
        }
        result = run_tool("write_file", {"path": path, "content": code}, root)
        yield {"type": "tool_result", "name": "write_file", "content": result}
        reply = (
            f"{DEMO_HELP}\n\nCriei `{path}` como exemplo de edição local sem LLM:\n\n"
            f"```python\n{code}```"
        )
    else:
        reply = (
            f"{DEMO_HELP}\n\nConteúdo atual do workspace `{root}`:\n\n```\n{listing}\n```\n\n"
            "Experimente: *liste o projeto*, *leia demo-app/main.py* ou *crie um endpoint*."
        )

    chunk = 64
    for i in range(0, len(reply), chunk):
        yield {"type": "token", "content": reply[i : i + chunk]}
    yield {"type": "done", "model": "demo-offline", "workspace": str(root)}


def wants_demo(event_content: str | None) -> bool:
    if not event_content:
        return False
    needles = ("Não foi possível falar com o Ollama", "Falha no Ollama", "Ollama offline")
    return any(n in event_content for n in needles)
