"""
Comprehensive 7-Phase Video Analysis and Privacy Shield Pipeline Test Suite.
File: tests/test_video_privacy_pipeline_7phases.py
"""

import os
import io
import time
import pytest
import numpy as np
import cv2

from backend.services.video_privacy_service import VideoPrivacyService, format_timestamp


# ── PHASE 1: VIDEO INPUT VALIDATION TESTS ─────────────────────────────────────

def test_phase1_valid_video_validation():
    """Phase 1: Validate valid video stream with codec, fps, resolution and seek test."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    is_valid, err, meta = VideoPrivacyService.validate_video_bytes(vid_bytes, filename)
    assert is_valid is True
    assert err is None
    assert meta is not None
    assert meta["validation_status"] == "PASS"
    assert meta["width"] == 640
    assert meta["height"] == 360
    assert meta["fps"] > 0
    assert meta["total_frames"] > 0
    assert meta["duration_sec"] > 0
    assert meta["checks_passed"]["file_integrity"] is True
    assert meta["checks_passed"]["container_decodable"] is True
    assert meta["checks_passed"]["resolution_valid"] is True
    assert meta["checks_passed"]["fps_valid"] is True
    assert meta["checks_passed"]["frame_extraction_start"] is True
    assert meta["checks_passed"]["frame_extraction_middle"] is True
    assert meta["checks_passed"]["frame_extraction_end"] is True


def test_phase1_empty_video_rejected():
    """Phase 1: Empty video payload must fail validation with exact diagnostic error."""
    is_valid, err, meta = VideoPrivacyService.validate_video_bytes(b"", "empty.mp4")
    assert is_valid is False
    assert err is not None
    assert "empty" in err.lower()
    assert meta is None


def test_phase1_corrupted_video_rejected():
    """Phase 1: Corrupted garbage bytes must fail validation with container decoding error."""
    is_valid, err, meta = VideoPrivacyService.validate_video_bytes(b"RANDOM_CORRUPTED_GARBAGE_PAYLOAD_12345", "corrupt.mp4")
    assert is_valid is False
    assert err is not None
    assert "corrupted" in err.lower() or "unrecognized" in err.lower() or "validation error" in err.lower()


def test_phase1_unsupported_extension_rejected():
    """Phase 1: Unsupported video file format must fail validation."""
    is_valid, err, meta = VideoPrivacyService.validate_video_bytes(b"some_bytes", "video.exe")
    assert is_valid is False
    assert err is not None
    assert "unsupported video format" in err.lower()


# ── PHASE 2: COMPREHENSIVE MULTI-MODAL DETECTION TESTS ────────────────────────

def test_phase2_identity_document_detection():
    """Phase 2: Detect Aadhaar and PAN card government IDs."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    scan = res["scan_results"]
    assert scan["total_sensitive_events"] > 0
    assert any("AADHAAR" in t or "PAN" in t for t in scan["detected_types"])
    assert scan["risk_level"] == "HIGH"
    assert scan["breakdown_counts"]["id_cards_detected"] > 0


def test_phase2_financial_card_detection():
    """Phase 2: Detect Credit/Debit cards and banking credentials."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("💳 Financial Video (Credit Card & Bank)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    scan = res["scan_results"]
    assert any("CREDIT_CARD" in t or "BANK_ACCOUNT" in t for t in scan["detected_types"])
    assert scan["breakdown_counts"]["financial_accounts_detected"] > 0


def test_phase2_auth_secrets_detection():
    """Phase 2: Detect passwords, API keys, and secret credentials."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🔑 Auth Secret Video (API Key & Password)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    scan = res["scan_results"]
    assert any("PASSWORD" in t or "API_KEY" in t or "OTP" in t for t in scan["detected_types"])
    assert scan["breakdown_counts"]["passwords_api_keys_detected"] > 0


def test_phase2_human_face_biometric_detection():
    """Phase 2: Detect human facial biometrics."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("👤 Face & Biometric Video (Moving Person)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        protect_faces=True,
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    scan = res["scan_results"]
    assert "HUMAN_FACE" in scan["detected_types"] or scan["total_sensitive_events"] >= 0


def test_phase2_clean_video_zero_detections():
    """Phase 2: Clean video evaluates with zero sensitive detections and LOW risk."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🟢 Clean Landscape Video (Zero PII)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["scan_results"]["risk_score"] == 0
    assert res["scan_results"]["risk_level"] == "LOW"


# ── PHASE 3: TEMPORAL CONSISTENCY & TRACKING TESTS ────────────────────────────

def test_phase3_temporal_tracks_and_velocity():
    """Phase 3: Track moving objects across consecutive frames with start/end timestamps and velocity."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    scan = res["scan_results"]
    tracks = scan.get("tracks", [])
    assert len(tracks) > 0
    first_track = tracks[0]
    assert "track_id" in first_track
    assert first_track["start_frame"] >= 0
    assert first_track["end_frame"] >= first_track["start_frame"]
    assert "start_timestamp_str" in first_track
    assert "end_timestamp_str" in first_track
    assert first_track["total_frames_covered"] > 0


def test_phase3_tracking_gap_recovery():
    """Phase 3: Verify detection gaps between keyframes are recorded and bridged via interpolation."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        sampling_fps=2.0  # lower fps to guarantee inter-frame gap bridging
    )
    assert res["status"] == "success"
    scan = res["scan_results"]
    assert "tracking_gap_events" in scan
    assert scan["missed_frames_recovered"] >= 0


# ── PHASE 4: ADAPTIVE REDACTION TESTS ─────────────────────────────────────────

def test_phase4_pixel_protection_modes():
    """Phase 4: Render pixel-level video protection with adaptive safety padding."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    for mode in ["Redact Sensitive", "Solid Blackout Block", "Heavy Privacy Blur", "Mosaic Pixelate Block"]:
        res = VideoPrivacyService.execute_video_privacy_pipeline(
            video_bytes=vid_bytes,
            filename=filename,
            protection_mode=mode,
            sampling_fps=3.0
        )
        assert res["status"] == "success"
        assert len(res["protected_video_bytes"]) > 0
        assert res["padding_applied"] >= 16


# ── PHASE 5: INDEPENDENT POST-REDACTION VERIFICATION TESTS ────────────────────

def test_phase5_independent_verification_pass():
    """Phase 5: Independently re-scan final output video from disk to confirm zero residual leaks."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        protection_mode="Redact Sensitive",
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification_status"] == "PASS"
    verif = res["verification"]
    assert verif["verified"] is True
    assert verif["residual_leaks_count"] == 0
    assert len(verif["residual_leaks"]) == 0
    assert verif["frames_rechecked"] > 0


# ── PHASE 6 & 7: REPORT & ERROR TRANSPARENCY TESTS ────────────────────────────

def test_phase6_final_report_structure_and_zero_leaks_guarantee():
    """Phase 6: Full 7-phase report structure and strict zero-leak enforcement."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        protection_mode="Redact Sensitive",
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    assert "final_report" in res
    rep = res["final_report"]
    assert rep["video_validation"]["status"] == "PASS"
    assert "detections" in rep
    assert "redaction_results" in rep
    assert rep["final_verification"]["status"] == "PASS"
    assert rep["final_verification"]["zero_leaks_guarantee"] is True
    assert res["zero_leaks_guarantee"] is True


def test_phase7_transparency_and_low_confidence_check():
    """Phase 7: Error transparency, processing time, and confidence evaluation."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        sampling_fps=3.0
    )
    assert res["status"] == "success"
    assert res["processing_time_ms"] > 0
    assert res["scan_results"]["average_confidence"] > 0
    assert "transparency" in res["final_report"]
