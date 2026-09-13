"""PDF helpers: text-layer extraction, with an OCR fallback for scanned PDFs."""
from __future__ import annotations

import io

from pypdf import PdfReader


class OcrUnavailable(Exception):
    """OCR was requested but the libraries or Tesseract engine aren't available."""


def extract_text_from_pdf(data: bytes) -> str:
    """Return the concatenated text layer of every page in the PDF.

    Empty for scanned/image-only PDFs (they have no selectable text) — use
    :func:`ocr_pdf` as a fallback in that case.
    """
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts).strip()


def ocr_pdf(data: bytes, *, dpi: int = 200, max_pages: int = 50) -> str:
    """Rasterise each page and OCR it, returning the recognised text.

    Raises :class:`OcrUnavailable` if the OCR libraries (PyMuPDF, pytesseract,
    Pillow) or the Tesseract engine are not installed.
    """
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - depends on install
        raise OcrUnavailable(f"OCR Python packages are not installed ({exc}).") from exc

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise OcrUnavailable(f"Could not open the PDF for OCR: {exc}") from exc

    parts: list[str] = []
    try:
        for index, page in enumerate(doc):
            if index >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            try:
                text = pytesseract.image_to_string(img) or ""
            except pytesseract.TesseractNotFoundError as exc:  # pragma: no cover
                raise OcrUnavailable(
                    "The Tesseract OCR engine is not installed. Install it "
                    "(e.g. 'apt-get install tesseract-ocr' or "
                    "'brew install tesseract') to read scanned PDFs."
                ) from exc
            if text.strip():
                parts.append(text.strip())
    finally:
        doc.close()

    return "\n\n".join(parts).strip()
