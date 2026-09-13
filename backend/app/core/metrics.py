"""Prometheus metrics: definitions and record helpers.

This module holds the metric objects and thin ``record_*`` helpers only — it
never touches the database. HTTP metrics are recorded by middleware, LLM metrics
by :mod:`app.agents.llm`, and the DB-derived gauges are refreshed at scrape time
by :mod:`app.services.metrics_service`. Exposed via ``GET /metrics``.
"""
from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# A dedicated registry keeps our series isolated from any process-global default.
registry = CollectorRegistry()

# --- HTTP ----------------------------------------------------------------
http_requests = Counter(
    "http_requests_total",
    "HTTP requests handled.",
    labelnames=("method", "path", "status"),
    registry=registry,
)
http_latency = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
    registry=registry,
)

# --- LLM -----------------------------------------------------------------
llm_calls = Counter(
    "llm_calls_total",
    "LLM API calls, by operation and outcome.",
    labelnames=("op", "model", "outcome"),
    registry=registry,
)
llm_latency = Histogram(
    "llm_call_latency_seconds",
    "LLM call wall-clock latency in seconds (including retries).",
    labelnames=("op",),
    registry=registry,
)
llm_retries = Counter(
    "llm_retries_total",
    "LLM call retries (transient errors that were retried).",
    labelnames=("op",),
    registry=registry,
)
llm_rate_limited = Counter(
    "llm_rate_limited_total",
    "LLM calls that hit a rate limit (429) at least once.",
    labelnames=("op",),
    registry=registry,
)
llm_tokens = Counter(
    "llm_tokens_total",
    "LLM tokens consumed, by direction.",
    labelnames=("direction",),
    registry=registry,
)
llm_cost = Counter(
    "llm_cost_usd_total",
    "Estimated LLM spend in USD.",
    registry=registry,
)
llm_web_search = Counter(
    "llm_web_search_total",
    "Web-search tool usage while researching notes.",
    labelnames=("tool", "forced"),
    registry=registry,
)
llm_web_search_disabled = Counter(
    "llm_web_search_disabled_total",
    "Notes generated without web search despite it being requested (no sources).",
    registry=registry,
)

# --- DB-derived gauges (refreshed at scrape time) ------------------------
chapters_by_status = Gauge(
    "chapters_by_status",
    "Chapters by notes status.",
    labelnames=("status",),
    registry=registry,
)
generation_jobs_by_status = Gauge(
    "generation_jobs_by_status",
    "Question generation jobs by status.",
    labelnames=("status",),
    registry=registry,
)
assessments_by_status = Gauge(
    "assessments_by_status",
    "Assessments by status.",
    labelnames=("status",),
    registry=registry,
)
total_spend = Gauge(
    "estimated_spend_usd",
    "Cumulative estimated spend recorded on chapters + assessments.",
    registry=registry,
)


def record_llm_call(
    op: str,
    model: str,
    *,
    latency_s: float,
    retries: int,
    rate_limited: bool,
    outcome: str,
) -> None:
    """Record one LLM call's outcome, latency and retry behaviour."""
    llm_calls.labels(op=op, model=model, outcome=outcome).inc()
    llm_latency.labels(op=op).observe(latency_s)
    if retries:
        llm_retries.labels(op=op).inc(retries)
    if rate_limited:
        llm_rate_limited.labels(op=op).inc()


def record_tokens(input_tokens: int, output_tokens: int, cost_usd: float) -> None:
    if input_tokens:
        llm_tokens.labels(direction="input").inc(input_tokens)
    if output_tokens:
        llm_tokens.labels(direction="output").inc(output_tokens)
    if cost_usd:
        llm_cost.inc(cost_usd)


def record_web_search(tool: str, forced: bool) -> None:
    llm_web_search.labels(tool=tool, forced=str(forced).lower()).inc()


def record_web_search_disabled() -> None:
    llm_web_search_disabled.inc()


def render() -> tuple[bytes, str]:
    """Return (body, content_type) for the /metrics endpoint."""
    return generate_latest(registry), CONTENT_TYPE_LATEST
