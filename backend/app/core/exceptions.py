"""Domain exceptions and their FastAPI handlers.

Keeping HTTP translation in one place lets services and agents raise meaningful,
transport-agnostic errors instead of ``HTTPException`` everywhere.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for expected, translatable application errors."""

    status_code: int = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    status_code = 400


class AgentError(AppError):
    """The LLM is misconfigured or a model call failed."""

    status_code = 502


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        # Log every domain error so the log file shows what was rejected and why:
        # 5xx (misconfig / upstream) at error, 4xx (bad input) at info.
        log = logger.error if exc.status_code >= 500 else logger.info
        log("%s (%d) on %s %s: %s", type(exc).__name__, exc.status_code,
            request.method, request.url.path, exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Catch-all so unexpected bugs land in the log file with a full traceback
        # instead of only in uvicorn's own (non-propagating) logger.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {type(exc).__name__}: {exc}"},
        )
