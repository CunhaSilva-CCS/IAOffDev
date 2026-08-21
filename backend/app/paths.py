from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    """Raiz do repositório ou do bundle .app."""
    if getattr(sys, "frozen", False):
        # PyInstaller
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    env = os.environ.get("IAOFFDEV_APP_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    # backend/app/paths.py → backend/app → backend → repo
    return Path(__file__).resolve().parents[2]


def resolve_static_dir() -> Path | None:
    env = os.environ.get("IAOFFDEV_STATIC_DIR")
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.exists() else None

    root = project_root()
    candidates = [
        root / "ui",
        root / "frontend" / "dist",
        root / "Resources" / "ui",
        Path(__file__).resolve().parents[1] / "ui",
    ]
    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    return None
