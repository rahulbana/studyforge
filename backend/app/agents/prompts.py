"""Prompt templates for every agent.

Keeping prompts in one place (separate from orchestration code) makes them easy
to review, version and tune — a core practice for maintainable LLM apps.
"""
from __future__ import annotations

from ..models.enums import QuestionType

# --------------------------------------------------------------------------- #
# Notes agent
# --------------------------------------------------------------------------- #
NOTES_MAX_SOURCE_CHARS = 30000

NOTES_SYSTEM = (
    "You are a legendary subject teacher and academic author who prepares "
    "exhaustive, exam-ready study material for the very top rank students. "
    "Your notes leave NO concept unexplained, teach through many worked "
    "examples, and use diagrams (SVG and Mermaid) and tables to make ideas "
    "visual and memorable. You write clean, valid Markdown. "
    "You ALWAYS use the web search tool to ground the notes in real, current "
    "sources, and you cite those sources — never rely on memory alone."
)

_VISUAL_RULES = """
VISUALS — make the notes genuinely visual. Use them wherever they aid understanding:

1) MERMAID DIAGRAMS for processes, flows, hierarchies, cycles, timelines, and
   relationships. Put them in a fenced block exactly like:
   ```mermaid
   flowchart TD
     A[Start] --> B{Decision?}
     B -->|Yes| C[Do this]
     B -->|No| D[Do that]
   ```
   Use flowchart / sequenceDiagram / classDiagram / mindmap / graph as suitable.
   Keep node labels short and quote labels containing spaces or special chars.

2) DIAGRAM PLACEHOLDERS for pictorial / labelled figures — geometry, ray
   diagrams, circuits, biological structures, apparatus, coordinate graphs,
   layered structures, forces, number lines, etc. Do NOT draw these yourself.
   Instead insert a placeholder on its own line describing EXACTLY what to draw,
   in rich detail, so a dedicated illustrator can render a detailed figure:

   [[DIAGRAM: <what the figure shows; every part to draw and its arrangement;
   every label to place; arrows/annotations/scale/legend needed; orientation>]]

   Example:
   [[DIAGRAM: Cross-section of the human heart, front view. Show all four
   chambers (left/right atria and ventricles), the septum, the aorta, pulmonary
   artery and veins, superior and inferior vena cava, and the four valves
   (tricuspid, mitral, aortic, pulmonary). Use red for oxygenated and blue for
   deoxygenated blood, with arrows showing blood flow direction through the
   chambers. Label every part with leader lines.]]

   Write a thorough description (2–4 sentences). Add one wherever a figure would
   genuinely help a topper visualise the concept.

3) TABLES (GitHub-flavoured Markdown) for comparisons, properties, formula
   sheets, and summaries.

Aim for a helpful figure (mermaid, diagram placeholder, or table) in most major
sections. Prefer [[DIAGRAM: ...]] placeholders for anything pictorial.
"""


