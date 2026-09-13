"""Refresh DB-derived Prometheus gauges from the current database state.

Called at scrape time by the ``/metrics`` route so the gauges reflect a live
snapshot without a background poller.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..core import metrics
from ..models.enums import AssessmentStatus, JobStatus, NotesStatus
from ..repositories import assessment_repo, chapter_repo, job_repo


def _set_status_gauge(gauge, counts: dict[str, int], known: list[str]) -> None:
    """Set a per-status gauge, ensuring every known status has a value (0 if absent)."""
    for status in known:
        gauge.labels(status=status).set(counts.get(status, 0))


def refresh_db_gauges(db: Session) -> None:
    _set_status_gauge(
        metrics.chapters_by_status,
        chapter_repo.status_counts(db),
        [s.value for s in NotesStatus],
    )
    _set_status_gauge(
        metrics.generation_jobs_by_status,
        job_repo.status_counts(db),
        [s.value for s in JobStatus],
    )
    _set_status_gauge(
        metrics.assessments_by_status,
        assessment_repo.status_counts(db),
        [s.value for s in AssessmentStatus],
    )
    metrics.total_spend.set(chapter_repo.cost_total(db) + assessment_repo.cost_total(db))
