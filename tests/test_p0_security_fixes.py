"""
Regression tests for Pipeline 1 — Critical Security Fixes & Single Source of Truth Alignment.
File: tests/test_p0_security_fixes.py
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from privacy_engine.context_detector import ContextAwareEntityDetector
from backend.services.evidence_risk import run_full_analysis


@pytest.fixture
def detector():
    return ContextAwareEntityDetector()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# FIX 1: PASSWORD DISCLOSURE DETECTION TESTS
# ==============================================================================

class TestPasswordDisclosureDetection:
    """Tests that realistic password disclosures are detected and educational questions are not."""

    @pytest.mark.parametrize("prompt, expected_val", [
        ("My database password is superSecretPassword123!", "superSecretPassword123!"),
        ("password: HelloWorld123!", "HelloWorld123!"),
        ("db password = Test@123", "Test@123"),
        ("my login password is Abc@12345", "Abc@12345"),
        ("server pwd is Secret123", "Secret123"),
        ("The admin password is AdminRoot#99", "AdminRoot#99"),
        ("application password: AppSecretToken2026", "AppSecretToken2026"),
    ])
    def test_password_disclosures_detected(self, detector, prompt, expected_val):
        entities = detector.detect_entities(prompt)
        assert len(entities) > 0, f"Expected password detection for: '{prompt}'"
        pwd_entities = [e for e in entities if "PASSWORD" in e["entity_type"]]
        assert len(pwd_entities) > 0, f"Expected CREDENTIAL_PASSWORD entity for: '{prompt}'"
        assert pwd_entities[0]["severity"] == "CRITICAL"

    @pytest.mark.parametrize("prompt", [
        "What is a strong password?",
        "How to hash a password using bcrypt?",
        "Explain the difference between password and token authentication.",
        "What are the best practices for password policy?",
        "Define a password manager and how it works.",
    ])
    def test_educational_password_queries_not_blocked(self, detector, prompt):
        assert detector.is_educational_inquiry(prompt) is True
        entities = detector.detect_entities(prompt)
        pwd_entities = [e for e in entities if "PASSWORD" in e["entity_type"]]
        assert len(pwd_entities) == 0, f"Educational query incorrectly flagged as password disclosure: '{prompt}'"

    def test_password_disclosure_evidence_risk_decision(self):
        prompt = "My database password is superSecretPassword123!"
        analysis = run_full_analysis(prompt)
        assert analysis["decision"] == "BLOCK"
        assert analysis["risk_score"] >= 65
        assert any(e["severity"] == "CRITICAL" for e in analysis["entities"])


# ==============================================================================
# FIX 2: BANK ACCOUNT DETECTION TESTS
# ==============================================================================

class TestBankAccountDetection:
    """Tests that contextual bank account disclosures are detected and non-financial numbers are not."""

    @pytest.mark.parametrize("prompt", [
        "bank account number 987654321098",
        "my account number is 987654321098",
        "send money to account 987654321098",
        "my bank account is 123456789012",
        "Please transfer money to bank account number 987654321098.",
        "beneficiary account: 554433221100",
        "payment to account 112233445566",
    ])
    def test_bank_account_disclosures_detected(self, detector, prompt):
        entities = detector.detect_entities(prompt)
        assert len(entities) > 0, f"Expected bank account detection for: '{prompt}'"
        bank_entities = [e for e in entities if "BANK" in e["entity_type"] or "ACCOUNT" in e["entity_type"]]
        assert len(bank_entities) > 0, f"Expected BANK_ACCOUNT entity for: '{prompt}'"

    @pytest.mark.parametrize("prompt", [
        "The population of the country is 1428627663 people.",
        "Order reference #987654321098 for the book shipment.",
        "Product SKU: 123456789012 in warehouse 4.",
    ])
    def test_non_bank_random_numbers_not_flagged_as_bank_account(self, detector, prompt):
        entities = detector.detect_entities(prompt)
        bank_entities = [e for e in entities if "BANK" in e["entity_type"]]
        assert len(bank_entities) == 0, f"Non-financial number incorrectly flagged as bank account: '{prompt}'"

    def test_bank_account_evidence_risk_detection(self):
        prompt = "Please transfer money to bank account number 987654321098."
        analysis = run_full_analysis(prompt)
        assert analysis["risk_score"] > 0
        assert len(analysis["entities"]) > 0
        assert analysis["decision"] in ("WARN", "BLOCK")


# ==============================================================================
# FIX 3 & 4: FRONTEND API ROUTE & BACKEND DECISION AUTHORITY TESTS
# ==============================================================================

class TestBackendAPIAuthoritativeRoutes:
    """Tests that /api/v1/privacy/analyze is live, authoritative, and returns genuine calculations."""

    def test_privacy_analyze_endpoint_registered_and_working(self, client):
        res = client.post("/api/v1/privacy/analyze", json={"text": "What is the capital of France?"})
        assert res.status_code == 200
        data = res.json()
        assert data["decision"] == "ALLOW"
        assert data["risk_score"] == 0
        assert data["is_demo_mode"] is False

    def test_privacy_analyze_endpoint_detects_sensitive_credentials(self, client):
        res = client.post("/api/v1/privacy/analyze", json={"text": "My database password is superSecretPassword123!"})
        assert res.status_code == 200
        data = res.json()
        assert data["decision"] == "BLOCK"
        assert data["can_send_to_llm"] is False
        assert data["risk_score"] >= 65
        assert len(data["detected_entities"]) > 0

    def test_privacy_analyze_endpoint_detects_bank_account(self, client):
        res = client.post("/api/v1/privacy/analyze", json={"text": "send money to account 987654321098"})
        assert res.status_code == 200
        data = res.json()
        assert data["risk_score"] > 0
        assert len(data["detected_entities"]) > 0


# ==============================================================================
# FIX 5: EXPLAINABILITY ENDPOINT TESTS (NO FAKE MOCK VALUES)
# ==============================================================================

class TestExplainabilityEndpoint:
    """Tests that /api/v1/explainability does not return fabricated mock values."""

    def test_explainability_text_returns_attributions(self, client):
        res = client.post("/api/v1/explainability", json={"modality": "Text", "content": "My email is test@example.com"})
        assert res.status_code == 200
        data = res.json()
        assert data["explainability_status"] == "available"
        assert isinstance(data["token_attributions"], list)
        # Ensure fake static values (0.1513, 0.1483) are not in the response
        weights = [fc.get("weight") for fc in data.get("feature_contributions", [])]
        assert 0.1513 not in weights
        assert 0.1483 not in weights

    def test_explainability_multimodal_returns_explicit_unavailable(self, client):
        res = client.post("/api/v1/explainability", json={"modality": "Image", "content": "base64_image_data"})
        assert res.status_code == 200
        data = res.json()
        assert data["explainability_status"] == "not_available"
        assert "not available" in data["message"].lower()
