"""Chapter endpoints: upload, list, detail, notes (re)generation, stream, delete."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...models.enums import NotesStatus
from ...schemas import ChapterCreateMeta, ChapterDetail, ChapterSummary, StatusResponse
from ...services import chapter_service
from ..deps import get_db

router = APIRouter(prefix="/api/chapters", tags=["chapters"])

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _schedule_notes(background: BackgroundTasks, chapter_id: int) -> None:
    # When streaming is on, the frontend drives generation via the SSE endpoint;
    # otherwise generate in the background and let the UI poll.
    if not get_settings().stream_notes:
        background.add_task(chapter_service.run_notes_generation, chapter_id)


@router.post("", response_model=ChapterDetail)
async def upload_chapter(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    class_name: str = Form(...),
    subject: str = Form(...),
    chapter_name: str = Form(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    meta = ChapterCreateMeta(class_name=class_name, subject=subject, chapter_name=chapter_name)
    chapter = chapter_service.create_from_pdf(
        db, data=data, filename=file.filename or "", meta=meta
    )
    _schedule_notes(background, chapter.id)
    return chapter


@router.get("", response_model=list[ChapterSummary])
def list_chapters(db: Session = Depends(get_db)):
    return chapter_service.list_summaries(db)


@router.get("/{chapter_id}", response_model=ChapterDetail)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    return chapter_service.get_or_404(db, chapter_id)


@router.get("/{chapter_id}/notes/stream")
async def stream_notes(chapter_id: int, db: Session = Depends(get_db)):
    """Server-Sent Events: stream notes text live as it is generated."""
    chapter = chapter_service.get_or_404(db, chapter_id)

    if chapter.notes_status == NotesStatus.READY.value:
        notes = chapter.notes

        async def ready_gen():
            yield _sse("chunk", {"text": notes})
            yield _sse("done", {})

        return StreamingResponse(ready_gen(), media_type="text/event-stream", headers=_SSE_HEADERS)

    stream = chapter_service.start_notes_stream(chapter_id)

    async def event_gen():
        idx = 0
        while True:
            while idx < len(stream.chunks):
                yield _sse("chunk", {"text": stream.chunks[idx]})
                idx += 1
            if stream.error:
                yield _sse("error", {"detail": stream.error})
                return
            if stream.done:
                yield _sse("done", {})
                return
            await asyncio.sleep(0.25)

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/{chapter_id}/notes/regenerate", response_model=ChapterDetail)
def regenerate_notes(
    chapter_id: int, background: BackgroundTasks, db: Session = Depends(get_db)
):
    chapter = chapter_service.get_or_404(db, chapter_id)
    chapter = chapter_service.mark_notes_pending(db, chapter)
    _schedule_notes(background, chapter.id)
    return chapter


@router.delete("/{chapter_id}", response_model=StatusResponse)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = chapter_service.get_or_404(db, chapter_id)
    chapter_service.delete(db, chapter)
    return StatusResponse(ok=True, message="deleted")
