"""normalize_mermaid_typography repairs Mermaid fences without touching prose."""
from app.utils.markdown import normalize_mermaid_typography

_MD = (
    "Intro prose — keep this em dash and “curly” quotes.\n\n"
    "```mermaid\n"
    "flowchart LR\n"
    "  A ––> B\n"          # en-dash arrow
    "  B ——> C[“Hi”]\n"  # em-dash arrow + curly quotes
    "  C  --> D\n"             # non-breaking space
    "```\n\n"
    "Outro – en dash stays.\n"
)


def test_fixes_typography_inside_mermaid_fence():
    out = normalize_mermaid_typography(_MD)
    assert "A --> B" in out
    assert "B --> C" in out
    assert 'C["Hi"]' in out
    assert "C  --> D" in out or "C --> D" in out


def test_leaves_prose_typography_untouched():
    out = normalize_mermaid_typography(_MD)
    assert "Intro prose — keep this em dash and “curly” quotes." in out
    assert "Outro – en dash stays." in out


def test_no_mermaid_is_a_noop():
    md = "Just prose with an en–dash and “quotes”."
    assert normalize_mermaid_typography(md) == md


def test_empty_input():
    assert normalize_mermaid_typography("") == ""
