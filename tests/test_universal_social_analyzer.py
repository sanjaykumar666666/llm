"""
Unit and Integration Tests for Universal Social Media Content Analyzer.
File: tests/test_universal_social_analyzer.py
"""

import pytest
from backend.adapters.platform_adapters import (
    SocialMediaAdapterRegistry,
    YouTubeAdapter,
    InstagramAdapter,
    FacebookAdapter,
    XAdapter,
    TikTokAdapter,
    VimeoAdapter,
    RedditAdapter,
    GenericPublicMediaAdapter,
)
from backend.services.universal_content_service import UniversalContentService
from backend.routes.youtube_analysis import run_social_media_pipeline, run_youtube_pipeline


def test_platform_adapter_detection():
    """Verify that all social media URLs are automatically dispatched to the proper adapter."""
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube", "video"),
        ("https://youtu.be/dQw4w9WgXcQ", "YouTube", "video"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "YouTube", "short"),
        ("https://www.instagram.com/reel/C8qL9pXu12A/", "Instagram", "reel"),
        ("https://www.instagram.com/p/C8qL9pXu12A/", "Instagram", "post"),
        ("https://www.facebook.com/watch?v=1029384756", "Facebook", "video"),
        ("https://x.com/cyber_analyst/status/1784920482019485760", "X / Twitter", "post"),
        ("https://twitter.com/user/status/1234567890", "X / Twitter", "post"),
        ("https://www.tiktok.com/@creator/video/7382910482910482910", "TikTok", "video"),
        ("https://vimeo.com/76979871", "Vimeo", "video"),
        ("https://www.reddit.com/r/technology/comments/1ct8x92/post/", "Reddit", "post"),
        ("https://example.com/stream/sample.mp4", "Public Web Media", "video"),
        ("https://images.unsplash.com/photo-sample.jpg", "Public Web Media", "image"),
    ]

    for url, expected_plat, expected_type in test_cases:
        adapter = SocialMediaAdapterRegistry.get_adapter(url)
        assert adapter is not None, f"Failed to find adapter for {url}"
        assert adapter.get_platform_name() == expected_plat, f"Expected {expected_plat} got {adapter.get_platform_name()}"
        assert adapter.get_content_type(url) == expected_type, f"Expected {expected_type} got {adapter.get_content_type(url)}"


def test_invalid_url_and_unsupported_detection():
    """Verify invalid strings return unsupported gracefully without exceptions."""
    info_invalid = SocialMediaAdapterRegistry.identify_platform_info("not_a_valid_url")
    assert info_invalid["is_supported"] is False
    assert info_invalid["status"] == "Unsupported URL format"

    res_err = UniversalContentService.analyze_social_content("")
    assert res_err["status"] == "error"
    assert res_err["error_type"] == "INVALID_URL"


def test_copyright_risk_assessment_across_platforms():
    """Verify copyright risk engine correctly classifies across diverse media types."""
    # 1. Verified Creative Commons (Vimeo CC-BY)
    vimeo_adapter = VimeoAdapter()
    meta_vimeo = vimeo_adapter.fetch_metadata("https://vimeo.com/76979871")
    lic_vimeo = vimeo_adapter.get_license_info(meta_vimeo)
    c_vimeo = UniversalContentService.assess_copyright_risk("Vimeo", meta_vimeo, "Educational lecture", lic_vimeo)
    assert c_vimeo["copyright_risk_level"] == "LOW"
    assert c_vimeo["recommendation"] == "POTENTIALLY USABLE"

    # 2. Commercial / Studio Music Sound (TikTok / Film)
    tiktok_adapter = TikTokAdapter()
    meta_tt = tiktok_adapter.fetch_metadata("https://www.tiktok.com/@dance/video/123456")
    lic_tt = tiktok_adapter.get_license_info(meta_tt)
    c_tt = UniversalContentService.assess_copyright_risk("TikTok", meta_tt, "Official music video soundtrack Warner Music", lic_tt)
    assert c_tt["copyright_risk_level"] == "HIGH"
    assert c_tt["recommendation"] == "DO NOT REUSE"
    assert "copyright-free" not in c_tt["reason"].lower()

    # 3. Proprietary Social Post (Instagram / X)
    ig_adapter = InstagramAdapter()
    meta_ig = ig_adapter.fetch_metadata("https://www.instagram.com/p/123456/")
    lic_ig = ig_adapter.get_license_info(meta_ig)
    c_ig = UniversalContentService.assess_copyright_risk("Instagram", meta_ig, "Daily office vlog", lic_ig)
    assert c_ig["copyright_risk_level"] in ["MEDIUM", "UNKNOWN"]
    assert c_ig["recommendation"] == "VERIFY LICENSE"


