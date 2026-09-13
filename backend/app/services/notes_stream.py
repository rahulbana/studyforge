"""In-process registry of live notes-generation streams.

Generation runs in a background thread and appends text chunks to a NotesStream;
SSE requests tail that buffer. Because generation is decoupled from the HTTP
connection, it completes and persists even if the browser disconnects, and a
second connection (e.g. React StrictMode) subscribes to the same stream instead
of starting a duplicate run.
"""
from __future__ import annotations

import threading
from collections.abc import Callable

from ..core.logging import get_logger

logger = get_logger(__name__)


class NotesStream:
    def __init__(self) -> None:
        self.chunks: list[str] = []
        self.done: bool = False
        self.error: str | None = None

    def push(self, text: str) -> None:
        if text:
            self.chunks.append(text)

    def finish(self) -> None:
        self.done = True

    def fail(self, message: str) -> None:
        self.error = message
        self.done = True


_streams: dict[int, NotesStream] = {}
_lock = threading.Lock()


def get_or_start(chapter_id: int, runner: Callable[[NotesStream], None]) -> NotesStream:
    """Return the active stream for a chapter, or start one running ``runner``."""
    with _lock:
        existing = _streams.get(chapter_id)
        if existing and not existing.done:
            return existing
        stream = NotesStream()
        _streams[chapter_id] = stream

    def _run() -> None:
        try:
            runner(stream)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Notes stream runner crashed for chapter %s", chapter_id)
            stream.fail(str(exc))
        finally:
            if not stream.done:
                stream.finish()

    threading.Thread(target=_run, daemon=True).start()
    return stream
