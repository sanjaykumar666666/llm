"""
Test Suite: Input-Level Sensitive Credential Detection & Security Warning System.
File: tests/test_credential_detection.py

Covers:
  1. Password detection (including number-only passwords)
  2. OTP detection (4-8 digit codes with context)
  3. PIN detection (4-6 digit codes with context)
  4. API key / token detection
  5. Auth token / secret key disclosure
  6. Bank / Net Banking / UPI credential detection
  7. Educational question safety (false positive avoidance)
  8. Context-free number safety (no false positives)
  9. Sanitizer masking/redaction
  10. Evaluator CRITICAL_SECRET_TYPES coverage
"""

import sys
import os
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from privacy_engine.context_detector import ContextAwareEntityDetector
from privacy_engine.sanitizer import PrivacySanitizer
from privacy_engine.evaluator import CRITICAL_SECRET_TYPES


# ── Test Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def detector():
    return ContextAwareEntityDetector()


@pytest.fixture
def sanitizer():
    return PrivacySanitizer()


# ── 1. Password Detection ────────────────────────────────────────────────────

class TestPasswordDetection:
    """Test password disclosure detection including number-only passwords."""

    def test_password_with_keyword_assignment(self, detector):
        """'password=SuperSecret123' should be detected as CREDENTIAL_PASSWORD."""
        entities = detector.detect_entities("password=SuperSecret123")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_PASSWORD" for e in entities)

    def test_password_is_phrase(self, detector):
        """'my password is 1234567890' should detect the number as a password."""
        entities = detector.detect_entities("my password is 1234567890")
        assert len(entities) > 0
        cred_types = [e["entity_type"] for e in entities]
        assert "CREDENTIAL_PASSWORD" in cred_types

    def test_password_number_only(self, detector):
        """'my password 123456' — number-only string with password context = credential."""
        entities = detector.detect_entities("my password 123456 ")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_PASSWORD" for e in entities)

    def test_password_with_colon(self, detector):
        """'admin password: MyP@ss2024' should be detected."""
        entities = detector.detect_entities("admin password: MyP@ss2024")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_PASSWORD" for e in entities)

    def test_password_severity_critical(self, detector):
        """Password detections should have CRITICAL severity."""
        entities = detector.detect_entities("password=secret123")
        pwd_entities = [e for e in entities if e["entity_type"] == "CREDENTIAL_PASSWORD"]
        assert len(pwd_entities) > 0
        assert all(e["severity"] == "CRITICAL" for e in pwd_entities)


# ── 2. OTP Detection ─────────────────────────────────────────────────────────

class TestOTPDetection:
    """Test One-Time Password (OTP) detection."""

    def test_otp_is_phrase(self, detector):
        """'my OTP is 456789' should be detected as CREDENTIAL_OTP."""
        entities = detector.detect_entities("my OTP is 456789")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_OTP" for e in entities)

    def test_otp_colon_assignment(self, detector):
        """'OTP: 123456' should be detected."""
        entities = detector.detect_entities("OTP: 123456")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_OTP" for e in entities)

    def test_otp_4_digit(self, detector):
        """'otp is 4567' — 4-digit OTP should be detected."""
        entities = detector.detect_entities("otp is 4567")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_OTP" for e in entities)

    def test_otp_8_digit(self, detector):
        """'my OTP is 12345678' — 8-digit OTP should be detected."""
        entities = detector.detect_entities("my OTP is 12345678")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_OTP" for e in entities)

    def test_verification_code(self, detector):
        """'verification code is 987654' should be detected as OTP."""
        entities = detector.detect_entities("verification code is 987654")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_OTP" for e in entities)

    def test_2fa_code(self, detector):
        """'2fa code is 123456' should be detected."""
        entities = detector.detect_entities("2fa code is 123456")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_OTP" for e in entities)

    def test_otp_severity_critical(self, detector):
        """OTP detections should have CRITICAL severity."""
        entities = detector.detect_entities("my OTP is 456789")
        otp_entities = [e for e in entities if e["entity_type"] == "CREDENTIAL_OTP"]
        assert len(otp_entities) > 0
        assert all(e["severity"] == "CRITICAL" for e in otp_entities)


# ── 3. PIN Detection ─────────────────────────────────────────────────────────

