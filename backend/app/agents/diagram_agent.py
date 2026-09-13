"""Diagram agent — turns [[DIAGRAM: ...]] placeholders into detailed inline SVG.

The notes agent focuses on content and drops rich placeholders describing what a
figure should show. This focused pass renders a high-detail, self-contained SVG
for each placeholder, so diagrams look far better than when the notes call has to
draw them as an afterthought.
"""
from __future__ import annotations

import re

from ..core.exceptions import AgentError
from ..core.logging import get_logger
from . import prompts
from .llm import LLMClient, get_llm

logger = get_logger(__name__)

# Matches [[DIAGRAM: a full description of what to draw]]
PLACEHOLDER_RE = re.compile(r"\[\[DIAGRAM:(.+?)\]\]", re.DOTALL)
# Extracts the <svg>...</svg> from a possibly fenced/explained model reply.
_SVG_RE = re.compile(r"<svg[\s\S]*?</svg>", re.IGNORECASE)


def _render_one(
    description: str, class_name: str, subject: str, chapter_name: str, llm: LLMClient
) -> str:
    prompt = prompts.build_diagram_prompt(
        description=description,
        class_name=class_name,
        subject=subject,
        chapter_name=chapter_name,
    )
    raw = llm.complete_text(prompts.DIAGRAM_SYSTEM, prompt, max_tokens=4000, temperature=0.5)
    match = _SVG_RE.search(raw)
    if not match:
        raise AgentError("No SVG returned")
    svg = match.group(0)
    # Ensure it scales nicely even if the model forgot the sizing style.
    if "max-width" not in svg[:400]:
        svg = svg.replace("<svg", '<svg width="100%" style="max-width:640px;height:auto"', 1)
    return svg


def enrich_with_diagrams(
    notes: str,
    class_name: str,
    subject: str,
    chapter_name: str,
    *,
    max_diagrams: int = 8,
    llm: LLMClient | None = None,
) -> str:
    """Replace [[DIAGRAM: ...]] placeholders with detailed SVGs.

    Placeholders beyond ``max_diagrams`` (or ones that fail to render) are removed
    so no raw tokens leak to the reader.
    """
    llm = llm or get_llm()
    matches = list(PLACEHOLDER_RE.finditer(notes))
    if not matches:
        return notes

    out: list[str] = []
    last = 0
    rendered = 0
    for m in matches:
        out.append(notes[last:m.start()])
        last = m.end()
        description = m.group(1).strip()
        if not description or rendered >= max_diagrams:
            continue
        try:
            svg = _render_one(description, class_name, subject, chapter_name, llm)
            out.append(f"\n\n{svg}\n\n")
            rendered += 1
        except Exception as exc:  # noqa: BLE001  (never let one figure break notes)
            logger.warning("Diagram rendering failed, dropping placeholder: %s", exc)
    out.append(notes[last:])
    return "".join(out)
