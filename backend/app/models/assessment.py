"""Assessment (test) ORM models: an attempt plus its questions."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base
from .enums import AssessmentStatus
from .timeutils import utcnow


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_name: Mapped[str] = mapped_column(String(120))
    subject: Mapped[str] = mapped_column(String(120))
    topic: Mapped[str] = mapped_column(String(255))
    # Optional link to an uploaded chapter used as ground truth.
    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default=AssessmentStatus.GENERATING.value)
    params: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")

    score: Mapped[float | None] = mapped_column(Float, nullable=True)  # percentage 0-100
    points_awarded: Mapped[float] = mapped_column(Float, default=0.0)
    points_max: Mapped[int] = mapped_column(Integer, default=0)
    # JSON: {summary, recommendations[], concept_breakdown[], weak_concepts[], strong_concepts[]}
    feedback: Mapped[str] = mapped_column(Text, default="")

    # Cumulative AI usage/cost for this test (generation + grading).
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    questions: Mapped[list[AssessmentQuestion]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestion.order_index",
    )


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE")
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    qtype: Mapped[str] = mapped_column(String(30))
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text, default="")  # JSON list for MCQ
    correct_answer: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    concept: Mapped[str] = mapped_column(String(160), default="General")
    max_points: Mapped[int] = mapped_column(Integer, default=1)

    # Filled when the student submits / grading runs.
    student_answer: Mapped[str] = mapped_column(Text, default="")
    awarded_points: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default="")

    assessment: Mapped[Assessment] = relationship(back_populates="questions")
