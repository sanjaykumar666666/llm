"""
Comprehensive Test Suite for Context-Aware Privacy Risk System in Privacy Chat.
File: tests/test_context_aware_privacy_chat.py

Covers:
  1. Location Hierarchy (Country -> State -> City -> Locality -> Street -> Full Address -> Address+Phone)
  2. False Positive Prevention & General Knowledge Queries
  3. Contact Data (Phone, Email) with Secure Masking
  4. Government IDs (PAN, Aadhaar, Passport)
  5. Authentication Secrets (Passwords, OTPs, API Keys) with Zero Raw Leakage
  6. Context Sensitivity & Distinctions
  7. Cross-Message Cumulative Exposure & Multi-Turn Combination Risk
  8. Full /chat Integration & Privacy Card Payload Validation
"""

import pytest
from backend.services.privacy_risk_service import PrivacyRiskService
from backend.routes.chatbot import chat_endpoint, ChatRequest


# ── 1. LOCATION HIERARCHY TESTS ──────────────────────────────────────────────

def test_location_level1_country():
    """Level 1: Country-level disclosure (e.g. 'I am from India') -> MINIMAL."""
    res = PrivacyRiskService.analyze_message("I am from India")
    assert res["overall_risk"]["level"] in ("MINIMAL", "LOW")
    assert res["overall_risk"]["score"] <= 2
    assert any(d["type"] == "BROAD_LOCATION" for d in res["detections"])


def test_location_level2_state():
    """Level 2: State-level disclosure (e.g. 'I live in Tamil Nadu') -> LOW."""
    res = PrivacyRiskService.analyze_message("I live in Tamil Nadu")
    assert res["overall_risk"]["level"] == "LOW"
    assert res["overall_risk"]["score"] == 2
    assert any(d["type"] == "BROAD_LOCATION" for d in res["detections"])


def test_location_level3_city():
    """Level 3: City-level disclosure (e.g. 'I live in Krishnagiri') -> LOW."""
    res = PrivacyRiskService.analyze_message("I live in Krishnagiri")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "LOW"
    assert res["overall_risk"]["score"] in (2, 3)
    assert any(d["type"] == "GENERAL_LOCATION" for d in res["detections"])
    assert "Krishnagiri" in res["detections"][0]["masked_value"]


def test_location_level4_locality():
    """Level 4: Locality / Landmark (e.g. 'I live near Krishnagiri bus stand') -> LOW/MEDIUM."""
    res = PrivacyRiskService.analyze_message("I live near Krishnagiri bus stand")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] in ("LOW", "MEDIUM")
    assert res["overall_risk"]["score"] in (4, 5)


def test_location_level5_street():
    """Level 5: Street-level location (e.g. 'I live on Gandhi Road in Krishnagiri') -> MEDIUM."""
    res = PrivacyRiskService.analyze_message("I live on Gandhi Road in Krishnagiri")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "MEDIUM"
    assert res["overall_risk"]["score"] in (5, 6)


def test_location_level6_full_address():
    """Level 6: Full Address (House Number 24, Gandhi Street, Krishnagiri) -> HIGH."""
    res = PrivacyRiskService.analyze_message("House Number 24, Gandhi Street, Krishnagiri")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "HIGH"
    assert res["overall_risk"]["score"] in (7, 8)
    assert any(d["type"] == "EXACT_RESIDENTIAL_ADDRESS" for d in res["detections"])


def test_location_level7_full_address_plus_contact():
    """Level 7: Full Address + Phone together -> CRITICAL."""
    res = PrivacyRiskService.analyze_message("House Number 24, Gandhi Street, Krishnagiri. Phone 9876543210")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "CRITICAL"
    assert res["overall_risk"]["score"] in (9, 10)


# ── 2. FALSE POSITIVE PREVENTION TESTS ───────────────────────────────────────

@pytest.mark.parametrize("query", [
    "Krishnagiri is famous for mangoes.",
    "What is the weather in Krishnagiri?",
    "I like Chennai.",
    "Chennai is a big city.",
    "I have 3 dogs.",
    "Train number is 12671.",
    "The temperature is 32 degrees.",
    "Chapter 12.",
    "Explain how photosynthesis works.",
    "What is the capital of Tamil Nadu?",
    "Route from Bangalore to Krishnagiri",
])
def test_false_positive_prevention(query):
    """General knowledge questions and non-sensitive numbers must have 0 risk score."""
    res = PrivacyRiskService.analyze_message(query)
    assert res["has_privacy_risk"] is False
    assert res["overall_risk"]["score"] == 0
    assert res["overall_risk"]["level"] == "MINIMAL"
    assert len(res["detections"]) == 0


