"""
Test Suite: Facebook Specific Analysis Features.
File: tests/test_facebook_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_facebook_watch_video_analysis():
    """Verify Facebook Watch video analysis."""
    url = "https://www.facebook.com/watch/?v=1029384756"
    res = UniversalContentService.analyze_social_content(url)
    assert res["status"] == "success"
    assert res["platform"] == "Facebook"
    assert res["content_type"] == "video"
    assert res["copyright_assessment"]["license_status"] == "PROPRIETARY"
    assert len(res["analyzed_frames"]) > 0
