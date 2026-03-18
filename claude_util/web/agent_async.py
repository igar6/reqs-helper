"""
Async CTO agent — supports two backends:
  1. Anthropic (claude-sonnet-4-6, etc.)  — set ANTHROPIC_API_KEY
  2. OpenRouter free models               — set OPENROUTER_API_KEY

Priority: Anthropic > OpenRouter. First key found wins.
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from ..prompts import (
    SYSTEM_PROMPT,
    CLARIFICATION_INSTRUCTION,
    sufficiency_check_prompt,
    REQUIREMENTS_REFINEMENT_PROMPT,
    INITIAL_EVALUATION_PROMPT,
    PERSONAS_USECASES_PROMPT,
    PI_PLANNING_PROMPT,
    BUSINESS_SUMMARY_PROMPT,
    TECHNICAL_DESIGN_PROMPT,
    RACI_TIMELINE_PROMPT,
    DIAGRAM_SUFFICIENCY_CHECK,
    ARCHITECTURE_DIAGRAM_PROMPT,
    safe_deliverables_prompt,
    dor_prompt,
    role_scope_preamble,
    clarification_focus,
)
from .session import SessionState

# ---------------------------------------------------------------------------
# Model defaults
# ---------------------------------------------------------------------------

ANTHROPIC_DEFAULT_MODEL  = "claude-sonnet-4-6"
OPENROUTER_DEFAULT_MODEL = "arcee-ai/trinity-large-preview:free"

FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "deepseek/deepseek-chat:free",
    "mistralai/mistral-7b-instruct:free",
]

# ---------------------------------------------------------------------------
# Artifact sequence (same for both backends)
# ---------------------------------------------------------------------------

def _history_as_text(history: list) -> str:
    """Flatten session history to plain text, handling multimodal entries."""
    lines = []
    for m in history:
        content = m["content"]
        if isinstance(content, str):
            lines.append(f"{m['role'].upper()}: {content}")
        elif isinstance(content, list):
            texts = [b.get("text", "") for b in content if b.get("type") == "text"]
            combined = " ".join(t for t in texts if t)
            suffix = " [+ attached image]" if any(b.get("type") == "image" for b in content) else ""
            lines.append(f"{m['role'].upper()}: {combined}{suffix}")
    return "\n".join(lines)


def _personas_usecases(s: SessionState) -> str:
    return PERSONAS_USECASES_PROMPT.format(refined_requirements=s.refined_requirements)

def _pi_planning(s: SessionState) -> str:
    return PI_PLANNING_PROMPT.format(refined_requirements=s.refined_requirements)

def _business_summary(s: SessionState) -> str:
    return BUSINESS_SUMMARY_PROMPT.format(refined_requirements=s.refined_requirements)

def _dor(s: SessionState) -> str:
    return dor_prompt(s.scope, s.refined_requirements)

def _technical_design(s: SessionState) -> str:
    return TECHNICAL_DESIGN_PROMPT.format(refined_requirements=s.refined_requirements)

def _safe_deliverables(s: SessionState) -> str:
    return safe_deliverables_prompt(s.scope, s.refined_requirements)

def _raci_timeline(s: SessionState) -> str:
    return RACI_TIMELINE_PROMPT.format(refined_requirements=s.refined_requirements)

ARTIFACT_SEQUENCE: list[tuple[str, str, object]] = [
    ("business_summary",  "Business Summary",     _business_summary),
    ("personas_usecases", "Personas & Use Cases", _personas_usecases),
    ("dor",               "Definition of Ready",  _dor),
    ("technical_design",  "Technical Design",     _technical_design),
    ("safe_deliverables", "SAFe Deliverables",    _safe_deliverables),
    ("pi_planning",       "PI Planning",          _pi_planning),
    ("raci_timeline",     "RACI & Timeline",      _raci_timeline),
]


# ---------------------------------------------------------------------------
# Backend: Anthropic
# ---------------------------------------------------------------------------

class _AnthropicBackend:
    def __init__(self, api_key: str, model: str) -> None:
        from anthropic import AsyncAnthropic
        self.model = model
        self._client = AsyncAnthropic(api_key=api_key)

    async def stream(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as s:
            async for text in s.text_stream:
                yield text

    async def complete(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 10,
    ) -> str:
        resp = await self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return resp.content[0].text if resp.content else ""


# ---------------------------------------------------------------------------
# Backend: OpenRouter (OpenAI-compatible)
# ---------------------------------------------------------------------------

def _to_openai_content(messages: list[dict]) -> list[dict]:
    """Convert Anthropic-format message list to OpenAI format (handles multimodal)."""
    result = []
    for msg in messages:
        content = msg["content"]
        if isinstance(content, str):
            result.append(msg)
        else:
            openai_content = []
            for block in content:
                if block.get("type") == "text":
                    openai_content.append({"type": "text", "text": block["text"]})
                elif block.get("type") == "image":
                    src = block.get("source", {})
                    if src.get("type") == "base64":
                        url = f"data:{src['media_type']};base64,{src['data']}"
                        openai_content.append({"type": "image_url", "image_url": {"url": url}})
            result.append({"role": msg["role"], "content": openai_content})
    return result


class _OpenRouterBackend:
    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI
        self.model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/cto-agent",
                "X-Title": "CTO Requirements Agent",
            },
        )

    async def stream(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        full_messages = [{"role": "system", "content": system}, *_to_openai_content(messages)]
        s = await self._client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=0.4,
            stream=True,
        )
        async for chunk in s:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def complete(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 10,
    ) -> str:
        full_messages = [{"role": "system", "content": system}, *_to_openai_content(messages)]
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=0.0,
            stream=False,
        )
        return resp.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Agent (backend-agnostic)
# ---------------------------------------------------------------------------

class AsyncCTOAgent:
    def __init__(self, backend: _AnthropicBackend | _OpenRouterBackend) -> None:
        self._backend = backend
        self.model = backend.model
        # Human-readable provider name for the UI
        self.provider = (
            "Anthropic" if isinstance(backend, _AnthropicBackend) else "OpenRouter"
        )

    # ------------------------------------------------------------------
    # Clarification phase
    # ------------------------------------------------------------------

    def _system(self, session: SessionState, extra: str = "") -> str:
        """Build the system prompt, injecting user role and any extra instruction."""
        role_line = (
            f"\n\nThe person you are collaborating with is a **{session.user_role}**. "
            "Tailor your language, level of detail, and emphasis to their perspective."
            if session.user_role else ""
        )
        return SYSTEM_PROMPT + role_line + ("\n\n" + extra if extra else "")

    async def stream_clarification(self, session: SessionState) -> AsyncIterator[str]:
        focus = clarification_focus(session.user_role, session.scope, session.round)
        instruction = CLARIFICATION_INSTRUCTION.format(
            round=session.round,
            max_rounds=session.max_rounds,
            focus=focus,
        )
        system = self._system(session, instruction)
        async for chunk in self._backend.stream(system, session.history):
            yield chunk

    async def check_sufficiency(self, session: SessionState) -> bool:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in session.history
        )
        prompt = sufficiency_check_prompt(session.user_role)
        result = await self._backend.complete(
            system=prompt,
            messages=[{"role": "user", "content": f"Conversation:\n{history_text}"}],
            max_tokens=5,
        )
        return "YES" in result.upper()

    # ------------------------------------------------------------------
    # Initial evaluation (scores raw conversation before refinement)
    # ------------------------------------------------------------------

    async def stream_initial_evaluation(self, session: SessionState) -> AsyncIterator[str]:
        history_text = _history_as_text(session.history)
        user_msg = INITIAL_EVALUATION_PROMPT.format(conversation=history_text)
        async for chunk in self._backend.stream(
            system=self._system(session),
            messages=[{"role": "user", "content": user_msg}],
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Refinement phase
    # ------------------------------------------------------------------

    async def stream_refinement(self, session: SessionState) -> AsyncIterator[str]:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in session.history
        )
        user_msg = (
            f"Conversation history:\n{history_text}\n\n"
            + REQUIREMENTS_REFINEMENT_PROMPT
        )
        async for chunk in self._backend.stream(
            system=self._system(session),
            messages=[{"role": "user", "content": user_msg}],
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Artifact generation phase
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Diagram agent (dedicated, minimal context — diagram only)
    # ------------------------------------------------------------------

    _DIAGRAM_SYSTEM = (
        "You are a software architecture diagram specialist. "
        "Your only job is to output valid Mermaid flowchart code. "
        "Never include explanations, prose, or markdown fences."
    )

    async def check_diagram_sufficiency(self, technical_design: str) -> bool:
        result = await self._backend.complete(
            system=DIAGRAM_SUFFICIENCY_CHECK,
            messages=[{"role": "user", "content": technical_design}],
            max_tokens=5,
        )
        return "YES" in result.upper()

    async def stream_diagram(self, technical_design: str) -> AsyncIterator[str]:
        prompt = ARCHITECTURE_DIAGRAM_PROMPT.format(technical_design=technical_design)
        async for chunk in self._backend.stream(
            system=self._DIAGRAM_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        ):
            yield chunk

    async def stream_artifact(
        self, session: SessionState, prompt_fn: object, correction: str = ""
    ) -> AsyncIterator[str]:
        preamble = role_scope_preamble(session.user_role, session.scope)
        user_prompt = preamble + prompt_fn(session)  # type: ignore[operator]
        if correction:
            user_prompt += (
                "\n\n---\n"
                f"**User correction:** {correction}\n"
                "Regenerate the artifact above applying this correction throughout. "
                "Keep the same structure."
            )
        async for chunk in self._backend.stream(
            system=self._system(session),
            messages=[{"role": "user", "content": user_prompt}],
        ):
            yield chunk


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_agent(
    api_key: str | None = None,
    model: str | None = None,
) -> AsyncCTOAgent:
    """
    Create an AsyncCTOAgent.

    Backend selection (priority order):
      1. ANTHROPIC_API_KEY  → Anthropic (claude-sonnet-4-6 by default)
      2. OPENROUTER_API_KEY → OpenRouter free models

    Model override via AGENT_MODEL env var or `model` argument.
    """
    anthropic_key = api_key if api_key and "sk-ant" in api_key else os.getenv("ANTHROPIC_API_KEY")
    openrouter_key = api_key if api_key and "sk-or" in api_key else os.getenv("OPENROUTER_API_KEY")

    if anthropic_key:
        selected_model = model or os.getenv("AGENT_MODEL", ANTHROPIC_DEFAULT_MODEL)
        backend: _AnthropicBackend | _OpenRouterBackend = _AnthropicBackend(
            api_key=anthropic_key, model=selected_model
        )
    elif openrouter_key:
        selected_model = model or os.getenv("AGENT_MODEL", OPENROUTER_DEFAULT_MODEL)
        backend = _OpenRouterBackend(api_key=openrouter_key, model=selected_model)
    else:
        raise EnvironmentError(
            "No API key found.\n"
            "  Option A (Claude): set ANTHROPIC_API_KEY in your .env file\n"
            "  Option B (Free):   set OPENROUTER_API_KEY in your .env file\n"
            "  Get a free OpenRouter key at https://openrouter.ai/keys"
        )

    return AsyncCTOAgent(backend)
