"""
Phase 3: Feature & Semantic Extraction Layer Test Suite.
Tests all 8 required feature extraction scenarios across Text, Image, Video, and YouTube.
"""

import io
import pytest
import asyncio
from pathlib import Path
from PIL import Image

from pipeline.input_handler import MultimodalInputHandler, StandardizedInput
from pipeline.preprocessor import MultimodalPreprocessor, PreprocessedData
from pipeline.feature_extractor import MultimodalFeatureExtractor, ExtractedFeatures


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


@pytest.fixture
def feature_extractor():
    return MultimodalFeatureExtractor()


# ── TEST 1: Text → BERT semantic features generated ──────────────────────────

def test_text_bert_semantic_features(input_handler, preprocessor, feature_extractor):
    raw_text = "This is a confidential payload containing API keys sk_live_991823."
    std_input = input_handler.handle_text(raw_text)
    preprocessed = preprocessor.preprocess(std_input)

    features = feature_extractor.extract_features(preprocessed)

    assert isinstance(features, ExtractedFeatures)
    assert features.feature_status == "success"
    assert features.input_type == "text"
    assert "embedding_dim" in features.semantic_features
    assert features.semantic_features["embedding_dim"] == 768
    assert len(features.semantic_features["embedding_sample"]) > 0


# ── TEST 2: OCR text → semantic features generated ───────────────────────────

def test_ocr_text_semantic_features(feature_extractor):
    # PreprocessedData with OCR text simulating OCR output
    mock_preprocessed = PreprocessedData(
        input_type="image",
        source="scan.png",
        original="scan.png",
        extracted_text="Aadhaar Card No 9918-4019-2011 Name John Doe",
        ocr=[{"text": "Aadhaar", "bbox": [10, 10, 50, 20], "confidence": 0.95}],
        metadata={"original_width": 400, "original_height": 200},
        preprocessing_status="success",
    )

    features = feature_extractor.extract_features(mock_preprocessed)

    assert features.feature_status == "success"
    assert features.semantic_features["has_ocr_text"] is True
    assert features.semantic_features["ocr_embedding_dim"] == 768
    assert len(features.semantic_features["ocr_embedding_sample"]) > 0


# ── TEST 3: Image → visual features generated ────────────────────────────────

def test_image_visual_features(input_handler, preprocessor, feature_extractor):
    async def _test():
        buf = io.BytesIO()
        img = Image.new("RGB", (800, 600), color=(120, 140, 160))
        img.save(buf, format="PNG")

        file = DummyUploadFile(filename="test_visual.png", content=buf.getvalue())
        std_input = await input_handler.handle_image(file)
        preprocessed = preprocessor.preprocess(std_input)

        features = feature_extractor.extract_features(preprocessed)

        assert features.feature_status == "success"
        assert features.input_type == "image"
        assert features.visual_features["original_width"] == 800
        assert features.visual_features["original_height"] == 600
        assert features.visual_features["aspect_ratio"] == 1.333

        MultimodalInputHandler.cleanup(std_input)

    asyncio.run(_test())


# ── TEST 4: Video frame → visual features with frame/timestamp preserved ─────

def test_video_frame_features(feature_extractor):
    # Simulating PreprocessedData video output with sampled frames
    mock_preprocessed = PreprocessedData(
        input_type="video",
        source="meeting.mp4",
        extracted_text="[00:02] Security Overview\n[00:10] Database Password",
        frames=[
            {"frame_id": 1, "timestamp_sec": 2.0, "timestamp_str": "00:02", "extracted_text": "Security Overview"},
            {"frame_id": 2, "timestamp_sec": 10.0, "timestamp_str": "00:10", "extracted_text": "Database Password"},
        ],
        metadata={"duration_sec": 15.0, "duration_str": "00:15", "fps": 30.0, "total_frames": 450, "width": 1920, "height": 1080},
        preprocessing_status="success",
    )

    features = feature_extractor.extract_features(mock_preprocessed)

    assert features.feature_status == "success"
    assert features.input_type == "video"
    assert features.visual_features["duration_str"] == "00:15"
    assert len(features.visual_features["frame_level_features"]) == 2
    assert features.visual_features["frame_level_features"][0]["timestamp_str"] == "00:02"
    assert features.visual_features["frame_level_features"][1]["timestamp_str"] == "00:10"
    assert features.semantic_features["global_ocr_embedding_dim"] == 768


# ── TEST 5: YouTube transcript → chunk-level semantic features generated ──────

def test_youtube_chunk_semantic_features(feature_extractor):
    # Simulating PreprocessedData YouTube output with timestamped segments
    mock_preprocessed = PreprocessedData(
        input_type="youtube",
        source="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        extracted_text="Welcome to the cloud security briefing. Make sure not to expose API tokens sk_live_123.",
        frames=[
            {"timestamp_sec": 5.0, "timestamp_str": "00:05", "text": "Welcome to the cloud security briefing."},
            {"timestamp_sec": 15.0, "timestamp_str": "00:15", "text": "Make sure not to expose API tokens sk_live_123."},
        ],
        metadata={"youtube_video_id": "dQw4w9WgXcQ", "has_transcript": True},
        preprocessing_status="success",
    )

    features = feature_extractor.extract_features(mock_preprocessed)

    assert features.feature_status == "success"
    assert features.input_type == "youtube"
    assert features.semantic_features["has_transcript"] is True
    assert features.semantic_features["global_transcript_embedding_dim"] == 768
    assert len(features.semantic_features["segment_features"]) == 2
    assert features.semantic_features["segment_features"][0]["timestamp_str"] == "00:05"


# ── TEST 6: Long text → chunking works correctly ─────────────────────────────

def test_long_text_chunking(feature_extractor):
    long_text = " ".join([f"Word{i} sensitive token info" for i in range(150)])
    chunks = feature_extractor.chunk_text(long_text)

    assert len(chunks) > 1
    assert chunks[0]["chunk_id"] == 1
    assert chunks[1]["chunk_id"] == 2
    assert "start_word_idx" in chunks[0]


# ── TEST 7: Empty / invalid input → proper error ─────────────────────────────

def test_feature_extraction_invalid_input(feature_extractor):
    invalid_preprocessed = PreprocessedData(
        input_type="text",
        source="direct_input",
        preprocessing_status="error",
        preprocessing_errors=["Invalid input payload."],
    )

    features = feature_extractor.extract_features(invalid_preprocessed)

    assert features.feature_status == "error"
    assert len(features.feature_errors) > 0


# ── TEST 8: Canonical Feature Object Schema Check ────────────────────────────

def test_feature_object_canonical_schema(feature_extractor):
    mock_preprocessed = PreprocessedData(
        input_type="text",
        source="direct_input",
        processed="Standardized feature test.",
        preprocessing_status="success",
    )
    features = feature_extractor.extract_features(mock_preprocessed)
    feature_dict = features.to_dict()

    assert "input_type" in feature_dict
    assert "semantic_features" in feature_dict
    assert "visual_features" in feature_dict
    assert "ocr_features" in feature_dict
    assert "metadata" in feature_dict
    assert "feature_status" in feature_dict
    assert feature_dict["feature_status"] == "success"
