"""
Universal Content Analyzer — Quality Assurance Test Runner & Report Generator.
File: tests/run_universal_analyzer_tests.py
"""

import sys
import os
import subprocess
import time

TEST_CATEGORIES = [
    ("Platform Detection", [
        "tests/test_platform_detection.py",
        "tests/test_content_adapters.py",
        "tests/test_youtube_analysis.py",
        "tests/test_instagram_analysis.py",
        "tests/test_facebook_analysis.py",
        "tests/test_x_analysis.py",
        "tests/test_tiktok_analysis.py"
    ]),
    ("URL Validation", ["tests/test_url_validation.py"]),
    ("Privacy Detection", ["tests/test_privacy_analysis.py"]),
    ("PII Detection", ["tests/test_pii_detection.py"]),
    ("Copyright Analysis", ["tests/test_copyright_analysis.py"]),
    ("Frame Analysis", [
        "tests/test_frame_analysis.py",
        "tests/test_media_processing.py"
    ]),
    ("Recommendation Engine", ["tests/test_safe_use_recommendations.py"]),
    ("Beginner Explanations", [
        "tests/test_risk_explanations.py",
        "tests/test_summary_generation.py"
    ]),
    ("Stale Result Protection", ["tests/test_stale_result_protection.py"]),
    ("Error Handling", ["tests/test_error_handling.py"]),
    ("Security Tests", ["tests/test_security.py"]),
    ("API Tests", ["tests/test_phase1_routes.py"]),
    ("End-to-End Tests", ["tests/test_universal_analyzer_e2e.py"]),
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

    print("\nExecuting Universal Content Analyzer Complete Quality Assurance Suite...\n")

    for category_name, test_files in TEST_CATEGORIES:
        existing_files = [f for f in test_files if os.path.exists(f)]
        if not existing_files:
            category_results.append((category_name, "SKIPPED"))
            total_skipped += 1
            continue

        cmd = [sys.executable, "-m", "pytest"] + existing_files + ["-q"]
        t_start = time.perf_counter()
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = round(time.perf_counter() - t_start, 2)

        output = proc.stdout + proc.stderr
        # Parse passed count from pytest output (e.g., '14 passed in 0.45s')
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

    # Print Official Report
    print("=" * 40)
    print(" UNIVERSAL ANALYZER TEST REPORT")
    print("=" * 40)
    for cat_name, res in category_results:
        print(f"{cat_name:<25} {res}")
    print("=" * 40)
    print(f"TOTAL:\nPassed: {total_passed}\nFailed: {total_failed}\nSkipped: {total_skipped}")
    print("=" * 40)

    if failures:
        print("\nFAILURES DETECTED:")
        for cat_name, out in failures:
            print(f"\nFAILED: {cat_name}\nReason:\n{out[:400]}\n")
        sys.exit(1)
    else:
        print("\nAll quality gates passed successfully. System is production ready.\n")
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
