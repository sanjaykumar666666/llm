"""
Phase 1: Multimodal Input Validation & Normalization Test Suite.
Tests all four modalities: Text, Image, Video, YouTube URL.
Verifies valid inputs, invalid inputs, edge cases, and schema conformance.
"""

import pytest
import asyncio
import io
from pathlib import Path
from pipeline.input_handler import MultimodalInputHandler, StandardizedInput


class DummyUploadFile:
    """Mock UploadFile for async testing without running FastAPI server."""
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


@pytest.fixture
def input_handler():
    return MultimodalInputHandler()


# ── TEXT INPUT TESTS ─────────────────────────────────────────────────────────

def test_text_input_valid(input_handler):
    sample_text = "My Aadhaar number is 9918-4019-2011 and email is test@company.com"
    inp = input_handler.handle_text(sample_text)

    assert isinstance(inp, StandardizedInput)
    assert inp.is_valid() is True
    assert inp.validation_status == "VALID"
    assert inp.input_type == "text"
    assert inp.modality == "text"
    assert inp.content == sample_text
    assert inp.raw_text == sample_text
    assert inp.file_size_bytes == len(sample_text.encode("utf-8"))
    assert inp.content_type == "text/plain"
    assert inp.metadata["word_count"] > 0
    assert len(inp.validation_errors) == 0


def test_text_input_multiline(input_handler):
    multiline_text = "Line 1: Customer Record\nLine 2: Aadhaar: 1234-5678-9012\nLine 3: Phone: 9876543210"
    inp = input_handler.handle_text(multiline_text)

    assert inp.is_valid() is True
    assert inp.metadata["is_multiline"] is True
    assert inp.metadata["line_count"] == 3
    assert inp.content == multiline_text


def test_text_input_empty(input_handler):
    inp = input_handler.handle_text("")
    assert inp.is_valid() is False
    assert inp.validation_status == "INVALID"
    assert len(inp.validation_errors) > 0


def test_text_input_whitespace_only(input_handler):
    inp = input_handler.handle_text("   \n\t  ")
    assert inp.is_valid() is False
    assert inp.validation_status == "INVALID"
    assert "empty or contains only whitespace" in inp.validation_errors[0]


def test_text_input_oversized(input_handler, monkeypatch):
    monkeypatch.setattr(input_handler, "MAX_TEXT_LENGTH", 20)
    inp = input_handler.handle_text("This text is definitely longer than 20 characters.")
    assert inp.is_valid() is False
    assert inp.validation_status == "INVALID"
    assert "exceeds maximum length" in inp.validation_errors[0]


# ── IMAGE INPUT TESTS ────────────────────────────────────────────────────────

def test_image_input_valid(input_handler):
    async def _test():
        from PIL import Image
        buf = io.BytesIO()
        img = Image.new("RGB", (50, 50), color=(255, 0, 0))
        img.save(buf, format="PNG")
        dummy_png = buf.getvalue()

        file = DummyUploadFile(filename="scan_doc.png", content=dummy_png)

        inp = await input_handler.handle_image(file)

        assert isinstance(inp, StandardizedInput)
        assert inp.is_valid() is True
        assert inp.input_type == "image"
        assert inp.modality == "image"
        assert inp.file_name == "scan_doc.png"
        assert inp.file_extension == ".png"
        assert inp.file_size_bytes == len(dummy_png)
        assert inp.content_type == "image/png"
        assert inp.file_path is not None
        assert inp.file_path.exists()

        # Test cleanup
        MultimodalInputHandler.cleanup(inp)
        assert not inp.file_path.exists()

    asyncio.run(_test())


def test_image_input_invalid_extension(input_handler):
    async def _test():
        file = DummyUploadFile(filename="malicious.exe", content=b"MZ12345678")
        inp = await input_handler.handle_image(file)

        assert inp.is_valid() is False
        assert inp.validation_status == "INVALID"
        assert any("Unsupported image format" in err for err in inp.validation_errors)

    asyncio.run(_test())


