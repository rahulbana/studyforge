"""Question-related schemas."""
from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from ..models.enums import QuestionType

_MAX_PER_TYPE = 25


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    qtype: str
    question: str
    answer: str
    options: list[str] = []
    explanation: str = ""
    difficulty: str = "medium"
    source: str = "generated"
    verification_status: str = "unverified"
    verification_note: str = ""
    created_at: datetime | None = None

    @field_validator("options", mode="before")
    @classmethod
    def _parse_options(cls, v):
        if isinstance(v, str):
            if not v:
                return []
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []


class GenerateQuestionsRequest(BaseModel):
    # map of qtype -> count, e.g. {"mcq": 5, "true_false": 3}
    counts: dict[str, int]
    difficulty: str = "mixed"
    verify: bool = True

    @field_validator("counts")
    @classmethod
    def _validate_counts(cls, v: dict[str, int]) -> dict[str, int]:
        valid = {t.value for t in QuestionType}
        cleaned = {
            k: min(n, _MAX_PER_TYPE)
            for k, n in v.items()
            if k in valid and isinstance(n, int) and n > 0
        }
        if not cleaned:
            raise ValueError("Select at least one question type with a count > 0.")
        return cleaned


class GenerationJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    status: str
    result_count: int = 0
    error: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ManualQuestionIn(BaseModel):
    qtype: str
    question: str
    answer: str = ""
    options: list[str] = []
    explanation: str = ""
    difficulty: str = "medium"

    @field_validator("qtype")
    @classmethod
    def _validate_qtype(cls, v: str) -> str:
        if v not in {t.value for t in QuestionType}:
            raise ValueError(f"Unknown question type: {v}")
        return v
