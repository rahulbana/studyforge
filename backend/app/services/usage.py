"""Accumulate an LLM client's token usage/cost onto a model row."""
from __future__ import annotations

from ..agents.llm import LLMClient, estimate_cost


def record_usage(obj, llm: LLMClient) -> None:
    """Add ``llm``'s cumulative usage to ``obj`` (Chapter or Assessment).

    ``obj`` must expose tokens_input / tokens_output / cost_usd. Costs accumulate,
    so repeated generations sum into the row's running total.
    """
    obj.tokens_input = (obj.tokens_input or 0) + llm.usage["input_tokens"]
    obj.tokens_output = (obj.tokens_output or 0) + llm.usage["output_tokens"]
    obj.cost_usd = estimate_cost(
        {"input_tokens": obj.tokens_input, "output_tokens": obj.tokens_output}
    )
