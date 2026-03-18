"""Parse LLM-generated timeline data and render a matplotlib Gantt chart PNG."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, must be before pyplot import
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


@dataclass
class GanttPhase:
    name: str
    start: int    # week offset from 0
    duration: int # weeks
    color: str


_SENTINEL_RE = re.compile(
    r"<<<GANTT_START>>>(.*?)<<<GANTT_END>>>", re.DOTALL
)
_LINE_RE = re.compile(
    r"Phase:\s*(.+?)\s*\|\s*Start:\s*(\d+)\s*\|\s*Duration:\s*(\d+)\s*\|\s*Color:\s*(\w+)",
    re.IGNORECASE,
)

_FALLBACK_PHASES: list[GanttPhase] = [
    GanttPhase("Pre-PI: Foundation",        0,  4,  "steelblue"),
    GanttPhase("PI 1: Core Build",          4,  10, "darkorange"),
    GanttPhase("PI 2: Integration",         14, 10, "seagreen"),
    GanttPhase("PI 3: Launch & Stabilise",  24, 10, "mediumpurple"),
]


def parse_gantt_data(text: str) -> list[GanttPhase]:
    """Extract GanttPhase list from LLM sentinel-delimited output."""
    match = _SENTINEL_RE.search(text)
    if not match:
        return _FALLBACK_PHASES

    phases: list[GanttPhase] = []
    for line in match.group(1).strip().splitlines():
        m = _LINE_RE.match(line.strip())
        if m:
            phases.append(GanttPhase(
                name=m.group(1).strip(),
                start=int(m.group(2)),
                duration=int(m.group(3)),
                color=m.group(4).strip(),
            ))

    return phases if len(phases) >= 2 else _FALLBACK_PHASES


def generate_gantt_png(phases: list[GanttPhase], title: str = "Project Timeline") -> bytes:
    """Render a horizontal Gantt bar chart. Returns PNG bytes."""
    fig, ax = plt.subplots(figsize=(13, max(3, len(phases) * 0.9 + 1.2)))

    bg_color  = "#0d0d14"
    surf_color = "#16162a"
    text_color = "#e2e8f0"
    muted_color = "#64748b"

    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(surf_color)

    max_week = max(p.start + p.duration for p in phases)

    for i, phase in enumerate(phases):
        y = len(phases) - 1 - i   # top-to-bottom ordering
        ax.barh(
            y, phase.duration, left=phase.start,
            height=0.55, color=phase.color, alpha=0.88,
            edgecolor="white", linewidth=0.5,
        )
        label = f"  {phase.name}  (W{phase.start}–W{phase.start + phase.duration})"
        ax.text(
            phase.start + phase.duration / 2, y, phase.name,
            ha="center", va="center",
            color="white", fontsize=9, fontweight="bold",
        )

    # Week markers (every 5 weeks)
    tick_marks = list(range(0, max_week + 6, 5))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels([f"W{w}" for w in tick_marks], color=muted_color, fontsize=8)
    ax.set_xlim(0, max_week + 2)

    ax.set_yticks([])
    ax.set_xlabel("Week", color=muted_color, fontsize=10)
    ax.set_title(title, color=text_color, fontsize=13, fontweight="bold", pad=12)

    for spine in ax.spines.values():
        spine.set_edgecolor("#2a2a45")

    ax.tick_params(axis="x", colors=muted_color)
    ax.xaxis.label.set_color(muted_color)

    # Vertical grid lines at PI boundaries
    ax.xaxis.grid(True, color="#2a2a45", linewidth=0.6, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout(pad=1.5)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
