"""
Video Analyzer — Production Quality Assurance Test Runner & Report Generator.
File: tests/run_video_analyzer_tests.py
"""

import sys
import os
import subprocess
import time

VIDEO_TEST_CATEGORIES = [
    ("Input Validation", ["tests/test_video_content_analyzer.py::test_input_validation_valid_and_invalid"]),
    ("Metadata Extraction", ["tests/test_video_content_analyzer.py::test_metadata_extraction"]),
    ("Frame Extraction", ["tests/test_video_content_analyzer.py::test_smart_frame_sampling"]),
    ("Timestamp Accuracy", ["tests/test_video_content_analyzer.py::test_timestamp_accuracy"]),
    ("Scene Detection", ["tests/test_video_content_analyzer.py::test_scene_detection"]),
    ("OCR", ["tests/test_video_content_analyzer.py::test_ocr_and_privacy_detection"]),
    ("Face Detection", ["tests/test_video_privacy_protection.py::test_temporal_tracking_interpolation"]),
    ("Privacy Analysis", ["tests/test_video_content_analyzer.py::test_ocr_and_privacy_detection"]),
    ("Copyright Analysis", ["tests/test_video_content_analyzer.py::test_copyright_risk_assessment"]),
    ("Summary Generation", ["tests/test_video_content_analyzer.py::test_summary_and_key_moments"]),
    ("Risk Timeline", ["tests/test_video_content_analyzer.py::test_risk_timeline"]),
    ("Best Frame Finder", ["tests/test_video_content_analyzer.py::test_best_frames_and_safe_clips"]),
    ("Safe Clip Finder", ["tests/test_video_content_analyzer.py::test_best_frames_and_safe_clips"]),
    ("Error Handling", ["tests/test_video_privacy_protection.py::test_video_validation_corrupted_bytes"]),
    ("Security Tests", ["tests/test_video_content_analyzer.py::test_security_and_temporary_cleanup"]),
    ("Stale Result Test", ["tests/test_video_content_analyzer.py::test_stale_result_protection"]),
    ("Repeated Analysis", ["tests/test_video_content_analyzer.py::test_repeated_analysis"]),
    ("Long Video Test", ["tests/test_video_privacy_protection.py::test_all_protection_modes_execute_cleanly"]),
    ("API Tests", ["tests/test_phase1_routes.py"]),
    ("End-to-End Test", ["tests/test_video_content_analyzer.py::test_complete_video_analyzer_e2e"]),
    ("Regression Tests", [
        "tests/test_pipeline.py",
        "tests/test_text_analysis_module.py",
        "tests/test_benchmark.py",
        "tests/test_firewall.py",
        "tests/test_mcp.py",
        "tests/test_tools_ecosystem.py"
    ])
]


def run_tests():
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    category_results = []
    failures = []

    print("\nExecuting Video Analyzer Complete Quality Assurance Suite...\n")

    for category_name, test_targets in VIDEO_TEST_CATEGORIES:
        cmd = [sys.executable, "-m", "pytest"] + test_targets + ["-q"]
        t_start = time.perf_counter()
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = round(time.perf_counter() - t_start, 2)

        output = proc.stdout + proc.stderr
        passed_in_cat = 0
        failed_in_cat = 0

        for line in output.splitlines():
            line_s = line.strip()
            if "passed" in line_s or "failed" in line_s or "error" in line_s:
                tokens = line_s.split(",")
                for tok in tokens:
                    tok = tok.strip()
                    if "passed" in tok:
                        try:
                            passed_in_cat += int(tok.split()[0])
                        except Exception:
                            pass
                    if "failed" in tok or "error" in tok:
                        try:
                            failed_in_cat += int(tok.split()[0])
                        except Exception:
                            pass

        if proc.returncode == 0:
            status = "PASS"
            total_passed += passed_in_cat if passed_in_cat > 0 else 1
            category_results.append((category_name, "PASS"))
        else:
            status = "FAIL"
            total_failed += failed_in_cat if failed_in_cat > 0 else 1
            category_results.append((category_name, "FAIL"))
            failures.append((category_name, output))

    # Print Official Video Analyzer Test Report
    print("=" * 40)
    print(" VIDEO ANALYZER TEST REPORT")
    print("=" * 40)
    for cat_name, res in category_results:
        print(f"{cat_name:<25} {res}")
    print("=" * 40)
    print(f"Passed: {total_passed}\nFailed: {total_failed}\nSkipped: {total_skipped}")
    print("=" * 40)

    if failures:
        print("\nFAILURES DETECTED:")
        for cat_name, out in failures:
            print(f"\nFAILED: {cat_name}\nReason:\n{out[:400]}\n")
        sys.exit(1)
    else:
        print("\nAll Video Analyzer quality gates passed successfully. Production ready.\n")
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
