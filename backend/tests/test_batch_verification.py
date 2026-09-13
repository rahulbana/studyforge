"""Batched verification: one LLM call grades all questions."""
from types import SimpleNamespace

from app.agents import verifier


class FakeLLM:
    def __init__(self, results):
        self._results = results
        self.calls = 0

    def complete_json(self, system, user):
        self.calls += 1
        return {"results": self._results}


def _chapter():
    return SimpleNamespace(subject="Bio", chapter_name="Cells", notes="notes", raw_text="")


def test_batch_returns_result_per_item_in_one_call():
    items = [
        {"id": 0, "qtype": "mcq", "question": "q0", "options": ["a", "b"], "answer": "a"},
        {"id": 1, "qtype": "short_answer", "question": "q1", "options": [], "answer": "x"},
    ]
    llm = FakeLLM(
        [
            {"id": 0, "status": "verified", "answer": "a", "options": ["a", "b"],
             "explanation": "", "note": "ok"},
            {"id": 1, "status": "corrected", "answer": "y", "options": [],
             "explanation": "fixed", "note": "was wrong"},
        ]
    )
    out = verifier.verify_questions_batch(_chapter(), items, llm=llm)
    assert llm.calls == 1  # single call for the whole batch
    assert out[0]["status"] == "verified"
    assert out[1]["status"] == "corrected"
    assert out[1]["answer"] == "y"


def test_batch_fills_missing_items_with_needs_review():
    items = [
        {"id": 0, "qtype": "mcq", "question": "q0", "options": [], "answer": "a"},
        {"id": 1, "qtype": "mcq", "question": "q1", "options": [], "answer": "b"},
    ]
    llm = FakeLLM([{"id": 0, "status": "verified", "answer": "a", "note": "ok"}])
    out = verifier.verify_questions_batch(_chapter(), items, llm=llm)
    assert out[0]["status"] == "verified"
    assert out[1]["status"] == "needs_review"  # model omitted it


def test_empty_batch_makes_no_call():
    llm = FakeLLM([])
    assert verifier.verify_questions_batch(_chapter(), [], llm=llm) == {}
    assert llm.calls == 0
