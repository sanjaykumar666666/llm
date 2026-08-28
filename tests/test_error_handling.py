"""
Test Suite: Error Handling and Graceful Failure Modes.
File: tests/test_error_handling.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_unsupported_platform_graceful_error():
    """Verify unsupported URL returns structured error without stack traces."""
    res = UniversalContentService.analyze_social_content("https://unsupported-site.org/video/123")
    assert res["status"] == "error"
    assert res["error_type"] == "UNSUPPORTED_PLATFORM"
    assert "error_message" in res
    assert not res.get("is_mock", True)


def test_inaccessible_or_empty_content():
    """Verify empty input returns INVALID_URL without crashing."""
    res = UniversalContentService.analyze_social_content("")
    assert res["status"] == "error"
    assert res["error_type"] == "INVALID_URL"
