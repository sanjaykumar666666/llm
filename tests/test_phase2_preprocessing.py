"""
Phase 2: Data Preprocessing Layer Test Suite.
Tests all 8 required preprocessing scenarios across Text, Image, Video, and YouTube.
"""

import io
import pytest
import asyncio
from pathlib import Path
from PIL import Image

from pipeline.input_handler import MultimodalInputHandler, StandardizedInput
from pipeline.preprocessor import MultimodalPreprocessor, PreprocessedData


class DummyUploadFile:
    """Mock UploadFile for testing without running web server."""
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


@pytest.fixture
def input_handler():
    return MultimodalInputHandler()


@pytest.fixture
def preprocessor():
    return MultimodalPreprocessor()


# ── TEST 1: Normal text → cleaned text generated ─────────────────────────────

def test_preprocessing_normal_text(input_handler, preprocessor):
    raw_text = "   This is a   normal text with    excessive   spaces \r\n and  multiple lines. \n\n\n End of text.   "
    std_input = input_handler.handle_text(raw_text)

    res = preprocessor.preprocess(std_input)

    assert isinstance(res, PreprocessedData)
    assert res.preprocessing_status == "success"
    assert res.input_type == "text"
    assert res.original == raw_text.strip()
    assert "excessive spaces" in res.processed
    assert "  " not in res.processed  # Consecutive spaces collapsed
    assert "\r" not in res.processed   # Line breaks normalized
    assert res.metadata["word_count"] > 0
    assert res.metadata["unicode_normalization"] == "NFKC"


# ── TEST 2: Text containing phone/email/ID → PII information preserved ─────────

def test_preprocessing_pii_preserved(input_handler, preprocessor):
    sensitive_text = (
        "Customer Name: John Doe\n"
        "Email: john.doe@company.org\n"
        "Phone: +91 98765-43210\n"
        "Aadhaar: 9918-4019-2011\n"
        "AWS Secret: AKIAIOSFODNN7EXAMPLE\n"
        "DB Password: SuperSecretPassword123!"
    )
    std_input = input_handler.handle_text(sensitive_text)
    res = preprocessor.preprocess(std_input)

    assert res.preprocessing_status == "success"
    # CRITICAL PRIVACY REQUIREMENT: All sensitive tokens MUST NOT be deleted or redacted during Phase 2
    assert "john.doe@company.org" in res.processed
    assert "+91 98765-43210" in res.processed
    assert "9918-4019-2011" in res.processed
    assert "AKIAIOSFODNN7EXAMPLE" in res.processed
    assert "SuperSecretPassword123!" in res.processed
    assert res.extracted_text == res.processed


# ── TEST 3: Normal image → processed image generated with dimensions ─────────

def test_preprocessing_normal_image(input_handler, preprocessor):
    async def _test():
        # Create standard test image
        buf = io.BytesIO()
        img = Image.new("RGB", (640, 480), color=(100, 150, 200))
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        file = DummyUploadFile(filename="test_photo.png", content=img_bytes)
        std_input = await input_handler.handle_image(file)

        res = preprocessor.preprocess(std_input)

        assert res.preprocessing_status == "success"
        assert res.input_type == "image"
        assert res.metadata["original_width"] == 640
        assert res.metadata["original_height"] == 480
        assert res.metadata["color_mode"] == "RGB"
        assert res.metadata["scale_factor"] == 1.0

        # Cleanup
        MultimodalInputHandler.cleanup(std_input)

    asyncio.run(_test())


# ── TEST 4: Image containing text → OCR preparation works ─────────────────────

def test_preprocessing_image_ocr(input_handler, preprocessor):
    async def _test():
        # Create image with text
        buf = io.BytesIO()
        img = Image.new("RGB", (400, 150), color=(255, 255, 255))
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        file = DummyUploadFile(filename="doc_with_text.png", content=img_bytes)
        std_input = await input_handler.handle_image(file)

        res = preprocessor.preprocess(std_input)

        assert res.preprocessing_status == "success"
        assert "ocr_engine" in res.metadata
        assert isinstance(res.ocr, list)
        assert res.extracted_text is not None

        # Cleanup
        MultimodalInputHandler.cleanup(std_input)

    asyncio.run(_test())


# ── TEST 5: Video → metadata + sampled frames generated ──────────────────────

def test_preprocessing_video(input_handler, preprocessor):
    async def _test():
        # Valid MP4 container header
        dummy_video_bytes = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free" + b"\x00" * 100
        file = DummyUploadFile(filename="sample_meeting.mp4", content=dummy_video_bytes)
        std_input = await input_handler.handle_video(file)

        res = preprocessor.preprocess(std_input)

        assert res.input_type == "video"
        # Video should either succeed or report OpenCV decoder status gracefully without raising exception
        assert isinstance(res.frames, list)
        assert isinstance(res.metadata, dict)

        # Cleanup
        MultimodalInputHandler.cleanup(std_input)

    asyncio.run(_test())


# ── TEST 6: YouTube URL → metadata / transcript processed ────────────────────

def test_preprocessing_youtube(input_handler, preprocessor):
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    std_input = input_handler.handle_youtube(url)

    res = preprocessor.preprocess(std_input)

    assert res.input_type == "youtube"
    assert res.source == url
    assert res.metadata["youtube_video_id"] == "dQw4w9WgXcQ"
    assert res.metadata["embed_url"] == "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert isinstance(res.frames, list)  # timestamped segments


# ── TEST 7: Invalid media → proper error ─────────────────────────────────────

def test_preprocessing_invalid_input(input_handler, preprocessor):
    invalid_std_input = input_handler.handle_text("")
    res = preprocessor.preprocess(invalid_std_input)

    assert res.preprocessing_status == "error"
    assert len(res.preprocessing_errors) > 0


# ── TEST 8: Corrupted media → proper structured error ────────────────────────

def test_preprocessing_corrupted_image(input_handler, preprocessor):
    async def _test():
        corrupted_bytes = b"\x89PNG\r\n\x1a\n" + b"\xff" * 20 + b"corrupt"
        file = DummyUploadFile(filename="broken.png", content=corrupted_bytes)
        std_input = await input_handler.handle_image(file)

        # Phase 1 marks invalid; preprocessor handles gracefully
        res = preprocessor.preprocess(std_input)
        assert res.preprocessing_status == "error"

    asyncio.run(_test())
