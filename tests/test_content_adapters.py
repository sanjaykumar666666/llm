"""
Test Suite: Content Adapters Conformance.
File: tests/test_content_adapters.py
"""

import pytest
from backend.adapters.platform_adapters import SocialMediaAdapterRegistry


def test_all_adapters_conform_to_contract():
    """Verify all registered adapters implement the required interface methods and return valid schemas."""
    sample_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.instagram.com/reel/C8qL9pXu12A/",
        "https://www.facebook.com/watch?v=123456",
        "https://x.com/user/status/1784920482019485760",
        "https://www.tiktok.com/@user/video/7382910482910482910",
        "https://vimeo.com/76979871",
        "https://www.reddit.com/r/technology/comments/1ct8x92/post/",
        "https://example.com/stream/sample.mp4",
    ]

    for url in sample_urls:
        adapter = SocialMediaAdapterRegistry.get_adapter(url)
        assert adapter is not None

        # 1. Metadata Schema
        meta = adapter.fetch_metadata(url)
        assert "platform" in meta
        assert "content_type" in meta
        assert "title" in meta
        assert "author" in meta
        assert "availability" in meta
        assert "is_accessible" in meta

        # 2. Content Schema
        content = adapter.fetch_content(url, custom_text="[00:05] Test content payload")
        assert "text" in content
        assert "segments" in content
        assert "has_media" in content

        # 3. Frames Schema
        frames = adapter.extract_media_frames(url, meta, max_samples=3)
        assert len(frames) > 0
        for f in frames:
            assert "frame_index" in f
            assert "timestamp_str" in f
            assert "thumbnail_data_uri" in f
            assert f["thumbnail_data_uri"].startswith("data:image/jpeg;base64,")

        # 4. License Info Schema
        lic = adapter.get_license_info(meta)
        assert "license_name" in lic
        assert "license_status" in lic
        assert "safe_use_guidance" in lic
