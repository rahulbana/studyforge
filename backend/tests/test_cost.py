from types import SimpleNamespace

from app.agents.llm import LLMClient, estimate_cost
from app.core.config import Settings


def test_estimate_cost_uses_configured_prices():
    settings = Settings(price_input_per_1m=2.5, price_output_per_1m=10.0)
    cost = estimate_cost({"input_tokens": 1_000_000, "output_tokens": 500_000}, settings)
    assert cost == round(2.5 + 5.0, 6)  # 7.5


def test_add_usage_handles_responses_and_chat_shapes():
    llm = LLMClient(Settings(openai_api_key="sk-test"))
    # Responses API shape
    llm._add_usage(SimpleNamespace(usage=SimpleNamespace(input_tokens=100, output_tokens=40)))
    # Chat Completions shape
    llm._add_usage(SimpleNamespace(usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5)))
    assert llm.usage == {"input_tokens": 110, "output_tokens": 45}
    assert llm.cost_usd == estimate_cost(llm.usage, llm._settings)


def test_add_usage_tolerates_missing_usage():
    llm = LLMClient(Settings(openai_api_key="sk-test"))
    llm._add_usage(SimpleNamespace())  # no usage attribute
    assert llm.usage == {"input_tokens": 0, "output_tokens": 0}
