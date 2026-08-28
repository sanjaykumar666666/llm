"""
Test Suite: X / Twitter Specific Analysis Features.
File: tests/test_x_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_x_post_with_credential_leak():
    """Verify X (Twitter) post analysis correctly identifies exposed API keys and blocks reuse."""
    url = "https://x.com/dev_ops/status/1784920482019485760"
    tweet_text = "Found leaked key: AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE and secret=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    res = UniversalContentService.analyze_social_content(url, custom_text=tweet_text)
    assert res["status"] == "success"
    assert res["platform"] == "X / Twitter"
    assert res["content_type"] == "post"
    assert res["risk_breakdown"]["privacy_risk_level"] in ["CRITICAL", "HIGH"]
    assert res["decision"] == "BLOCK"
    assert len(res["privacy_detections"]) >= 1
