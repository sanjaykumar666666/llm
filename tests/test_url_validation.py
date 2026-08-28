"""
Test Suite: URL Validation and Error Resilience.
File: tests/test_url_validation.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_url_with_tracking_and_query_parameters():
    """Verify URLs with query tracking parameters (?utm_source, ?si, ?feature) parse properly."""
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share&utm_source=twitter",
        "https://youtu.be/dQw4w9WgXcQ?si=cIXA9no3mS1sqDAv",
        "https://www.instagram.com/reel/C8qL9pXu12A/?igsh=MWQ1ZGUxMzBkMA==",
        "https://x.com/user/status/1784920482019485760?s=20&t=abcdef123",
    ]
    for u in urls:
        res = UniversalContentService.analyze_social_content(u)
        assert res["status"] == "success", f"Failed for URL with tracking query: {u}"
        assert res["platform"] in ["YouTube", "Instagram", "X / Twitter"]


def test_empty_and_whitespace_urls():
    """Verify empty or whitespace strings return structured error."""
    for empty_val in ["", "   ", None]:
        res = UniversalContentService.analyze_social_content(empty_val)
        assert res["status"] == "error"
        assert res["error_type"] == "INVALID_URL"


def test_malformed_and_random_text_urls():
    """Verify random text strings return graceful unsupported platform error."""
    for random_str in ["hello world", "just a random comment", "ftp://invalid-server"]:
        res = UniversalContentService.analyze_social_content(random_str)
        assert res["status"] == "error"
        assert res["error_type"] in ["UNSUPPORTED_PLATFORM", "INVALID_URL"]
