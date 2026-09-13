"""Prometheus metrics endpoint (GET /metrics).

Exposed outside the ``/api`` prefix so a scraper hits it directly on the backend
(it is not proxied through the frontend). DB-derived gauges are refreshed from a
live snapshot on each scrape.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ...core import metrics
from ...core.config import get_settings
from ...core.logging import get_logger
from ...db.session import get_db
from ...services import metrics_service

router = APIRouter(tags=["meta"])
logger = get_logger(__name__)


@router.get("/metrics")
def prometheus_metrics(db: Session = Depends(get_db)) -> Response:
    if not get_settings().metrics_enabled:
        return Response(status_code=404)
    try:
        metrics_service.refresh_db_gauges(db)
    except Exception:  # noqa: BLE001 — never let a gauge refresh break scraping
        logger.exception("Failed to refresh DB gauges for /metrics")
    body, content_type = metrics.render()
    return Response(content=body, media_type=content_type)
