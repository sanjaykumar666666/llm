"""
Test Suite: Platform Detection across all Supported & Unsupported URLs.
File: tests/test_platform_detection.py
"""

import pytest
from backend.adapters.platform_adapters import SocialMediaAdapterRegistry


def test_youtube_url_detection():
    """Verify detection of YouTube watch, youtu.be, shorts, and embed formats."""
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
    ]
    for u in urls:
        info = SocialMediaAdapterRegistry.identify_platform_info(u)
        assert info["is_supported"] is True
        assert info["platform"] == "YouTube"


def test_instagram_url_detection():
    """Verify detection of Instagram reels, posts, and TV clips."""
    urls = [
        "https://www.instagram.com/reel/C8qL9pXu12A/",
        "https://www.instagram.com/p/C8qL9pXu12A/",
        "https://www.instagram.com/tv/C8qL9pXu12A/",
        "https://instagr.am/p/C8qL9pXu12A/",
    ]
    for u in urls:
        info = SocialMediaAdapterRegistry.identify_platform_info(u)
        assert info["is_supported"] is True
        assert info["platform"] == "Instagram"


def test_facebook_url_detection():
    """Verify detection of Facebook watch and video post URLs."""
    urls = [
        "https://www.facebook.com/watch/?v=1029384756",
        "https://fb.watch/abcd1234ef/",
        "https://www.facebook.com/page/videos/987654321/",
    ]
    for u in urls:
        info = SocialMediaAdapterRegistry.identify_platform_info(u)
        assert info["is_supported"] is True
        assert info["platform"] == "Facebook"


def test_x_twitter_url_detection():
    """Verify detection of X.com and Twitter.com status posts."""
    urls = [
        "https://x.com/cyber_analyst/status/1784920482019485760",
        "https://twitter.com/cyber_analyst/status/1784920482019485760",
    ]
    for u in urls:
        info = SocialMediaAdapterRegistry.identify_platform_info(u)
        assert info["is_supported"] is True
        assert info["platform"] == "X / Twitter"


def test_tiktok_url_detection():
    """Verify detection of TikTok video and short URLs."""
    urls = [
        "https://www.tiktok.com/@dance_creator/video/7382910482910482910",
        "https://vm.tiktok.com/ZM8rX9q12/",
    ]
    for u in urls:
        info = SocialMediaAdapterRegistry.identify_platform_info(u)
        assert info["is_supported"] is True
        assert info["platform"] == "TikTok"


def test_vimeo_and_reddit_url_detection():
    """Verify detection of Vimeo and Reddit content URLs."""
    assert SocialMediaAdapterRegistry.identify_platform_info("https://vimeo.com/76979871")["platform"] == "Vimeo"
    assert SocialMediaAdapterRegistry.identify_platform_info("https://www.reddit.com/r/technology/comments/1ct8x92/post/")["platform"] == "Reddit"


def test_unsupported_and_invalid_url_detection():
    """Verify invalid strings return unsupported gracefully without crashing."""
    assert SocialMediaAdapterRegistry.identify_platform_info("not_a_valid_url")["is_supported"] is False
    assert SocialMediaAdapterRegistry.identify_platform_info("")["is_supported"] is False
    assert SocialMediaAdapterRegistry.identify_platform_info(None)["is_supported"] is False
