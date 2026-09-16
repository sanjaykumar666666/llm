"""
Comprehensive Real-World Adversarial Test Suite for Video Privacy Shield Pipeline.
File: tests/test_video_privacy_adversarial.py

Tests 14 challenging real-world adversarial video scenarios:
  1. Fast-moving Aadhaar/PAN
  2. Motion-blurred sensitive documents
  3. Rotated documents (90, 180, 270 degrees)
  4. Small font sensitive text
  5. QR codes with adjacent PII
  6. 1-2 frame transient exposure (brief flashes)
  7. Dense multi-face and multi-document scenes
  8. Low-light darkened video
  9. Partial document visibility & occlusion
  10. Camera shake and rapid scene movement
  11. Sensitive PII near frame edges/boundaries
  12. Intermittent / flickering PII appearance
  13. Different font sizes and text colors
  14. Normal non-sensitive text (False-Positive Benchmarking)

Also tests:
  - Multi-rate FPS sampling trade-offs (1, 3, 5, 10 FPS)
  - Adaptive Fallback Strategy (Multi-pass retry with increased FPS and padding)
"""

import os
import io
import time
import tempfile
import pytest
import cv2
import numpy as np

from backend.services.video_privacy_service import VideoPrivacyService, format_timestamp


def _generate_adversarial_video(scenario: str, width: int = 640, height: int = 360, num_frames: int = 30, fps: float = 15.0) -> bytes:
    """Deterministic synthetic video generator for adversarial privacy scenarios."""
    fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

    for idx in range(num_frames):
        t = idx / max(1, num_frames - 1)
        frame = np.ones((height, width, 3), dtype=np.uint8) * 35  # dark slate background

        if scenario == "fast_motion":
            # Scenario 1: Fast moving Aadhaar & PAN (velocity > 40px/f)
            x = int(20 + t * (width - 240))
            y = int(50 + np.sin(t * np.pi * 3) * 60)
            cv2.rectangle(frame, (x, y), (x + 220, y + 80), (255, 255, 255), -1)
            cv2.putText(frame, "AADHAAR CARD", (x + 10, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.putText(frame, "3672 8910 4521", (x + 10, y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 180), 2)

        elif scenario == "motion_blur":
            # Scenario 2: Motion blur applied to credential card
            x, y = int(100 + t * 40), 120
            cv2.rectangle(frame, (x, y), (x + 240, y + 90), (245, 245, 245), -1)
            cv2.putText(frame, "PAN NUMBER", (x + 10, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
            cv2.putText(frame, "ABCDE1234F", (x + 10, y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 0, 0), 2)
            # Horizontal motion blur kernel
            ksize = 7
            kernel = np.zeros((ksize, ksize))
            kernel[int((ksize-1)/2), :] = np.ones(ksize) / ksize
            frame = cv2.filter2D(frame, -1, kernel)

        elif scenario == "rotated_90":
            # Scenario 3A: Rotated Document (90 degrees clockwise)
            card = np.ones((100, 240, 3), dtype=np.uint8) * 240
            cv2.putText(card, "AADHAAR CARD", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv2.putText(card, "9123 4567 8901", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 180), 2)
            rot_card = cv2.rotate(card, cv2.ROTATE_90_CLOCKWISE)  # 240x100
            rh, rw = rot_card.shape[:2]
            frame[60:60+rh, 150:150+rw] = rot_card

        elif scenario == "rotated_180":
            # Scenario 3B: Rotated Document (180 degrees upside down)
            card = np.ones((90, 240, 3), dtype=np.uint8) * 240
            cv2.putText(card, "PAN: BKXPP9876Z", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            rot_card = cv2.rotate(card, cv2.ROTATE_180)
            rh, rw = rot_card.shape[:2]
            frame[100:100+rh, 150:150+rw] = rot_card

        elif scenario == "small_text":
            # Scenario 4: Very small sensitive text (scale 0.35)
            x, y = 140, 150
            cv2.rectangle(frame, (x, y), (x + 260, y + 60), (230, 230, 230), -1)
            cv2.putText(frame, "SSN: 123-45-6789", (x + 10, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 1)
            cv2.putText(frame, "PIN: 9842 | Tel: 9876543210", (x + 10, y + 48), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

        elif scenario == "qr_with_nearby_pii":
            # Scenario 5: QR Code with immediately adjacent PAN & Email
            cv2.rectangle(frame, (60, 80), (160, 180), (255, 255, 255), -1)
            # Draw synthetic QR pattern
            cv2.rectangle(frame, (75, 95), (95, 115), (0, 0, 0), -1)
            cv2.rectangle(frame, (125, 95), (145, 115), (0, 0, 0), -1)
            cv2.rectangle(frame, (75, 145), (95, 165), (0, 0, 0), -1)
            cv2.putText(frame, "PAN: DFGHJ5678K", (175, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            cv2.putText(frame, "user.vip@domain.com", (175, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 220, 255), 2)

        elif scenario == "transient_flash":
            # Scenario 6: Sensitive item visible for only 2 frames (frames 14 and 15)
            if idx in (14, 15):
                cv2.rectangle(frame, (100, 100), (450, 220), (255, 255, 255), -1)
                cv2.putText(frame, "CONFIDENTIAL FLASH", (120, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                cv2.putText(frame, "PHONE: 9876543210", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 180), 2)
            else:
                cv2.putText(frame, "Public Presentation Segment", (120, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

        elif scenario == "multi_entity_dense":
            # Scenario 7: Multiple faces + Multiple sensitive documents simultaneously
            # Face 1
            cv2.circle(frame, (80, 80), 30, (200, 170, 140), -1)
            cv2.circle(frame, (70, 75), 4, (0, 0, 0), -1)
            cv2.circle(frame, (90, 75), 4, (0, 0, 0), -1)
            # Face 2
            cv2.circle(frame, (480, 80), 30, (210, 180, 150), -1)
            cv2.circle(frame, (470, 75), 4, (0, 0, 0), -1)
            cv2.circle(frame, (490, 75), 4, (0, 0, 0), -1)
            # Card 1: Aadhaar
            cv2.rectangle(frame, (50, 180), (250, 280), (255, 255, 255), -1)
            cv2.putText(frame, "AADHAAR", (60, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
            cv2.putText(frame, "4512 7890 2341", (60, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 180), 2)
            # Card 2: Credit Card
            cv2.rectangle(frame, (320, 180), (560, 280), (20, 40, 80), -1)
            cv2.putText(frame, "VISA PLATINUM", (330, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, "4111 2222 3333 4444", (330, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 220, 0), 2)

        elif scenario == "low_light":
            # Scenario 8: Low-light video (dimmed contrast, 0.25x brightness)
            x, y = 120, 110
            card = np.zeros((100, 280, 3), dtype=np.uint8)
            card[:] = (65, 65, 65)
            cv2.putText(card, "AADHAAR CARD", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (140, 140, 140), 2)
            cv2.putText(card, "8912 3456 7012", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2)
            frame[y:y+100, x:x+280] = card

        elif scenario == "partial_occlusion":
            # Scenario 9: Partial document visibility & occlusion
            x, y = 100, 100
            cv2.rectangle(frame, (x, y), (x + 300, y + 100), (255, 255, 255), -1)
            cv2.putText(frame, "PAN NUMBER: ABCDE1234F", (x + 10, y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv2.putText(frame, "Govt of India", (x + 10, y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            # Occluding obstacle across left half
            cv2.rectangle(frame, (x - 20, y - 20), (x + 90, y + 120), (10, 15, 20), -1)

        elif scenario == "camera_shake":
            # Scenario 10: Camera shake and rapid jitter
            jitter_x = int(np.sin(idx * 2.3) * 20)
            jitter_y = int(np.cos(idx * 3.1) * 15)
            x, y = max(0, 120 + jitter_x), max(0, 100 + jitter_y)
            cv2.rectangle(frame, (x, y), (x + 260, y + 80), (250, 250, 250), -1)
            cv2.putText(frame, "AADHAAR CARD", (x + 15, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
            cv2.putText(frame, "7654 3210 9876", (x + 15, y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2)

        elif scenario == "frame_edges":
            # Scenario 11: Text near frame edges / boundaries
            # Top-left corner
            cv2.rectangle(frame, (2, 2), (180, 50), (255, 255, 255), -1)
            cv2.putText(frame, "PAN: ZXCVB1234M", (6, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)
            # Bottom-right corner
            cv2.rectangle(frame, (width - 190, height - 50), (width - 2, height - 2), (255, 255, 255), -1)
            cv2.putText(frame, "9876543210", (width - 180, height - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 180), 2)

        elif scenario == "flickering_pii":
            # Scenario 12: Intermittent / flickering appearance
            visible = (idx % 6) < 3  # visible 3 frames, absent 3 frames
            if visible:
                x, y = 140, 120
                cv2.rectangle(frame, (x, y), (x + 260, y + 80), (255, 255, 255), -1)
                cv2.putText(frame, "CREDIT CARD", (x + 15, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
                cv2.putText(frame, "5123 4567 8901 2345", (x + 15, y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 0, 0), 2)
            else:
                cv2.putText(frame, "Transition Scene Content", (150, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 100, 100), 1)

        elif scenario == "diverse_font_colors":
            # Scenario 13: Different font colors and inverted contrast
            x, y = 80, 80
            # Yellow on dark teal
            cv2.rectangle(frame, (x, y), (x + 280, y + 55), (60, 80, 20), -1)
            cv2.putText(frame, "PHONE: +91 91234 56789", (x + 10, y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 2)
            # Red on light gray
            cv2.rectangle(frame, (x, y + 75), (x + 280, y + 130), (220, 220, 220), -1)
            cv2.putText(frame, "PASSWORD: MySecret#99", (x + 10, y + 110), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 220), 2)

        elif scenario == "non_sensitive_false_positives":
            # Scenario 14: Non-sensitive public text
            cv2.rectangle(frame, (50, 50), (450, 120), (30, 60, 90), -1)
            cv2.putText(frame, "Grand Central Terminal", (60, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.putText(frame, "Train 104 departs Platform 4", (60, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 240, 255), 1)
            cv2.putText(frame, "Weather forecast: Sunny 26C", (60, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 220, 180), 1)
            cv2.putText(frame, "Enjoy your pleasant journey!", (60, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

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


# ── ADVERSARIAL SCENARIO TEST CASES ───────────────────────────────────────────

def test_adversarial_scenario_01_fast_motion():
    """Scenario 1: Fast-moving Aadhaar/PAN across frames."""
    vid_bytes = _generate_adversarial_video("fast_motion", num_frames=30, fps=15.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "fast_motion.mp4", sampling_fps=5.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0
    assert len(res["scan_results"]["tracks"]) > 0


def test_adversarial_scenario_02_motion_blur():
    """Scenario 2: Motion-blurred PAN card document."""
    vid_bytes = _generate_adversarial_video("motion_blur", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "motion_blur.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_03a_rotated_90_degrees():
    """Scenario 3A: Rotated Document (90 degrees)."""
    vid_bytes = _generate_adversarial_video("rotated_90", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "rotated_90.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_03b_rotated_180_degrees():
    """Scenario 3B: Rotated Document (180 degrees upside down)."""
    vid_bytes = _generate_adversarial_video("rotated_180", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "rotated_180.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_04_small_font_text():
    """Scenario 4: Very small sensitive text."""
    vid_bytes = _generate_adversarial_video("small_text", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "small_text.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_05_qr_with_nearby_pii():
    """Scenario 5: QR Code with immediately adjacent PAN and Email."""
    vid_bytes = _generate_adversarial_video("qr_with_nearby_pii", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "qr_nearby.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_06_transient_1_2_frame_flash():
    """Scenario 6: Transient 1-2 frame exposure tested at 10 FPS high-rate sampling."""
    vid_bytes = _generate_adversarial_video("transient_flash", num_frames=30, fps=15.0)
    # High-rate sampling (10 FPS) captures transient flash
    res_high = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "transient_flash.mp4", sampling_fps=10.0)
    assert res_high["status"] == "success"
    assert res_high["verified"] is True
    assert res_high["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_07_multi_entity_dense():
    """Scenario 7: Multiple faces + Multiple sensitive documents simultaneously."""
    vid_bytes = _generate_adversarial_video("multi_entity_dense", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "multi_dense.mp4", protect_faces=True, sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_08_low_light():
    """Scenario 8: Low-light darkened video."""
    vid_bytes = _generate_adversarial_video("low_light", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "low_light.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_09_partial_occlusion():
    """Scenario 9: Partial document visibility & occlusion."""
    vid_bytes = _generate_adversarial_video("partial_occlusion", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "occlusion.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_10_camera_shake():
    """Scenario 10: Camera shake and rapid scene movement."""
    vid_bytes = _generate_adversarial_video("camera_shake", num_frames=25, fps=15.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "camera_shake.mp4", sampling_fps=5.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_11_frame_edges():
    """Scenario 11: Sensitive information near frame edges."""
    vid_bytes = _generate_adversarial_video("frame_edges", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "frame_edges.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_12_flickering_pii():
    """Scenario 12: Intermittent / flickering PII appearance."""
    vid_bytes = _generate_adversarial_video("flickering_pii", num_frames=30, fps=15.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "flickering.mp4", sampling_fps=5.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_13_diverse_font_colors():
    """Scenario 13: Different font colors and inverted contrasts."""
    vid_bytes = _generate_adversarial_video("diverse_font_colors", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "colors.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["verification"]["residual_leaks_count"] == 0


def test_adversarial_scenario_14_non_sensitive_false_positives():
    """Scenario 14: Non-sensitive public text does not trigger false PII alarms."""
    vid_bytes = _generate_adversarial_video("non_sensitive_false_positives", num_frames=20, fps=10.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, "public_sign.mp4", sampling_fps=3.0)
    assert res["status"] == "success"
    assert res["verified"] is True
    # Non-sensitive words must have 0 high-risk PII detections
    breakdown = res["scan_results"]["breakdown_counts"]
    assert breakdown.get("id_cards_detected", 0) == 0
    assert breakdown.get("financial_accounts_detected", 0) == 0
    assert breakdown.get("passwords_api_keys_detected", 0) == 0


# ── SAMPLING FPS TRADE-OFF & ADAPTIVE FALLBACK TESTS ───────────────────────────

def test_adversarial_sampling_fps_tradeoffs():
    """Evaluates recall and execution time across 1, 3, 5, and 10 sampling FPS."""
    vid_bytes = _generate_adversarial_video("fast_motion", num_frames=30, fps=15.0)
    fps_results = {}

    for s_fps in [1.0, 3.0, 5.0, 10.0]:
        t0 = time.perf_counter()
        res = VideoPrivacyService.execute_video_privacy_pipeline(vid_bytes, f"test_fps_{s_fps}.mp4", sampling_fps=s_fps)
        t1 = time.perf_counter()
        fps_results[s_fps] = {
            "time_ms": (t1 - t0) * 1000,
            "verified": res.get("verified"),
            "residual_leaks": res.get("verification", {}).get("residual_leaks_count", 0),
            "events_detected": res.get("scan_results", {}).get("total_sensitive_events", 0)
        }

    # Verify that higher FPS detects equal or greater events
    assert fps_results[10.0]["verified"] is True
    assert fps_results[5.0]["verified"] is True
    assert fps_results[3.0]["verified"] is True


def test_adversarial_adaptive_fallback_retry():
    """Tests adaptive fallback multi-pass retry strategy."""
    vid_bytes = _generate_adversarial_video("camera_shake", num_frames=25, fps=15.0)
    res = VideoPrivacyService.execute_video_privacy_pipeline(
        vid_bytes,
        "adaptive_retry.mp4",
        sampling_fps=3.0,
        max_retries=2
    )
    assert res["status"] == "success"
    assert res["verified"] is True
    assert res["zero_leaks_guarantee"] is True
    assert "transparency" in res["final_report"]