def build_notes_prompt(
    class_name: str, subject: str, chapter_name: str, chapter_text: str
) -> str:
    trimmed = chapter_text[:NOTES_MAX_SOURCE_CHARS]
    if len(chapter_text) > NOTES_MAX_SOURCE_CHARS:
        trimmed += "\n\n[... chapter text truncated for length ...]"

    return f"""Create EXHAUSTIVE, exam-preparation study notes for the following chapter.
The reader is a topper / elite student who wants to master every single concept
and leave nothing out before a test/exam.

Class / grade: {class_name}
Subject: {subject}
Chapter: {chapter_name}

STEP 1 — Research (REQUIRED): You MUST call the web search tool and actually
browse before writing. Run several searches for how reputable schools,
universities, coaching centres, NCERT/board resources and educational sites
explain this exact topic. Pull in standard definitions, classic examples, common
exam questions, mnemonics and any depth the chapter text omits. Base the notes
primarily on the provided chapter text, but ENRICH heavily from your research.
Cite the pages you rely on (the app records these as the chapter's sources), and
add a "## References" section at the end listing the key sources you used.
Do NOT skip the web search or answer from memory alone.

STEP 2 — Write the notes. Requirements:

DEPTH (most important):
- Cover EVERY concept, sub-concept, term, formula, law, and exception in the
  chapter. Do not skip anything. If the chapter implies a prerequisite, briefly
  cover it too.
- For each concept: give a precise definition, the intuition/"why it works",
  and at least one — ideally two — fully WORKED examples with step-by-step
  reasoning (show the working, not just the answer).
- Add derivations/proofs where relevant, and note edge cases and exceptions.
- Include numeric values, units, and real-world applications.

STRUCTURE (use Markdown headings):
- "## Chapter Overview" — what this chapter is about and why it matters.
- "## Key Terms & Definitions" — a table of important terms.
- One "## <Concept>" section per major concept, each with:
  - definition + intuition
  - a diagram or table (see visual rules)
  - **Worked Example(s)** with full steps
  - "Common mistakes / exam tips" call-out (use a > blockquote)
- "## Formula / Quick-Reference Sheet" — a table of all formulas & rules.
- "## Solved Problems" — 3–6 harder, exam-style solved problems across the chapter.
- "## Practice Questions" — a handful WITHOUT answers for self-testing.
- "## Key Takeaways" — concise bullet summary.
- "## Common Misconceptions" — bullet list of traps students fall into.

FORMAT:
- Clean GitHub-flavoured Markdown. Bold key terms. Use blockquotes for tips.
- Do NOT wrap the whole answer in a code fence.
- Be thorough and long — prioritise completeness over brevity.

{_VISUAL_RULES}

--- CHAPTER TEXT ---
{trimmed}
--- END CHAPTER TEXT ---
"""


# --------------------------------------------------------------------------- #
# Question agent
# --------------------------------------------------------------------------- #
QUESTION_MAX_CONTEXT_CHARS = 18000

QUESTION_SYSTEM = (
    "You are an expert examiner creating high-quality exam questions for "
    "elite students. You always return valid JSON and never invent facts that "
    "contradict the provided study material."
)

QUESTION_TYPE_INSTRUCTIONS: dict[str, str] = {
    QuestionType.TRUE_FALSE.value: (
        "True/False statements. 'answer' must be exactly 'True' or 'False'. "
        "'options' must be empty. Include a one-line 'explanation'."
    ),
    QuestionType.MCQ.value: (
        "Multiple choice questions with exactly 4 plausible 'options'. "
        "'answer' must be the full text of the correct option (matching one of the options exactly). "
        "Include a short 'explanation'."
    ),
    QuestionType.FILL_BLANK.value: (
        "Fill-in-the-blank statements using '______' to mark the blank in the 'question'. "
        "'answer' is the missing word/phrase. 'options' empty."
    ),
    QuestionType.ONE_WORD.value: (
        "Very short one-word (or a very short phrase) answer questions. "
        "'answer' is a single word or short phrase. 'options' empty."
    ),
    QuestionType.SHORT_ANSWER.value: (
        "Short-answer questions answerable in 2-4 sentences. Provide a concise model 'answer'. "
        "'options' empty."
    ),
    QuestionType.LONG_ANSWER.value: (
        "Long-answer / essay questions. Provide a detailed, well-structured model 'answer' "
        "(a few paragraphs). 'options' empty."
    ),
    QuestionType.CASE_BASED.value: (
        "Case-based questions: give a short real-world scenario/case in the 'question', followed by "
        "the actual question about it. Provide a thorough model 'answer'. 'options' empty."
    ),
}


def build_questions_prompt(
    *, class_name: str, subject: str, chapter_name: str, qtype: str,
    count: int, difficulty: str, context: str,
) -> str:
    instruction = QUESTION_TYPE_INSTRUCTIONS[qtype]
    return f"""Based ONLY on the study material below, create {count} {qtype} question(s).

Class: {class_name} | Subject: {subject} | Chapter: {chapter_name}
Target difficulty: {difficulty}

Type-specific rules: {instruction}

Return JSON of the exact shape:
{{
  "questions": [
    {{
      "question": "...",
      "answer": "...",
      "options": ["...", "..."],
      "explanation": "...",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

--- STUDY MATERIAL ---
{context}
--- END STUDY MATERIAL ---
"""


