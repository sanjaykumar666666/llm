"""
Test Suite: Beginner-Friendly 4-Part Risk Explanations.
File: tests/test_risk_explanations.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_four_part_beginner_explanation_structure():
    """Verify that every warning includes: WHERE, WHY, WHAT COULD HAPPEN, WHAT TO DO."""
    scenarios = [
        ("00:15", "HIGH", "LOW", "AWS_ACCESS_KEY"),
        ("00:30", "MEDIUM", "LOW", "1 Face(s)"),
        ("01:00", "HIGH", "LOW", "AADHAAR_NUMBER"),
        ("02:15", "LOW", "HIGH", "Commercial Footage"),
        ("03:00", "LOW", "UNKNOWN", "No sensitive entities"),
    ]

    for where_val, p_risk, c_risk, det_obj in scenarios:
        exp = UniversalContentService.generate_beginner_explanation(
            where=where_val,
            privacy_risk=p_risk,
            copyright_risk=c_risk,
            detected_objects=det_obj
        )

        assert "where" in exp and len(exp["where"].strip()) > 0, "Missing 'where' component"
        assert "why" in exp and len(exp["why"].strip()) > 0, "Missing 'why' component"
        assert "what_could_happen" in exp and len(exp["what_could_happen"].strip()) > 0, "Missing 'what_could_happen' component"
        assert "what_to_do" in exp and len(exp["what_to_do"].strip()) > 0, "Missing 'what_to_do' component"


def test_analyzed_frames_include_beginner_explanations():
    """Verify that analyzed frames directly provide beginner-friendly explanation attributes."""
    raw_frames = [{"frame_index": 1, "frame_number": "Frame 0001", "timestamp_sec": 10.0, "timestamp_str": "00:10", "thumbnail_data_uri": "data:image/jpeg;base64,123"}]
    segments = [{"segment_id": "s1", "timestamp_sec": 10.0, "timestamp_str": "00:10", "text": "Contact phone is +1 (555) 234-5678."}]

    analyzed, detections = UniversalContentService.analyze_frames_and_privacy(
        platform_name="Instagram",
        raw_frames=raw_frames,
        segments=segments,
        copyright_assessment={"copyright_risk_level": "LOW"}
    )

    f = analyzed[0]
    assert "beginner_explanation" in f
    assert "where" in f
    assert "why" in f
    assert "what_could_happen" in f
    assert "what_to_do" in f
