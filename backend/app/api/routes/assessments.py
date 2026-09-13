"""Assessment endpoints: create/generate, take, submit/grade, history."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from ...schemas import (
    AssessmentCreate,
    AssessmentDetail,
    AssessmentSummary,
    ProgressResponse,
    StatusResponse,
    SubmitAnswersRequest,
)
from ...services import assessment_service
from ..deps import get_db

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.get("/progress", response_model=ProgressResponse)
def get_progress(db: Session = Depends(get_db)):
    """Aggregated progress across graded attempts (declared before /{id})."""
    return assessment_service.progress(db)


@router.post("", response_model=AssessmentDetail, status_code=status.HTTP_202_ACCEPTED)
def create_assessment(
    req: AssessmentCreate, background: BackgroundTasks, db: Session = Depends(get_db)
):
    """Create a test and generate its questions in the background."""
    assessment = assessment_service.create(db, req)
    background.add_task(assessment_service.run_generation, assessment.id)
    return assessment_service.serialize_detail(assessment)


@router.get("", response_model=list[AssessmentSummary])
def list_assessments(db: Session = Depends(get_db)):
    return assessment_service.list_summaries(db)


@router.get("/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    return assessment_service.serialize_detail(assessment_service.get_or_404(db, assessment_id))


@router.post("/{assessment_id}/submit", response_model=AssessmentDetail)
def submit_assessment(
    assessment_id: int,
    payload: SubmitAnswersRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    answers = {a.question_id: a.answer for a in payload.answers}
    assessment = assessment_service.submit(db, assessment_id, answers)
    background.add_task(assessment_service.run_grading, assessment.id)
    return assessment_service.serialize_detail(assessment)


@router.delete("/{assessment_id}", response_model=StatusResponse)
def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment_service.delete(db, assessment_id)
    return StatusResponse(ok=True, message="deleted")