def test_image_input_corrupted(input_handler):
    async def _test():
        # Valid PNG extension but corrupted binary payload
        corrupted_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20 + b"garbage_non_image_bytes"
        file = DummyUploadFile(filename="corrupted.png", content=corrupted_bytes)
        inp = await input_handler.handle_image(file)

        assert inp.is_valid() is False
        assert inp.validation_status == "INVALID"
        assert any("Corrupted or invalid image" in err for err in inp.validation_errors)

    asyncio.run(_test())


def test_image_input_empty(input_handler):
    async def _test():
        file = DummyUploadFile(filename="empty.jpg", content=b"")
        inp = await input_handler.handle_image(file)

        assert inp.is_valid() is False
        assert any("empty" in err for err in inp.validation_errors)

    asyncio.run(_test())


# ── VIDEO INPUT TESTS ────────────────────────────────────────────────────────

def test_video_input_valid(input_handler):
    async def _test():
        dummy_video_bytes = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free"
        file = DummyUploadFile(filename="sample_clip.mp4", content=dummy_video_bytes)

        inp = await input_handler.handle_video(file)

        assert isinstance(inp, StandardizedInput)
        assert inp.is_valid() is True
        assert inp.input_type == "video"
        assert inp.modality == "video"
        assert inp.file_name == "sample_clip.mp4"
        assert inp.file_extension == ".mp4"
        assert inp.content_type == "video/mp4"
        assert inp.file_path is not None
        assert inp.file_path.exists()

        # Cleanup
        MultimodalInputHandler.cleanup(inp)
        assert not inp.file_path.exists()

    asyncio.run(_test())


def test_video_input_invalid_extension(input_handler):
    async def _test():
        file = DummyUploadFile(filename="recording.pdf", content=b"%PDF-1.4")
        inp = await input_handler.handle_video(file)

        assert inp.is_valid() is False
        assert any("Unsupported video format" in err for err in inp.validation_errors)

    asyncio.run(_test())


def test_video_input_empty(input_handler):
    async def _test():
        file = DummyUploadFile(filename="empty_video.mp4", content=b"")
        inp = await input_handler.handle_video(file)

        assert inp.is_valid() is False
        assert any("empty" in err for err in inp.validation_errors)

    asyncio.run(_test())


# ── YOUTUBE INPUT TESTS ──────────────────────────────────────────────────────

def test_youtube_input_valid_standard(input_handler):
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    inp = input_handler.handle_youtube(url)

    assert inp.is_valid() is True
    assert inp.input_type == "youtube"
    assert inp.modality == "youtube"
    assert inp.youtube_video_id == "dQw4w9WgXcQ"
    assert inp.content_type == "text/url"
    assert inp.source == url


def test_youtube_input_valid_short_url(input_handler):
    url = "https://youtu.be/dQw4w9WgXcQ"
    inp = input_handler.handle_youtube(url)

    assert inp.is_valid() is True
    assert inp.youtube_video_id == "dQw4w9WgXcQ"


def test_youtube_input_valid_shorts(input_handler):
    url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    inp = input_handler.handle_youtube(url)

    assert inp.is_valid() is True
    assert inp.youtube_video_id == "dQw4w9WgXcQ"


def test_youtube_input_invalid_url(input_handler):
    url = "https://example.com/not-a-youtube-video"
    inp = input_handler.handle_youtube(url)

    assert inp.is_valid() is False
    assert any("Invalid YouTube URL format" in err for err in inp.validation_errors)


def test_youtube_input_empty(input_handler):
    inp = input_handler.handle_youtube("")
    assert inp.is_valid() is False
    assert any("empty" in err for err in inp.validation_errors)


# ── STANDARDIZED OBJECT SCHEMA CONFORMANCE ───────────────────────────────────

def test_standardized_object_canonical_schema(input_handler):
    inp = input_handler.handle_text("Sample input for schema check")
    canonical = inp.to_standard_dict()

    # Schema must match: { "input_type": ..., "source": ..., "file_path": ..., "metadata": ..., "content": ... }
    assert "input_type" in canonical
    assert canonical["input_type"] == "text"
    assert "source" in canonical
    assert "file_path" in canonical
    assert "metadata" in canonical
    assert "content" in canonical
    assert canonical["content"] == "Sample input for schema check"
    assert "validation_status" in canonical
    assert canonical["validation_status"] == "VALID"