# ── 3. PERSONAL NAME TESTS ───────────────────────────────────────────────────

def test_personal_name_alone():
    """First name alone (e.g. 'My name is Arun') -> LOW/MINIMAL."""
    res = PrivacyRiskService.analyze_message("My name is Arun")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] in ("MINIMAL", "LOW")
    assert res["overall_risk"]["score"] in (1, 2)
    assert any(d["type"] == "PERSONAL_NAME" for d in res["detections"])


# ── 4. CONTACT INFORMATION TESTS ─────────────────────────────────────────────

def test_phone_number_masked():
    """Phone number disclosure -> MEDIUM risk with safe masking ******3210."""
    res = PrivacyRiskService.analyze_message("My phone number is 9876543210")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "MEDIUM"
    assert res["overall_risk"]["score"] == 5
    phone_det = next(d for d in res["detections"] if d["type"] == "PHONE_NUMBER")
    assert phone_det["masked_value"] == "******3210"
    assert "987654" not in phone_det["masked_value"]


def test_email_address_masked():
    """Email address disclosure -> LOW/MEDIUM risk with safe masking."""
    res = PrivacyRiskService.analyze_message("My email is example@email.com")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] in ("LOW", "MEDIUM")
    assert res["overall_risk"]["score"] in (3, 4)
    email_det = next(d for d in res["detections"] if d["type"] == "EMAIL_ADDRESS")
    assert email_det["masked_value"] == "e***@email.com"


# ── 5. GOVERNMENT IDENTITY INFORMATION TESTS ─────────────────────────────────

def test_pan_number_masked():
    """PAN number disclosure -> HIGH risk with masking ABCDE****F."""
    res = PrivacyRiskService.analyze_message("My PAN number is ABCDE1234F")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "HIGH"
    assert res["overall_risk"]["score"] == 8
    pan_det = next(d for d in res["detections"] if d["type"] == "PAN_NUMBER")
    assert pan_det["masked_value"] == "ABCDE****F"
    assert "1234" not in pan_det["masked_value"]


def test_aadhaar_number_masked():
    """Aadhaar number disclosure -> HIGH risk with masking **** **** 7890."""
    res = PrivacyRiskService.analyze_message("My Aadhaar is 9012 3456 7890")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "HIGH"
    assert res["overall_risk"]["score"] == 8
    aadhaar_det = next(d for d in res["detections"] if d["type"] == "AADHAAR_NUMBER")
    assert aadhaar_det["masked_value"] == "**** **** 7890"
    assert "9012" not in aadhaar_det["masked_value"]


# ── 6. AUTHENTICATION SECRETS TESTS ──────────────────────────────────────────

def test_password_critical_masked():
    """Password disclosure -> CRITICAL risk (10/10) with complete masking."""
    res = PrivacyRiskService.analyze_message("My password is SecretP@ssw0rd!2026")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "CRITICAL"
    assert res["overall_risk"]["score"] == 10
    pwd_det = next(d for d in res["detections"] if d["type"] == "PASSWORD")
    assert pwd_det["masked_value"] == "******"
    assert "SecretP" not in pwd_det["masked_value"]


def test_otp_code_critical_masked():
    """OTP code disclosure -> CRITICAL risk (9/10) with complete masking."""
    res = PrivacyRiskService.analyze_message("My OTP is 849201")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "CRITICAL"
    assert res["overall_risk"]["score"] in (9, 10)
    otp_det = next(d for d in res["detections"] if d["type"] == "OTP_CODE")
    assert otp_det["masked_value"] == "******"
    assert "849201" not in otp_det["masked_value"]


def test_api_key_critical_masked():
    """API key disclosure -> CRITICAL risk (10/10) with masking."""
    res = PrivacyRiskService.analyze_message("My API key is sk-1234567890abcdef1234567890abcdef")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "CRITICAL"
    assert res["overall_risk"]["score"] == 10
    api_det = next(d for d in res["detections"] if d["type"] == "API_KEY")
    assert "sk-****KEY" in api_det["masked_value"] or api_det["masked_value"] == "******"


# ── 7. FINANCIAL CREDENTIALS TESTS ───────────────────────────────────────────