# --------------------------------------------------------------------------- #
# Verifier agent
# --------------------------------------------------------------------------- #
VERIFY_MAX_CONTEXT_CHARS = 16000

VERIFY_SYSTEM = (
    "You are a meticulous answer-verification expert. You check whether a "
    "question's given answer is correct and consistent with the study material, "
    "and you fix it when it is wrong. You always return valid JSON."
)


def build_verify_batch_prompt(*, subject: str, chapter_name: str, items: str, context: str) -> str:
    return f"""Verify a batch of questions and their given answers against the study material.

Subject: {subject} | Chapter: {chapter_name}

For EACH item: decide if the given answer is correct and well-formed for its type.
If correct, keep it. If wrong/incomplete/inconsistent with the material, provide the
corrected answer. For MCQ, ensure the answer exactly matches one of the options (fix
options if needed). If the material can't confirm it, mark it for review.

Items (JSON):
{items}

Return JSON of the exact shape (one result per item, echoing its id):
{{
  "results": [
    {{
      "id": <item id>,
      "status": "verified" | "corrected" | "needs_review",
      "answer": "<final answer>",
      "options": ["..."],
      "explanation": "<clear justification>",
      "note": "<what you checked or changed, one or two sentences>"
    }}
  ]
}}

--- STUDY MATERIAL ---
{context}
--- END STUDY MATERIAL ---
"""


def build_verify_prompt(*, subject: str, chapter_name: str, q: dict, context: str) -> str:
    options_text = "\n".join(f"- {o}" for o in q.get("options", [])) or "(none)"
    return f"""Verify the following {q.get('qtype')} question and its answer against the study material.

Subject: {subject} | Chapter: {chapter_name}

QUESTION:
{q.get('question')}

OPTIONS:
{options_text}

GIVEN ANSWER:
{q.get('answer')}

Tasks:
1. Decide if the given answer is correct and well-formed for this question type.
2. If it is correct, keep it. If it is wrong, incomplete, or inconsistent with the
   material, provide the corrected answer.
3. For MCQ, ensure the answer exactly matches one of the options; fix options if needed.
4. If the material does not contain enough information to confirm, mark it for review.

Return JSON:
{{
  "status": "verified" | "corrected" | "needs_review",
  "answer": "<final answer>",
  "options": ["..."],
  "explanation": "<clear justification of the correct answer>",
  "note": "<what you checked or changed, one or two sentences>"
}}

--- STUDY MATERIAL ---
{context}
--- END STUDY MATERIAL ---
"""


# --------------------------------------------------------------------------- #
# Diagram agent
# --------------------------------------------------------------------------- #
DIAGRAM_SYSTEM = (
    "You are an expert scientific/technical illustrator who draws detailed, "
    "textbook-quality diagrams as clean, self-contained SVG. You output ONLY the "
    "SVG markup — no explanation, no code fences."
)

_DIAGRAM_DETAIL_RULES = """
Draw a DETAILED, textbook-quality diagram as a single self-contained <svg>.

Quality bar (make it genuinely detailed, not a rough sketch):
- Canvas: use viewBox with a generous size (about 640x460 for scenes, adjust to
  fit). Set width="100%" style="max-width:640px;height:auto". Match the viewBox
  to the actual content — no large empty margins.
- A clear title <text> at the top (bold, ~18px).
- Draw the real structure with multiple parts/layers, correct proportions and
  arrangement — not a few plain rectangles. Use paths, circles, ellipses,
  polygons, lines and arcs as the subject needs.
- LABEL every important part with <text>, using thin leader lines/arrows
  (define an arrowhead <marker> in <defs> and reuse it) pointing from the label
  to the part. Keep labels from overlapping.
- Use subtle depth: <linearGradient>/<radialGradient> fills in <defs>, light
  strokes, and a soft color palette that reads on white
  (#1f2937 for text/outlines; accents like #4f46e5, #059669, #dc2626, #d97706,
  #0891b2). Avoid pure primary colors.
- Add helpful annotations where relevant: arrows for direction/flow/force,
  dashed guide lines, angle marks, a small scale or legend, axis ticks with
  values for graphs, +/- charges, etc.
- Keep text >= 11px so it stays readable. Never use external images or fonts.
- NEVER include <script> or event handlers.

Output ONLY the <svg>...</svg> markup.
"""


