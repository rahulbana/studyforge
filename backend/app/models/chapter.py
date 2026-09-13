"""Chapter ORM model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base
from .enums import NotesStatus
from .timeutils import utcnow


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_name: Mapped[str] = mapped_column(String(120))
    subject: Mapped[str] = mapped_column(String(120))
    chapter_name: Mapped[str] = mapped_column(String(255))
    source_filename: Mapped[str] = mapped_column(String(255), default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    # JSON-encoded list of {url, title} web sources used to write the notes.
    sources: Mapped[str] = mapped_column(Text, default="")
    notes_status: Mapped[str] = mapped_column(String(20), default=NotesStatus.PENDING.value)
    notes_error: Mapped[str] = mapped_column(Text, default="")
    # Cumulative AI usage/cost for this chapter (notes + diagrams + questions).
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    questions: Mapped[list[Question]] = relationship(  # noqa: F821
        back_populates="chapter", cascade="all, delete-orphan"
    )
