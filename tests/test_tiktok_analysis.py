"""
Test Suite: TikTok Specific Analysis Features.
File: tests/test_tiktok_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_tiktok_video_commercial_sound_warning():
    """Verify TikTok video analysis checks for commercial music copyright warning."""
    url = "https://www.tiktok.com/@creator/video/7382910482910482910"
    caption = "Dance video with official soundtrack Universal Music Group commercial song."
    res = UniversalContentService.analyze_social_content(url, custom_text=caption)
    assert res["status"] == "success"
    assert res["platform"] == "TikTok"
    assert res["copyright_assessment"]["copyright_risk_level"] == "HIGH"
    assert "DO NOT REUSE" in res["copyright_assessment"]["recommendation"]
