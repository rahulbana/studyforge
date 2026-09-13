"""DEEP_SEARCH controls the web_search context size."""
from app.agents.llm import LLMClient
from app.core.config import Settings


class FakeResp:
    output_text = "notes"

    def model_dump(self):
        return {"output": []}


class FakeResponses:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeResp()


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def _client_with(deep: bool) -> tuple[LLMClient, FakeClient]:
    settings = Settings(openai_api_key="sk-test", enable_web_search=True, deep_search=deep)
    llm = LLMClient(settings)
    fake = FakeClient()
    llm._client = fake  # bypass real OpenAI construction
    return llm, fake


def _tool(fake):
    return fake.responses.last_kwargs["tools"][0]


def test_deep_search_uses_high_context():
    llm, fake = _client_with(deep=True)
    llm.respond_with_search("prompt")
    tool = _tool(fake)
    assert tool["type"] == "web_search"
    assert tool["search_context_size"] == "high"


def test_shallow_search_uses_medium_context():
    llm, fake = _client_with(deep=False)
    llm.respond_with_search("prompt")
    assert _tool(fake)["search_context_size"] == "medium"


def test_per_call_override_wins():
    llm, fake = _client_with(deep=False)
    llm.respond_with_search("prompt", deep=True)
    assert _tool(fake)["search_context_size"] == "high"


def test_web_search_is_forced():
    # The first (successful) attempt must force the tool call.
    llm, fake = _client_with(deep=False)
    llm.respond_with_search("prompt")
    assert fake.responses.last_kwargs.get("tool_choice") == "required"

