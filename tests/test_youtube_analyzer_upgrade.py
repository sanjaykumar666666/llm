"""
Unit and Integration Tests for YouTube Analyzer — Copyright, Privacy & Frame Safety Upgrade.
File: tests/test_youtube_analyzer_upgrade.py
"""

import pytest
from backend.services.youtube_risk_service import YouTubeRiskService
from backend.routes.youtube_analysis import run_youtube_pipeline


def test_url_validation_formats():
    """Verify that all standard YouTube URL formats are correctly parsed."""
    urls = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ]
    for url, expected_id in urls:
        assert YouTubeRiskService.extract_video_id(url) == expected_id

    # Invalid URL formats
    assert YouTubeRiskService.extract_video_id("https://example.com/video") is None
    assert YouTubeRiskService.extract_video_id("invalid_string") is None


def test_metadata_extraction_structure():
    """Verify metadata dictionary schema and availability fields."""
    meta = YouTubeRiskService.fetch_video_metadata("dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert "video_id" in meta
    assert "title" in meta
    assert "channel" in meta
    assert "duration" in meta
    assert "duration_sec" in meta
    assert "published_date" in meta
    assert "thumbnail_url" in meta
    assert "license" in meta
    assert "availability" in meta


def test_original_video_summary_synthesis():
    """Verify that video summary is an original synthesis without verbatim copyright reproduction."""
    sample_text = (
        "[00:05] Welcome to today's cloud computing and privacy seminar. "
        "[00:30] We are demonstrating differential privacy and secure token handling. "
        "[01:10] Machine learning models process encrypted gradients to protect data."
    )
    metadata = {
        "title": "Cloud Privacy Seminar",
        "channel": "Tech Academy",
        "duration": "02:30",
        "duration_sec": 150.0,
    }
    summary = YouTubeRiskService.generate_original_summary(
        title=metadata["title"],
        channel=metadata["channel"],
        transcript_text=sample_text,
        metadata=metadata,
        detections=[],
    )
    assert "what_it_is_about" in summary
    assert "main_topics" in summary
    assert "important_points" in summary
    assert "overall_summary" in summary
    assert summary["is_original_synthesis"] is True
    assert len(summary["main_topics"]) > 0
    assert len(summary["important_points"]) > 0


def test_copyright_risk_classification_risk_first():
    """Verify copyright risk classification uses risk-first categories and never claims unverified copyright-free."""
    # 1. Commercial / Studio Music Video
    meta_music = {
        "title": "Official Music Video - Mega Hit (Warner Records)",
        "categories": ["Music"],
        "is_creative_commons": False,
        "license": "Standard YouTube License",
    }
    res_music = YouTubeRiskService.assess_copyright_and_licensing_risk(meta_music, "Lyrics singing love song")
    assert res_music["copyright_risk_level"] == "HIGH"
    assert res_music["recommendation"] == "DO NOT REUSE"
    assert "copyright-free" not in res_music["reason"].lower()

    # 2. Verified Creative Commons Video
    meta_cc = {
        "title": "Open Source Tutorial",
        "categories": ["Education"],
        "is_creative_commons": True,
        "license": "Creative Commons Attribution (CC BY)",
    }
    res_cc = YouTubeRiskService.assess_copyright_and_licensing_risk(meta_cc, "Welcome to open source coding")
    assert res_cc["copyright_risk_level"] == "LOW"
    assert res_cc["recommendation"] == "POTENTIALLY USABLE"

    # 3. Standard YouTube Video without explicit open license
    meta_std = {
        "title": "My Weekend Vlog",
        "categories": ["People & Blogs"],
        "is_creative_commons": False,
        "license": "Standard YouTube License / Unspecified",
    }
    res_std = YouTubeRiskService.assess_copyright_and_licensing_risk(meta_std, "Having coffee in the morning")
    assert res_std["copyright_risk_level"] in ["UNKNOWN", "MEDIUM"]
    assert res_std["recommendation"] == "VERIFY LICENSE"
    assert ("verif" in res_std["safe_use_guidance"].lower() or "obtain creator permission" in res_std["safe_use_guidance"].lower())


def test_frame_sampling_and_pii_detection():
    """Verify frame-level sampling, PII entity detection, and structured frame results."""
    transcript_segs = [
        {"timestamp_sec": 15.0, "timestamp_str": "00:15", "text": "Customer Aadhaar is 9876 5432 1098 and PAN is ABCDE1234F."},
        {"timestamp_sec": 60.0, "timestamp_str": "01:00", "text": "Email contact is security@enterprise.corp with AWS key AKIAIOSFODNN7EXAMPLE."},
        {"timestamp_sec": 120.0, "timestamp_str": "02:00", "text": "Normal safe conversation without secrets."},
    ]
    copyright_assessment = {
        "copyright_risk_level": "UNKNOWN",
        "reason": "Standard platform licensing applies",
    }

    frames = YouTubeRiskService.sample_and_analyze_frames(
        video_id="dQw4w9WgXcQ",
        duration_sec=150.0,
        title="Security Webinar",
        channel="Cyber Corp",
        copyright_assessment=copyright_assessment,
        transcript_segments=transcript_segs,
        max_samples=6,
    )

    assert len(frames) > 0
    for f in frames:
        assert "frame_number" in f
        assert "timestamp_str" in f
        assert "privacy_risk" in f
        assert "copyright_risk" in f
        assert "recommendation" in f
        assert "explanation" in f
        assert "thumbnail_data_uri" in f
        assert f["thumbnail_data_uri"].startswith("data:image/jpeg;base64,")

    # Verify at least one high-risk frame was flagged due to Aadhaar / AWS key
    has_high_priv = any(f["privacy_risk"] == "HIGH" for f in frames)
    assert has_high_priv is True


def test_frame_safety_recommendation_categories():
    """Verify that every frame receives one of the 4 standardized recommendations."""
    valid_recs = {"POTENTIALLY USABLE", "VERIFY LICENSE", "REDACT / REVIEW", "DO NOT REUSE"}

    transcript_segs = [
        {"timestamp_sec": 10.0, "timestamp_str": "00:10", "text": "Password is SecretPassword123!"},
        {"timestamp_sec": 45.0, "timestamp_str": "00:45", "text": "Presenter John Doe is on camera."},
        {"timestamp_sec": 90.0, "timestamp_str": "01:30", "text": "Standard discussion topic."},
    ]
    copyright_assessment = {"copyright_risk_level": "LOW", "reason": "Creative Commons"}

    frames = YouTubeRiskService.sample_and_analyze_frames(
        video_id="dQw4w9WgXcQ",
        duration_sec=120.0,
        title="Lecture",
        channel="Instructor",
        copyright_assessment=copyright_assessment,
        transcript_segments=transcript_segs,
        max_samples=5,
    )

    for f in frames:
        assert f["recommendation"] in valid_recs


def test_final_report_compilation_and_disclaimer():
    """Verify final report consolidation and legal disclaimer presence."""
    meta = {"title": "Test Video", "channel": "Creator", "duration": "03:00"}
    summary = {"what_it_is_about": "Test summary", "overall_summary": "Overall summary"}
    copyright_data = {"copyright_risk_level": "LOW", "license_name": "CC BY", "has_third_party_media": False}
    frames = [
        {"privacy_risk": "HIGH", "copyright_risk": "LOW", "entities": [{"type": "AADHAAR_NUMBER"}], "recommendation": "DO NOT REUSE"},
        {"privacy_risk": "LOW", "copyright_risk": "LOW", "entities": [], "recommendation": "POTENTIALLY USABLE"},
    ]

    report = YouTubeRiskService.compile_comprehensive_report(
        metadata=meta,
        summary=summary,
        copyright_assessment=copyright_data,
        analyzed_frames=frames,
        transcript_detections=[],
    )

    assert "privacy_report" in report
    assert "copyright_report" in report
    assert "overall_decision" in report
    assert "overall_recommendation" in report
    assert "disclaimer" in report
    assert "not legal advice" in report["disclaimer"].lower()


def test_end_to_end_youtube_pipeline_integration():
    """Verify full end-to-end execution of run_youtube_pipeline with enriched fields."""
    custom_transcript = """
    [00:05] Welcome to today's cloud deployment session.
    [00:20] The database password is DatabaseSecret2026! and AWS key is AKIAIOSFODNN7EXAMPLE.
    [00:45] Please ensure you do not commit these credentials to public repositories.
    """
    res = run_youtube_pipeline("https://www.youtube.com/watch?v=dQw4w9WgXcQ", custom_transcript=custom_transcript)

    assert res["status"] == "success"
    assert "video_summary" in res
    assert "copyright_assessment" in res
    assert "analyzed_frames" in res
    assert "final_report" in res
    assert "disclaimer" in res
    assert "standardized_input" in res
    assert res["decision"] in ["BLOCK", "SANITIZE", "WARN", "ALLOW"]
    assert len(res["analyzed_frames"]) > 0


def test_invalid_url_graceful_error():
    """Verify invalid URL returns a graceful structured error without crashing."""
    res = run_youtube_pipeline("https://not-youtube.com/invalid_page")
    assert res["status"] == "error"
    assert res["error_type"] == "INVALID_URL"
    assert "validation_status" in res or "error_message" in res
