"""OpenAI client wrapper with retries and three call shapes.

Capabilities:
  * ``respond_with_search`` — free-form generation that may browse the web via
    the Responses API ``web_search`` tool (falls back to no-tools if unavailable).
  * ``complete_json`` — structured JSON via Chat Completions (json_object mode).
  * ``complete_text`` — plain-text Chat Completion.

All calls retry transient errors with exponential backoff and translate failures
into :class:`AgentError` so the API layer can return a clean 502.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

from ..core import metrics
from ..core.config import Settings, get_settings
from ..core.exceptions import AgentError
from ..core.logging import get_logger

logger = get_logger(__name__)

_TRANSIENT_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)


@dataclass
class ResearchResult:
    """Text plus the web sources (citations) the model used to produce it."""

    text: str
    sources: list[dict] = field(default_factory=list)


def _collect_citations(node: Any, sources: list[dict], seen: set[str]) -> None:
    """Recursively find url_citation entries anywhere in a (dict/list) tree."""
    if isinstance(node, dict):
        if node.get("type") == "url_citation":
            url = node.get("url") or node.get("href")
            if url and url not in seen:
                seen.add(url)
                sources.append({"url": url, "title": node.get("title") or url})
        for value in node.values():
            _collect_citations(value, sources, seen)
    elif isinstance(node, list):
        for value in node:
            _collect_citations(value, sources, seen)


def _extract_sources(resp: Any) -> list[dict]:
    """Pull unique {url, title} web citations from a Responses API result.

    The exact nesting of url_citation annotations varies across SDK/model
    versions, so we walk the whole serialised response defensively.
    """
    sources: list[dict] = []
    seen: set[str] = set()
    try:
        data = resp.model_dump() if hasattr(resp, "model_dump") else resp
    except Exception:  # noqa: BLE001
        data = None
    if data is not None:
        _collect_citations(data, sources, seen)
    logger.info("Captured %d web source(s) from the notes research call", len(sources))
    return sources


def estimate_cost(usage: dict, settings: Settings | None = None) -> float:
    """USD cost for a token-usage dict, using configured per-1M prices."""
    s = settings or get_settings()
    inp = usage.get("input_tokens", 0)
    out = usage.get("output_tokens", 0)
    cost = inp / 1_000_000 * s.price_input_per_1m + out / 1_000_000 * s.price_output_per_1m
    return round(cost, 6)


class LLMClient:
    """Thin, retrying wrapper around the OpenAI SDK.

    Tracks cumulative token usage across all calls made through this instance,
    so a caller can create one client per operation and read the totals after.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: OpenAI | None = None
        self.usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

    @property
    def model(self) -> str:
        return self._settings.openai_model

    @property
    def cost_usd(self) -> float:
        return estimate_cost(self.usage, self._settings)

    def _add_usage(self, resp: Any) -> None:
        u = getattr(resp, "usage", None)
        if not u:
            return
        inp = getattr(u, "input_tokens", None)
        if inp is None:
            inp = getattr(u, "prompt_tokens", 0) or 0
        out = getattr(u, "output_tokens", None)
        if out is None:
            out = getattr(u, "completion_tokens", 0) or 0
        inp, out = int(inp), int(out)
        self.usage["input_tokens"] += inp
        self.usage["output_tokens"] += out
        metrics.record_tokens(
            inp, out, estimate_cost({"input_tokens": inp, "output_tokens": out}, self._settings)
        )

    # --- internals -------------------------------------------------------
    def _client_or_raise(self) -> OpenAI:
        # An injected client (tests) is used as-is; the key only gates lazy
        # construction of a real client.
        if self._client is not None:
            return self._client
        if not self._settings.has_openai_key:
            raise AgentError(
                "OPENAI_API_KEY is not set. Add it to backend/.env before generating content."
            )
        self._client = OpenAI(api_key=self._settings.openai_api_key)
        return self._client

    def _call(self, fn: Callable[[], Any], what: str, *, op: str = "llm") -> Any:
        attempts = max(1, self._settings.openai_max_retries)
        delay = 1.0
        last_exc: Exception | None = None
        started = time.monotonic()
        retries = 0
        rate_limited = False
        for attempt in range(1, attempts + 1):
            try:
                result = fn()
                metrics.record_llm_call(
                    op, self.model, latency_s=time.monotonic() - started,
                    retries=retries, rate_limited=rate_limited, outcome="success",
                )
                return result
            except (AuthenticationError, PermissionDeniedError) as exc:
                # A bad/placeholder/unauthorized key never succeeds on retry —
                # fail fast with an actionable message.
                metrics.record_llm_call(
                    op, self.model, latency_s=time.monotonic() - started,
                    retries=retries, rate_limited=rate_limited, outcome="error",
                )
                raise AgentError(
                    "OpenAI rejected the API key (check OPENAI_API_KEY in "
                    "backend/.env — setup.sh resets it to a placeholder on each run)."
                ) from exc
            except RateLimitError as exc:
                # Out-of-quota is not transient; retrying just wastes time.
                if "insufficient_quota" in str(exc):
                    metrics.record_llm_call(
                        op, self.model, latency_s=time.monotonic() - started,
                        retries=retries, rate_limited=True, outcome="error",
                    )
                    raise AgentError(
                        "OpenAI quota exceeded for this API key (check your plan and "
                        "billing at platform.openai.com)."
                    ) from exc
                last_exc = exc
                retries += 1
                rate_limited = True
                logger.warning(
                    "Transient OpenAI error on %s (attempt %d/%d): %s",
                    what, attempt, attempts, exc,
                )
                if attempt < attempts:
                    time.sleep(delay)
                    delay *= 2
            except _TRANSIENT_ERRORS as exc:
                last_exc = exc
                retries += 1
                rate_limited = rate_limited or isinstance(exc, RateLimitError)
                logger.warning(
                    "Transient OpenAI error on %s (attempt %d/%d): %s",
                    what, attempt, attempts, exc,
                )
                if attempt < attempts:
                    time.sleep(delay)
                    delay *= 2
            except Exception as exc:  # non-transient -> fail fast
                metrics.record_llm_call(
                    op, self.model, latency_s=time.monotonic() - started,
                    retries=retries, rate_limited=rate_limited, outcome="error",
                )
                raise AgentError(f"OpenAI request failed: {exc}") from exc
        metrics.record_llm_call(
            op, self.model, latency_s=time.monotonic() - started,
            retries=retries, rate_limited=rate_limited, outcome="error",
        )
        raise AgentError(f"OpenAI request failed after {attempts} attempts: {last_exc}")

    # --- public API ------------------------------------------------------
    def respond_with_search(
        self,
        prompt: str,
        *,
        system: str = "",
        use_web: bool | None = None,
        deep: bool | None = None,
        max_output_tokens: int = 8000,
    ) -> ResearchResult:
        client = self._client_or_raise()
        want_web = self._settings.enable_web_search if use_web is None else use_web
        is_deep = self._settings.deep_search if deep is None else deep
        context_size = "high" if is_deep else "medium"

        blocks: list[dict[str, Any]] = []
        if system:
            blocks.append({"role": "system", "content": system})
        blocks.append({"role": "user", "content": prompt})

        def _create(tool_type: str | None, force: bool = False):
            kwargs: dict[str, Any] = {
                "model": self.model,
                "input": blocks,
                "max_output_tokens": max_output_tokens,
            }
            if tool_type:
                tool: dict[str, Any] = {"type": tool_type}
                # search_context_size controls research depth; only the modern
                # "web_search" tool accepts it, so keep it off the preview tool.
                if tool_type == "web_search":
                    tool["search_context_size"] = context_size
                kwargs["tools"] = [tool]
                if force:
                    # Require the model to actually call the search tool.
                    kwargs["tool_choice"] = "required"
            return client.responses.create(**kwargs)

        resp = None
        used_web = False
        if want_web:
            # Try the modern tool forced, then unforced, then the legacy name.
            # (tool_choice/tool names vary across API versions; fall through safely.)
            attempts = [
                ("web_search", True),
                ("web_search", False),
                ("web_search_preview", False),
            ]
            for tool_type, force in attempts:
                label = f"responses.create ({tool_type}{', forced' if force else ''})"
                try:
                    resp = self._call(
                        lambda tt=tool_type, f=force: _create(tt, f),
                        label, op="respond_with_search",
                    )
                    used_web = True
                    metrics.record_web_search(tool_type, force)
                    logger.info(
                        "Notes generation used web search '%s' (depth=%s, forced=%s).",
                        tool_type, context_size, force,
                    )
                    break
                except AgentError as exc:
                    logger.warning("Web search attempt [%s] failed: %s", label, exc)
        if resp is None:
            resp = self._call(
                lambda: _create(None), "responses.create (no tools)", op="respond_with_search"
            )
            if want_web:
                metrics.record_web_search_disabled()
                logger.warning(
                    "Notes generated WITHOUT web search — no sources will be captured."
                )

        self._add_usage(resp)
        text = getattr(resp, "output_text", "") or ""
        if not text.strip():
            raise AgentError("The model returned an empty response.")
        sources = _extract_sources(resp) if used_web else []
        return ResearchResult(text=text.strip(), sources=sources)

    def stream_research(
        self,
        prompt: str,
        *,
        system: str = "",
        on_delta: Callable[[str], None],
        deep: bool | None = None,
        max_output_tokens: int = 8000,
    ) -> ResearchResult:
        """Stream a web-grounded response, invoking on_delta(text) as it arrives.

        Raises AgentError on failure so the caller can fall back to the
        non-streaming path.
        """
        client = self._client_or_raise()
        is_deep = self._settings.deep_search if deep is None else deep
        blocks: list[dict[str, Any]] = []
        if system:
            blocks.append({"role": "system", "content": system})
        blocks.append({"role": "user", "content": prompt})

        tool = {"type": "web_search", "search_context_size": "high" if is_deep else "medium"}
        started = time.monotonic()
        try:
            events = client.responses.create(
                model=self.model,
                input=blocks,
                max_output_tokens=max_output_tokens,
                tools=[tool],
                stream=True,
            )
            final = None
            parts: list[str] = []
            for event in events:
                etype = getattr(event, "type", "")
                if etype == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        parts.append(delta)
                        on_delta(delta)
                elif etype in ("response.completed", "response.incomplete"):
                    final = getattr(event, "response", None)
        except Exception as exc:  # noqa: BLE001
            metrics.record_llm_call(
                "stream_research", self.model, latency_s=time.monotonic() - started,
                retries=0, rate_limited=isinstance(exc, RateLimitError), outcome="error",
            )
            raise AgentError(f"Streaming request failed: {exc}") from exc

        metrics.record_llm_call(
            "stream_research", self.model, latency_s=time.monotonic() - started,
            retries=0, rate_limited=False, outcome="success",
        )
        metrics.record_web_search("web_search", forced=False)

        text = (getattr(final, "output_text", "") if final else "".join(parts)) or "".join(parts)
        if not text.strip():
            raise AgentError("The model returned an empty response.")
        if final is not None:
            self._add_usage(final)
        sources = _extract_sources(final) if final is not None else []
        return ResearchResult(text=text.strip(), sources=sources)

    def complete_json(self, system: str, user: str) -> Any:
        client = self._client_or_raise()
        resp = self._call(
            lambda: client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            ),
            "chat.completions (json)",
            op="complete_json",
        )
        self._add_usage(resp)
        content = resp.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise AgentError(f"Model returned invalid JSON: {exc}") from exc

    def complete_text(
        self, system: str, user: str, *, max_tokens: int = 4000, temperature: float = 0.5
    ) -> str:
        client = self._client_or_raise()
        resp = self._call(
            lambda: client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            ),
            "chat.completions (text)",
            op="complete_text",
        )
        self._add_usage(resp)
        return (resp.choices[0].message.content or "").strip()


_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    """Return a process-wide :class:`LLMClient` (lazily constructed)."""
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm
