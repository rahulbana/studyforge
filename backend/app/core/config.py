"""Application settings, loaded from the environment / .env file."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration.

    Values are read from environment variables (case-insensitive) and an
    optional ``.env`` file. See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Meta ---
    app_name: str = "StudyForge"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    # "text" (human-readable, default) or "json" (one structured object per line).
    log_format: str = "text"
    # Also write logs to this rotating file (relative to backend/). Empty = console only.
    log_file: str = "logs/app.log"

    # --- Observability ---
    # Expose GET /metrics in Prometheus text format.
    metrics_enabled: bool = True

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_retries: int = 3
    # USD price per 1,000,000 tokens (override to match your account's pricing).
    price_input_per_1m: float = 2.5
    price_output_per_1m: float = 10.0

    # --- Notes streaming ---
    stream_notes: bool = True

    # --- Agent behaviour ---
    enable_web_search: bool = True
    # Deeper, more thorough online research (higher web_search context size).
    deep_search: bool = False
    enable_diagrams: bool = True
    max_diagrams: int = 8
    # Verify a whole set of questions in one LLM call instead of one call each.
    batch_verification: bool = True

    @property
    def search_context_size(self) -> str:
        """web_search thoroughness: 'high' for deep search, else 'medium'."""
        return "high" if self.deep_search else "medium"

    # --- Uploads ---
    max_upload_mb: int = 25  # reject PDFs larger than this
    # OCR fallback for scanned/image-only PDFs (needs the Tesseract engine).
    enable_ocr: bool = True
    ocr_dpi: int = 200
    ocr_max_pages: int = 50

    # --- Persistence ---
    database_url: str = "sqlite:///./data/study_notes.db"

    # --- HTTP ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_openai_key(self) -> bool:
        """True only for a plausible real key.

        Rejects empties and the ``.env.example`` placeholder ``sk-...`` (which
        ``setup.sh`` recreates on every run) so the UI honestly reports a missing
        key instead of showing "configured" and then failing at call time.
        """
        key = (self.openai_api_key or "").strip()
        if not key.startswith("sk-") or "..." in key:
            return False
        return len(key) >= 20 and key != "sk-test-key"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (safe to call anywhere)."""
    return Settings()