def test_credit_card_with_cvv_critical():
    """Credit card with CVV -> CRITICAL (10/10)."""
    res = PrivacyRiskService.analyze_message("Payment card: 4532-1234-5678-9010 with CVV 482")
    assert res["has_privacy_risk"] is True
    assert res["overall_risk"]["level"] == "CRITICAL"
    assert res["overall_risk"]["score"] == 10
    card_det = next(d for d in res["detections"] if d["type"] == "PAYMENT_CARD")
    assert "9010" in card_det["masked_value"]
    assert "4532" not in card_det["masked_value"]


# ── 8. CROSS-MESSAGE COMBINATION RISK TESTS ──────────────────────────────────

def test_cross_message_combination_escalation():
    """
    Test cumulative multi-message exposure:
      Turn 1: Name ('Arun')
      Turn 2: City ('Krishnagiri')
      Turn 3: Phone ('9876543210')
      -> Combined risk escalates to HIGH (score 8).
    """
    history = [
        {"role": "user", "text": "My name is Arun Kumar"},
        {"role": "assistant", "text": "Hello Arun Kumar! How can I help you today?"},
        {"role": "user", "text": "I live in Krishnagiri"},
        {"role": "assistant", "text": "Krishnagiri is a historic district in Tamil Nadu."},
    ]

    current_msg = "My phone number is 9876543210"
    res = PrivacyRiskService.analyze_message(current_msg, chat_history=history)

    assert res["has_privacy_risk"] is True
    assert res["combined_exposure"]["level"] == "HIGH"
    assert res["combined_exposure"]["score"] >= 8
    assert res["combined_exposure"]["is_escalated"] is True
    assert "Cumulative profile exposure" in res["combined_exposure"]["reason"]


# ── 9. FULL /CHAT INTEGRATION TESTS ──────────────────────────────────────────

def test_chat_endpoint_normal_answer_with_privacy_card(monkeypatch):
    """
    Full /chat route test:
      User: 'I live in Krishnagiri'
      Expect: Normal AI response + privacy_analysis with LOW risk (2/10).
    """
    import backend.routes.chatbot as cb_mod
    monkeypatch.setattr(cb_mod, "_get_gemini_client", lambda: type("DummyGemini", (), {
        "generate_chat_response": lambda self, messages: {"success": True, "response_text": "Krishnagiri is a district located in northwestern Tamil Nadu."}
    })())

    req = ChatRequest(prompt="I live in Krishnagiri", mcp_enabled=False)
    resp = chat_endpoint(req)

    assert resp["success"] is True
    assert resp["decision"] == "ALLOW"
    assert resp["response"] is not None and len(resp["response"]) > 0
    assert "privacy_analysis" in resp
    p_analysis = resp["privacy_analysis"]
    assert p_analysis["has_privacy_risk"] is True
    assert p_analysis["overall_risk"]["level"] == "LOW"
    assert p_analysis["overall_risk"]["score"] in (2, 3)
    assert len(p_analysis["detections"]) >= 1
    assert "Krishnagiri" in p_analysis["detections"][0]["masked_value"]


def test_chat_endpoint_general_query_no_privacy_card(monkeypatch):
    """
    Full /chat route test:
      User: 'What is the weather in Krishnagiri?'
      Expect: Normal AI response + privacy_analysis with 0 risk.
    """
    import backend.routes.chatbot as cb_mod
    monkeypatch.setattr(cb_mod, "_get_gemini_client", lambda: type("DummyGemini", (), {
        "generate_chat_response": lambda self, messages: {"success": True, "response_text": "The weather in Krishnagiri is typically tropical and pleasant."}
    })())

    req = ChatRequest(prompt="What is the weather in Krishnagiri?", mcp_enabled=False)
    resp = chat_endpoint(req)

    assert resp["success"] is True
    assert resp["decision"] == "ALLOW"
    p_analysis = resp["privacy_analysis"]
    assert p_analysis["has_privacy_risk"] is False
    assert p_analysis["overall_risk"]["score"] == 0


# ── 10. AI RESPONSE MEMORY & UNEXPECTED PERSONALIZATION LEAKAGE TESTS ────────

def test_height_alone_is_low_risk():
    """Height alone (170 cm) is LOW risk because it cannot uniquely identify a person."""
    res = PrivacyRiskService.analyze_ai_response_leakage(
        user_message="My height is 170 cm",
        ai_response="170 cm is approximately 5 feet 7 inches."
    )
    assert res["final_risk_level"] in ("LOW", "MINIMAL")
    assert res["has_unexpected_personalization"] is False