def test_multimodal_privacy_detection_and_frame_safety():
    """Verify face detection, PII regex detection, and frame safety recommendations."""
    raw_frames = [
        {"frame_index": 1, "frame_number": "Frame 0001", "timestamp_sec": 5.0, "timestamp_str": "00:05", "thumbnail_data_uri": "data:image/jpeg;base64,123"},
        {"frame_index": 2, "frame_number": "Frame 0002", "timestamp_sec": 30.0, "timestamp_str": "00:30", "thumbnail_data_uri": "data:image/jpeg;base64,456"},
    ]
    segments = [
        {"segment_id": "s1", "timestamp_sec": 5.0, "timestamp_str": "00:05", "text": "Customer Aadhaar is 9876-5432-1098 and AWS key is AKIAIOSFODNN7EXAMPLE."},
        {"segment_id": "s2", "timestamp_sec": 30.0, "timestamp_str": "00:30", "text": "Safe conversation without personal data."},
    ]
    copyright_assessment = {"copyright_risk_level": "LOW", "reason": "Verified Open CC"}

    analyzed_frames, detections = UniversalContentService.analyze_frames_and_privacy(
        platform_name="X / Twitter",
        raw_frames=raw_frames,
        segments=segments,
        copyright_assessment=copyright_assessment
    )

    assert len(detections) >= 2
    types = [d["type"] for d in detections]
    assert "AADHAAR_NUMBER" in types
    assert "AWS_ACCESS_KEY" in types

    # First frame should be flagged HIGH privacy risk due to AWS key & Aadhaar at 00:05
    assert analyzed_frames[0]["privacy_risk"] == "HIGH"
    assert analyzed_frames[0]["recommendation"] == "DO NOT REUSE"

    # Second frame should be POTENTIALLY USABLE
    assert analyzed_frames[1]["privacy_risk"] == "LOW"
    assert analyzed_frames[1]["recommendation"] == "POTENTIALLY USABLE"


def test_multidimensional_risk_scoring():
    """Verify that independent risk scores are calculated without masking individual factors."""
    c_high = {"copyright_risk_level": "HIGH"}
    detections = [{"type": "AWS_ACCESS_KEY", "severity": "CRITICAL"}]
    frames = [{"privacy_risk": "HIGH"}]

    scores = UniversalContentService.calculate_multidimensional_risks(
        copyright_assessment=c_high,
        privacy_detections=detections,
        analyzed_frames=frames,
        segments=[]
    )

    assert scores["privacy_risk_level"] == "CRITICAL"
    assert scores["privacy_risk_score"] >= 90
    assert scores["copyright_risk_level"] == "HIGH"
    assert scores["copyright_risk_score"] >= 90
    assert scores["overall_risk_level"] == "HIGH"


def test_original_content_summary_synthesis():
    """Verify summary is an original non-infringing synthesis."""
    meta = {"duration": "01:30"}
    summary = UniversalContentService.synthesize_media_summary(
        platform="Instagram",
        content_type="reel",
        title="Machine Learning AI Security",
        author="ai_researcher",
        text_content="Discussing neural models and token security",
        metadata=meta,
        detections=[]
    )

    assert summary["is_original_synthesis"] is True
    assert "what_it_is_about" in summary
    assert "main_topics" in summary
    assert "important_points" in summary
    assert "overall_summary" in summary
    assert len(summary["main_topics"]) > 0


def test_end_to_end_social_pipeline_instagram_and_x():
    """Verify full end-to-end execution of run_social_media_pipeline for Instagram and X."""
    # Instagram Reel test
    res_ig = run_social_media_pipeline(
        "https://www.instagram.com/reel/C8qL9pXu12A/",
        custom_transcript="[00:05] Today we are reviewing employee records.\n[00:15] Contact email is admin@company.org with phone +1-555-987-6543."
    )
    assert res_ig["status"] == "success"
    assert res_ig["platform"] == "Instagram"
    assert res_ig["content_type"] == "reel"
    assert "risk_breakdown" in res_ig
    assert len(res_ig["analyzed_frames"]) > 0
    assert "disclaimer" in res_ig

    # X / Twitter post test
    res_x = run_social_media_pipeline(
        "https://x.com/analyst/status/1784920482019485760",
        custom_transcript="AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE and database password is SecretDBPassword2026!"
    )
    assert res_x["status"] == "success"
    assert res_x["platform"] == "X / Twitter"
    assert res_x["risk_breakdown"]["privacy_risk_level"] in ["CRITICAL", "HIGH"]
    assert res_x["decision"] == "BLOCK"


def test_backward_compatibility_run_youtube_pipeline():
    """Verify existing run_youtube_pipeline still works and returns all required legacy and new fields."""
    res_yt = run_youtube_pipeline(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        custom_transcript="[00:10] Machine learning security and privacy presentation."
    )
    assert res_yt["status"] == "success"
    assert "video_metadata" in res_yt
    assert "video_summary" in res_yt
    assert "copyright_assessment" in res_yt
    assert "analyzed_frames" in res_yt
    assert "standardized_input" in res_yt
    assert "final_report" in res_yt
