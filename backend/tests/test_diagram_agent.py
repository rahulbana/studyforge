from app.agents.diagram_agent import enrich_with_diagrams
from app.core.exceptions import AgentError


class FakeLLM:
    """Stub LLMClient: returns an SVG unless the prompt says FAILME."""

    def __init__(self):
        self.calls = 0

    def complete_text(self, system, user, **kw):
        self.calls += 1
        if "FAILME" in user:
            raise AgentError("boom")
        return '<svg viewBox="0 0 640 460"><text>ok</text></svg>'


def test_placeholders_replaced_and_failures_dropped():
    llm = FakeLLM()
    notes = (
        "## Heart\nintro\n\n"
        "[[DIAGRAM: detailed heart cross-section]]\n\n"
        "more\n\n"
        "[[DIAGRAM: FAILME this errors]]\n\nend"
    )
    out = enrich_with_diagrams(notes, "10", "Bio", "Circulation", llm=llm)
    assert llm.calls == 2
    assert "<svg" in out
    assert "[[DIAGRAM" not in out


def test_max_diagrams_cap():
    llm = FakeLLM()
    notes = "\n".join(f"[[DIAGRAM: d{i}]]" for i in range(5))
    out = enrich_with_diagrams(notes, "10", "Bio", "C", max_diagrams=2, llm=llm)
    assert out.count("<svg") == 2
    assert llm.calls == 2
    assert "[[DIAGRAM" not in out


def test_no_placeholders_is_noop():
    llm = FakeLLM()
    notes = "## Just text\nno figures here"
    assert enrich_with_diagrams(notes, "10", "Bio", "C", llm=llm) == notes
    assert llm.calls == 0
