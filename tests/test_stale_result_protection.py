"""
Test Suite: Stale Result Protection Across Consecutive Analyses.
File: tests/test_stale_result_protection.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_consecutive_analyses_do_not_leak_prior_state():
    """Verify that analyzing Video A, then Video B, then Video C completely replaces all data."""
    # 1. Analyze Payload A (High Risk X Post with AWS Key)
    url_a = "https://x.com/user/status/1111111111111111111"
    res_a = UniversalContentService.analyze_social_content(
        url_a, custom_text="[00:05] AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
    )
    assert res_a["platform"] == "X / Twitter"
    assert res_a["risk_breakdown"]["privacy_risk_level"] in ["CRITICAL", "HIGH"]
    assert "AKIAIOSFODNN7EXAMPLE" in [d["value_preview"] for d in res_a["privacy_detections"] if "AKIA" in d["value_preview"]] or len(res_a["privacy_detections"]) > 0

    # 2. Analyze Payload B (Clean Safe Vimeo CC-BY Video)
    url_b = "https://vimeo.com/76979871"
    res_b = UniversalContentService.analyze_social_content(
        url_b, custom_text="[00:05] Clean theoretical machine learning seminar."
    )
    assert res_b["platform"] == "Vimeo"
    assert res_b["risk_breakdown"]["privacy_risk_level"] == "LOW"
    assert len(res_b["privacy_detections"]) == 0
    # Confirm NO trace of Payload A exists in Payload B
    assert res_b["url"] == url_b
    assert "AKIA" not in str(res_b)

    # 3. Analyze Payload C (Instagram Reel with Phone Number)
    url_c = "https://www.instagram.com/reel/C8qL9pXu12A/"
    res_c = UniversalContentService.analyze_social_content(
        url_c, custom_text="[00:05] Contact my office at +1 (555) 019-2834."
    )
    assert res_c["platform"] == "Instagram"
    assert res_c["content_type"] == "reel"
    assert len(res_c["privacy_detections"]) == 1
    assert res_c["privacy_detections"][0]["type"] == "PHONE_NUMBER"
    # Confirm NO trace of Payload B or A exists in Payload C
    assert res_c["url"] == url_c
    assert "vimeo" not in str(res_c).lower()
