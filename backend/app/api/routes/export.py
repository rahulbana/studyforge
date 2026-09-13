"""Export endpoint: notes and/or question bank as PDF or DOCX."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ...core.exceptions import ValidationError
from ...services import chapter_service, export_service
from ...services.export_service import DOCX_MIME
from ..deps import get_db

router = APIRouter(prefix="/api", tags=["export"])


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_") or "chapter"


@router.get("/chapters/{chapter_id}/export")
def export_chapter(
    chapter_id: int,
    fmt: str = Query("pdf", pattern="^(pdf|docx)$"),
    include: str = Query("notes,questions"),
    layout: str = Query("full", pattern="^(full|worksheet)$"),
    db: Session = Depends(get_db),
):
    chapter = chapter_service.get_or_404(db, chapter_id)

    parts = {p.strip() for p in include.split(",") if p.strip()}
    include_notes = "notes" in parts
    include_questions = "questions" in parts
    if not (include_notes or include_questions):
        raise ValidationError("Nothing selected to export.")

    questions = chapter.questions
    worksheet = layout == "worksheet"
    base = _safe_name(chapter.chapter_name)
    suffix = "_worksheet" if worksheet else ""

    if fmt == "pdf":
        content = export_service.build_pdf(
            chapter, questions, include_notes, include_questions, worksheet=worksheet
        )
        media_type, filename = "application/pdf", f"{base}{suffix}.pdf"
    else:
        content = export_service.build_docx(
            chapter, questions, include_notes, include_questions, worksheet=worksheet
        )
        media_type, filename = DOCX_MIME, f"{base}{suffix}.docx"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
