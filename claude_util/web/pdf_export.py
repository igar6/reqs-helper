"""
PDF export — assembles all artifacts into a professional multi-section PDF using fpdf2.
Handles markdown-formatted LLM output with a lightweight inline parser.
"""

from __future__ import annotations

import base64
import io
import re
import tempfile
import os
from pathlib import Path

from fpdf import FPDF, XPos, YPos


# ---------------------------------------------------------------------------
# Colours & typography
# ---------------------------------------------------------------------------

_BG        = (13, 13, 20)      # #0d0d14  — page background
_SURFACE   = (22, 22, 42)      # #16162a  — card background
_ACCENT    = (124, 58, 237)    # #7c3aed  — section title stripe
_TEXT      = (226, 232, 240)   # #e2e8f0  — body text
_MUTED     = (100, 116, 139)   # #64748b  — captions
_WHITE     = (255, 255, 255)
_DARK_TEXT = (15, 15, 25)      # for light-background code blocks

_FONT_BODY  = "Helvetica"
_FONT_MONO  = "Courier"

ARTIFACT_TITLES: dict[str, str] = {
    "evaluation":          "Requirements Evaluation Scorecard",
    "business_summary":    "Business Summary",
    "dor":                 "Definition of Ready",
    "technical_design":    "Technical Design Summary",
    "safe_deliverables":   "SAFe Deliverables",
    "raci_timeline":       "RACI & Delivery Timeline",
    "architecture_diagram":"Architecture Diagram",
}


# ---------------------------------------------------------------------------
# Minimal markdown parser
# ---------------------------------------------------------------------------

def _parse_markdown(text: str) -> list[tuple[str, str]]:
    """
    Convert markdown text to a list of (type, content) tokens.
    Types: h1, h2, h3, bullet, table_row, code, blank, body
    """
    tokens: list[tuple[str, str]] = []
    in_code_block = False
    code_buf: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code_block:
                tokens.append(("code", "\n".join(code_buf)))
                code_buf = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_buf.append(line)
            continue

        if not line.strip():
            tokens.append(("blank", ""))
            continue

        if line.startswith("### "):
            tokens.append(("h3", line[4:].strip()))
        elif line.startswith("## "):
            tokens.append(("h2", line[3:].strip()))
        elif line.startswith("# "):
            tokens.append(("h1", line[2:].strip()))
        elif line.lstrip().startswith(("- ", "* ", "+ ")):
            content = re.sub(r"^[\s\-\*\+]+", "", line).strip()
            tokens.append(("bullet", content))
        elif re.match(r"^\d+\.\s", line.lstrip()):
            content = re.sub(r"^\s*\d+\.\s", "", line).strip()
            tokens.append(("numbered", content))
        elif line.startswith("|"):
            tokens.append(("table_row", line))
        else:
            tokens.append(("body", line))

    if code_buf:
        tokens.append(("code", "\n".join(code_buf)))

    return tokens


