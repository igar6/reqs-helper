"""
CTO Requirements Agent
======================
Takes vague requirements and produces a SAFe Agile work breakdown
across all delivery roles: PM, RTE, PO, Developers, Architect, TPM.

Uses OpenRouter free models via the OpenAI-compatible API.
"""

from __future__ import annotations

import os
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Iterator

from openai import OpenAI

from .prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT, CLARIFICATION_PROMPT

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Free models available on OpenRouter (as of 2025).
# Override with OPENROUTER_MODEL env var.
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "deepseek/deepseek-chat:free",
    "mistralai/mistral-7b-instruct:free",
]
DEFAULT_MODEL = FREE_MODELS[0]

# Minimum token threshold below which we consider requirements "too vague"
# and switch to clarification mode instead of full analysis.
VAGUENESS_THRESHOLD = 20  # words


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AgentConfig:
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.4
    max_tokens: int = 4096
    stream: bool = True
    site_url: str = "https://github.com/cto-agent"
    site_name: str = "CTO Requirements Agent"


@dataclass
class AnalysisResult:
    requirements: str
    mode: str  # "analysis" | "clarification"
    content: str
    model_used: str
    tokens_used: int = 0
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core agent
# ---------------------------------------------------------------------------

class CTOAgent:
    """
    Two-phase SAFe Requirements Agent.

    Phase 1 — Assess: Determine if requirements are actionable or need
               clarification first.
    Phase 2 — Generate: Produce full SAFe breakdown or a targeted
               clarification guide, depending on Phase 1 verdict.
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            default_headers={
                "HTTP-Referer": config.site_url,
                "X-Title": config.site_name,
            },
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, requirements: str) -> AnalysisResult:
        """Run the full two-phase analysis."""
        requirements = requirements.strip()
        if not requirements:
            raise ValueError("Requirements cannot be empty.")

        word_count = len(requirements.split())
        warnings: list[str] = []

        # Phase 1: decide mode
        if word_count < VAGUENESS_THRESHOLD:
            mode = "clarification"
            warnings.append(
                f"Requirements are very short ({word_count} words). "
                "Switching to clarification mode."
            )
        else:
            mode = self._assess_mode(requirements)

        # Phase 2: generate output
        if mode == "clarification":
            prompt = CLARIFICATION_PROMPT.format(requirements=requirements)
        else:
            prompt = ANALYSIS_PROMPT.format(requirements=requirements)

        content, tokens = self._call(prompt)

        return AnalysisResult(
            requirements=requirements,
            mode=mode,
            content=content,
            model_used=self.config.model,
            tokens_used=tokens,
            warnings=warnings,
        )

    def analyze_stream(self, requirements: str) -> Iterator[str]:
        """Stream the analysis token-by-token. Yields text chunks."""
        requirements = requirements.strip()
        if not requirements:
            raise ValueError("Requirements cannot be empty.")

        word_count = len(requirements.split())

        if word_count < VAGUENESS_THRESHOLD:
            yield (
                f"\n[CTO Agent] Requirements are short ({word_count} words) — "
                "running clarification mode.\n\n"
            )
            prompt = CLARIFICATION_PROMPT.format(requirements=requirements)
        else:
            mode = self._assess_mode(requirements)
            if mode == "clarification":
                yield "\n[CTO Agent] Gaps detected — switching to clarification mode.\n\n"
                prompt = CLARIFICATION_PROMPT.format(requirements=requirements)
            else:
                yield "\n[CTO Agent] Requirements assessed — generating SAFe breakdown.\n\n"
                prompt = ANALYSIS_PROMPT.format(requirements=requirements)

        yield from self._call_stream(prompt)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _assess_mode(self, requirements: str) -> str:
        """
        Ask the model if there's enough to do a full SAFe breakdown.
        Returns 'analysis' or 'clarification'.
        """
        assessment_prompt = (
            "You are a senior technical advisor. Given the following requirements, "
            "answer with ONLY one word: 'analysis' if there is enough substance to produce "
            "a SAFe Agile breakdown, or 'clarification' if critical information is missing.\n\n"
            f"Requirements:\n{requirements}"
        )

        content, _ = self._call(assessment_prompt, max_tokens=10, temperature=0.0)
        verdict = content.strip().lower()
        return "clarification" if "clarification" in verdict else "analysis"

    def _call(
        self,
        user_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> tuple[str, int]:
        """Make a non-streaming API call. Returns (content, total_tokens)."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=temperature if temperature is not None else self.config.temperature,
            stream=False,
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return content, tokens

    def _call_stream(self, user_prompt: str) -> Iterator[str]:
        """Stream an API call, yielding text chunks."""
        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_agent(
    api_key: str | None = None,
    model: str | None = None,
) -> CTOAgent:
    """
    Create a CTOAgent from env vars or explicit arguments.

    Env vars:
      OPENROUTER_API_KEY  — required
      OPENROUTER_MODEL    — optional, defaults to llama-3.3-70b-instruct:free
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise EnvironmentError(
            "No API key found. Set OPENROUTER_API_KEY or pass api_key=... "
            "Get a free key at https://openrouter.ai/keys"
        )

    selected_model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    config = AgentConfig(api_key=key, model=selected_model)
    return CTOAgent(config)
