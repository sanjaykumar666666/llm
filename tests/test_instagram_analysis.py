"""
Test Suite: Instagram Specific Analysis Features.
File: tests/test_instagram_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_instagram_reel_analysis():
    """Verify Instagram Reel analysis with biometric face and caption evaluation."""
    url = "https://www.instagram.com/reel/C8qL9pXu12A/"
    res = UniversalContentService.analyze_social_content(url, custom_text="[00:05] Team daily standup meeting in office.")
    assert res["status"] == "success"
    assert res["platform"] == "Instagram"
    assert res["content_type"] == "reel"
    assert res["copyright_assessment"]["license_status"] == "PROPRIETARY"
    assert len(res["analyzed_frames"]) > 0


def test_instagram_post_analysis():
    """Verify Instagram photo post analysis."""
    url = "https://www.instagram.com/p/C8qL9pXu12A/"
    res = UniversalContentService.analyze_social_content(url)
    assert res["status"] == "success"
    assert res["platform"] == "Instagram"
    assert res["content_type"] == "post"
