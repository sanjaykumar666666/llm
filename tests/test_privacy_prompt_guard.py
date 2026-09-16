"""
Comprehensive Test Suite for Privacy-Sensitive Prompt Guard, Detection, Risk Scoring,
Blocking, Sanitization, and Zero Data Leakage.
File: tests/test_privacy_prompt_guard.py
"""

import pytest
from privacy_engine.context_detector import ContextAwareEntityDetector
from privacy_engine.sanitizer import PrivacySanitizer
from backend.services.privacy_risk_service import PrivacyRiskService
from backend.services.evidence_risk import run_full_analysis, calculate_evidence_risk


class TestPrivacyPromptGuard:
    @classmethod
    def setup_class(cls):
        cls.detector = ContextAwareEntityDetector()
        cls.sanitizer = PrivacySanitizer()

    # ── 1. PERSONAL INFORMATION (PII) TESTS ──────────────────────────────────
    def test_pii_detection_and_sanitization(self):
        prompt = "My name is John Doe, email is john.doe@enterprise.org, and phone is +91 9876543210. Aadhaar is 9918-4019-2011."
        entities = self.detector.detect_entities(prompt)
        ent_types = [e["entity_type"] for e in entities]

        assert "EMAIL_ADDRESS" in ent_types
        assert "PHONE_NUMBER" in ent_types
        assert "GOVERNMENT_ID_AADHAAR" in ent_types

        # Sanitize prompt
        san_res = self.sanitizer.sanitize_text(prompt, mode="REDACT")
        san_text = san_res["sanitized_text"]

        assert "john.doe@enterprise.org" not in san_text
        assert "9876543210" not in san_text
        assert "9918-4019-2011" not in san_text
        assert "[EMAIL_REDACTED]" in san_text
        assert "[PHONE_REDACTED]" in san_text
        assert "[AADHAAR_REDACTED]" in san_text

    def test_pan_and_ssn_sanitization(self):
        prompt = "US SSN is 123-45-6789 and India PAN card is ABCDE1234F."
        san_res = self.sanitizer.sanitize_text(prompt, mode="REDACT")
        san_text = san_res["sanitized_text"]

        assert "123-45-6789" not in san_text
        assert "ABCDE1234F" not in san_text
        assert "[SSN_REDACTED]" in san_text
        assert "[PAN_REDACTED]" in san_text

    # ── 2. PASSWORDS & CREDENTIALS (BLOCK) TESTS ─────────────────────────────
    def test_password_strict_blocking(self):
        prompt = "Deploy server with username=admin and password=SuperSecretP@ssw0rd!123 database=prod"
        analysis = run_full_analysis(prompt)

        assert analysis["decision"] == "BLOCK"
        assert analysis["risk_level"] == "CRITICAL"
        assert analysis["risk_score"] >= 80
        assert analysis["forward_prompt"] is None  # Blocked prompts must have None forward_prompt

    def test_otp_pin_and_api_key_blocking(self):
        # OTP
        otp_prompt = "My verification OTP is 849201 please verify my session"
        otp_analysis = run_full_analysis(otp_prompt)
        assert otp_analysis["decision"] == "BLOCK"
        assert otp_analysis["risk_level"] == "CRITICAL"

        # Cloud API Key
        api_prompt = "Use AWS key AKIAIOSFODNN7EXAMPLE to upload files"
        api_analysis = run_full_analysis(api_prompt)
        assert api_analysis["decision"] == "BLOCK"
        assert api_analysis["risk_level"] == "CRITICAL"

        # Database Connection URI
        db_prompt = "Connect to postgresql://root:SecretPassword99@db.prod.internal:5432/customers"
        db_analysis = run_full_analysis(db_prompt)
        assert db_analysis["decision"] == "BLOCK"
        assert db_analysis["risk_level"] == "CRITICAL"

    # ── 3. FINANCIAL DETAILS TESTS ───────────────────────────────────────────
    def test_card_with_cvv_blocking(self):
        prompt = "Billing card number 4532 1234 5678 9010 expiration 12/28 CVV 882"
        analysis = run_full_analysis(prompt)

        assert analysis["decision"] == "BLOCK"
        assert analysis["risk_level"] == "CRITICAL"

    def test_bank_account_and_upi_sanitization(self):
        prompt = "Transfer funds to bank account 98765432109876 or UPI ID alex.smith@okhdfcbank."
        entities = self.detector.detect_entities(prompt)
        ent_types = [e["entity_type"] for e in entities]

        assert "BANK_ACCOUNT_NUMBER" in ent_types or "UPI_ID" in ent_types

        san_res = self.sanitizer.sanitize_text(prompt, mode="REDACT")
        san_text = san_res["sanitized_text"]

        assert "alex.smith@okhdfcbank" not in san_text
        assert "[UPI_ID_REDACTED]" in san_text or "[BANK_ACCOUNT_REDACTED]" in san_text

    # ── 4. MEDICAL RECORDS & PHI TESTS ───────────────────────────────────────
    def test_medical_diagnosis_and_prescription_detection(self):
        prompt = "Patient intake MRN-489201: diagnosed with Type 2 Diabetes and prescribed Metformin 500mg daily."
        entities = self.detector.detect_entities(prompt)
        ent_types = [e["entity_type"] for e in entities]

        assert any("MEDICAL" in t or "PRESCRIPTION" in t for t in ent_types)

        # Full analysis should detect health risk
        analysis = run_full_analysis(prompt)
        assert analysis["risk_score"] >= 60
        assert analysis["sanitized_text"] is not None

        # Zero leakage: specific health diagnosis and dosage sanitized
        assert "[HEALTH_DATA_REDACTED]" in analysis["sanitized_text"]
        assert "MRN-489201" not in analysis["sanitized_text"]

    # ── 5. CONFIDENTIAL COMPANY INFORMATION & TRADE SECRETS TESTS ────────────
    def test_company_confidential_and_trade_secret_detection(self):
        prompt = "Confidential Project Titan: Q3 revenue was $15.4M with proprietary trade secret under strict NDA."
        entities = self.detector.detect_entities(prompt)
        ent_types = [e["entity_type"] for e in entities]

        assert "CONFIDENTIAL_BUSINESS_INFO" in ent_types

        priv_analysis = PrivacyRiskService.analyze_message(prompt)
        assert priv_analysis["overall_risk"]["score"] >= 7

        san_res = self.sanitizer.sanitize_text(prompt, mode="REDACT")
        assert "[CONFIDENTIAL_REDACTED]" in san_res["sanitized_text"]

    # ── 6. SAFE GENERAL QUERIES (0% RISK / ALLOW) TESTS ──────────────────────
    def test_safe_scientific_and_educational_prompts(self):
        safe_prompts = [
            "Explain how photosynthesis works in green plants and why it is important.",
            "What is a password manager and how does it help protect user accounts?",
            "Write a Python function to compute the Fibonacci sequence using memoization.",
            "What are the main causes of climate change according to climate scientists?",
        ]
        for prompt in safe_prompts:
            analysis = run_full_analysis(prompt)
            assert analysis["decision"] == "ALLOW", f"Failed for prompt: {prompt}"
            assert analysis["risk_score"] == 0, f"Expected 0% risk for safe prompt: {prompt}"
            assert analysis["risk_level"] == "LOW"
            assert analysis["forward_prompt"] == prompt

    # ── 7. IDEMPOTENCY & STABILITY TESTS ─────────────────────────────────────
    def test_sanitization_idempotency(self):
        prompt = "User email [EMAIL_REDACTED] and phone [PHONE_REDACTED] with card [CREDIT_CARD_REDACTED]."
        san_res = self.sanitizer.sanitize_text(prompt, mode="REDACT")
        assert san_res["sanitized_text"] == prompt


if __name__ == "__main__":
    pytest.main(["-v", "tests/test_privacy_prompt_guard.py"])
