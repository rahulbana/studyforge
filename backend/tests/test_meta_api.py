def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "model" in body


def test_question_types(client):
    resp = client.get("/api/question-types")
    assert resp.status_code == 200
    keys = {row["key"] for row in resp.json()}
    assert {"mcq", "true_false", "case_based"} <= keys


def test_upload_rejects_non_pdf(client):
    resp = client.post(
        "/api/chapters",
        data={"class_name": "10", "subject": "Bio", "chapter_name": "Cells"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_rejects_pdf_extension_without_magic(client):
    # A .pdf name but non-PDF content must be rejected (defends against spoofed
    # extensions).
    resp = client.post(
        "/api/chapters",
        data={"class_name": "10", "subject": "Bio", "chapter_name": "Cells"},
        files={"file": ("fake.pdf", b"not really a pdf", "application/pdf")},
    )
    assert resp.status_code == 400
    assert "does not look like a PDF" in resp.json().get("detail", "")


def test_upload_rejects_oversized_pdf(client):
    from app.core.config import get_settings

    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    oversized = b"%PDF-" + b"0" * (max_bytes + 1)
    resp = client.post(
        "/api/chapters",
        data={"class_name": "10", "subject": "Bio", "chapter_name": "Cells"},
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )
    assert resp.status_code == 400
    assert "too large" in resp.json().get("detail", "")
