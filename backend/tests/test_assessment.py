"""End-to-end assessment lifecycle with the LLM stubbed."""
from app.db.session import SessionLocal
from app.schemas import AssessmentCreate
from app.services import assessment_service


def _fake_generate(**kwargs):
    return [
        {
            "qtype": "mcq",
            "question": "2 + 2 = ?",
            "correct_answer": "4",
            "options": ["3", "4", "5", "6"],
            "explanation": "Basic addition.",
            "concept": "Arithmetic",
            "difficulty": "easy",
        },
        {
            "qtype": "short_answer",
            "question": "Define photosynthesis.",
            "correct_answer": "Conversion of light to chemical energy.",
            "options": [],
            "explanation": "",
            "concept": "Photosynthesis",
            "difficulty": "medium",
        },
    ]


def _fake_grade(*, subject, topic, items, **kwargs):
    # Award partial credit (2 of 3) to every subjective item.
    return {it["id"]: {"awarded": 2, "is_correct": True, "feedback": "Good."} for it in items}


def _fake_feedback(**kwargs):
    return {"summary": "Solid effort.", "recommendations": ["Revise photosynthesis."]}


def test_full_assessment_flow(monkeypatch):
    monkeypatch.setattr(assessment_service.assessment_agent, "generate_test", _fake_generate)
    monkeypatch.setattr(assessment_service.assessment_agent, "grade_answers", _fake_grade)
    monkeypatch.setattr(assessment_service.assessment_agent, "overall_feedback", _fake_feedback)

    db = SessionLocal()
    req = AssessmentCreate(
        source="topic", class_name="10", subject="Bio", topic="Cells",
        counts={"mcq": 1, "short_answer": 1}, difficulty="easy",
    )
    assessment = assessment_service.create(db, req)
    assessment_id = assessment.id
    assert assessment.status == "generating"

    # Generate questions.
    assessment_service.run_generation(assessment_id)

    gen_db = SessionLocal()
    detail = assessment_service.serialize_detail(
        assessment_service.get_or_404(gen_db, assessment_id)
    )
    assert detail.status == "ready"
    assert len(detail.questions) == 2
    assert detail.points_max == 4  # mcq(1) + short_answer(3)
    # Answers are hidden before grading.
    assert all(q.correct_answer is None for q in detail.questions)
    q_by_type = {q.qtype: q for q in detail.questions}
    gen_db.close()

    # Submit: mcq correct, short answer non-empty.
    answers = {q_by_type["mcq"].id: "4", q_by_type["short_answer"].id: "energy from light"}
    submit_db = SessionLocal()
    assessment_service.submit(submit_db, assessment_id, answers)
    submit_db.close()

    # Grade.
    assessment_service.run_grading(assessment_id)

    res_db = SessionLocal()
    graded = assessment_service.serialize_detail(
        assessment_service.get_or_404(res_db, assessment_id)
    )
    assert graded.status == "graded"
    # mcq: 1/1 correct, short: 2/3 -> 3/4 = 75%
    assert graded.score == 75.0
    assert graded.feedback is not None
    assert graded.feedback.summary == "Solid effort."
    assert len(graded.feedback.concept_breakdown) == 2
    # Correct answers now revealed.
    assert any(q.correct_answer for q in graded.questions)
    res_db.close()
    db.close()
