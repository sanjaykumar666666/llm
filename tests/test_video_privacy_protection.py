"""
Unit and Integration Tests for Video Privacy Protection, Tracking & Verification.
File: tests/test_video_privacy_protection.py
"""

import os
import pytest
import numpy as np
import cv2

from backend.services.video_privacy_service import VideoPrivacyService


def test_video_validation_valid_preset():
    """Test video validation on a valid generated preset video."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    is_valid, err_msg, meta = VideoPrivacyService.validate_video_bytes(vid_bytes, filename)
    assert is_valid is True
    assert err_msg is None
    assert meta is not None
    assert meta["width"] == 640
    assert meta["height"] == 360
    assert meta["total_frames"] > 0
    assert meta["fps"] > 0


def test_video_validation_empty_bytes():
    """Test video validation rejects empty bytes gracefully."""
    is_valid, err_msg, meta = VideoPrivacyService.validate_video_bytes(b"", "empty.mp4")
    assert is_valid is False
    assert "empty" in err_msg.lower()
    assert meta is None


def test_video_validation_corrupted_bytes():
    """Test video validation rejects corrupted files safely."""
    is_valid, err_msg, meta = VideoPrivacyService.validate_video_bytes(b"corrupted_garbage_bytes_12345", "test.mp4")
    assert is_valid is False
    assert meta is None


def test_clean_video_no_sensitive_data():
    """Test clean landscape video evaluates to 0% LOW risk with no sensitive events."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🟢 Clean Landscape Video (Zero PII)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        protection_mode="Redact Sensitive",
        protect_faces=True,
        protect_qr_barcodes=True,
        sampling_fps=3.0,
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["scan_results"]["risk_score"] == 0
    assert res["scan_results"]["risk_level"] == "LOW"


def test_identity_video_detection_and_protection():
    """Test video containing Aadhaar & PAN triggers HIGH risk and is verified protected."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        protection_mode="Redact Sensitive",
        protect_faces=True,
        protect_qr_barcodes=True,
        sampling_fps=3.0,
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification_status"] == "PROTECTED"
    assert res["scan_results"]["risk_score"] >= 85
    assert res["scan_results"]["risk_level"] == "HIGH"
    assert len(res["protected_video_bytes"]) > 0


def test_financial_video_detection():
    """Test video containing credit card and bank account triggers critical detections."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("💳 Financial Video (Credit Card & Bank)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        protection_mode="Redact Sensitive",
        protect_faces=True,
        protect_qr_barcodes=True,
        sampling_fps=3.0,
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["scan_results"]["risk_score"] >= 85
    assert len(res["protected_video_bytes"]) > 0


def test_auth_secret_video_detection():
    """Test video containing passwords and API keys triggers critical detections."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🔑 Auth Secret Video (API Key & Password)")
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        video_bytes=vid_bytes,
        filename=filename,
        protection_mode="Redact Sensitive",
        protect_faces=True,
        protect_qr_barcodes=True,
        sampling_fps=3.0,
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["scan_results"]["risk_score"] >= 85


def test_temporal_tracking_interpolation():
    """Test temporal tracking interpolates bounding boxes across intermediate frames."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    is_valid, _, meta = VideoPrivacyService.validate_video_bytes(vid_bytes, filename)
    assert is_valid is True

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(vid_bytes)
        tmp_path = tmp.name

    try:
        scan_res = VideoPrivacyService.scan_video_with_temporal_tracking(
            tmp_path, sampling_fps=2.0, protect_faces=True, protect_qr_barcodes=True
        )
        total_frames = scan_res["total_frames"]
        frame_regions = scan_res["frame_regions"]
        assert len(frame_regions) == total_frames
        # Verify regions exist across multiple continuous frames
        frames_with_protection = [f for f, regs in frame_regions.items() if len(regs) > 0]
        assert len(frames_with_protection) > 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_all_protection_modes_execute_cleanly():
    """Test all 5 video pixel protection modes execute cleanly without error."""
    vid_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
    modes = [
        "Redact Sensitive",
        "Blur Sensitive",
        "Pixelate Sensitive",
        "Blackout Sensitive",
        "Blur All"
    ]
    for mode in modes:
        res = VideoPrivacyService.execute_video_privacy_pipeline(
            video_bytes=vid_bytes,
            filename=filename,
            protection_mode=mode,
            protect_faces=True,
            protect_qr_barcodes=True,
            sampling_fps=2.0,
        )
        assert res["status"] == "success"
        assert len(res["protected_video_bytes"]) > 0
        assert res["protection_mode"] == mode
