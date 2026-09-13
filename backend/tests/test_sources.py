from app.schemas import ChapterDetail

_BASE = dict(
    id=1,
    class_name="10",
    subject="Bio",
    chapter_name="Cells",
    source_filename="",
    notes="",
    notes_status="ready",
)


def test_sources_parsed_from_json_string():
    detail = ChapterDetail(**_BASE, sources='[{"url": "https://x.com", "title": "X"}]')
    assert len(detail.sources) == 1
    assert detail.sources[0].url == "https://x.com"
    assert detail.sources[0].title == "X"


def test_sources_empty_string_becomes_empty_list():
    detail = ChapterDetail(**_BASE, sources="")
    assert detail.sources == []


def test_sources_invalid_json_is_tolerated():
    detail = ChapterDetail(**_BASE, sources="not json")
    assert detail.sources == []
