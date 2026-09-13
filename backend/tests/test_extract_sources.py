from app.agents.llm import _extract_sources


class FakeResp:
    def __init__(self, data):
        self._data = data

    def model_dump(self):
        return self._data


def test_extracts_nested_url_citations():
    # Mirrors the Responses API shape: output -> message -> content -> annotations.
    resp = FakeResp(
        {
            "output": [
                {"type": "web_search_call", "action": {"query": "atmosphere layers"}},
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "…",
                            "annotations": [
                                {"type": "url_citation", "url": "https://a.com", "title": "A"},
                                {"type": "url_citation", "url": "https://b.com", "title": "B"},
                                {"type": "url_citation", "url": "https://a.com", "title": "dup"},
                            ],
                        }
                    ],
                },
            ]
        }
    )
    sources = _extract_sources(resp)
    urls = [s["url"] for s in sources]
    assert urls == ["https://a.com", "https://b.com"]  # order preserved, deduped
    assert sources[0]["title"] == "A"


def test_no_citations_returns_empty():
    assert _extract_sources(FakeResp({"output": [{"type": "message", "content": []}]})) == []
