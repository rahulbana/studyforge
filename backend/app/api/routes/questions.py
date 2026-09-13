"""Question endpoints: generate, list, add manual, verify, update, delete."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from ...schemas import (
    GenerateQuestionsRequest,
    GenerationJobOut,
    ManualQuestionIn,
    QuestionOut,
    StatusResponse,
)
from ...services import question_service
from ..deps import get_db

router = APIRouter(prefix="/api", tags=["questions"])


@router.post(
    "/chapters/{chapter_id}/questions/generate",
    response_model=GenerationJobOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_questions(
    chapter_id: int,
    req: GenerateQuestionsRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start generation in the background; poll the returned job for completion."""
    job = question_service.start_generation(db, chapter_id, req)
    background.add_task(question_service.run_generation_job, job.id)
    return job


@router.get("/generation-jobs/{job_id}", response_model=GenerationJobOut)
def get_generation_job(job_id: int, db: Session = Depends(get_db)):
    return question_service.get_job_or_404(db, job_id)


@router.get("/chapters/{chapter_id}/questions", response_model=list[QuestionOut])
def list_questions(chapter_id: int, db: Session = Depends(get_db)):
    return question_service.list_for_chapter(db, chapter_id)


@router.post("/chapters/{chapter_id}/questions", response_model=QuestionOut)
def add_manual_question(
    chapter_id: int, payload: ManualQuestionIn, db: Session = Depends(get_db)
):
    return question_service.add_manual(db, chapter_id, payload)


@router.post("/questions/{question_id}/verify", response_model=QuestionOut)
def verify_single(question_id: int, db: Session = Depends(get_db)):
    return question_service.verify_one(db, question_id)


@router.post("/chapters/{chapter_id}/questions/verify-all", response_model=list[QuestionOut])
def verify_all(chapter_id: int, db: Session = Depends(get_db)):
    return question_service.verify_all(db, chapter_id)


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, payload: ManualQuestionIn, db: Session = Depends(get_db)):
    return question_service.update(db, question_id, payload)


@router.delete("/questions/{question_id}", response_model=StatusResponse)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    question_service.delete(db, question_id)
    return StatusResponse(ok=True, message="deleted")
