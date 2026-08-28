"""
Test Suite: YouTube Specific Analysis Features.
File: tests/test_youtube_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_youtube_video_analysis():
    """Verify YouTube standard video analysis with metadata and transcript."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    transcript = "[00:10] In this presentation we review data protection policies."
    res = UniversalContentService.analyze_social_content(url, custom_text=transcript)
    assert res["status"] == "success"
    assert res["platform"] == "YouTube"
    assert res["content_type"] == "video"
    assert "video_metadata" in res
    assert len(res["analyzed_frames"]) > 0


def test_youtube_shorts_analysis():
    """Verify YouTube Shorts detection and frame extraction."""
    url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    res = UniversalContentService.analyze_social_content(url)
    assert res["status"] == "success"
    assert res["platform"] == "YouTube"
    assert res["content_type"] == "short"
