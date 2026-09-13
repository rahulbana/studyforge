"""The background question-generation job, with the LLM stubbed out."""
from app.db.session import SessionLocal
from app.models import Chapter
from app.repositories import chapter_repo
from app.schemas import GenerateQuestionsRequest
from app.services import question_service


def _fake_generate(chapter, qtype, count, difficulty, **kwargs):
    return [
        {
            "qtype": qtype,
            "question": f"{qtype} q{i}",
            "answer": "a",
            "options": [],
            "explanation": "",
            "difficulty": "easy",
        }
        for i in range(count)
    ]


def test_generation_job_runs_and_persists(monkeypatch):
    monkeypatch.setattr(question_service, "generate_for_type", _fake_generate)

    db = SessionLocal()
    chapter = chapter_repo.add(
        db, Chapter(class_name="10", subject="Bio", chapter_name="Cells", raw_text="x")
    )
    req = GenerateQuestionsRequest(
        counts={"mcq": 2, "true_false": 1}, difficulty="easy", verify=False
    )
    job = question_service.start_generation(db, chapter.id, req)
    assert job.status == "pending"

    # Run the background job (uses its own session).
    question_service.run_generation_job(job.id)

    verify_db = SessionLocal()
    finished = question_service.get_job_or_404(verify_db, job.id)
    assert finished.status == "done"
    assert finished.result_count == 3
    assert len(question_service.list_for_chapter(verify_db, chapter.id)) == 3
    verify_db.close()
    db.close()


def test_generation_job_records_error(monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(question_service, "generate_for_type", boom)

    db = SessionLocal()
    chapter = chapter_repo.add(
        db, Chapter(class_name="10", subject="Bio", chapter_name="Photosynthesis", raw_text="x")
    )
    job = question_service.start_generation(
        db, chapter.id, GenerateQuestionsRequest(counts={"mcq": 1}, verify=False)
    )
    question_service.run_generation_job(job.id)

    verify_db = SessionLocal()
    finished = question_service.get_job_or_404(verify_db, job.id)
    assert finished.status == "error"
    assert "model exploded" in finished.error
    verify_db.close()
    db.close()
