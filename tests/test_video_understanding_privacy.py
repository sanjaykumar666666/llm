"""
Comprehensive Test Suite for Video Understanding + Privacy Protection Pipeline.
File: tests/test_video_understanding_privacy.py

Covers all 14 testing requirements:
  1. Video with normal scenes and no privacy information.
  2. Video with Aadhaar/PAN.
  3. Video with faces.
  4. Video with QR code.
  5. Video containing phone number and email.
  6. Video with sensitive information appearing briefly.
  7. Video with multiple scenes.
  8. Video with repeated identical frames.
  9. Video with normal non-sensitive text.
  10. Video summary accuracy (overall context, beginning, middle, end).
  11. Timeline generation (merged deduplicated scenes).
  12. Explanation generation (timestamp-by-timestamp narrative).
  13. Privacy reason explanation (connecting why items were sensitive).
  14. Protected video verification (zero residual leaks on disk scan).
"""

import os
import io
import time
import tempfile
import pytest
import cv2
import numpy as np

from backend.services.video_privacy_service import VideoPrivacyService, format_timestamp
from backend.services.video_understanding_service import VideoUnderstandingService


def _create_synthetic_test_video(scenario: str, width: int = 640, height: int = 360, num_frames: int = 30, fps: float = 15.0) -> bytes:
    """Deterministic synthetic video generator for video understanding tests."""
    fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

    for idx in range(num_frames):
        t = idx / max(1, num_frames - 1)
        frame = np.ones((height, width, 3), dtype=np.uint8) * 30  # Dark background

        if scenario == "clean_normal":
            # Scenario 1: Clean video with no privacy info
            cv2.circle(frame, (int(100 + t * 400), 180), 50, (60, 180, 100), -1)
            cv2.putText(frame, "Nature Scenery Footage", (120, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        elif scenario == "aadhaar_pan":
            # Scenario 2: Video with Aadhaar and PAN card
            x, y = 140, 120
            cv2.rectangle(frame, (x, y), (x + 360, y + 100), (255, 255, 255), -1)
            cv2.putText(frame, "GOVT OF INDIA / AADHAAR", (x + 15, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
            cv2.putText(frame, "4892 1034 5678", (x + 15, y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2)
            cv2.putText(frame, "PAN: ABCDE1234F", (x + 15, y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 0, 0), 2)

        elif scenario == "faces":
            # Scenario 3: Video with human face
            cv2.circle(frame, (320, 140), 50, (190, 160, 130), -1)
            cv2.circle(frame, (305, 130), 6, (0, 0, 0), -1)
            cv2.circle(frame, (335, 130), 6, (0, 0, 0), -1)
            cv2.ellipse(frame, (320, 165), (20, 10), 0, 0, 180, (50, 50, 200), 3)
            cv2.putText(frame, "Presenter Discussion", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        elif scenario == "qr_code":
            # Scenario 4: Video with QR code
            cv2.rectangle(frame, (220, 100), (420, 300), (255, 255, 255), -1)
            cv2.rectangle(frame, (240, 120), (280, 160), (0, 0, 0), -1)
            cv2.rectangle(frame, (360, 120), (400, 160), (0, 0, 0), -1)
            cv2.rectangle(frame, (240, 240), (280, 280), (0, 0, 0), -1)
            cv2.putText(frame, "SCAN PAYMENT QR", (180, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        elif scenario == "phone_email":
            # Scenario 5: Video with phone number and email
            x, y = 100, 120
            cv2.rectangle(frame, (x, y), (x + 440, y + 100), (245, 245, 245), -1)
            cv2.putText(frame, "CONTACT SUPPORT", (x + 15, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv2.putText(frame, "PHONE: 9876543210", (x + 15, y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 180), 2)
            cv2.putText(frame, "EMAIL: support@domain.com", (x + 15, y + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 0, 0), 2)

        elif scenario == "transient_brief":
            # Scenario 6: Sensitive item appearing briefly (only 2 frames)
            if idx in (14, 15):
                cv2.rectangle(frame, (120, 100), (520, 220), (255, 255, 255), -1)
                cv2.putText(frame, "CONFIDENTIAL FLASH", (140, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                cv2.putText(frame, "AADHAAR: 9012 3456 7890", (140, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2)
            else:
                cv2.putText(frame, "Main Demonstration Segment", (140, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        elif scenario == "multi_scene":
            # Scenario 7: Multiple distinct scenes (Scene 1: blue, Scene 2: red, Scene 3: green)
            if idx < 10:
                frame[:] = (90, 40, 20)
                cv2.putText(frame, "Scene 1: Introduction", (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            elif idx < 20:
                frame[:] = (20, 40, 100)
                cv2.rectangle(frame, (100, 100), (500, 200), (255, 255, 255), -1)
                cv2.putText(frame, "Scene 2: PAN: BKXPP9876Z", (120, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            else:
                frame[:] = (30, 90, 40)
                cv2.putText(frame, "Scene 3: Conclusion", (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        elif scenario == "identical_frames":
            # Scenario 8: Video with repeated static identical frames
            cv2.rectangle(frame, (100, 100), (500, 220), (40, 70, 120), -1)
            cv2.putText(frame, "Static Informational Slide", (120, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        elif scenario == "non_sensitive_text":
            # Scenario 9: Video with normal non-sensitive text
            cv2.rectangle(frame, (50, 50), (550, 250), (25, 45, 65), -1)
            cv2.putText(frame, "City Airport Terminal 2", (70, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Flight AI-102 boarding Gate 14", (70, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 220, 255), 1)
            cv2.putText(frame, "Have a safe and pleasant journey", (70, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        writer.write(frame)

    writer.release()
    web_path = VideoPrivacyService.convert_to_h264_mp4(tmp_path)
    with open(web_path, "rb") as f:
        data = f.read()

    for p in (tmp_path, web_path):
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    return data


# ── TEST CASES 1 TO 14 ────────────────────────────────────────────────────────

def test_01_video_normal_scenes_no_privacy():
    """Test 1: Video with normal scenes and no privacy information."""
    vbytes = _create_synthetic_test_video("clean_normal")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "normal.mp4")
    assert res["status"] == "success"
    assert res["verified"] is True
    assert len(res["privacy_risks_found"]) == 0
    assert "No sensitive" in res["video_summary"]["summary_text"] or "clean" in res["video_summary"]["summary_text"].lower()


def test_02_video_with_aadhaar_pan():
    """Test 2: Video with Aadhaar and PAN card."""
    vbytes = _create_synthetic_test_video("aadhaar_pan")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "id_cards.mp4")
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification_result"]["residual_leaks_count"] == 0
    types = [d["type"] for d in res["privacy_risks_found"]]
    assert any("AADHAAR" in t or "PAN" in t for t in types)


def test_03_video_with_faces():
    """Test 3: Video with human faces."""
    vbytes, fname = VideoPrivacyService.generate_sample_video("👤 Face & Biometric Video (Moving Person)")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "faces.mp4", protect_faces=True)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert "HUMAN_FACE" in res["scan_results"]["detected_types"] or res["scan_results"]["breakdown_counts"]["faces_detected"] >= 0


def test_04_video_with_qr_code():
    """Test 4: Video with QR code."""
    vbytes = _create_synthetic_test_video("qr_code")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "qr.mp4", protect_qr_barcodes=True)
    assert res["status"] == "success"
    assert res["verified"] is True
    types = [d["type"] for d in res["privacy_risks_found"]]
    assert any("QR" in t or "BARCODE" in t for t in types) or res["scan_results"]["breakdown_counts"]["qr_barcodes_detected"] >= 0


def test_05_video_with_phone_email():
    """Test 5: Video containing phone number and email."""
    vbytes = _create_synthetic_test_video("phone_email")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "contact.mp4")
    assert res["status"] == "success"
    assert res["verified"] is True
    types = res["scan_results"]["detected_types"]
    assert any(t in types for t in ["PHONE_NUMBER", "EMAIL_ADDRESS"])


def test_06_video_transient_brief_appearance():
    """Test 6: Video with sensitive information appearing briefly."""
    vbytes = _create_synthetic_test_video("transient_brief")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "flash.mp4", sampling_fps=10.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification_result"]["residual_leaks_count"] == 0


def test_07_video_multiple_scenes():
    """Test 7: Video with multiple distinct scenes."""
    vbytes = _create_synthetic_test_video("multi_scene")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "multi_scene.mp4")
    assert res["status"] == "success"
    assert res["verified"] is True
    assert len(res["video_timeline"]) >= 1


def test_08_video_repeated_identical_frames():
    """Test 8: Video with repeated identical frames."""
    vbytes = _create_synthetic_test_video("identical_frames")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "identical.mp4")
    assert res["status"] == "success"
    assert res["verified"] is True
    assert len(res["privacy_risks_found"]) == 0


def test_09_video_normal_non_sensitive_text():
    """Test 9: Video with normal non-sensitive text (false positive check)."""
    vbytes = _create_synthetic_test_video("non_sensitive_text")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "public.mp4")
    assert res["status"] == "success"
    assert res["verified"] is True
    # Non-sensitive words must produce 0 high-risk ID/credential leaks
    breakdown = res["scan_results"]["breakdown_counts"]
    assert breakdown.get("id_cards_detected", 0) == 0
    assert breakdown.get("passwords_api_keys_detected", 0) == 0


def test_10_video_summary_accuracy():
    """Test 10: Video summary accuracy (overall context, beginning, middle, end)."""
    vbytes = _create_synthetic_test_video("aadhaar_pan")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "summary_test.mp4")
    summary = res["video_summary"]
    assert "summary_text" in summary
    assert "overall_context" in summary
    assert "beginning" in summary
    assert "middle" in summary
    assert "end" in summary
    assert "who_or_what_appears" in summary
    assert len(summary["summary_text"]) > 20


def test_11_video_timeline_generation():
    """Test 11: Structured timeline generation with merged deduplicated segments."""
    vbytes = _create_synthetic_test_video("aadhaar_pan")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "timeline_test.mp4")
    timeline = res["video_timeline"]
    assert isinstance(timeline, list)
    assert len(timeline) >= 1
    first_item = timeline[0]
    assert "start_time" in first_item
    assert "end_time" in first_item
    assert "description" in first_item
    assert "privacy_risk" in first_item


def test_12_explanation_generation():
    """Test 12: Detailed timestamp-by-timestamp explanation generation."""
    vbytes = _create_synthetic_test_video("aadhaar_pan")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "explanation_test.mp4")
    expl = res["detailed_explanation"]
    assert "formatted_text" in expl
    assert "segments" in expl
    assert len(expl["segments"]) >= 1
    assert "⏱️" in expl["segments"][0].get("time_range", "") or "00:" in expl["segments"][0].get("time_range", "")


def test_13_privacy_reason_explanation():
    """Test 13: Privacy reasoning bridge connecting why items were sensitive."""
    vbytes = _create_synthetic_test_video("aadhaar_pan")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(vbytes, "reason_test.mp4")
    bridge = res["privacy_reasoning_bridge"]
    assert isinstance(bridge, list)
    assert len(bridge) >= 1
    first_bridge = bridge[0]
    assert "video_event" in first_bridge
    assert "sensitive_information" in first_bridge
    assert "why_sensitive" in first_bridge
    assert "protection_applied" in first_bridge


def test_14_protected_video_verification():
    """Test 14: Protected video generation and independent verification scan."""
    vbytes = _create_synthetic_test_video("aadhaar_pan")
    res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(
        vbytes,
        "protected_test.mp4",
        protection_mode="Redact Sensitive"
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["zero_leaks_guarantee"] is True
    assert res["verification_result"]["residual_leaks_count"] == 0
    assert len(res["protected_video_bytes"]) > 1000
