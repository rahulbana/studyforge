"""Request/job correlation id, carried via a context variable.

The id is set per HTTP request (middleware) and per background job/thread, then
injected into every log record so a single operation's whole lifecycle can be
traced — including work that runs in a threadpool or the SSE streaming thread,
which each open their own DB session.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def new_request_id() -> str:
    """A short, unique id suitable for correlating one operation's logs."""
    return uuid.uuid4().hex[:12]


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()


@contextmanager
def bind_request_id(value: str) -> Iterator[str]:
    """Bind ``value`` as the correlation id for the duration of the block.

    Restores the previous id on exit; safe for background jobs and threads
    (``contextvars`` are per-thread when set inside the thread).
    """
    token = _request_id.set(value)
    try:
        yield value
    finally:
        _request_id.reset(token)
