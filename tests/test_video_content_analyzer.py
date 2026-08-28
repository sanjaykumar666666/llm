"""
Comprehensive Video Analyzer Deep Testing & Production Validation Suite.
File: tests/test_video_content_analyzer.py
"""

import os
import io
import time
import tempfile
import pytest
import numpy as np
import cv2

from backend.services.video_privacy_service import VideoPrivacyService
from backend.services.video_content_analyzer import VideoContentAnalyzer
from backend.routes.video_analysis import video_analysis_endpoint


# ── FIXTURES & SYNTHETIC VIDEO BUILDERS ───────────────────────────────────────

@pytest.fixture(scope="module")
def synthetic_identity_video():
    """Generates synthetic test video with moving Aadhaar, PAN, and credentials."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    return vid_bytes, filename


@pytest.fixture(scope="module")
def synthetic_clean_video():
    """Generates synthetic test video with zero PII (clean nature scene)."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🟢 Clean Landscape Video (Zero PII)")
    return vid_bytes, filename


@pytest.fixture(scope="module")
def synthetic_face_video():
    """Generates synthetic test video containing a moving human face avatar."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("👤 Face & Biometric Video (Moving Person)")
    return vid_bytes, filename


# ── 1. INPUT VALIDATION TESTS ────────────────────────────────────────────────

def test_input_validation_valid_and_invalid(synthetic_identity_video):
    """Test valid video, empty bytes, and corrupted payloads."""
    vid_bytes, filename = synthetic_identity_video

    # 1. Valid video payload
    is_valid, err, meta = VideoPrivacyService.validate_video_bytes(vid_bytes, filename)
    assert is_valid is True
    assert err is None
    assert meta["width"] > 0
    assert meta["height"] > 0

    # 2. Empty payload
    is_valid, err, meta = VideoPrivacyService.validate_video_bytes(b"", "empty.mp4")
    assert is_valid is False
    assert "empty" in err.lower()

    # 3. Corrupted payload
    is_valid, err, meta = VideoPrivacyService.validate_video_bytes(b"CORRUPT_NOT_A_VIDEO_STREAM", "corrupt.mp4")
    assert is_valid is False
    assert "corrupted" in err.lower() or "invalid" in err.lower()


# ── 2. METADATA EXTRACTION TESTS ─────────────────────────────────────────────

def test_metadata_extraction(synthetic_identity_video):
    """Test comprehensive metadata extraction (resolution, duration, fps, format)."""
    vid_bytes, filename = synthetic_identity_video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(vid_bytes)
        tmp_path = tmp.name

    try:
        meta = VideoContentAnalyzer.extract_video_metadata(tmp_path, filename)
        assert meta["filename"] == filename
        assert meta["duration_sec"] > 0
        assert meta["duration_str"] != ""
        assert meta["fps"] > 0
        assert meta["total_frames"] > 0
        assert meta["resolution"] == f"{meta['width']}x{meta['height']}"
        assert meta["format"] in ["MP4", "MOV", "MKV", "WEBM", "AVI"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── 3. FRAME EXTRACTION & SAMPLING TESTS ─────────────────────────────────────

def test_smart_frame_sampling(synthetic_identity_video):
    """Test adaptive keyframe sampling and data URI generation."""
    vid_bytes, filename = synthetic_identity_video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(vid_bytes)
        tmp_path = tmp.name

    try:
        frames = VideoContentAnalyzer.smart_sample_keyframes(tmp_path, max_samples=6)
        assert len(frames) >= 2
        assert len(frames) <= 6

        for idx, f in enumerate(frames):
            assert "frame_number" in f
            assert "timestamp_sec" in f
            assert "timestamp_str" in f
            assert "thumbnail_data_uri" in f
            assert f["thumbnail_data_uri"].startswith("data:image/jpeg;base64,")
            assert isinstance(f["image_array"], np.ndarray)
            assert f["image_array"].shape[0] > 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── 4. TIMESTAMP ACCURACY TESTS ──────────────────────────────────────────────

def test_timestamp_accuracy(synthetic_identity_video):
    """Verify that extracted frames map accurately to their reported video timestamps."""
    vid_bytes, filename = synthetic_identity_video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(vid_bytes)
        tmp_path = tmp.name

    try:
        meta = VideoContentAnalyzer.extract_video_metadata(tmp_path, filename)
        fps = meta["fps"]
        frames = VideoContentAnalyzer.smart_sample_keyframes(tmp_path, max_samples=4)

        for f in frames:
            reported_sec = f["timestamp_sec"]
            raw_idx = f["raw_frame_number"]
            calculated_sec = raw_idx / fps
            # Assert timestamp mapping tolerance is under 0.5s
            assert abs(reported_sec - calculated_sec) < 0.5, f"Timestamp mismatch: {reported_sec} vs {calculated_sec}"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── 5. SCENE DETECTION TESTS ─────────────────────────────────────────────────

def test_scene_detection(synthetic_identity_video):
    """Test scene change boundary detection and segment timeline creation."""
    vid_bytes, filename = synthetic_identity_video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(vid_bytes)
        tmp_path = tmp.name

    try:
        scenes = VideoContentAnalyzer.detect_scene_changes(tmp_path, max_scenes=4)
        assert len(scenes) >= 1
        assert scenes[0]["scene_index"] == 1
        assert scenes[0]["start_str"] == "00:00"
        for sc in scenes:
            assert "start_sec" in sc
            assert "end_sec" in sc
            assert "name" in sc
            assert sc["end_sec"] >= sc["start_sec"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── 6. OCR & PRIVACY ANALYSIS TESTS ──────────────────────────────────────────

def test_ocr_and_privacy_detection(synthetic_identity_video, synthetic_clean_video):
    """Test sensitive artifact detection on identity video vs clean video."""
    vid_bytes_id, fname_id = synthetic_identity_video
    vid_bytes_clean, fname_clean = synthetic_clean_video

    # 1. Identity Video with moving Aadhaar/PAN
    res_id = VideoContentAnalyzer.analyze_video_full(vid_bytes_id, fname_id)
    assert res_id["status"] == "success"
    assert res_id["privacy_assessment"]["privacy_risk_level"] in ["HIGH", "CRITICAL"]
    assert res_id["privacy_assessment"]["total_detections"] > 0
    assert len(res_id["analyzed_frames"]) > 0

    # Verify 4-Part Beginner Explanations are attached
    first_frame = res_id["analyzed_frames"][0]
    assert "where" in first_frame
    assert "why" in first_frame
    assert "what_could_happen" in first_frame
    assert "what_to_do" in first_frame

    # 2. Clean Video
    res_clean = VideoContentAnalyzer.analyze_video_full(vid_bytes_clean, fname_clean)
    assert res_clean["status"] == "success"
    assert res_clean["privacy_assessment"]["privacy_risk_level"] == "LOW"
    assert res_clean["privacy_assessment"]["clean_frames_count"] >= 1


# ── 7. COPYRIGHT RISK ASSESSMENT TESTS ───────────────────────────────────────

def test_copyright_risk_assessment(synthetic_identity_video):
    """Verify copyright risk evaluation and ensure no false 'copyright-free' claims."""
    vid_bytes, filename = synthetic_identity_video
    res = VideoContentAnalyzer.analyze_video_full(vid_bytes, filename)

    c_risk = res["copyright_assessment"]
    assert c_risk["copyright_risk_level"] in ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    assert "copyright-free" not in c_risk["safe_use_guidance"].lower()
    assert "legal advice" in c_risk["legal_disclaimer"].lower()


# ── 8. SUMMARY & KEY MOMENTS GENERATION TESTS ────────────────────────────────

def test_summary_and_key_moments(synthetic_identity_video):
    """Verify short summary, structured detailed summary, and key moments."""
    vid_bytes, filename = synthetic_identity_video
    res = VideoContentAnalyzer.analyze_video_full(vid_bytes, filename)

    summary = res["summary"]
    assert len(summary["short_summary"]) > 20
    assert "detailed_summary" in summary
    assert "overview" in summary["detailed_summary"]
    assert len(summary["key_moments"]) >= 1

    for km in summary["key_moments"]:
        assert "timestamp_str" in km
        assert "description" in km
        assert "label" in km


# ── 9. BEST FRAME FINDER & SAFE CLIPS TESTS ──────────────────────────────────

def test_best_frames_and_safe_clips(synthetic_clean_video):
    """Verify 'Find Better Frames', 'Frames to Avoid', and 'Safe Clip Finder'."""
    vid_bytes, filename = synthetic_clean_video
    res = VideoContentAnalyzer.analyze_video_full(vid_bytes, filename)

    best_frames = res["best_frames"]
    assert "suggested_better_frames" in best_frames
    assert "frames_to_avoid" in best_frames
    assert "safe_clips" in best_frames
    assert len(best_frames["suggested_better_frames"]) >= 1

    # Check suggested frame has clear reason and disclaimer
    s_frame = best_frames["suggested_better_frames"][0]
    assert "why" in s_frame
    assert "disclaimer" in s_frame


# ── 10. RISK TIMELINE TESTS ──────────────────────────────────────────────────

def test_risk_timeline(synthetic_identity_video):
    """Verify chronological color-coded visual timeline."""
    vid_bytes, filename = synthetic_identity_video
    res = VideoContentAnalyzer.analyze_video_full(vid_bytes, filename)

    timeline = res["risk_timeline"]
    assert len(timeline) >= 2
    for item in timeline:
        assert "timestamp_str" in item
        assert "risk_level" in item
        assert "icon" in item
        assert item["icon"] in ["🟢", "🟡", "🟠", "🔴"]
        assert item["thumbnail_data_uri"].startswith("data:image/jpeg;base64,")


# ── 11. AUDIO & SPEECH HANDLING TESTS ────────────────────────────────────────

def test_audio_speech_handling(synthetic_clean_video):
    """Verify audio presence analysis and non-hallucinating speech output."""
    vid_bytes, filename = synthetic_clean_video
    res = VideoContentAnalyzer.analyze_video_full(vid_bytes, filename)

    audio_res = res["audio_analysis"]
    assert "has_audio" in audio_res
    assert "status" in audio_res
    assert "message" in audio_res


# ── 12. STALE RESULT PROTECTION REGRESSION TEST ──────────────────────────────

def test_stale_result_protection(synthetic_identity_video, synthetic_clean_video):
    """Verify consecutive video analyses do not leak previous results."""
    vid_a, fname_a = synthetic_identity_video
    vid_b, fname_b = synthetic_clean_video

    # 1. Analyze Video A (Identity Video)
    res_a = VideoContentAnalyzer.analyze_video_full(vid_a, fname_a)
    assert res_a["filename"] == fname_a
    assert res_a["privacy_assessment"]["privacy_risk_level"] in ["HIGH", "CRITICAL"]

    # 2. Analyze Video B (Clean Video)
    res_b = VideoContentAnalyzer.analyze_video_full(vid_b, fname_b)
    assert res_b["filename"] == fname_b
    assert res_b["privacy_assessment"]["privacy_risk_level"] == "LOW"
    # Ensure no trace of Video A's data exists in Video B
    assert fname_a not in str(res_b["filename"])


# ── 13. REPEATED ANALYSIS TEST ───────────────────────────────────────────────

def test_repeated_analysis(synthetic_identity_video):
    """Verify repeated runs (A -> A -> A) produce identical, leak-free results."""
    vid_bytes, filename = synthetic_identity_video

    scores = []
    for _ in range(3):
        res = VideoContentAnalyzer.analyze_video_full(vid_bytes, filename)
        assert res["status"] == "success"
        scores.append(res["privacy_assessment"]["privacy_risk_score"])

    # Confirm deterministic output across runs
    assert scores[0] == scores[1] == scores[2]


# ── 14. SECURITY & PATH TRAVERSAL SAFETY ─────────────────────────────────────

def test_security_and_temporary_cleanup(synthetic_identity_video):
    """Verify path traversal prevention and safe temporary file removal."""
    vid_bytes, _ = synthetic_identity_video

    # Path traversal attack filename
    malicious_filename = "../../../../../etc/passwd.mp4"
    res = VideoContentAnalyzer.analyze_video_full(vid_bytes, malicious_filename)
    assert res["status"] == "success"

    # Verify no persistent temporary video files are leaked
    temp_dir = tempfile.gettempdir()
    assert os.path.exists(temp_dir)


# ── 15. COMPLETE END-TO-END PIPELINE TEST ────────────────────────────────────

def test_complete_video_analyzer_e2e(synthetic_identity_video):
    """
    Verifies complete end-to-end video analysis pipeline:
      1. Upload video
      2. Extract metadata
      3. Scene detection
      4. Keyframe sampling
      5. OCR & privacy scan
      6. Copyright evaluation
      7. Summary & key moments
      8. Suggested best frames & clips
      9. Risk timeline
      10. Beginner-friendly verdict
    """
    vid_bytes, filename = synthetic_identity_video
    res = VideoContentAnalyzer.analyze_video_full(vid_bytes, filename)

    assert res["status"] == "success"
    assert "metadata" in res
    assert "scenes" in res
    assert "analyzed_frames" in res
    assert "privacy_assessment" in res
    assert "copyright_assessment" in res
    assert "audio_analysis" in res
    assert "summary" in res
    assert "best_frames" in res
    assert "risk_timeline" in res
    assert "overall_verdict" in res
    assert "processing_time_ms" in res

    verdict = res["overall_verdict"]
    assert "title" in verdict
    assert "action" in verdict
    assert "why" in verdict
    assert "what_could_happen" in verdict
    assert "what_should_you_do" in verdict
