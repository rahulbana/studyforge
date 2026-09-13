"""Health and metadata endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ...core.config import get_settings
from ...models.enums import QUESTION_TYPE_LABELS
from ...schemas import QuestionTypeInfo

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "ok": True,
        "model": settings.openai_model,
        "web_search": settings.enable_web_search,
        "diagrams": settings.enable_diagrams,
        "openai_configured": settings.has_openai_key,
    }


@router.get("/question-types", response_model=list[QuestionTypeInfo])
def question_types():
    return [QuestionTypeInfo(key=t.value, label=label) for t, label in QUESTION_TYPE_LABELS.items()]
