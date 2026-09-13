"""Chapter-related schemas."""
from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from .question import QuestionOut


class SourceOut(BaseModel):
    url: str
    title: str = ""


class ChapterCreateMeta(BaseModel):
    class_name: str
    subject: str
    chapter_name: str


class ChapterSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_name: str
    subject: str
    chapter_name: str
    source_filename: str
    notes_status: str
    cost_usd: float = 0.0
    created_at: datetime | None = None
    question_count: int = 0


class ChapterDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_name: str
    subject: str
    chapter_name: str
    source_filename: str
    notes: str
    notes_status: str
    notes_error: str = ""
    sources: list[SourceOut] = []
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    created_at: datetime | None = None
    questions: list[QuestionOut] = []

    @field_validator("sources", mode="before")
    @classmethod
    def _parse_sources(cls, v):
        if isinstance(v, str):
            if not v:
                return []
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []
