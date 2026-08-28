"""
Test Suite: Standardized Safe-Use Recommendations.
File: tests/test_safe_use_recommendations.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_recommendation_matrix():
    """Verify exact recommendation output for every combination of privacy and copyright risk."""
    raw_frame = [{"frame_index": 1, "frame_number": "Frame 0001", "timestamp_sec": 0.0, "timestamp_str": "00:00", "thumbnail_data_uri": "data:image/jpeg;base64,123"}]

    # 1. High Privacy + High Copyright -> 🔴 DO NOT REUSE
    f1, _ = UniversalContentService.analyze_frames_and_privacy(
        platform_name="YouTube",
        raw_frames=raw_frame,
        segments=[{"segment_id": "1", "timestamp_sec": 0.0, "timestamp_str": "00:00", "text": "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"}],
        copyright_assessment={"copyright_risk_level": "HIGH", "reason": "Commercial movie"}
    )
    assert f1[0]["recommendation"] == "DO NOT REUSE"

    # 2. Low Privacy + Unknown Copyright -> 🟡 VERIFY LICENSE
    f2, _ = UniversalContentService.analyze_frames_and_privacy(
        platform_name="YouTube",
        raw_frames=raw_frame,
        segments=[{"segment_id": "1", "timestamp_sec": 0.0, "timestamp_str": "00:00", "text": "Clean educational speech"}],
        copyright_assessment={"copyright_risk_level": "UNKNOWN", "reason": "Unspecified license"}
    )
    assert f2[0]["recommendation"] == "VERIFY LICENSE"

    # 3. Low Privacy + Low Copyright -> 🟢 POTENTIALLY USABLE
    f3, _ = UniversalContentService.analyze_frames_and_privacy(
        platform_name="Vimeo",
        raw_frames=raw_frame,
        segments=[{"segment_id": "1", "timestamp_sec": 0.0, "timestamp_str": "00:00", "text": "Clean lecture"}],
        copyright_assessment={"copyright_risk_level": "LOW", "reason": "CC-BY"}
    )
    assert f3[0]["recommendation"] == "POTENTIALLY USABLE"

    # 4. Medium Privacy + Low Copyright -> 🟠 REDACT / REVIEW
    f4, _ = UniversalContentService.analyze_frames_and_privacy(
        platform_name="Instagram",
        raw_frames=raw_frame,
        segments=[{"segment_id": "1", "timestamp_sec": 0.0, "timestamp_str": "00:00", "text": "Call me at +1-555-123-4567"}],
        copyright_assessment={"copyright_risk_level": "LOW", "reason": "CC-BY"}
    )
    assert f4[0]["recommendation"] == "REDACT / REVIEW"