class TestPINDetection:
    """Test Personal Identification Number (PIN) detection."""

    def test_atm_pin(self, detector):
        """'ATM PIN is 5678' should be detected as CREDENTIAL_PIN."""
        entities = detector.detect_entities("ATM PIN is 5678")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_PIN" for e in entities)

    def test_pin_colon(self, detector):
        """'my pin: 1234' should be detected."""
        entities = detector.detect_entities("my pin: 1234")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_PIN" for e in entities)

    def test_debit_card_pin(self, detector):
        """'debit card PIN is 9876' should be detected."""
        entities = detector.detect_entities("debit card PIN is 9876")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_PIN" for e in entities)

    def test_upi_pin(self, detector):
        """'upi pin: 4567' should be detected."""
        entities = detector.detect_entities("upi pin: 4567")
        assert len(entities) > 0
        pin_types = [e["entity_type"] for e in entities]
        assert "CREDENTIAL_PIN" in pin_types or "CREDENTIAL_BANK_LOGIN" in pin_types

    def test_pin_severity_critical(self, detector):
        """PIN detections should have CRITICAL severity."""
        entities = detector.detect_entities("ATM PIN is 5678")
        pin_entities = [e for e in entities if e["entity_type"] == "CREDENTIAL_PIN"]
        assert len(pin_entities) > 0
        assert all(e["severity"] == "CRITICAL" for e in pin_entities)


# ── 4. Auth Token / Secret Key Detection ─────────────────────────────────────

class TestAuthTokenDetection:
    """Test authentication token and secret key disclosure detection."""

    def test_auth_token_disclosure(self, detector):
        """'my auth token is abc123xyz789def0' should be detected."""
        entities = detector.detect_entities("my auth token is abc123xyz789def0")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_AUTH_TOKEN" for e in entities)

    def test_session_token(self, detector):
        """'session token is eyJhbGciOiJIUzI1' should be detected."""
        entities = detector.detect_entities("session token is eyJhbGciOiJIUzI1")
        assert len(entities) > 0
        token_types = [e["entity_type"] for e in entities]
        assert "CREDENTIAL_AUTH_TOKEN" in token_types or "JWT_TOKEN" in token_types

    def test_secret_key_disclosure(self, detector):
        """'my secret key is sk_live_abcdef123456' should be detected."""
        entities = detector.detect_entities("my secret key is sk_live_abcdef123456")
        assert len(entities) > 0
        key_types = [e["entity_type"] for e in entities]
        assert "CREDENTIAL_SECRET_KEY" in key_types or "GENERIC_API_SECRET" in key_types


# ── 5. Bank / Net Banking Credential Detection ──────────────────────────────

class TestBankCredentialDetection:
    """Test banking credential detection."""

    def test_net_banking_password(self, detector):
        """'net banking password is MyBankP@ss' should be detected."""
        entities = detector.detect_entities("net banking password is MyBankP@ss")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_BANK_LOGIN" for e in entities)

    def test_mobile_banking_pin(self, detector):
        """'mobile banking pin is 654321' should be detected."""
        entities = detector.detect_entities("mobile banking pin is 654321")
        assert len(entities) > 0
        assert any(e["entity_type"] == "CREDENTIAL_BANK_LOGIN" for e in entities)

    def test_upi_pin_disclosure(self, detector):
        """'upi pin is 1234' should be detected as bank credential."""
        entities = detector.detect_entities("upi pin is 1234")
        assert len(entities) > 0
        bank_types = [e["entity_type"] for e in entities]
        assert "CREDENTIAL_BANK_LOGIN" in bank_types or "CREDENTIAL_PIN" in bank_types


# ── 6. Educational Questions — No False Positives ────────────────────────────

class TestEducationalSafety:
    """Ensure educational questions are NOT flagged as credential leaks."""

    def test_what_is_password(self, detector):
        """'What is a password?' should be educational, no credential detection."""
        assert detector.is_educational_inquiry("What is a password?") is True

    def test_how_to_reset_password(self, detector):
        """'How to reset a password?' should be educational."""
        assert detector.is_educational_inquiry("How to reset a password?") is True

    def test_password_best_practices(self, detector):
        """'password guidelines and best practices' should be educational."""
        assert detector.is_educational_inquiry("password guidelines and best practices") is True

    def test_explain_otp(self, detector):
        """'What is an OTP and how does it work?' — no credential detection."""
        entities = detector.detect_entities("What is an OTP and how does it work?")
        credential_entities = [e for e in entities if e["entity_type"].startswith("CREDENTIAL_")]
        assert len(credential_entities) == 0

    def test_explain_api_key(self, detector):
        """'explain how API key authentication works' — no credential detection."""
        assert detector.is_educational_inquiry("explain how API key authentication works") is True


# ── 7. Context-Free Numbers — No False Positives ────────────────────────────

class TestContextFreeNumbers:
    """Numbers without credential context words should NOT be treated as credentials."""

    def test_plain_number(self, detector):
        """'1234567890' alone should NOT be detected as a credential."""
        entities = detector.detect_entities("1234567890")
        credential_entities = [e for e in entities if e["entity_type"].startswith("CREDENTIAL_")]
        assert len(credential_entities) == 0

    def test_phone_number_context(self, detector):
        """'Call me at 1234567890' — number should NOT be credential."""
        entities = detector.detect_entities("Call me at 1234567890")
        credential_entities = [e for e in entities if e["entity_type"].startswith("CREDENTIAL_")]
        assert len(credential_entities) == 0

    def test_quantity_number(self, detector):
        """'Order 456789 items' — number should NOT be credential."""
        entities = detector.detect_entities("Order 456789 items")
        credential_entities = [e for e in entities if e["entity_type"].startswith("CREDENTIAL_")]
        assert len(credential_entities) == 0


