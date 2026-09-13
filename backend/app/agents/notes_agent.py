"""Notes agent — researches the topic online and writes exhaustive notes."""
from __future__ import annotations

from collections.abc import Callable

from . import prompts
from .llm import LLMClient, ResearchResult, get_llm


def generate_notes(
    class_name: str,
    subject: str,
    chapter_name: str,
    chapter_text: str,
    *,
    llm: LLMClient | None = None,
) -> ResearchResult:
    """Return the notes text plus the web sources used to write them."""
    llm = llm or get_llm()
    prompt = prompts.build_notes_prompt(class_name, subject, chapter_name, chapter_text)
    return llm.respond_with_search(
        prompt, system=prompts.NOTES_SYSTEM, max_output_tokens=12000
    )


def stream_notes(
    class_name: str,
    subject: str,
    chapter_name: str,
    chapter_text: str,
    *,
    on_delta: Callable[[str], None],
    llm: LLMClient | None = None,
) -> ResearchResult:
    """Stream notes generation, invoking on_delta(text) as tokens arrive.

    Raises AgentError on failure so the caller can fall back to generate_notes.
    """
    llm = llm or get_llm()
    prompt = prompts.build_notes_prompt(class_name, subject, chapter_name, chapter_text)
    return llm.stream_research(
        prompt, system=prompts.NOTES_SYSTEM, on_delta=on_delta, max_output_tokens=12000
    )
