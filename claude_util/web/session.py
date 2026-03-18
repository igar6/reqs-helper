"""In-memory session state for the web CTO agent."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class Phase(str, Enum):
    CLARIFYING = "CLARIFYING"
    REFINING = "REFINING"
    GENERATING = "GENERATING"
    DONE = "DONE"


@dataclass
class SessionState:
    session_id: str
    model: str
    phase: Phase = Phase.CLARIFYING
    round: int = 1
    max_rounds: int = 4
    # OpenAI-format message history [{role, content}, ...]
    history: list[dict[str, str]] = field(default_factory=list)
    # Stored after REFINING phase
    refined_requirements: str = ""
    # Generated artifacts keyed by artifact_id
    artifacts: dict[str, str] = field(default_factory=dict)
    # Index into ARTIFACT_SEQUENCE — tracks step-by-step generation progress
    artifact_index: int = 0
    # Correction text supplied by the user during a generation pause
    artifact_correction: str = ""
    # True when the last artifact was stopped mid-stream (index not yet incremented)
    artifact_stopped: bool = False
    # Gantt chart PNG as base64 string
    gantt_png_b64: str | None = None
    # PDF as bytes
    pdf_bytes: bytes | None = None
    # Role of the person writing the requirements
    user_role: str = ""
    # Scope / type of work
    scope: str = ""
    # Derived project name (extracted from refined requirements)
    project_name: str = "Project"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)

    def touch(self) -> None:
        self.last_active = datetime.utcnow()

    def is_expired(self, ttl_minutes: int = 60) -> bool:
        return datetime.utcnow() - self.last_active > timedelta(minutes=ttl_minutes)


# ---------------------------------------------------------------------------
# Global session store
# ---------------------------------------------------------------------------

_store: dict[str, SessionState] = {}
_cleanup_task: asyncio.Task[None] | None = None


def create_session(model: str) -> SessionState:
    session = SessionState(session_id=str(uuid.uuid4()), model=model)
    _store[session.session_id] = session
    return session


def get_session(session_id: str) -> SessionState | None:
    return _store.get(session_id)


def delete_session(session_id: str) -> None:
    _store.pop(session_id, None)


async def _cleanup_loop(ttl_minutes: int = 60, interval_seconds: int = 300) -> None:
    """Periodically remove expired sessions."""
    while True:
        await asyncio.sleep(interval_seconds)
        expired = [sid for sid, s in list(_store.items()) if s.is_expired(ttl_minutes)]
        for sid in expired:
            _store.pop(sid, None)


def start_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_cleanup_loop())


def stop_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
