"""API routers, aggregated into a single router."""
from fastapi import APIRouter

from . import assessments, chapters, export, meta, metrics, questions

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(metrics.router)
api_router.include_router(chapters.router)
api_router.include_router(questions.router)
api_router.include_router(export.router)
api_router.include_router(assessments.router)

__all__ = ["api_router"]
