"""FastAPI application entrypoint.

Serves the static frontend (backend/static) and the game API under /api/game.

Run with:
    cd backend
    venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

Then open http://localhost:8000/
"""
from __future__ import annotations

import os
import sys

# The game logic prints debug lines containing Unicode (e.g. "→"). Under uvicorn
# on Windows the default stdout encoding is cp1252, which raises UnicodeEncodeError
# on those characters. Force UTF-8 so debug prints never crash a request.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.game import router as game_router

app = FastAPI(title="You Know Ball?")

app.include_router(game_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Static frontend ───────────────────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
STATIC_DIR = os.path.abspath(STATIC_DIR)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# Mounted last so it doesn't shadow the /api routes above.
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:  # pragma: no cover - defensive
    @app.get("/{_path:path}")
    def _missing_static(_path: str):
        return JSONResponse(
            status_code=500,
            content={"detail": f"Static directory not found: {STATIC_DIR}"},
        )
