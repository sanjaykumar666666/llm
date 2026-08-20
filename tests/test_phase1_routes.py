"""
Phase 1: FastAPI Route Integration Tests for Multimodal Input Layer.
Verifies all 4 analysis endpoints: /analyze/text, /analyze/image, /analyze/video, /analyze/youtube.
"""

import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


# ── HEALTH CHECK TEST ────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ── TEXT ANALYSIS ROUTE TESTS ────────────────────────────────────────────────

def test_route_text_valid():
    response = client.post(
        "/api/v1/analyze/text",
        json={"text": "Contact john.doe@example.com or call +1 555-123-4567 for support."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "standardized_input" in data
    assert data["standardized_input"]["validation_status"] == "VALID"
    assert data["standardized_input"]["modality"] == "text"
    assert "risk_score" in data
    assert "decision" in data


def test_route_text_invalid_empty():
    response = client.post(
        "/api/v1/analyze/text",
        json={"text": "   "}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "error"
    assert data.get("validation_status") == "INVALID"
    assert len(data.get("validation_errors", [])) > 0


# ── IMAGE ANALYSIS ROUTE TESTS ───────────────────────────────────────────────

def test_route_image_valid():
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color=(73, 109, 137))
    img.save(buf, format="PNG")
    valid_png_bytes = buf.getvalue()

    response = client.post(
        "/api/v1/analyze/image",
        files={"file": ("test_doc.png", io.BytesIO(valid_png_bytes), "image/png")},
        data={"protection_mode": "BLUR_ALL"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "standardized_input" in data
    assert data["standardized_input"]["validation_status"] == "VALID"
    assert data["standardized_input"]["file_name"] == "test_doc.png"


def test_route_image_invalid_extension():
    response = client.post(
        "/api/v1/analyze/image",
        files={"file": ("malicious.exe", io.BytesIO(b"MZ123"), "application/octet-stream")},
        data={"protection_mode": "BLUR_ALL"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "error"
    assert data.get("validation_status") == "INVALID"
    assert any("Unsupported image format" in err for err in data.get("validation_errors", []))


# ── VIDEO ANALYSIS ROUTE TESTS ───────────────────────────────────────────────

def test_route_video_invalid_extension():
    response = client.post(
        "/api/v1/analyze/video",
        files={"file": ("document.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "error"
    assert data.get("validation_status") == "INVALID"
    assert any("Unsupported video format" in err for err in data.get("validation_errors", []))


# ── YOUTUBE ANALYSIS ROUTE TESTS ─────────────────────────────────────────────

def test_route_youtube_valid_url():
    response = client.post(
        "/api/v1/analyze/youtube",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "standardized_input" in data
    assert data["standardized_input"]["validation_status"] == "VALID"
    assert data["youtube_video_id"] == "dQw4w9WgXcQ"
    assert data["is_mock"] is False


def test_route_youtube_invalid_url():
    response = client.post(
        "/api/v1/analyze/youtube",
        json={"youtube_url": "https://notyoutube.com/something"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "error"
    assert data.get("validation_status") == "INVALID"
    assert any("Invalid YouTube URL format" in err for err in data.get("validation_errors", []))