# ── 8. Sanitizer Redaction ───────────────────────────────────────────────────

class TestSanitizerRedaction:
    """Test that credentials are properly redacted/masked."""

    def test_password_redacted(self, sanitizer):
        """Password should be replaced with [PASSWORD_REDACTED]."""
        result = sanitizer.sanitize_text("password=SuperSecret123", mode="REDACT")
        assert "[PASSWORD_REDACTED]" in result["sanitized_text"]
        assert "SuperSecret123" not in result["sanitized_text"]

    def test_otp_redacted(self, sanitizer):
        """OTP should be replaced with [OTP_REDACTED]."""
        result = sanitizer.sanitize_text("OTP: 456789", mode="REDACT")
        assert "[OTP_REDACTED]" in result["sanitized_text"]
        assert "456789" not in result["sanitized_text"]

    def test_pin_redacted(self, sanitizer):
        """PIN should be replaced with [PIN_REDACTED]."""
        result = sanitizer.sanitize_text("ATM pin: 5678", mode="REDACT")
        assert "[PIN_REDACTED]" in result["sanitized_text"]
        assert "5678" not in result["sanitized_text"]

    def test_bank_credential_redacted(self, sanitizer):
        """Bank credential should be redacted (either BANK_CREDENTIAL or PASSWORD placeholder)."""
        result = sanitizer.sanitize_text("net banking password is MyBankP@ss", mode="REDACT")
        san_text = result["sanitized_text"]
        # Accepts either specific bank credential or generic password redaction
        assert "[BANK_CREDENTIAL_REDACTED]" in san_text or "[PASSWORD_REDACTED]" in san_text
        assert "MyBankP@ss" not in san_text


# ── 9. Evaluator CRITICAL_SECRET_TYPES Coverage ────────────────────────────

class TestEvaluatorCoverage:
    """Test that new credential types are in CRITICAL_SECRET_TYPES."""

    def test_otp_in_critical(self):
        assert "CREDENTIAL_OTP" in CRITICAL_SECRET_TYPES

    def test_pin_in_critical(self):
        assert "CREDENTIAL_PIN" in CRITICAL_SECRET_TYPES

    def test_auth_token_in_critical(self):
        assert "CREDENTIAL_AUTH_TOKEN" in CRITICAL_SECRET_TYPES

    def test_secret_key_in_critical(self):
        assert "CREDENTIAL_SECRET_KEY" in CRITICAL_SECRET_TYPES

    def test_bank_login_in_critical(self):
        assert "CREDENTIAL_BANK_LOGIN" in CRITICAL_SECRET_TYPES

    def test_password_in_critical(self):
        assert "CREDENTIAL_PASSWORD" in CRITICAL_SECRET_TYPES


# ── 10. Integration: Full Analysis Pipeline ──────────────────────────────────

class TestFullPipelineIntegration:
    """End-to-end integration tests through run_full_analysis."""

    def test_password_blocks(self):
        """'My password 1234567890' should result in BLOCK decision."""
        from backend.services.evidence_risk import run_full_analysis
        result = run_full_analysis("My password 1234567890 ")
        assert result["decision"] == "BLOCK"
        assert result["risk_score"] >= 80

    def test_otp_blocks(self):
        """'my OTP is 456789' should result in BLOCK decision."""
        from backend.services.evidence_risk import run_full_analysis
        result = run_full_analysis("my OTP is 456789")
        assert result["decision"] == "BLOCK"

    def test_pin_blocks(self):
        """'ATM PIN is 5678' should result in BLOCK decision."""
        from backend.services.evidence_risk import run_full_analysis
        result = run_full_analysis("ATM PIN is 5678")
        assert result["decision"] == "BLOCK"

    def test_safe_question_allows(self):
        """'What is a password manager?' should result in ALLOW decision."""
        from backend.services.evidence_risk import run_full_analysis
        result = run_full_analysis("What is a password manager?")
        assert result["decision"] == "ALLOW"
        assert result["risk_score"] == 0

    def test_security_advisory_generated(self):
        """Credential BLOCK should include a security_advisory."""
        from backend.services.evidence_risk import run_full_analysis
        result = run_full_analysis("my OTP is 456789")
        assert result.get("security_advisory") is not None
        assert len(result["security_advisory"]["items"]) > 0

    def test_credential_types_populated(self):
        """Credential BLOCK should populate credential_types_detected."""
        from backend.services.evidence_risk import run_full_analysis
        result = run_full_analysis("password=SuperSecret123")
        assert len(result.get("credential_types_detected", [])) > 0
