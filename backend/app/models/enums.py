"""Domain enumerations shared across models, schemas and services."""
from __future__ import annotations

from enum import Enum


class QuestionType(str, Enum):
    TRUE_FALSE = "true_false"
    MCQ = "mcq"
    FILL_BLANK = "fill_blank"
    ONE_WORD = "one_word"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    CASE_BASED = "case_based"

    @property
    def label(self) -> str:
        return QUESTION_TYPE_LABELS[self]


QUESTION_TYPE_LABELS: dict[QuestionType, str] = {
    QuestionType.TRUE_FALSE: "True / False",
    QuestionType.MCQ: "Multiple Choice",
    QuestionType.FILL_BLANK: "Fill in the Blanks",
    QuestionType.ONE_WORD: "One Word Answer",
    QuestionType.SHORT_ANSWER: "Short Answer",
    QuestionType.LONG_ANSWER: "Long Answer",
    QuestionType.CASE_BASED: "Case Based",
}


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    CORRECTED = "corrected"
    NEEDS_REVIEW = "needs_review"


class NotesStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    ERROR = "error"


class QuestionSource(str, Enum):
    GENERATED = "generated"
    UPLOADED = "uploaded"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class AssessmentStatus(str, Enum):
    GENERATING = "generating"  # questions being generated
    READY = "ready"            # ready to take
    GRADING = "grading"        # answers submitted, being graded
    GRADED = "graded"          # results available
    ERROR = "error"


# Marks awarded per question type when generating a test.
DEFAULT_POINTS: dict[QuestionType, int] = {
    QuestionType.TRUE_FALSE: 1,
    QuestionType.MCQ: 1,
    QuestionType.FILL_BLANK: 1,
    QuestionType.ONE_WORD: 1,
    QuestionType.SHORT_ANSWER: 3,
    QuestionType.LONG_ANSWER: 5,
    QuestionType.CASE_BASED: 5,
}

# Types graded by exact/normalised match; the rest are graded by the LLM.
OBJECTIVE_TYPES: set[str] = {QuestionType.MCQ.value, QuestionType.TRUE_FALSE.value}


def default_points(qtype: str) -> int:
    try:
        return DEFAULT_POINTS[QuestionType(qtype)]
    except (ValueError, KeyError):
        return 1


def label_for(qtype: str) -> str:
    """Human label for a raw question-type value, tolerant of unknown values."""
    try:
        return QuestionType(qtype).label
    except ValueError:
        return qtype
