"""Chapter orchestration: upload, notes generation, listing, deletion."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from ..agents.diagram_agent import enrich_with_diagrams
from ..agents.llm import LLMClient
from ..agents.notes_agent import generate_notes, stream_notes
from ..core.config import get_settings
from ..core.context import set_request_id
from ..core.exceptions import AgentError, NotFoundError, ValidationError
from ..core.logging import get_logger
from ..db.session import SessionLocal
from ..models import Chapter
from ..models.enums import NotesStatus
from ..repositories import chapter_repo
from ..schemas import ChapterCreateMeta, ChapterSummary
from ..utils.markdown import normalize_mermaid_typography
from ..utils.pdf import OcrUnavailable, extract_text_from_pdf, ocr_pdf
from . import notes_stream
from .usage import record_usage

logger = get_logger(__name__)


def get_or_404(db: Session, chapter_id: int) -> Chapter:
    chapter = chapter_repo.get(db, chapter_id)
    if not chapter:
        raise NotFoundError("Chapter not found.")
    return chapter


def create_from_pdf(
    db: Session, *, data: bytes, filename: str, meta: ChapterCreateMeta
) -> Chapter:
    if not (filename or "").lower().endswith(".pdf"):
        raise ValidationError("Please upload a PDF file.")
    if not data:
        raise ValidationError("The uploaded file is empty.")
    if not data.startswith(b"%PDF-"):
        raise ValidationError("That file does not look like a PDF.")
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise ValidationError(
            f"PDF is too large (max {get_settings().max_upload_mb} MB)."
        )

    try:
        text = extract_text_from_pdf(data)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"Could not read the PDF: {exc}") from exc

    settings = get_settings()
    if not text and settings.enable_ocr:
        # Scanned / image-only PDF: no text layer. Try OCR.
        logger.info("No text layer in %s; attempting OCR.", filename or "upload")
        try:
            text = ocr_pdf(data, dpi=settings.ocr_dpi, max_pages=settings.ocr_max_pages)
        except OcrUnavailable as exc:
            raise ValidationError(
                "This looks like a scanned PDF (no selectable text) and OCR is "
                f"unavailable: {exc}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("OCR failed for %s", filename or "upload")
            raise ValidationError(f"OCR failed while reading the scanned PDF: {exc}") from exc

    if not text:
        detail = "No selectable text found in the PDF (it may be scanned images)."
        if not settings.enable_ocr:
            detail += " Enable OCR (ENABLE_OCR=true) to read scanned PDFs."
        raise ValidationError(detail)

    chapter = Chapter(
        class_name=meta.class_name.strip(),
        subject=meta.subject.strip(),
        chapter_name=meta.chapter_name.strip(),
        source_filename=filename or "",
        raw_text=text,
        notes_status=NotesStatus.PENDING.value,
    )
    return chapter_repo.add(db, chapter)


def list_summaries(db: Session) -> list[ChapterSummary]:
    counts = chapter_repo.question_counts(db)
    summaries: list[ChapterSummary] = []
    for chapter in chapter_repo.list_all(db):
        summary = ChapterSummary.model_validate(chapter)
        summary.question_count = counts.get(chapter.id, 0)
        summaries.append(summary)
    return summaries


def mark_notes_pending(db: Session, chapter: Chapter) -> Chapter:
    chapter.notes_status = NotesStatus.PENDING.value
    chapter.notes_error = ""
    return chapter_repo.save(db, chapter)


def delete(db: Session, chapter: Chapter) -> None:
    chapter_repo.delete(db, chapter)


def run_notes_generation(chapter_id: int) -> None:
    """Background job: research + write notes, then render diagrams.

    Opens its own DB session; safe to hand to ``BackgroundTasks``.
    """
    settings = get_settings()
    set_request_id(f"notes:{chapter_id}")
    db = SessionLocal()
    try:
        chapter = chapter_repo.get(db, chapter_id)
        if not chapter:
            return
        try:
            llm = LLMClient()
            result = generate_notes(
                chapter.class_name, chapter.subject, chapter.chapter_name, chapter.raw_text,
                llm=llm,
            )
            notes = result.text
            if settings.enable_diagrams:
                notes = enrich_with_diagrams(
                    notes,
                    chapter.class_name,
                    chapter.subject,
                    chapter.chapter_name,
                    max_diagrams=settings.max_diagrams,
                    llm=llm,
                )
            chapter.notes = normalize_mermaid_typography(notes)
            chapter.sources = json.dumps(result.sources)
            chapter.notes_status = NotesStatus.READY.value
            chapter.notes_error = ""
            record_usage(chapter, llm)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Notes generation failed for chapter %s", chapter_id)
            chapter.notes_status = NotesStatus.ERROR.value
            chapter.notes_error = str(exc)
        chapter_repo.save(db, chapter)
    finally:
        db.close()


def start_notes_stream(chapter_id: int) -> notes_stream.NotesStream:
    """Start (or attach to) a live streaming generation for a chapter."""

    def runner(stream: notes_stream.NotesStream) -> None:
        _stream_notes_generation(chapter_id, stream)

    return notes_stream.get_or_start(chapter_id, runner)


def _stream_notes_generation(chapter_id: int, stream: notes_stream.NotesStream) -> None:
    """Generate notes with token streaming, persist, then finish the stream."""
    settings = get_settings()
    set_request_id(f"notes-stream:{chapter_id}")
    db = SessionLocal()
    try:
        chapter = chapter_repo.get(db, chapter_id)
        if not chapter:
            stream.fail("Chapter not found.")
            return
        try:
            llm = LLMClient()
            try:
                result = stream_notes(
                    chapter.class_name, chapter.subject, chapter.chapter_name, chapter.raw_text,
                    on_delta=stream.push, llm=llm,
                )
            except AgentError as exc:
                logger.warning("Streaming notes failed (%s); falling back to non-streaming.", exc)
                result = generate_notes(
                    chapter.class_name, chapter.subject, chapter.chapter_name, chapter.raw_text,
                    llm=llm,
                )
                stream.push(result.text)
            notes = result.text
            if settings.enable_diagrams:
                notes = enrich_with_diagrams(
                    notes, chapter.class_name, chapter.subject, chapter.chapter_name,
                    max_diagrams=settings.max_diagrams, llm=llm,
                )
            chapter.notes = normalize_mermaid_typography(notes)
            chapter.sources = json.dumps(result.sources)
            chapter.notes_status = NotesStatus.READY.value
            chapter.notes_error = ""
            record_usage(chapter, llm)
            chapter_repo.save(db, chapter)
            stream.finish()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Streamed notes generation failed for chapter %s", chapter_id)
            chapter.notes_status = NotesStatus.ERROR.value
            chapter.notes_error = str(exc)
            chapter_repo.save(db, chapter)
            stream.fail(str(exc))
    finally:
        db.close()
