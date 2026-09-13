"""Shared/utility schemas."""
from __future__ import annotations

from pydantic import BaseModel


class StatusResponse(BaseModel):
    ok: bool
    message: str = ""


class QuestionTypeInfo(BaseModel):
    key: str
    label: str
