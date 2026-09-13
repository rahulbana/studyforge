"""Question agent — generates questions (with answers) of a given type."""
from __future__ import annotations

from . import prompts
from .llm import LLMClient, get_llm


def _context(chapter) -> str:
    base = (chapter.notes or "").strip() or (chapter.raw_text or "").strip()
    return base[: prompts.QUESTION_MAX_CONTEXT_CHARS]


def generate_for_type(
    chapter,
    qtype: str,
    count: int,
    difficulty: str,
    *,
    llm: LLMClient | None = None,
) -> list[dict]:
    """Return a list of question dicts for one question type."""
    llm = llm or get_llm()
    prompt = prompts.build_questions_prompt(
        class_name=chapter.class_name,
        subject=chapter.subject,
        chapter_name=chapter.chapter_name,
        qtype=qtype,
        count=count,
        difficulty=difficulty,
        context=_context(chapter),
    )
    data = llm.complete_json(prompts.QUESTION_SYSTEM, prompt)
    items = data.get("questions", []) if isinstance(data, dict) else []

    result: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question", "")).strip()
        if not question:
            continue
        options = item.get("options") or []
        if not isinstance(options, list):
            options = []
        result.append(
            {
                "qtype": qtype,
                "question": question,
                "answer": str(item.get("answer", "")).strip(),
                "options": [str(o) for o in options],
                "explanation": str(item.get("explanation", "")).strip(),
                "difficulty": str(item.get("difficulty", difficulty) or difficulty).strip().lower(),
            }
        )
    return result[:count]
