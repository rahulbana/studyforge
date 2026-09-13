"""Assessment agent — generate a test, grade subjective answers, write feedback."""
from __future__ import annotations

import json

from . import prompts
from .llm import LLMClient, get_llm


def generate_test(
    *,
    class_name: str,
    subject: str,
    topic: str,
    counts: dict[str, int],
    difficulty: str,
    context: str = "",
    llm: LLMClient | None = None,
) -> list[dict]:
    """Generate test questions (with correct answers + concept tags)."""
    llm = llm or get_llm()
    trimmed = context[: prompts.ASSESSMENT_MAX_CONTEXT_CHARS]
    questions: list[dict] = []
    for qtype, count in counts.items():
        prompt = prompts.build_assessment_prompt(
            class_name=class_name,
            subject=subject,
            topic=topic,
            qtype=qtype,
            count=count,
            difficulty=difficulty,
            context=trimmed,
        )
        data = llm.complete_json(prompts.ASSESSMENT_GEN_SYSTEM, prompt)
        items = data.get("questions", []) if isinstance(data, dict) else []
        for item in items[:count]:
            if not isinstance(item, dict):
                continue
            text = str(item.get("question", "")).strip()
            if not text:
                continue
            options = item.get("options") or []
            if not isinstance(options, list):
                options = []
            diff = str(item.get("difficulty", difficulty) or difficulty).strip().lower()
            questions.append(
                {
                    "qtype": qtype,
                    "question": text,
                    "correct_answer": str(item.get("answer", "")).strip(),
                    "options": [str(o) for o in options],
                    "explanation": str(item.get("explanation", "")).strip(),
                    "concept": (str(item.get("concept", "")).strip() or "General")[:160],
                    "difficulty": diff,
                }
            )
    return questions


def grade_answers(
    *, subject: str, topic: str, items: list[dict], llm: LLMClient | None = None
) -> dict[int, dict]:
    """Grade subjective answers. ``items`` carry id/question/correct_answer/max_points/
    student_answer. Returns {question_id: {awarded, is_correct, feedback}}."""
    if not items:
        return {}
    llm = llm or get_llm()
    prompt = prompts.build_grading_prompt(
        subject=subject, topic=topic, items=json.dumps(items, ensure_ascii=False)
    )
    data = llm.complete_json(prompts.GRADING_SYSTEM, prompt)
    result: dict[int, dict] = {}
    for g in (data.get("gradings", []) if isinstance(data, dict) else []):
        if not isinstance(g, dict) or "id" not in g:
            continue
        try:
            qid = int(g["id"])
        except (TypeError, ValueError):
            continue
        result[qid] = {
            "awarded": g.get("awarded", 0),
            "is_correct": bool(g.get("is_correct", False)),
            "feedback": str(g.get("feedback", "")).strip(),
        }
    return result


def overall_feedback(
    *, subject: str, topic: str, score_pct: float, breakdown: list[dict],
    llm: LLMClient | None = None,
) -> dict:
    """Return {summary, recommendations[]} for the whole attempt."""
    llm = llm or get_llm()
    prompt = prompts.build_feedback_prompt(
        subject=subject,
        topic=topic,
        score_pct=score_pct,
        breakdown=json.dumps(breakdown, ensure_ascii=False),
    )
    data = llm.complete_json(prompts.FEEDBACK_SYSTEM, prompt)
    if not isinstance(data, dict):
        return {"summary": "", "recommendations": []}
    recs = data.get("recommendations") or []
    if not isinstance(recs, list):
        recs = []
    return {
        "summary": str(data.get("summary", "")).strip(),
        "recommendations": [str(r).strip() for r in recs if str(r).strip()],
    }
