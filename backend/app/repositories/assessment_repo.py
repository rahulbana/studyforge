"""Data access for assessments."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Assessment, AssessmentQuestion


def get(db: Session, assessment_id: int) -> Assessment | None:
    return db.get(Assessment, assessment_id)


def list_all(db: Session) -> list[Assessment]:
    return list(
        db.execute(select(Assessment).order_by(Assessment.created_at.desc())).scalars().all()
    )


def question_counts(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(AssessmentQuestion.assessment_id, func.count(AssessmentQuestion.id)).group_by(
            AssessmentQuestion.assessment_id
        )
    ).all()
    return dict(rows)


def status_counts(db: Session) -> dict[str, int]:
    """Number of assessments grouped by ``status``."""
    rows = db.execute(
        select(Assessment.status, func.count(Assessment.id)).group_by(Assessment.status)
    ).all()
    return {str(status): count for status, count in rows}


def cost_total(db: Session) -> float:
    """Sum of estimated cost recorded across all assessments."""
    return float(
        db.execute(select(func.coalesce(func.sum(Assessment.cost_usd), 0.0))).scalar() or 0.0
    )


def add(db: Session, assessment: Assessment) -> Assessment:
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def save(db: Session, assessment: Assessment) -> Assessment:
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def delete(db: Session, assessment: Assessment) -> None:
    db.delete(assessment)
    db.commit()
