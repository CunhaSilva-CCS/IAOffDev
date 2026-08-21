from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Any

from .config import settings

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".cache",
    "target",
    ".idea",
    ".vscode",
}

TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".json",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".css",
    ".scss",
    ".html",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".swift",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".graphql",
    ".vue",
    ".svelte",
    ".env",
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
}


def resolve_workspace(workspace: str | None) -> Path:
    root = Path(workspace).expanduser().resolve() if workspace else settings.workspace_root.resolve()
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise ValueError(f"Workspace inválido: {root}")
    return root


def safe_join(workspace: Path, relative: str) -> Path:
    candidate = (workspace / relative).resolve()
    if not str(candidate).startswith(str(workspace)):
        raise ValueError("Caminho fora do workspace")
    return candidate


def list_directory(workspace: Path, relative: str = ".") -> list[dict[str, Any]]:
    target = safe_join(workspace, relative)
    if not target.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {relative}")
    if not target.is_dir():
        raise NotADirectoryError(f"Não é um diretório: {relative}")

    entries: list[dict[str, Any]] = []
    for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name in SKIP_DIRS:
            continue
        rel = str(item.relative_to(workspace))
        entries.append(
            {
                "name": item.name,
                "path": rel,
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else None,
            }
        )
    return entries


def read_file(workspace: Path, relative: str) -> str:
    target = safe_join(workspace, relative)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {relative}")
    size = target.stat().st_size
    if size > settings.max_file_bytes:
        raise ValueError(f"Arquivo muito grande ({size} bytes). Limite: {settings.max_file_bytes}")
    return target.read_text(encoding="utf-8", errors="replace")


def write_file(workspace: Path, relative: str, content: str) -> str:
    target = safe_join(workspace, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return str(target.relative_to(workspace))


def search_files(
    workspace: Path,
    query: str,
    *,
    glob: str = "*",
    max_results: int = 40,
) -> list[dict[str, Any]]:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results: list[dict[str, Any]] = []

    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            if not fnmatch.fnmatch(filename, glob):
                continue
            path = Path(root) / filename
            if path.suffix.lower() not in TEXT_EXTENSIONS and filename not in {
                "Dockerfile",
                "Makefile",
                "LICENSE",
                "README",
            }:
                continue
            try:
                if path.stat().st_size > settings.max_file_bytes:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for idx, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    results.append(
                        {
                            "path": str(path.relative_to(workspace)),
                            "line": idx,
                            "preview": line.strip()[:240],
                        }
                    )
                    if len(results) >= max_results:
                        return results
    return results


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Lista arquivos e pastas de um diretório relativo ao workspace do projeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho relativo. Use '.' para a raiz.",
                        "default": ".",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lê o conteúdo de um arquivo de texto do workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho relativo do arquivo"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Cria ou sobrescreve um arquivo no workspace com o conteúdo fornecido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho relativo do arquivo"},
                    "content": {"type": "string", "description": "Conteúdo completo do arquivo"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Busca um termo no código-fonte do workspace e retorna trechos com caminho e linha.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto a procurar"},
                    "glob": {
                        "type": "string",
                        "description": "Filtro de nome de arquivo, ex: '*.py'",
                        "default": "*",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def run_tool(name: str, arguments: dict[str, Any], workspace: Path) -> str:
    try:
        if name == "list_dir":
            entries = list_directory(workspace, arguments.get("path") or ".")
            if not entries:
                return "(diretório vazio)"
            lines = []
            for entry in entries:
                prefix = "[dir]" if entry["is_dir"] else "[file]"
                size = f" ({entry['size']} B)" if entry["size"] is not None else ""
                lines.append(f"{prefix} {entry['path']}{size}")
            return "\n".join(lines)

        if name == "read_file":
            return read_file(workspace, arguments["path"])

        if name == "write_file":
            written = write_file(workspace, arguments["path"], arguments["content"])
            return f"Arquivo gravado: {written}"

        if name == "search_code":
            hits = search_files(
                workspace,
                arguments["query"],
                glob=arguments.get("glob") or "*",
            )
            if not hits:
                return "Nenhum resultado."
            return "\n".join(f"{h['path']}:{h['line']}: {h['preview']}" for h in hits)

        return f"Ferramenta desconhecida: {name}"
    except Exception as exc:  # noqa: BLE001 — relatório para o modelo
        return f"Erro ao executar {name}: {exc}"
