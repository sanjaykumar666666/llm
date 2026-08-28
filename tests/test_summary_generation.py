"""
Test Suite: Original Content Summary Synthesis.
File: tests/test_summary_generation.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_summary_does_not_reproduce_full_copyrighted_transcript():
    """Verify summary is an original concise synthesis and does not verbatim copy full input."""
    large_transcript = (
        "This is an extensive verbatim spoken transcript detailing cloud security steps. " * 20
    )
    summary = UniversalContentService.synthesize_media_summary(
        platform="YouTube",
        content_type="video",
        title="Enterprise Cloud Security Lecture",
        author="CloudAcademy",
        text_content=large_transcript,
        metadata={"duration": "10:00"},
        detections=[]
    )

    assert summary["is_original_synthesis"] is True
    assert len(summary["overall_summary"]) < len(large_transcript)
    assert "what_it_is_about" in summary
    assert len(summary["main_topics"]) >= 2
    assert len(summary["important_points"]) >= 2
