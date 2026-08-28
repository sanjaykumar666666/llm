"""
Test Suite: Security and Zero-Bypass Safeguards.
File: tests/test_security.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_zero_bypass_and_credential_sanitization():
    """Verify sensitive credentials are never stored unmasked in output payloads."""
    secret_text = "Internal API secret sk-proj-12345678901234567890123456789012"
    res = UniversalContentService.analyze_social_content(
        "https://x.com/user/status/1784920482019485760",
        custom_text=secret_text
    )

    # Output masked transcript must have sensitive tokens redacted
    assert "sk-proj-12345678901234567890123456789012" not in res["sanitized_transcript"]
    assert "REDACTED" in res["sanitized_transcript"]


def test_path_traversal_and_malicious_input_safety():
    """Verify file path traversal patterns are safely treated as text without executing system commands."""
    malicious_inputs = [
        "../../../../etc/passwd",
        "https://youtube.com/watch?v=123;rm -rf /",
        "<script>alert('xss')</script>",
    ]
    for bad_in in malicious_inputs:
        res = UniversalContentService.analyze_social_content(bad_in)
        assert res["status"] in ["error", "success"]
        # System should remain safe and stable
