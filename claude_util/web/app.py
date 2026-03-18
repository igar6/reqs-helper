"""FastAPI application — CTO Requirements Agent Web UI."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn

# Load .env from project root (two levels up from this file: web/ → claude_util/ → project/)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"
if _ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE, override=False)
    except ImportError:
        pass  # dotenv not installed — user must set env vars manually
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from .session import start_cleanup_task, stop_cleanup_task
from .ws_handler import handle_websocket

_STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_cleanup_task()
    yield
    stop_cleanup_task()


app = FastAPI(
    title="CTO Requirements Agent",
    description="SAFe Agile requirements analysis and artifact generation",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Include REST routes
app.include_router(router)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(_STATIC_DIR / "index.html"))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await handle_websocket(websocket)


def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Entry point for `cto-web` CLI command and `python -m claude_util`."""
    import webbrowser
    import threading

    # Verify at least one API key is present before starting
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
        print("\n[ERROR] No API key found.")
        print("  Option A (Claude): add  ANTHROPIC_API_KEY=sk-ant-...  to your .env file")
        print("  Option B (Free):   add  OPENROUTER_API_KEY=sk-or-...  to your .env file")
        print("  Then re-run.\n")
        raise SystemExit(1)

    backend = "Anthropic (Claude)" if os.getenv("ANTHROPIC_API_KEY") else "OpenRouter"
    model = os.getenv("AGENT_MODEL", "claude-sonnet-4-6" if os.getenv("ANTHROPIC_API_KEY") else "llama-3.3-70b:free")
    print(f" Backend : {backend}")
    print(f" Model   : {model}")

    url = f"http://{host}:{port}"
    print(f"\n CTO Requirements Agent\n {'─' * 40}")
    print(f" URL : {url}")
    print(f" Stop: Ctrl+C\n")

    if not reload:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    uvicorn.run(
        "claude_util.web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="warning",
    )
