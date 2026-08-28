"""
Test Suite: Frame-by-Frame Keyframe Sampling & Inspection.
File: tests/test_frame_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_frame_analysis_correct_timestamps_and_numbers():
    """Verify frames contain correct frame numbers, valid timestamps, and consistent order."""
    raw_frames = [
        {"frame_index": 1, "frame_number": "Frame 0001", "timestamp_sec": 0.0, "timestamp_str": "00:00", "thumbnail_data_uri": "data:image/jpeg;base64,1"},
        {"frame_index": 2, "frame_number": "Frame 0002", "timestamp_sec": 45.0, "timestamp_str": "00:45", "thumbnail_data_uri": "data:image/jpeg;base64,2"},
        {"frame_index": 3, "frame_number": "Frame 0003", "timestamp_sec": 90.0, "timestamp_str": "01:30", "thumbnail_data_uri": "data:image/jpeg;base64,3"},
    ]
    segments = [
        {"segment_id": "s1", "timestamp_sec": 45.0, "timestamp_str": "00:45", "text": "Contact phone: +1 (555) 234-5678."}
    ]

    analyzed, detections = UniversalContentService.analyze_frames_and_privacy(
        platform_name="YouTube",
        raw_frames=raw_frames,
        segments=segments,
        copyright_assessment={"copyright_risk_level": "LOW"}
    )

    assert len(analyzed) == 3
    assert analyzed[0]["timestamp_str"] == "00:00"
    assert analyzed[0]["privacy_risk"] == "LOW"

    assert analyzed[1]["timestamp_str"] == "00:45"
    assert analyzed[1]["privacy_risk"] in ["MEDIUM", "HIGH"]

    assert analyzed[2]["timestamp_str"] == "01:30"
    assert analyzed[2]["privacy_risk"] == "LOW"
