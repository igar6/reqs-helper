"""
WebSocket handler — drives the full CTO agent conversation lifecycle.

Phase state machine:
  CLARIFYING  →  REFINING  →  GENERATING  →  DONE
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
import traceback
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from .agent_async import AsyncCTOAgent, ARTIFACT_SEQUENCE, create_agent
from .session import Phase, SessionState, create_session

ROLES = [
    "Product Manager",
    "Product Owner",
    "Business Analyst",
    "Architect / Tech Lead",
    "Release Train Engineer (RTE)",
    "Developer",
    "CTO / VP Engineering",
    "Business Stakeholder",
]

SCOPES = [
    "Strategic Initiative",
    "MVP / New Product",
    "Product Feature",
    "Proof of Concept",
    "Research Spike",
    "Bug Fix / Improvement",
]

_ROLE_NOTES: dict[str, str] = {
    "Product Manager":            "I'll focus on business value, feature prioritization, and market context.",
    "Product Owner":              "I'll focus on backlog-ready stories, acceptance criteria, and sprint clarity.",
    "Business Analyst":           "I'll focus on precise requirements, process flows, and traceability.",
    "Architect / Tech Lead":      "I'll focus on technical constraints, integration points, and NFRs.",
    "Release Train Engineer (RTE)":"I'll focus on ART-level dependencies, PI boundaries, and delivery flow.",
    "Developer":                  "I'll focus on clear acceptance criteria and technical feasibility.",
    "CTO / VP Engineering":       "I'll focus on strategic trade-offs, build vs. buy, and delivery risk.",
    "Business Stakeholder":       "I'll focus on business outcomes, ROI, and executive-level clarity.",
}

def _greeting_for_role_and_scope(role: str, scope: str) -> str:
    note = _ROLE_NOTES.get(role, "I'll tailor the output to your needs.")
    return (
        f"Got it — **{role}**, scope: **{scope}**. {note}\n\n"
        "Share your idea — even rough and incomplete. You can also attach documents or images "
        "using the 📎 button. "
        "I'll ask focused questions to shape it into a precise, SAFe-ready delivery plan: "
        "requirements scorecard, business summary, personas, Definition of Ready, "
        "technical design (with architecture diagram), SAFe deliverables "
        "(Epic → Capability → Feature → Story), PI Planning guide, RACI matrix, and timeline. "
        "Everything exportable as Markdown.\n\n"
        "**What are you building?**"
    )

# Regex to extract project name from refined requirements
_PROJECT_NAME_RE = re.compile(
    r"###\s*Project Name\s*\n+([^\n#]+)", re.IGNORECASE
)


def _extract_project_name(text: str) -> str:
    m = _PROJECT_NAME_RE.search(text)
    if m:
        return m.group(1).strip().strip("[]").strip()
    return "Your Project"


# ---------------------------------------------------------------------------
# Message builders (server → client)
# ---------------------------------------------------------------------------

def _msg(type_: str, **payload: Any) -> dict:
    return {"type": type_, "payload": payload}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

async def handle_websocket(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        agent = create_agent()
    except EnvironmentError as e:
        await websocket.send_json(_msg("error", code="no_api_key", message=str(e)))
        await websocket.close()
        return

    session = create_session(model=agent.model)

    # Announce session, then ask for role before anything else
    await websocket.send_json(_msg(
        "session_created",
        session_id=session.session_id,
        phase=session.phase.value,
        model=agent.model,
    ))
    await websocket.send_json(_msg(
        "role_selection",
        prompt="Before we start — what's your role? This helps me tailor the analysis.",
        roles=ROLES,
    ))

    gen_task: asyncio.Task | None = None

    try:
        while True:
            data = await websocket.receive_json()
            msg_type: str = data.get("type", "")
            payload: dict = data.get("payload", {})

            if msg_type == "set_role":
                role = payload.get("role", "")
                session.user_role = role
                # Ask for scope before starting
                await websocket.send_json(_msg(
                    "scope_selection",
                    prompt="Great. Now select the scope of this work:",
                    scopes=SCOPES,
                ))
            elif msg_type == "set_scope":
                scope = payload.get("scope", "")
                session.scope = scope
                await websocket.send_json(_msg(
                    "chat_message", role="assistant",
                    content=_greeting_for_role_and_scope(session.user_role, scope),
                ))
                # Enable input after both role and scope are set
                await websocket.send_json(_msg("ready"))
            elif msg_type == "user_message":
                await _handle_user_message(
                    websocket, session, agent,
                    payload.get("text", ""),
                    payload.get("attachments"),
                )
            elif msg_type in ("generate", "generate_next"):
                if gen_task and not gen_task.done():
                    continue  # already generating — ignore duplicate
                gen_task = asyncio.create_task(_handle_generate(websocket, session, agent))
            elif msg_type == "stop_artifact":
                if gen_task and not gen_task.done():
                    gen_task.cancel()
                    try:
                        await gen_task
                    except asyncio.CancelledError:
                        pass
            elif msg_type == "cancel":
                if gen_task and not gen_task.done():
                    gen_task.cancel()
                break

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        tb = traceback.format_exc()
        await websocket.send_json(_msg(
            "error", code="server_error", message=str(exc), detail=tb[:500]
        ))


# ---------------------------------------------------------------------------
# Phase handlers
# ---------------------------------------------------------------------------

async def _handle_user_message(
    ws: WebSocket,
    session: SessionState,
    agent: AsyncCTOAgent,
    text: str,
    attachments: list | None = None,
) -> None:
    if not text.strip() and not attachments:
        return

    # Build history entry — multimodal if attachments present
    if attachments:
        content: list | str = []
        for att in attachments:
            if att.get("type") == "image":
                content.append({  # type: ignore[union-attr]
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": att.get("media_type", "image/png"),
                        "data": att["data"],
                    },
                })
        if text.strip():
            content.append({"type": "text", "text": text})  # type: ignore[union-attr]
        elif not content:
            content = text
    else:
        content = text

    session.history.append({"role": "user", "content": content})
    session.touch()

    if session.phase == Phase.CLARIFYING:
        await _run_clarification(ws, session, agent)

    elif session.phase == Phase.REFINING:
        # User sent a correction — re-run refinement
        await _run_refinement(ws, session, agent)

    elif session.phase == Phase.GENERATING:
        # User sent a correction during a generation pause — re-generate the current artifact.
        # After a normal pause, artifact_index points to the NEXT artifact, so step back.
        # After a stop, artifact_index already points to the stopped artifact, so don't step back.
        session.artifact_correction = text.strip()
        if not session.artifact_stopped:
            session.artifact_index = max(0, session.artifact_index - 1)
        session.artifact_stopped = False
        await ws.send_json(_msg(
            "chat_message", role="assistant",
            content="Got it — regenerating with your correction…"
        ))
        await _handle_generate(ws, session, agent)

    elif session.phase == Phase.DONE:
        # User updating requirements after generation — revert to refinement
        session.phase = Phase.REFINING
        await ws.send_json(_msg("phase_change", phase=Phase.REFINING.value))
        await _run_refinement(ws, session, agent)


async def _run_clarification(
    ws: WebSocket,
    session: SessionState,
    agent: AsyncCTOAgent,
) -> None:
    """Ask clarifying questions or transition to refinement."""
    # Check if we already have sufficient information
    is_sufficient = False
    if session.round >= session.max_rounds:
        is_sufficient = True
    else:
        try:
            is_sufficient = await agent.check_sufficiency(session)
        except Exception:
            is_sufficient = False  # network issue — keep asking

    if is_sufficient:
        # Transition to refinement
        session.phase = Phase.REFINING
        await ws.send_json(_msg("phase_change", phase=Phase.REFINING.value))
        await ws.send_json(_msg(
            "chat_message", role="assistant",
            content="I have enough to work with. Let me now refine and structure your requirements..."
        ))
        await _run_refinement(ws, session, agent)
        return

    # Stream clarifying questions
    response_text = ""
    await ws.send_json(_msg("chat_stream_start", role="assistant"))
    async for chunk in agent.stream_clarification(session):
        response_text += chunk
        await ws.send_json(_msg("chat_stream_token", token=chunk))

    await ws.send_json(_msg("chat_stream_end"))

    # Check if model self-declared SUFFICIENT
    if "SUFFICIENT" in response_text.upper() and len(response_text.strip()) < 30:
        session.phase = Phase.REFINING
        await ws.send_json(_msg("phase_change", phase=Phase.REFINING.value))
        await _run_refinement(ws, session, agent)
        return

    # Add model response to history and advance round
    session.history.append({"role": "assistant", "content": response_text})
    session.round += 1

    await ws.send_json(_msg(
        "phase_progress",
        phase=Phase.CLARIFYING.value,
        round=session.round - 1,
        max_rounds=session.max_rounds,
    ))


async def _run_initial_evaluation(
    ws: WebSocket,
    session: SessionState,
    agent: AsyncCTOAgent,
) -> None:
    """Score the raw conversation before refinement and stream to the evaluation pane."""
    await ws.send_json(_msg("artifact_start", artifact_id="evaluation", title="Requirements Score"))
    eval_text = ""
    try:
        async for chunk in agent.stream_initial_evaluation(session):
            eval_text += chunk
            await ws.send_json(_msg("artifact_token", artifact_id="evaluation", token=chunk))
    except Exception as exc:
        await ws.send_json(_msg("error", code="llm_error",
                                message=f"Evaluation failed: {exc}"))
    session.artifacts["evaluation"] = eval_text
    await ws.send_json(_msg("artifact_complete", artifact_id="evaluation", full_text=eval_text))


async def _run_refinement(
    ws: WebSocket,
    session: SessionState,
    agent: AsyncCTOAgent,
) -> None:
    """Score raw requirements, then stream refined requirements and offer artifact generation."""
    # Step 1: Evaluate the raw conversation first
    await _run_initial_evaluation(ws, session, agent)

    # Step 2: Refine requirements
    refined_text = ""
    await ws.send_json(_msg("refined_requirements_start"))
    async for chunk in agent.stream_refinement(session):
        refined_text += chunk
        await ws.send_json(_msg("refined_requirements_token", token=chunk))

    await ws.send_json(_msg("refined_requirements_end"))

    session.refined_requirements = refined_text
    session.project_name = _extract_project_name(refined_text)
    session.artifacts["refined_requirements"] = refined_text

    await ws.send_json(_msg(
        "chat_message", role="assistant",
        content=(
            "Requirements refined. Review them in the panel on the right.\n\n"
            "Click **Generate Artifacts** to produce: Requirements Score, Business Summary, "
            "Personas & Use Cases, Definition of Ready, Technical Design (with architecture diagram), "
            "SAFe Deliverables (Epic → Capability → Feature → Story), PI Planning Guide, "
            "RACI & Timeline, and Timeline Chart. All exportable as Markdown."
        ),
    ))


async def _handle_generate(
    ws: WebSocket,
    session: SessionState,
    agent: AsyncCTOAgent,
) -> None:
    """Generate one artifact per call; pause between each for user confirmation."""
    if not session.refined_requirements:
        await ws.send_json(_msg("error", code="no_requirements",
                                message="Refined requirements are empty. Please complete clarification first."))
        return

    # Transition to GENERATING on first call; resume if already there
    if session.phase in (Phase.REFINING, Phase.CLARIFYING, Phase.DONE):
        session.phase = Phase.GENERATING
        session.artifact_index = 0
        session.touch()
        await ws.send_json(_msg("phase_change", phase=Phase.GENERATING.value))
    elif session.phase != Phase.GENERATING:
        await ws.send_json(_msg("error", code="invalid_phase",
                                message="Cannot generate — requirements not yet refined."))
        return

    idx = session.artifact_index
    if idx >= len(ARTIFACT_SEQUENCE):
        await _finalize_generation(ws, session)
        return

    artifact_id, title, prompt_fn = ARTIFACT_SEQUENCE[idx]
    await ws.send_json(_msg("artifact_start", artifact_id=artifact_id, title=title))

    full_text = ""
    correction = session.artifact_correction
    session.artifact_correction = ""
    stopped = False
    try:
        async for chunk in agent.stream_artifact(session, prompt_fn, correction):
            full_text += chunk
            await ws.send_json(_msg("artifact_token", artifact_id=artifact_id, token=chunk))
    except asyncio.CancelledError:
        stopped = True
    except Exception as exc:
        await ws.send_json(_msg(
            "error", code="llm_error", message=f"Failed to generate {title}: {exc}"
        ))

    session.artifacts[artifact_id] = full_text

    if stopped:
        session.artifact_stopped = True
        await ws.send_json(_msg("generation_stopped", artifact_id=artifact_id))
        return  # leave artifact_index unchanged so user can regenerate
    await ws.send_json(_msg("artifact_complete", artifact_id=artifact_id, full_text=full_text))

    # Extract Mermaid immediately after technical_design completes
    if artifact_id == "technical_design":
        mermaid_code = _extract_mermaid(full_text)
        if mermaid_code:
            await ws.send_json(_msg("mermaid_ready", mermaid_code=mermaid_code))

    session.artifact_stopped = False
    session.artifact_index += 1

    if session.artifact_index < len(ARTIFACT_SEQUENCE):
        _, next_title, _ = ARTIFACT_SEQUENCE[session.artifact_index]
        await ws.send_json(_msg(
            "generation_paused",
            completed=idx + 1,
            total=len(ARTIFACT_SEQUENCE),
            next_title=next_title,
        ))
    else:
        await _finalize_generation(ws, session)


async def _finalize_generation(ws: WebSocket, session: SessionState) -> None:
    await ws.send_json(_msg(
        "markdown_ready",
        download_url=f"/api/export/markdown?session_id={session.session_id}",
    ))
    session.phase = Phase.DONE
    await ws.send_json(_msg("phase_change", phase=Phase.DONE.value))


def _extract_mermaid(text: str) -> str:
    """Extract Mermaid code from LLM output.
    The architecture_diagram artifact should be raw Mermaid, but models sometimes
    wrap it in fences. Strip them if present.
    """
    # Remove ```mermaid ... ``` fences if present
    fence_match = re.search(r"```(?:mermaid)?\s*([\s\S]+?)```", text)
    if fence_match:
        return fence_match.group(1).strip()
    # If it starts with a known Mermaid keyword, return as-is
    stripped = text.strip()
    if stripped.startswith(("flowchart", "graph ", "sequenceDiagram", "classDiagram", "erDiagram")):
        return stripped
    return stripped  # best effort
