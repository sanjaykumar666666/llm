"""
Automated Testing and Security Auditing Suite for Privacy Shield AI.
File Location: tests/test_firewall.py
"""

import sys
import io
from pathlib import Path

# Force UTF-8 encoding on standard output for Windows console support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.api import process_firewall_request
import config


def run_system_audit():
    print("=" * 70)
    print("   PRIVACY SHIELD AI -- SYSTEM SECURITY & AUDIT SUITE   ")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = 0

    def assert_test(test_name, condition, details=""):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if condition:
            passed_tests += 1
            print(f"[PASS] [OK] Scenario {total_tests}: {test_name}")
        else:
            print(f"[FAIL] [ERR] Scenario {total_tests}: {test_name} | {details}")

    # -------------------------------------------------------------------
    # CATEGORY 1: TEXT PROMPT SCENARIOS
    # -------------------------------------------------------------------
    print("\n--- CATEGORY 1: TEXT PROMPT SCENARIOS ---")

    # Scenario 1: Clean/Safe Query
    res1 = process_firewall_request(modality="text", text_content="What are the three laws of thermodynamics?")
    assert_test("Safe Text Query (ALLOW expected)", res1["action"] == "ALLOW", f"Got {res1['action']}")

    # Scenario 2: Single PII (Phone Number)
    res2 = process_firewall_request(modality="text", text_content="Contact my office at 9876543210 for appointment.")
    assert_test("Single PII Query (SANITIZE expected)", res2["action"] == "SANITIZE", f"Got {res2['action']}")
    assert_test("Sanitized Token Presence", "[PHONE_REDACTED]" in res2.get("sanitized_prompt", ""))

    # Scenario 3: Multiple PII Entities (Phone + Email + Credentials)
    res3 = process_firewall_request(modality="text", text_content="Email me at admin@company.com phone 9876543210 bank pin 4321")
    assert_test("Multi PII Query (BLOCK expected)", res3["action"] == "BLOCK", f"Got {res3['action']}")

    # Scenario 4: Critical Secret Key Exposure
    res4_secret = process_firewall_request(modality="text", text_content="Secret AWS Key AKIAIOSFODNN7EXAMPLE")
    assert_test("Critical Secret Key (BLOCK expected)", res4_secret["action"] == "BLOCK", f"Got {res4_secret['action']}")

    # -------------------------------------------------------------------
    # CATEGORY 2: IMAGE & DOCUMENT MEDIA SCENARIOS
    # -------------------------------------------------------------------
    print("\n--- CATEGORY 2: IMAGE & DOCUMENT MEDIA SCENARIOS ---")

    # Scenario 5: Clean Dummy Image Upload
    dummy_image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    res5 = process_firewall_request(modality="image", file_bytes=dummy_image_bytes, file_name="sample.png")
    assert_test("Clean Image Ingestion (No Crash)", res5["status"] == "success", f"Got status {res5['status']}")

    # Scenario 6: Document Ingestion
    doc_bytes = b"User Email: test@privacy-shield.org | Phone: +1-555-0199"
    res6 = process_firewall_request(modality="document", file_bytes=doc_bytes, file_name="data.txt")
    assert_test("Document Ingestion & Sanitization", res6["status"] == "success" and res6["action"] in ["SANITIZE", "BLOCK"], f"Got {res6.get('action')}")

    # Scenario 7: Unsupported File Extension
    res7 = process_firewall_request(modality="image", file_bytes=dummy_image_bytes, file_name="executable.exe")
    assert_test("Unsupported File Extension Handling", res7["status"] == "error", "Allowed invalid extension")

    # -------------------------------------------------------------------
    # CATEGORY 3: EDGE CASES & SYSTEM CONSTRAINTS
    # -------------------------------------------------------------------
    print("\n--- CATEGORY 3: EDGE CASES & SYSTEM SECURITY ---")

    # Scenario 8: Empty Text Prompt
    res8 = process_firewall_request(modality="text", text_content="   ")
    assert_test("Empty Text Prompt Validation", res8["status"] == "error", "Allowed empty string")

    # Scenario 9: Audit Log Security File Check
    audit_file = config.LOGS_DIR / "privacy_audit.json"
    assert_test("Privacy Audit Log File Exists", audit_file.exists(), f"Log missing at {audit_file}")

    # -------------------------------------------------------------------
    # AUDIT SUMMARY REPORT
    # -------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"   AUDIT SUMMARY: Passed {passed_tests} / {total_tests} Scenarios ({passed_tests/total_tests*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    run_system_audit()
