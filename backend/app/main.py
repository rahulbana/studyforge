"""FastAPI application factory."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import api_router
from .core import metrics
from .core.config import get_settings
from .core.context import new_request_id, set_request_id
from .core.exceptions import register_exception_handlers
from .core.logging import configure_logging
from .db.session import init_db

_REQUEST_ID_HEADER = "X-Request-ID"


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    yield


def _route_label(request: Request) -> str:
    """Low-cardinality path label: the route template, not the concrete URL."""
    route = request.scope.get("route")
    return getattr(route, "path", None) or "unmatched"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        # Reuse an inbound correlation id (e.g. from a proxy) or mint a new one.
        request_id = request.headers.get(_REQUEST_ID_HEADER) or new_request_id()
        set_request_id(request_id)
        started = time.monotonic()
        response = await call_next(request)
        label = _route_label(request)
        # Don't let the metrics scrape count itself.
        if label != "/metrics":
            elapsed = time.monotonic() - started
            metrics.http_requests.labels(
                method=request.method, path=label, status=str(response.status_code)
            ).inc()
            metrics.http_latency.labels(method=request.method, path=label).observe(elapsed)
        response.headers[_REQUEST_ID_HEADER] = request_id
        return response

    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
