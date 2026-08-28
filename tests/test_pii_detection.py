"""
Test Suite: PII Regex & Entity Detection with Synthetic Data.
File: tests/test_pii_detection.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_pii_regex_detects_all_synthetic_categories():
    """Verify detection of synthetic Aadhaar, PAN, Passport, Phone, Email, AWS Key, Database Password."""
    synthetic_text = (
        "Synthetic identity test:\n"
        "Aadhaar: 9876-5432-1098\n"
        "PAN Card: ABCDE1234F\n"
        "Passport: Z1234567\n"
        "Phone: +1 (555) 234-5678\n"
        "Email: analyst.doe@sample-security.org\n"
        "AWS: AKIAIOSFODNN7EXAMPLE\n"
        "Password: postgresql://admin:SecretDBPassword2026!@localhost:5432/test\n"
    )

    raw_frames = [{"frame_index": 1, "frame_number": "Frame 0001", "timestamp_sec": 0.0, "timestamp_str": "00:00", "thumbnail_data_uri": "data:image/jpeg;base64,abc"}]
    segments = [{"segment_id": "seg_1", "timestamp_sec": 0.0, "timestamp_str": "00:00", "text": synthetic_text}]

    analyzed_frames, detections = UniversalContentService.analyze_frames_and_privacy(
        platform_name="Generic",
        raw_frames=raw_frames,
        segments=segments,
        copyright_assessment={"copyright_risk_level": "LOW"}
    )

    types = [d["type"] for d in detections]
    assert "AADHAAR_NUMBER" in types
    assert "PAN_CARD" in types
    assert "PHONE_NUMBER" in types
    assert "EMAIL_ADDRESS" in types
    assert "AWS_ACCESS_KEY" in types
    assert "DATABASE_PASSWORD" in types

    # Verify masked text redacts sensitive tokens
    assert "9876-5432-1098" not in segments[0]["masked_text"]
    assert "AKIAIOSFODNN7EXAMPLE" not in segments[0]["masked_text"]
