"""Data access for generation jobs."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import GenerationJob


def get(db: Session, job_id: int) -> GenerationJob | None:
    return db.get(GenerationJob, job_id)


def status_counts(db: Session) -> dict[str, int]:
    """Number of generation jobs grouped by ``status``."""
    rows = db.execute(
        select(GenerationJob.status, func.count(GenerationJob.id)).group_by(GenerationJob.status)
    ).all()
    return {str(status): count for status, count in rows}


def add(db: Session, job: GenerationJob) -> GenerationJob:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def save(db: Session, job: GenerationJob) -> GenerationJob:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
