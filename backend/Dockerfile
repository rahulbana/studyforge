# Backend: FastAPI + Alembic on Python 3.12
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Tesseract engine for the scanned-PDF OCR fallback (pytesseract needs it).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Runtime deps only (wheels bundle native libs for lxml/reportlab/pillow/pymupdf).
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code + migrations.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

EXPOSE 8000

# Migrations run automatically on startup (app lifespan -> init_db -> Alembic).
# Shell form so $PORT (set by Cloud Run, default 8080) is honoured; falls back
# to 8000 for local docker-compose where PORT is unset.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
