"""Observability: metrics endpoint, LLM metric recording, and correlation ids."""
from __future__ import annotations

from app.core import metrics


def test_metrics_endpoint_exposes_prometheus_text(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    # Metric families we always define should be present.
    assert "llm_calls_total" in body
    assert "http_requests_total" in body
    assert "chapters_by_status" in body
    assert "estimated_spend_usd" in body


def test_requests_get_a_correlation_id_header(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID")


def test_inbound_correlation_id_is_reused(client):
    resp = client.get("/api/health", headers={"X-Request-ID": "trace-abc123"})
    assert resp.headers.get("X-Request-ID") == "trace-abc123"


def test_record_llm_call_increments_counters():
    before = metrics.llm_calls.labels(op="unit_test", model="m", outcome="success")._value.get()
    metrics.record_llm_call(
        "unit_test", "m", latency_s=0.01, retries=2, rate_limited=True, outcome="success"
    )
    after = metrics.llm_calls.labels(op="unit_test", model="m", outcome="success")._value.get()
    assert after == before + 1
    assert metrics.llm_retries.labels(op="unit_test")._value.get() >= 2
    assert metrics.llm_rate_limited.labels(op="unit_test")._value.get() >= 1


def test_record_tokens_and_web_search():
    tin_before = metrics.llm_tokens.labels(direction="input")._value.get()
    metrics.record_tokens(100, 50, 0.5)
    assert metrics.llm_tokens.labels(direction="input")._value.get() == tin_before + 100
    assert metrics.llm_tokens.labels(direction="output")._value.get() >= 50

    metrics.record_web_search("web_search", forced=True)
    assert metrics.llm_web_search.labels(tool="web_search", forced="true")._value.get() >= 1
    metrics.record_web_search_disabled()
    assert metrics.llm_web_search_disabled._value.get() >= 1
