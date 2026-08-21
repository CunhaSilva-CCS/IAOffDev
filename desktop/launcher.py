#!/usr/bin/env python3
"""IAOffDev — aplicativo desktop (janela nativa via pywebview).

No macOS, abre uma janela WKWebView com a interface e sobe a API local.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


def _prepare_paths() -> Path:
    """Garante imports do backend e define raiz do app."""
    here = Path(__file__).resolve().parent
    repo = here.parent
    backend = repo / "backend"

    # Quando empacotado em .app, a estrutura é Resources/{backend,ui,launcher}
    if (here / "backend").is_dir():
        app_root = here
        backend = here / "backend"
    else:
        app_root = repo

    os.environ.setdefault("IAOFFDEV_APP_ROOT", str(app_root))
    ui = app_root / "ui"
    if not ui.exists():
        ui = app_root / "frontend" / "dist"
    if ui.exists():
        os.environ.setdefault("IAOFFDEV_STATIC_DIR", str(ui))

    os.environ.setdefault("IAOFFDEV_HOST", "127.0.0.1")
    os.environ.setdefault(
        "IAOFFDEV_WORKSPACE_ROOT",
        str(Path.home() / "Documents" / "IAOffDev"),
    )

    sys.path.insert(0, str(backend))
    return app_root


def _free_port(host: str, preferred: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, preferred))
            return preferred
        except OSError:
            sock.bind((host, 0))
            return int(sock.getsockname()[1])


def _wait_ready(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(0.2)
    return False


def _run_server(host: str, port: int) -> None:
    import uvicorn

    from app.config import settings

    settings.host = host
    settings.port = port
    uvicorn.run("app.main:app", host=host, port=port, reload=False, log_level="warning")


def main() -> int:
    _prepare_paths()

    host = os.environ.get("IAOFFDEV_HOST", "127.0.0.1")
    preferred = int(os.environ.get("IAOFFDEV_PORT", "8765"))
    port = _free_port(host, preferred)
    os.environ["IAOFFDEV_PORT"] = str(port)

    base = f"http://{host}:{port}"
    thread = threading.Thread(target=_run_server, args=(host, port), daemon=True)
    thread.start()

    if not _wait_ready(f"{base}/api/health"):
        print("Falha ao iniciar o servidor local do IAOffDev.", file=sys.stderr)
        return 1

    try:
        import webview
    except ImportError:
        print(
            "Dependência ausente: pywebview.\n"
            "Instale com: pip install pywebview\n"
            "Ou rode: ./scripts/install-mac.sh",
            file=sys.stderr,
        )
        # Fallback: abre no navegador padrão
        import webbrowser

        webbrowser.open(base)
        print(f"IAOffDev em {base} (navegador). Ctrl+C para encerrar.")
        try:
            while thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        return 0

    window = webview.create_window(
        title="IAOffDev",
        url=base,
        width=1280,
        height=840,
        min_size=(960, 640),
        background_color="#0b1210",
    )
    webview.start(debug=bool(os.environ.get("IAOFFDEV_DEBUG")))
    _ = window
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
