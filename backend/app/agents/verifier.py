"""Verifier agent — checks Q/A for correctness and auto-fixes it.

Supports single-question verification and a batched mode that checks a whole set
in one LLM call (far fewer API calls; controlled by settings.batch_verification).
"""
from __future__ import annotations

import json

from ..models.enums import VerificationStatus
from . import prompts
from .llm import LLMClient, get_llm

_VALID_STATUSES = {s.value for s in VerificationStatus}


def _context(chapter) -> str:
    return ((chapter.notes or "").strip() or (chapter.raw_text or "").strip())[
        : prompts.VERIFY_MAX_CONTEXT_CHARS
    ]


def _normalize_result(data: dict, q: dict) -> dict:
    """Coerce a raw model grading dict into our stable result shape."""
    status = str(data.get("status", "")).strip().lower()
    if status not in _VALID_STATUSES:
        status = VerificationStatus.NEEDS_REVIEW.value
    options = data.get("options")
    if not isinstance(options, list) or not options:
        options = q.get("options", [])
    return {
        "status": status,
        "answer": str(data.get("answer", q.get("answer", ""))).strip(),
        "options": [str(o) for o in options],
        "explanation": str(data.get("explanation", q.get("explanation", ""))).strip(),
        "note": str(data.get("note", "")).strip(),
    }


def _fallback(q: dict, note: str) -> dict:
    return {
        "status": VerificationStatus.NEEDS_REVIEW.value,
        "answer": q.get("answer", ""),
        "options": q.get("options", []),
        "explanation": q.get("explanation", ""),
        "note": note,
    }


def verify_question(chapter, q: dict, *, llm: LLMClient | None = None) -> dict:
    """Verify a single question. Returns {status, answer, options, explanation, note}."""
    llm = llm or get_llm()
    prompt = prompts.build_verify_prompt(
        subject=chapter.subject, chapter_name=chapter.chapter_name, q=q, context=_context(chapter)
    )
    data = llm.complete_json(prompts.VERIFY_SYSTEM, prompt)
    if not isinstance(data, dict):
        return _fallback(q, "Verifier returned an unexpected response.")
    return _normalize_result(data, q)


def verify_questions_batch(
    chapter, items: list[dict], *, llm: LLMClient | None = None
) -> dict:
    """Verify many questions in one call.

    ``items`` must each carry an ``id`` plus qtype/question/options/answer.
    Returns {id: {status, answer, options, explanation, note}}.
    """
    if not items:
        return {}
    llm = llm or get_llm()
    payload = [
        {
            "id": it["id"],
            "qtype": it.get("qtype"),
            "question": it.get("question"),
            "options": it.get("options", []),
            "answer": it.get("answer", ""),
        }
        for it in items
    ]
    prompt = prompts.build_verify_batch_prompt(
        subject=chapter.subject,
        chapter_name=chapter.chapter_name,
        items=json.dumps(payload, ensure_ascii=False),
        context=_context(chapter),
    )
    data = llm.complete_json(prompts.VERIFY_SYSTEM, prompt)
    by_id = {it["id"]: it for it in items}
    results: dict = {}
    for r in (data.get("results", []) if isinstance(data, dict) else []):
        if not isinstance(r, dict) or "id" not in r:
            continue
        rid = r["id"]
        if rid in by_id:
            results[rid] = _normalize_result(r, by_id[rid])
    # Any item the model skipped falls back to needs-review.
    for it in items:
        results.setdefault(it["id"], _fallback(it, "Not returned by the verifier."))
    return results