def test_unexpected_memory_retrieval_personalization():
    """
    User: 'My height is 170 cm?'
    AI: 'That is a great height, Sanjay! 170 cm is approximately 5 feet 7 inches.'
    History contains: 'My name is Sanjay'
    Expect: Unexpected personalization flagged (MEDIUM risk) because Name was retrieved unprompted.
    """
    history = [{"role": "user", "text": "My name is Sanjay"}]
    res = PrivacyRiskService.analyze_ai_response_leakage(
        user_message="My height is 170 cm?",
        ai_response="That is a great height, Sanjay! 170 cm is approximately 5 feet 7 inches.",
        chat_history=history
    )
    assert res["has_unexpected_personalization"] is True
    assert res["final_risk_level"] in ("LOW", "MEDIUM")
    assert any(item["source"] == "Previous conversation memory" for item in res["evaluated_items"])


def test_unnecessary_personal_context_exposure():
    """
    User: 'What is 10 + 10?'
    AI: '20, Sanjay from Krishnagiri.'
    History contains: 'My name is Sanjay', 'I live in Krishnagiri'
    Expect: Unnecessary exposure flagged on generic math query.
    """
    history = [
        {"role": "user", "text": "My name is Sanjay"},
        {"role": "user", "text": "I live in Krishnagiri"}
    ]
    res = PrivacyRiskService.analyze_ai_response_leakage(
        user_message="What is 10 + 10?",
        ai_response="20, Sanjay from Krishnagiri.",
        chat_history=history
    )
    assert res["has_unexpected_personalization"] is True
    assert res["is_unnecessary_exposure"] is True
    assert res["final_risk_level"] in ("MEDIUM", "HIGH")
    assert "Unexpected personal context exposure" in res["privacy_concern"]


def test_structured_privacy_report_output_format():
    """
    Verify Privacy Risk Output Format:
      ### INFORMATION DETECTED
      ### SOURCE
      ### INDIVIDUAL RISK
      ### COMBINATION RISK
      ### NECESSITY
      ### UNEXPECTED PERSONALIZATION
      ### PRIVACY CONCERN
      ### FINAL RISK SCORE
    """
    history = [{"role": "user", "text": "My name is Sanjay"}]
    report = PrivacyRiskService.generate_privacy_report(
        user_message="My height is 170 cm?",
        ai_response="That is a great height, Sanjay! 170 cm is approximately 5 feet 7 inches.",
        chat_history=history
    )
    assert "### INFORMATION DETECTED" in report
    assert "### SOURCE" in report
    assert "### INDIVIDUAL RISK" in report
    assert "### COMBINATION RISK" in report
    assert "### NECESSITY" in report
    assert "### UNEXPECTED PERSONALIZATION" in report
    assert "### PRIVACY CONCERN" in report
    assert "### FINAL RISK SCORE" in report
    assert "### SUMMARY EXPLANATION" in report


def test_personal_information_sanitization_and_masking():
    """
    Test sanitization of height, age, contact, and identity details:
      'My name is Sanjay, my height is 170 cm, I am 23 years old, living in Krishnagiri, phone: 9876543210'
    """
    raw = "My name is Sanjay, my height is 170 cm, I am 23 years old, living in Krishnagiri, phone: 9876543210"
    
    # 1. Masked Mode
    masked = PrivacyRiskService.sanitize_text(raw, mode="MASK")
    assert "9876543210" not in masked
    assert "******3210" in masked
    assert "170 cm" in masked or "[PHYSICAL_ATTRIBUTE_HEIGHT]" in masked

    # 2. Redacted Mode
    redacted = PrivacyRiskService.sanitize_text(raw, mode="REDACT")
    assert "9876543210" not in redacted
    assert "[PHONE_NUMBER]" in redacted
    assert "[PHYSICAL_ATTRIBUTE_HEIGHT]" in redacted or "[DEMOGRAPHIC_AGE]" in redacted
    
    # 3. Via analyze_message payload
    analysis = PrivacyRiskService.analyze_message(raw)
    assert analysis["has_privacy_risk"] is True
    assert "sanitized_text" in analysis
    assert "masked_text" in analysis
    assert "9876543210" not in analysis["sanitized_text"]

