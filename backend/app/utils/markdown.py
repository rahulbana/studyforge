"""Markdown helpers shared by the export layer."""
from __future__ import annotations

import re

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

_MERMAID_RE = re.compile(r"```mermaid[\s\S]*?```", re.IGNORECASE)
_SVG_RE = re.compile(r"<svg[\s\S]*?</svg>", re.IGNORECASE)
_FENCE_RE = re.compile(r"```[a-zA-Z0-9]*\n([\s\S]*?)```")
_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_DIAGRAM_TOKEN_RE = re.compile(r"\[\[DIAGRAM:[\s\S]*?\]\]", re.IGNORECASE)

DIAGRAM_PLACEHOLDER = "[Diagram — view in the app]"

# "Smart" typography that Mermaid's ASCII grammar rejects (en/em dashes break
# arrows, curly quotes break labels, non-breaking spaces break tokens).
_MERMAID_DASHES_RE = re.compile("[‐-―−]")
_MERMAID_SQUOTES_RE = re.compile("[‘’‛]")
_MERMAID_DQUOTES_RE = re.compile("[“”‟]")
_MERMAID_SPACES_RE = re.compile("[   ]")


def _to_ascii_typography(text: str) -> str:
    text = _MERMAID_DASHES_RE.sub("-", text)
    text = _MERMAID_SQUOTES_RE.sub("'", text)
    text = _MERMAID_DQUOTES_RE.sub('"', text)
    text = _MERMAID_SPACES_RE.sub(" ", text)
    return text


def normalize_mermaid_typography(md: str) -> str:
    """Repair smart typography *inside* ```mermaid fences so diagrams parse.

    Only the fenced Mermaid source is touched — prose keeps its en dashes and
    curly quotes. This fixes the notes at the source (DB + exports), not just at
    render time.
    """
    if not md:
        return md
    return _MERMAID_RE.sub(lambda m: _to_ascii_typography(m.group(0)), md)


def strip_md(text: str) -> str:
    """Remove **bold** markers, returning plain text."""
    return BOLD_RE.sub(r"\1", text)


def clean_markdown_for_export(md: str) -> str:
    """Replace visuals the PDF/DOCX renderers can't draw with a placeholder.

    Mermaid fences and inline SVG become a short note; other fenced code blocks
    keep their inner text; leftover diagram tokens and stray HTML tags are dropped.
    """
    md = _MERMAID_RE.sub(f"\n{DIAGRAM_PLACEHOLDER}\n", md)
    md = _SVG_RE.sub(f"\n{DIAGRAM_PLACEHOLDER}\n", md)
    md = _DIAGRAM_TOKEN_RE.sub(f"\n{DIAGRAM_PLACEHOLDER}\n", md)
    md = _FENCE_RE.sub(lambda m: "\n" + m.group(1) + "\n", md)
    md = _HTML_TAG_RE.sub("", md)
    return md
