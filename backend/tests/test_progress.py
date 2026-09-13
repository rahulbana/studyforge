"""Progress aggregation across graded assessments."""
import json

from app.db.session import SessionLocal
from app.models import Assessment
from app.services import assessment_service


def _graded(subject, topic, score, breakdown):
    return Assessment(
        class_name="10", subject=subject, topic=topic, status="graded", score=score,
        points_awarded=score, points_max=100,
        feedback=json.dumps({"concept_breakdown": breakdown}),
    )


def test_progress_aggregates_scores_and_concepts():
    db = SessionLocal()
    db.add(_graded("Bio", "Cells", 50.0, [
        {"concept": "Mitosis", "percentage": 40.0},
        {"concept": "Membranes", "percentage": 90.0},
    ]))
    db.add(_graded("Bio", "Cells", 80.0, [
        {"concept": "Mitosis", "percentage": 50.0},
        {"concept": "Membranes", "percentage": 100.0},
    ]))
    db.commit()

    report = assessment_service.progress(db)
    assert report.total_attempts >= 2
    assert report.best_score >= 80.0

    stats = {c.concept: c for c in report.concepts}
    # Mitosis averaged (40+50)/2 = 45, weak (<60) both times.
    assert stats["Mitosis"].avg_percentage == 45.0
    assert stats["Mitosis"].weak_count == 2
    # Worst concept comes first.
    assert report.concepts[0].avg_percentage <= report.concepts[-1].avg_percentage
    # Attempts are chronological (oldest first).
    times = [a.created_at for a in report.attempts if a.created_at]
    assert times == sorted(times)
    db.close()
