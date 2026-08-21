from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import DevAgent, ensure_demo_workspace
from .config import settings
from .models import (
    ChatRequest,
    FileEntry,
    ModelInfo,
    ReadFileRequest,
    SearchRequest,
    StatusResponse,
    WriteFileRequest,
)
from .ollama_client import OllamaClient
from .paths import resolve_static_dir
from .tools import list_directory, read_file, resolve_workspace, search_files, write_file

app = FastAPI(
    title="IAOffDev",
    description="Agente de IA offline para desenvolvimento de software",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = DevAgent()
ollama = OllamaClient()
STATIC_DIR = resolve_static_dir()


@app.on_event("startup")
async def startup() -> None:
    ensure_demo_workspace()


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "IAOffDev"}


@app.get("/api/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    online = await ollama.health()
    models: list[ModelInfo] = []
    message = "Ollama online"
    if online:
        try:
            raw = await ollama.list_models()
            for item in raw:
                models.append(
                    ModelInfo(
                        name=item.get("name", ""),
                        size=item.get("size"),
                        modified_at=item.get("modified_at"),
                        digest=item.get("digest"),
                        details=item.get("details") or {},
                    )
                )
            if not models:
                message = "Ollama online, mas nenhum modelo instalado. Ex.: ollama pull qwen2.5-coder:7b"
        except Exception as exc:  # noqa: BLE001
            online = False
            message = f"Erro ao listar modelos: {exc}"
    else:
        message = (
            f"Ollama offline em {settings.ollama_base_url}. "
            "Instale e execute: ollama serve"
        )

    return StatusResponse(
        online=online,
        ollama_url=settings.ollama_base_url,
        models=models,
        default_model=settings.default_model,
        message=message,
    )


class WorkspaceRequest(BaseModel):
    path: str = Field(default_factory=lambda: str(settings.workspace_root))


@app.get("/api/workspace")
async def get_workspace(path: str | None = None) -> dict:
    root = resolve_workspace(path)
    entries = list_directory(root, ".")
    return {
        "path": str(root),
        "entries": entries,
    }


@app.get("/api/workspace/tree", response_model=list[FileEntry])
async def workspace_tree(path: str | None = None, relative: str = ".") -> list[FileEntry]:
    root = resolve_workspace(path)
    try:
        entries = list_directory(root, relative)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [FileEntry(**e) for e in entries]


@app.post("/api/files/read")
async def api_read_file(body: ReadFileRequest) -> dict[str, str]:
    root = resolve_workspace(body.workspace)
    try:
        content = read_file(root, body.path)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"path": body.path, "content": content}


@app.post("/api/files/write")
async def api_write_file(body: WriteFileRequest) -> dict[str, str]:
    root = resolve_workspace(body.workspace)
    try:
        written = write_file(root, body.path, body.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"path": written, "status": "ok"}


@app.post("/api/search")
async def api_search(body: SearchRequest) -> dict:
    root = resolve_workspace(body.workspace)
    hits = search_files(root, body.query, glob=body.glob, max_results=body.max_results)
    return {"results": hits}


@app.post("/api/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    messages = [m.model_dump(exclude_none=True) for m in body.messages]

    async def event_stream():
        async for event in agent.run(
            messages,
            model=body.model,
            workspace=body.workspace,
            use_tools=body.use_tools,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class QuickPrompt(BaseModel):
    prompt: str
    model: str | None = None
    workspace: str | None = None


@app.post("/api/ask")
async def ask(body: QuickPrompt) -> StreamingResponse:
    messages = [{"role": "user", "content": body.prompt}]

    async def event_stream():
        async for event in agent.run(
            messages,
            model=body.model,
            workspace=body.workspace,
            use_tools=True,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _mount_frontend() -> None:
    """Serve a UI build when running as app (sem Vite separado)."""
    if STATIC_DIR is None or not STATIC_DIR.exists():
        return
    assets = STATIC_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index_file = STATIC_DIR / "index.html"

    @app.get("/")
    async def spa_index() -> FileResponse:
        return FileResponse(index_file)

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (STATIC_DIR / full_path).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid path") from exc
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)


_mount_frontend()


def create_app() -> FastAPI:
    return app
