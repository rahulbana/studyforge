"""Assessment orchestration: create, generate, submit, grade, report."""
from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from ..agents import assessment_agent
from ..agents.llm import LLMClient
from ..core.context import set_request_id
from ..core.exceptions import NotFoundError, ValidationError
from ..core.logging import get_logger
from ..db.session import SessionLocal
from ..models import Assessment, AssessmentQuestion
from ..models.enums import OBJECTIVE_TYPES, AssessmentStatus, default_points
from ..models.timeutils import utcnow
from ..repositories import assessment_repo, chapter_repo
from ..schemas import AssessmentCreate, AssessmentDetail, AssessmentSummary
from .usage import record_usage

logger = get_logger(__name__)

_WEAK_THRESHOLD = 60.0
_STRONG_THRESHOLD = 80.0


def _normalize(text: str) -> str:
    return re.sub(r"[\s]+", " ", re.sub(r"[^\w\s]", "", (text or "").lower())).strip()


def get_or_404(db: Session, assessment_id: int) -> Assessment:
    assessment = assessment_repo.get(db, assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found.")
    return assessment


# --------------------------------------------------------------------------- #
# Create + generate
# --------------------------------------------------------------------------- #
def create(db: Session, req: AssessmentCreate) -> Assessment:
    class_name, subject, topic, chapter_id = req.class_name, req.subject, req.topic, None

    if req.source == "chapter":
        if not req.chapter_id:
            raise ValidationError("Select a chapter to test on.")
        chapter = chapter_repo.get(db, req.chapter_id)
        if not chapter:
            raise NotFoundError("Chapter not found.")
        chapter_id = chapter.id
        class_name = class_name or chapter.class_name
        subject = subject or chapter.subject
        topic = topic or chapter.chapter_name
    else:
        if not topic.strip():
            raise ValidationError("Enter a topic to be tested on.")

    assessment = Assessment(
        class_name=class_name.strip(),
        subject=subject.strip(),
        topic=topic.strip(),
        chapter_id=chapter_id,
        status=AssessmentStatus.GENERATING.value,
        params=req.model_dump_json(),
    )
    return assessment_repo.add(db, assessment)


def run_generation(assessment_id: int) -> None:
    """Background: generate the test's questions."""
    set_request_id(f"assessment-gen:{assessment_id}")
    db = SessionLocal()
    try:
        assessment = assessment_repo.get(db, assessment_id)
        if not assessment:
            return
        try:
            req = AssessmentCreate.model_validate_json(assessment.params)
            context = ""
            if assessment.chapter_id:
                chapter = chapter_repo.get(db, assessment.chapter_id)
                if chapter:
                    context = (chapter.notes or "").strip() or (chapter.raw_text or "").strip()
            llm = LLMClient()
            items = assessment_agent.generate_test(
                class_name=assessment.class_name,
                subject=assessment.subject,
                topic=assessment.topic,
                counts=req.counts,
                difficulty=req.difficulty,
                context=context,
                llm=llm,
            )
            if not items:
                raise RuntimeError("No questions were generated.")
            for idx, item in enumerate(items):
                db.add(
                    AssessmentQuestion(
                        assessment_id=assessment.id,
                        order_index=idx,
                        qtype=item["qtype"],
                        question=item["question"],
                        options=json.dumps(item["options"]) if item["options"] else "",
                        correct_answer=item["correct_answer"],
                        explanation=item["explanation"],
                        concept=item["concept"],
                        max_points=default_points(item["qtype"]),
                    )
                )
            assessment.points_max = sum(default_points(i["qtype"]) for i in items)
            assessment.status = AssessmentStatus.READY.value
            assessment.error = ""
            record_usage(assessment, llm)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Assessment generation failed for %s", assessment_id)
            assessment.status = AssessmentStatus.ERROR.value
            assessment.error = str(exc)
        assessment_repo.save(db, assessment)
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Submit + grade
# --------------------------------------------------------------------------- #
def submit(db: Session, assessment_id: int, answers: dict[int, str]) -> Assessment:
    assessment = get_or_404(db, assessment_id)
    if assessment.status not in (AssessmentStatus.READY.value, AssessmentStatus.GRADED.value):
        raise ValidationError("This test is not ready to be submitted.")
    for q in assessment.questions:
        q.student_answer = (answers.get(q.id, "") or "").strip()
        db.add(q)
    assessment.status = AssessmentStatus.GRADING.value
    assessment.submitted_at = utcnow()
    return assessment_repo.save(db, assessment)


def _grade_objective(q: AssessmentQuestion) -> None:
    correct = _normalize(q.correct_answer) == _normalize(q.student_answer)
    q.is_correct = correct and bool(q.student_answer)
    q.awarded_points = float(q.max_points) if q.is_correct else 0.0
    if not q.student_answer:
        q.feedback = "No answer provided."
    elif correct:
        q.feedback = "Correct."
    else:
        q.feedback = f"Incorrect. Correct answer: {q.correct_answer}"


def _build_feedback(assessment: Assessment, llm: LLMClient | None = None) -> dict:
    """Aggregate per-concept scores and get an overall narrative from the LLM."""
    by_concept: dict[str, list[float]] = {}
    for q in assessment.questions:
        awarded = q.awarded_points or 0.0
        by_concept.setdefault(q.concept, [0.0, 0.0])
        by_concept[q.concept][0] += awarded
        by_concept[q.concept][1] += q.max_points

    breakdown = []
    for concept, (awarded, total) in by_concept.items():
        pct = round((awarded / total) * 100, 1) if total else 0.0
        breakdown.append(
            {"concept": concept, "points_awarded": round(awarded, 2),
             "points_max": total, "percentage": pct}
        )
    breakdown.sort(key=lambda c: c["percentage"])

    weak = [c["concept"] for c in breakdown if c["percentage"] < _WEAK_THRESHOLD]
    strong = [c["concept"] for c in breakdown if c["percentage"] >= _STRONG_THRESHOLD]

    score_pct = (
        round((assessment.points_awarded / assessment.points_max) * 100, 1)
        if assessment.points_max
        else 0.0
    )
    narrative = assessment_agent.overall_feedback(
        subject=assessment.subject, topic=assessment.topic,
        score_pct=score_pct, breakdown=breakdown, llm=llm,
    )
    return {
        "summary": narrative.get("summary", ""),
        "recommendations": narrative.get("recommendations", []),
        "concept_breakdown": breakdown,
        "weak_concepts": weak,
        "strong_concepts": strong,
    }


def run_grading(assessment_id: int) -> None:
    """Background: grade answers, compute scores and write feedback."""
    set_request_id(f"assessment-grade:{assessment_id}")
    db = SessionLocal()
    try:
        assessment = assessment_repo.get(db, assessment_id)
        if not assessment:
            return
        try:
            llm = LLMClient()
            subjective_items = []
            for q in assessment.questions:
                if q.qtype in OBJECTIVE_TYPES:
                    _grade_objective(q)
                elif not q.student_answer.strip():
                    q.awarded_points, q.is_correct = 0.0, False
                    q.feedback = "No answer provided."
                else:
                    subjective_items.append(
                        {
                            "id": q.id,
                            "qtype": q.qtype,
                            "question": q.question,
                            "correct_answer": q.correct_answer,
                            "max_points": q.max_points,
                            "student_answer": q.student_answer,
                        }
                    )

            gradings = assessment_agent.grade_answers(
                subject=assessment.subject, topic=assessment.topic,
                items=subjective_items, llm=llm,
            )
            for q in assessment.questions:
                if q.id not in gradings:
                    continue
                g = gradings[q.id]
                try:
                    awarded = float(g["awarded"])
                except (TypeError, ValueError, KeyError):
                    awarded = 0.0
                q.awarded_points = max(0.0, min(awarded, float(q.max_points)))
                q.is_correct = bool(g["is_correct"])
                q.feedback = g["feedback"] or ""

            assessment.points_awarded = sum(q.awarded_points or 0.0 for q in assessment.questions)
            assessment.score = (
                round((assessment.points_awarded / assessment.points_max) * 100, 1)
                if assessment.points_max
                else 0.0
            )
            assessment.feedback = json.dumps(_build_feedback(assessment, llm))
            assessment.status = AssessmentStatus.GRADED.value
            assessment.graded_at = utcnow()
            assessment.error = ""
            record_usage(assessment, llm)
            for q in assessment.questions:
                db.add(q)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Assessment grading failed for %s", assessment_id)
            assessment.status = AssessmentStatus.ERROR.value
            assessment.error = str(exc)
        assessment_repo.save(db, assessment)
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Read / serialize
# --------------------------------------------------------------------------- #
def progress(db: Session):
    """Aggregate graded attempts into a progress report (score trend + concepts)."""
    from ..schemas import AttemptPoint, ConceptStat, ProgressResponse

    graded = [
        a for a in assessment_repo.list_all(db)
        if a.status == AssessmentStatus.GRADED.value and a.score is not None
    ]
    graded.sort(key=lambda a: a.created_at or 0)  # oldest first for the trend

    attempts = [
        AttemptPoint(id=a.id, subject=a.subject, topic=a.topic, score=a.score,
                     created_at=a.created_at)
        for a in graded
    ]

    # concept -> [sum_pct, count, weak_count]
    agg: dict[str, list[float]] = {}
    for a in graded:
        try:
            fb = json.loads(a.feedback or "{}")
        except json.JSONDecodeError:
            continue
        for c in fb.get("concept_breakdown", []):
            name = c.get("concept")
            if not name:
                continue
            pct = float(c.get("percentage", 0) or 0)
            slot = agg.setdefault(name, [0.0, 0.0, 0.0])
            slot[0] += pct
            slot[1] += 1
            if pct < _WEAK_THRESHOLD:
                slot[2] += 1
    concepts = [
        ConceptStat(
            concept=name,
            attempts=int(count),
            avg_percentage=round(total / count, 1) if count else 0.0,
            weak_count=int(weak),
        )
        for name, (total, count, weak) in agg.items()
    ]
    concepts.sort(key=lambda c: c.avg_percentage)  # worst first

    scores = [a.score for a in graded]
    return ProgressResponse(
        total_attempts=len(graded),
        average_score=round(sum(scores) / len(scores), 1) if scores else None,
        best_score=max(scores) if scores else None,
        attempts=attempts,
        concepts=concepts,
    )


def list_summaries(db: Session) -> list[AssessmentSummary]:
    counts = assessment_repo.question_counts(db)
    result = []
    for a in assessment_repo.list_all(db):
        summary = AssessmentSummary.model_validate(a)
        summary.question_count = counts.get(a.id, 0)
        result.append(summary)
    return result


def serialize_detail(assessment: Assessment) -> AssessmentDetail:
    """Serialize an assessment, hiding answers/feedback until it is graded."""
    detail = AssessmentDetail.model_validate(assessment)
    if assessment.status != AssessmentStatus.GRADED.value:
        detail.feedback = None
        for q in detail.questions:
            q.correct_answer = None
            q.explanation = None
            q.awarded_points = None
            q.is_correct = None
            q.feedback = None
    return detail


def delete(db: Session, assessment_id: int) -> None:
    assessment = get_or_404(db, assessment_id)
    assessment_repo.delete(db, assessment)
