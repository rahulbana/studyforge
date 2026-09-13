"""Scanned-PDF OCR fallback in chapter_service.create_from_pdf."""
import pytest

from app.core.config import Settings
from app.core.exceptions import ValidationError
from app.db.session import SessionLocal
from app.schemas import ChapterCreateMeta
from app.services import chapter_service
from app.utils.pdf import OcrUnavailable

_PDF = b"%PDF-1.4 fake body"
_META = ChapterCreateMeta(class_name="9", subject="Sci", chapter_name="Ch")


def _make(db):
    return chapter_service.create_from_pdf(db, data=_PDF, filename="scan.pdf", meta=_META)


def test_ocr_used_when_no_text_layer(monkeypatch):
    monkeypatch.setattr(chapter_service, "extract_text_from_pdf", lambda data: "")
    monkeypatch.setattr(chapter_service, "ocr_pdf", lambda data, **kw: "text from ocr")
    db = SessionLocal()
    try:
        chapter = _make(db)
        assert chapter.raw_text == "text from ocr"
    finally:
        db.close()


def test_ocr_unavailable_gives_actionable_error(monkeypatch):
    monkeypatch.setattr(chapter_service, "extract_text_from_pdf", lambda data: "")

    def _raise(data, **kw):
        raise OcrUnavailable("Tesseract not installed")

    monkeypatch.setattr(chapter_service, "ocr_pdf", _raise)
    db = SessionLocal()
    try:
        with pytest.raises(ValidationError, match="scanned PDF"):
            _make(db)
    finally:
        db.close()


def test_ocr_disabled_mentions_the_flag(monkeypatch):
    monkeypatch.setattr(chapter_service, "extract_text_from_pdf", lambda data: "")
    monkeypatch.setattr(chapter_service, "get_settings", lambda: Settings(enable_ocr=False))
    db = SessionLocal()
    try:
        with pytest.raises(ValidationError, match="ENABLE_OCR"):
            _make(db)
    finally:
        db.close()
