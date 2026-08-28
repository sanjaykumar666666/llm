"""
Test Suite: Copyright & Licensing Risk Analysis.
File: tests/test_copyright_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_copyright_risk_first_no_copyright_free_claims():
    """Verify that unverified media is never claimed to be 'copyright-free'."""
    meta = {"title": "Sample User Video", "caption": "", "is_creative_commons": False}
    lic_info = {"license_name": "Standard License", "license_status": "UNKNOWN"}

    assessment = UniversalContentService.assess_copyright_risk("Generic", meta, "", lic_info)
    assert assessment["copyright_risk_level"] == "UNKNOWN"
    assert "copyright-free" not in assessment["reason"].lower()
    assert "could not be verified" in assessment["safe_use_guidance"].lower()


def test_copyright_third_party_detection():
    """Verify detection of movies, music videos, broadcast sports, and studio media."""
    meta = {"title": "Warner Bros Movie Trailer and Netflix Episode", "caption": "Official music video soundtrack", "is_creative_commons": False}
    lic_info = {"license_name": "Standard Terms", "license_status": "PROPRIETARY"}

    assessment = UniversalContentService.assess_copyright_risk("YouTube", meta, "", lic_info)
    assert assessment["copyright_risk_level"] == "HIGH"
    assert assessment["has_third_party_media"] is True
    assert assessment["recommendation"] == "DO NOT REUSE"
