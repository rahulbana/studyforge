"""Data access for chapters."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Chapter, Question


def get(db: Session, chapter_id: int) -> Chapter | None:
    return db.get(Chapter, chapter_id)


def list_all(db: Session) -> list[Chapter]:
    return list(
        db.execute(select(Chapter).order_by(Chapter.created_at.desc())).scalars().all()
    )


def question_counts(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(Question.chapter_id, func.count(Question.id)).group_by(Question.chapter_id)
    ).all()
    return dict(rows)


def status_counts(db: Session) -> dict[str, int]:
    """Number of chapters grouped by ``notes_status``."""
    rows = db.execute(
        select(Chapter.notes_status, func.count(Chapter.id)).group_by(Chapter.notes_status)
    ).all()
    return {str(status): count for status, count in rows}


def cost_total(db: Session) -> float:
    """Sum of estimated cost recorded across all chapters."""
    return float(db.execute(select(func.coalesce(func.sum(Chapter.cost_usd), 0.0))).scalar() or 0.0)


def add(db: Session, chapter: Chapter) -> Chapter:
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


def save(db: Session, chapter: Chapter) -> Chapter:
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


def delete(db: Session, chapter: Chapter) -> None:
    db.delete(chapter)
    db.commit()