def _strip_inline(text: str) -> str:
    """Remove inline markdown formatting and non-latin-1 characters for fpdf2."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)  # links
    # Replace common Unicode punctuation with ASCII equivalents
    replacements = {
        "\u2014": "--", "\u2013": "-", "\u2022": "*",
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
        "\u00b7": "*", "\u2026": "...", "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # Drop any remaining non-latin-1 characters
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ---------------------------------------------------------------------------
# FPDF2 subclass
# ---------------------------------------------------------------------------

class _CTOPdf(FPDF):
    def __init__(self, project_name: str) -> None:
        super().__init__()
        self.project_name = project_name
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_fill_color(*_BG)
        self.rect(0, 0, self.w, 12, "F")
        self.set_font(_FONT_BODY, "I", 7)
        self.set_text_color(*_MUTED)
        self.set_y(4)
        self.cell(0, 4, f"CTO Requirements Analysis - {self.project_name}", align="L")
        self.set_y(4)
        self.cell(0, 4, f"Page {self.page_no()}", align="R")
        self.ln(8)

    def footer(self) -> None:
        pass

    def cover_page(self, subtitle: str = "SAFe Agile Requirements Breakdown") -> None:
        self.add_page()
        self.set_fill_color(*_BG)
        self.rect(0, 0, self.w, self.h, "F")

        # Accent stripe
        self.set_fill_color(*_ACCENT)
        self.rect(0, 60, self.w, 6, "F")

        self.set_y(72)
        self.set_font(_FONT_BODY, "B", 26)
        self.set_text_color(*_WHITE)
        self.multi_cell(0, 12, self.project_name, align="C")
        self.ln(4)

        self.set_font(_FONT_BODY, "", 13)
        self.set_text_color(*_MUTED)
        self.multi_cell(0, 7, subtitle, align="C")
        self.ln(8)

        self.set_font(_FONT_BODY, "I", 9)
        from datetime import date
        self.multi_cell(0, 5, f"Generated by CTO Requirements Agent  |  {date.today()}", align="C")

    def section_header(self, title: str) -> None:
        self.ln(4)
        self.set_fill_color(*_ACCENT)
        self.rect(self.get_x(), self.get_y(), self.epw, 7, "F")
        self.set_font(_FONT_BODY, "B", 11)
        self.set_text_color(*_WHITE)
        self.set_x(self.l_margin + 2)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)
        self.set_text_color(*_TEXT)

    def render_tokens(self, tokens: list[tuple[str, str]]) -> None:
        """Render parsed markdown tokens to the PDF."""
        bullet_indent = 6
        consecutive_blanks = 0

        for typ, content in tokens:
            content_clean = _strip_inline(content)

            if typ == "blank":
                consecutive_blanks += 1
                if consecutive_blanks <= 1:
                    self.ln(3)
                continue
            else:
                consecutive_blanks = 0

            if typ == "h1":
                self.section_header(content_clean)

            elif typ == "h2":
                self.ln(3)
                self.set_font(_FONT_BODY, "B", 10)
                self.set_text_color(180, 140, 255)
                self.multi_cell(0, 6, content_clean,
                                new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                self.set_text_color(*_TEXT)

            elif typ == "h3":
                self.ln(2)
                self.set_font(_FONT_BODY, "B", 9)
                self.set_text_color(*_WHITE)
                self.multi_cell(0, 5, content_clean,
                                new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                self.ln(1)
                self.set_text_color(*_TEXT)

            elif typ == "bullet":
                self.set_font(_FONT_BODY, "", 8.5)
                self.set_text_color(*_TEXT)
                self.set_x(self.l_margin + bullet_indent)
                self.multi_cell(
                    self.epw - bullet_indent, 5,
                    f"• {content_clean}",
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )

            elif typ == "numbered":
                self.set_font(_FONT_BODY, "", 8.5)
                self.set_text_color(*_TEXT)
                self.set_x(self.l_margin + bullet_indent)
                self.multi_cell(
                    self.epw - bullet_indent, 5,
                    f"  {content_clean}",
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                )

            elif typ == "table_row":
                # Skip separator rows (|---|---|)
                if re.match(r"^\|[\s\-\|:]+\|$", content.strip()):
                    continue
                cells = [c.strip() for c in content.strip().strip("|").split("|")]
                if not any(cells):
                    continue
                self.set_font(_FONT_BODY, "", 7.5)
                self.set_text_color(*_TEXT)
                # Simple table: equal-width columns
                col_w = self.epw / max(len(cells), 1)
                for j, cell in enumerate(cells):
                    cell_clean = _strip_inline(cell)
                    if j == 0:
                        self.set_font(_FONT_BODY, "B", 7.5)
                    else:
                        self.set_font(_FONT_BODY, "", 7.5)
                    self.cell(col_w, 5, cell_clean[:40], border=0)
                self.ln(5)

            elif typ == "code":
                self.ln(2)
                self.set_fill_color(20, 20, 35)
                self.set_font(_FONT_MONO, "", 7)
                self.set_text_color(180, 255, 180)
                for code_line in content.splitlines()[:30]:  # max 30 lines
                    self.set_x(self.l_margin + 3)
                    self.multi_cell(
                        self.epw - 6, 4, code_line or " ",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                        fill=True,
                    )
                self.ln(2)
                self.set_text_color(*_TEXT)

            elif typ == "body":
                self.set_font(_FONT_BODY, "", 8.5)
                self.set_text_color(*_TEXT)
                self.multi_cell(0, 5, content_clean,
                                new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_pdf(
    project_name: str,
    refined_requirements: str,
    artifacts: dict[str, str],
    gantt_png_b64: str | None = None,
) -> bytes:
    """Assemble all artifacts into a complete PDF. Returns bytes."""
    pdf = _CTOPdf(project_name=project_name)

    # Page background for all content pages
    pdf.set_fill_color(*_BG)

    # Cover
    pdf.cover_page()

    # Refined requirements
    if refined_requirements:
        pdf.add_page()
        pdf.set_fill_color(*_BG)
        pdf.rect(0, 0, pdf.w, pdf.h, "F")
        tokens = _parse_markdown(refined_requirements)
        pdf.render_tokens(tokens)

    # Each generated artifact
    for artifact_id, title in ARTIFACT_TITLES.items():
        text = artifacts.get(artifact_id, "")
        if not text.strip():
            continue

        pdf.add_page()
        pdf.set_fill_color(*_BG)
        pdf.rect(0, 0, pdf.w, pdf.h, "F")

        tokens = _parse_markdown(text)
        pdf.render_tokens(tokens)

        # If this is the architecture diagram, note that it renders in the web UI
        if artifact_id == "architecture_diagram":
            pdf.ln(4)
            pdf.set_font(_FONT_BODY, "I", 8)
            pdf.set_text_color(*_MUTED)
            pdf.multi_cell(
                0, 5,
                "Note: The architecture diagram above renders as an interactive visual "
                "in the web UI (mermaid.js). The code above is the source definition.",
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )

    # Gantt chart image
    if gantt_png_b64:
        pdf.add_page()
        pdf.set_fill_color(*_BG)
        pdf.rect(0, 0, pdf.w, pdf.h, "F")
        pdf.section_header("Project Timeline (Gantt Chart)")
        pdf.ln(4)

        png_bytes = base64.b64decode(gantt_png_b64)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_bytes)
            tmp_path = tmp.name
        try:
            pdf.image(tmp_path, x=pdf.l_margin, w=pdf.epw)
        finally:
            os.unlink(tmp_path)

    return bytes(pdf.output())
