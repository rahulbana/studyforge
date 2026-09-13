"""Data access for questions."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Question


def get(db: Session, question_id: int) -> Question | None:
    return db.get(Question, question_id)


def list_for_chapter(db: Session, chapter_id: int) -> list[Question]:
    return list(
        db.execute(
            select(Question).where(Question.chapter_id == chapter_id).order_by(Question.id)
        )
        .scalars()
        .all()
    )


def add(db: Session, question: Question) -> Question:
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def save(db: Session, question: Question) -> Question:
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def delete(db: Session, question: Question) -> None:
    db.delete(question)
    db.commit()
