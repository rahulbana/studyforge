"""Question orchestration: generation, verification, and CRUD."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from ..agents.llm import LLMClient
from ..agents.question_agent import generate_for_type
from ..agents.verifier import verify_question, verify_questions_batch
from ..core.config import get_settings
from ..core.context import set_request_id
from ..core.exceptions import NotFoundError
from ..core.logging import get_logger
from ..db.session import SessionLocal
from ..models import Chapter, GenerationJob, Question
from ..models.enums import JobStatus, QuestionSource, VerificationStatus
from ..repositories import chapter_repo, job_repo, question_repo
from ..schemas import GenerateQuestionsRequest, ManualQuestionIn
from .usage import record_usage

logger = get_logger(__name__)

_AUTOFIX_STATUSES = {VerificationStatus.VERIFIED.value, VerificationStatus.CORRECTED.value}


def _q_payload(q: Question) -> dict:
    return {
        "qtype": q.qtype,
        "question": q.question,
        "answer": q.answer,
        "options": json.loads(q.options) if q.options else [],
        "explanation": q.explanation,
    }


def _apply_result(q: Question, result: dict) -> None:
    q.verification_status = result["status"]
    q.verification_note = result["note"]
    if result["status"] in _AUTOFIX_STATUSES:
        q.answer = result["answer"] or q.answer
        if result["options"]:
            q.options = json.dumps(result["options"])
        if result["explanation"]:
            q.explanation = result["explanation"]


def _get_chapter_or_404(db: Session, chapter_id: int) -> Chapter:
    chapter = chapter_repo.get(db, chapter_id)
    if not chapter:
        raise NotFoundError("Chapter not found.")
    return chapter


def _get_question_or_404(db: Session, question_id: int) -> Question:
    question = question_repo.get(db, question_id)
    if not question:
        raise NotFoundError("Question not found.")
    return question


def get_job_or_404(db: Session, job_id: int) -> GenerationJob:
    job = job_repo.get(db, job_id)
    if not job:
        raise NotFoundError("Generation job not found.")
    return job


def apply_verification(chapter: Chapter, q: Question, *, llm: LLMClient | None = None) -> None:
    """Verify a single Question in place (auto-fix + flag)."""
    _apply_result(q, verify_question(chapter, _q_payload(q), llm=llm))


def verify_questions(
    chapter: Chapter, questions: list[Question], *, llm: LLMClient | None = None
) -> None:
    """Verify many Questions in place, batching into one LLM call when enabled."""
    if not questions:
        return
    if get_settings().batch_verification and len(questions) > 1:
        items = [{"id": i, **_q_payload(q)} for i, q in enumerate(questions)]
        results = verify_questions_batch(chapter, items, llm=llm)
        for i, q in enumerate(questions):
            if i in results:
                _apply_result(q, results[i])
    else:
        for q in questions:
            apply_verification(chapter, q, llm=llm)


def list_for_chapter(db: Session, chapter_id: int) -> list[Question]:
    _get_chapter_or_404(db, chapter_id)
    return question_repo.list_for_chapter(db, chapter_id)


def start_generation(
    db: Session, chapter_id: int, req: GenerateQuestionsRequest
) -> GenerationJob:
    """Create a pending job for a generation request (run in the background)."""
    _get_chapter_or_404(db, chapter_id)
    job = GenerationJob(
        chapter_id=chapter_id,
        status=JobStatus.PENDING.value,
        params=req.model_dump_json(),
    )
    return job_repo.add(db, job)


def _generate_into_db(
    db: Session, chapter: Chapter, req: GenerateQuestionsRequest, *, llm: LLMClient | None = None
) -> int:
    """Generate + persist questions for a request; return how many were created."""
    created: list[Question] = []
    for qtype, count in req.counts.items():
        for item in generate_for_type(chapter, qtype, count, req.difficulty, llm=llm):
            created.append(
                Question(
                    chapter_id=chapter.id,
                    qtype=item["qtype"],
                    question=item["question"],
                    answer=item["answer"],
                    options=json.dumps(item["options"]) if item["options"] else "",
                    explanation=item["explanation"],
                    difficulty=item["difficulty"],
                    source=QuestionSource.GENERATED.value,
                    verification_status=VerificationStatus.UNVERIFIED.value,
                )
            )
    if req.verify:
        verify_questions(chapter, created, llm=llm)
    for q in created:
        db.add(q)
    db.commit()
    return len(created)


def run_generation_job(job_id: int) -> None:
    """Background job: generate (and optionally verify) questions for a job.

    Opens its own DB session; safe to hand to ``BackgroundTasks``.
    """
    set_request_id(f"questions-job:{job_id}")
    db = SessionLocal()
    try:
        job = job_repo.get(db, job_id)
        if not job:
            return
        job.status = JobStatus.RUNNING.value
        job_repo.save(db, job)
        try:
            chapter = _get_chapter_or_404(db, job.chapter_id)
            req = GenerateQuestionsRequest.model_validate_json(job.params)
            llm = LLMClient()
            count = _generate_into_db(db, chapter, req, llm=llm)
            record_usage(chapter, llm)
            chapter_repo.save(db, chapter)
            job.status = JobStatus.DONE.value
            job.result_count = count
            job.error = ""
        except Exception as exc:  # noqa: BLE001
            logger.exception("Question generation failed for job %s", job_id)
            job.status = JobStatus.ERROR.value
            job.error = str(exc)
        job_repo.save(db, job)
    finally:
        db.close()


def add_manual(db: Session, chapter_id: int, payload: ManualQuestionIn) -> Question:
    _get_chapter_or_404(db, chapter_id)
    q = Question(
        chapter_id=chapter_id,
        qtype=payload.qtype,
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        options=json.dumps(payload.options) if payload.options else "",
        explanation=payload.explanation.strip(),
        difficulty=payload.difficulty,
        source=QuestionSource.UPLOADED.value,
        verification_status=VerificationStatus.UNVERIFIED.value,
    )
    return question_repo.add(db, q)


def verify_one(db: Session, question_id: int) -> Question:
    q = _get_question_or_404(db, question_id)
    chapter = chapter_repo.get(db, q.chapter_id)
    apply_verification(chapter, q)
    return question_repo.save(db, q)


def verify_all(db: Session, chapter_id: int) -> list[Question]:
    chapter = _get_chapter_or_404(db, chapter_id)
    rows = question_repo.list_for_chapter(db, chapter_id)
    llm = LLMClient()
    verify_questions(chapter, rows, llm=llm)
    record_usage(chapter, llm)
    for q in rows:
        db.add(q)
    db.add(chapter)
    db.commit()
    for q in rows:
        db.refresh(q)
    return rows


def update(db: Session, question_id: int, payload: ManualQuestionIn) -> Question:
    q = _get_question_or_404(db, question_id)
    q.qtype = payload.qtype
    q.question = payload.question.strip()
    q.answer = payload.answer.strip()
    q.options = json.dumps(payload.options) if payload.options else ""
    q.explanation = payload.explanation.strip()
    q.difficulty = payload.difficulty
    # Manual edits invalidate any prior verification.
    q.verification_status = VerificationStatus.UNVERIFIED.value
    q.verification_note = ""
    return question_repo.save(db, q)


def delete(db: Session, question_id: int) -> None:
    q = _get_question_or_404(db, question_id)
    question_repo.delete(db, q)
