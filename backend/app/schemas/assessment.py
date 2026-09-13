"""Assessment (test) schemas."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from ..models.enums import QuestionType

_MAX_PER_TYPE = 25


class AssessmentCreate(BaseModel):
    source: Literal["chapter", "topic"] = "topic"
    chapter_id: int | None = None
    class_name: str = ""
    subject: str = ""
    topic: str = ""
    counts: dict[str, int]
    difficulty: str = "mixed"

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


class AnswerIn(BaseModel):
    question_id: int
    answer: str = ""


class SubmitAnswersRequest(BaseModel):
    answers: list[AnswerIn]


class AssessmentQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_index: int
    qtype: str
    question: str
    options: list[str] = []
    concept: str
    max_points: int
    student_answer: str = ""
    # Revealed only once the assessment is graded.
    correct_answer: str | None = None
    explanation: str | None = None
    awarded_points: float | None = None
    is_correct: bool | None = None
    feedback: str | None = None

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


class ConceptScore(BaseModel):
    concept: str
    points_awarded: float
    points_max: float
    percentage: float


class AssessmentFeedback(BaseModel):
    summary: str = ""
    recommendations: list[str] = []
    concept_breakdown: list[ConceptScore] = []
    weak_concepts: list[str] = []
    strong_concepts: list[str] = []


class AssessmentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_name: str
    subject: str
    topic: str
    chapter_id: int | None = None
    status: str
    error: str = ""
    score: float | None = None
    points_awarded: float = 0.0
    points_max: int = 0
    cost_usd: float = 0.0
    feedback: AssessmentFeedback | None = None
    created_at: datetime | None = None
    submitted_at: datetime | None = None
    graded_at: datetime | None = None
    questions: list[AssessmentQuestionOut] = []

    @field_validator("feedback", mode="before")
    @classmethod
    def _parse_feedback(cls, v):
        if v is None or isinstance(v, dict | AssessmentFeedback):
            return v or None
        if isinstance(v, str):
            if not v:
                return None
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return None


class AssessmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_name: str
    subject: str
    topic: str
    status: str
    score: float | None = None
    created_at: datetime | None = None
    question_count: int = 0


class AttemptPoint(BaseModel):
    id: int
    subject: str
    topic: str
    score: float
    created_at: datetime | None = None


class ConceptStat(BaseModel):
    concept: str
    attempts: int
    avg_percentage: float
    weak_count: int  # times this concept scored below the weak threshold


class ProgressResponse(BaseModel):
    total_attempts: int = 0
    average_score: float | None = None
    best_score: float | None = None
    attempts: list[AttemptPoint] = []   # chronological (oldest first)
    concepts: list[ConceptStat] = []    # worst average first