def build_diagram_prompt(
    *, description: str, class_name: str, subject: str, chapter_name: str
) -> str:
    return f"""Subject: {subject} | Class: {class_name} | Chapter: {chapter_name}

Draw this diagram:
{description.strip()}

{_DIAGRAM_DETAIL_RULES}
"""


# --------------------------------------------------------------------------- #
# Assessment: test generation
# --------------------------------------------------------------------------- #
ASSESSMENT_MAX_CONTEXT_CHARS = 16000

ASSESSMENT_GEN_SYSTEM = (
    "You are an expert examiner who designs fair, well-spread tests that reveal "
    "exactly what a student does and does not understand. You always return valid JSON."
)


def build_assessment_prompt(
    *, class_name: str, subject: str, topic: str, qtype: str,
    count: int, difficulty: str, context: str,
) -> str:
    instruction = QUESTION_TYPE_INSTRUCTIONS[qtype]
    grounding = (
        f"Base the questions on this study material:\n---\n{context}\n---\n"
        if context.strip()
        else "Base the questions on the standard curriculum for this class/subject/topic.\n"
    )
    return f"""Create {count} {qtype} exam question(s) to assess a student.

Class: {class_name} | Subject: {subject} | Topic: {topic}
Target difficulty: {difficulty}

Type-specific rules: {instruction}

Also tag EACH question with a short "concept" (the specific sub-topic it tests,
2-4 words) so the student's weak areas can be identified. Spread the questions
across different concepts of the topic.

{grounding}
Return JSON of the exact shape:
{{
  "questions": [
    {{
      "question": "...",
      "answer": "<the correct/model answer>",
      "options": ["...", "..."],
      "explanation": "<why this is correct>",
      "concept": "<sub-topic tested>",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}
"""


# --------------------------------------------------------------------------- #
# Assessment: grading (subjective answers)
# --------------------------------------------------------------------------- #
GRADING_SYSTEM = (
    "You are a fair, encouraging examiner grading a student's answers. You award "
    "partial credit where deserved, judge meaning over exact wording, and give "
    "specific, constructive feedback. You always return valid JSON."
)


def build_grading_prompt(*, subject: str, topic: str, items: str) -> str:
    return f"""Grade the following student answers for a {subject} test on "{topic}".

For each item, compare the student's answer to the correct/model answer and award
points from 0 to max_points (partial credit allowed, may be fractional). Judge by
meaning and key points, not exact wording. Mark is_correct true only if it earns
full or near-full marks. Give one or two sentences of specific feedback.

Items (JSON):
{items}

Return JSON of the exact shape:
{{
  "gradings": [
    {{"id": <question id>, "awarded": <number>, "is_correct": <bool>, "feedback": "..."}}
  ]
}}
"""


# --------------------------------------------------------------------------- #
# Assessment: overall feedback narrative
# --------------------------------------------------------------------------- #
FEEDBACK_SYSTEM = (
    "You are a supportive tutor writing a short, motivating performance report "
    "that tells a student exactly where to focus. You always return valid JSON."
)


def build_feedback_prompt(
    *, subject: str, topic: str, score_pct: float, breakdown: str
) -> str:
    return f"""A student took a {subject} test on "{topic}" and scored {score_pct:.0f}%.

Here is their per-concept performance (JSON):
{breakdown}

Write a concise performance report. Return JSON of the exact shape:
{{
  "summary": "<2-4 sentences: overall performance, tone encouraging but honest>",
  "recommendations": [
    "<specific, actionable study tip focused on the weakest concepts>",
    "..."
  ]
}}
Give 3-5 recommendations, prioritising the concepts with the lowest scores.
"""
