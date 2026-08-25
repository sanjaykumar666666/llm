"""
Unit and Integration Test Suite: Highly Personal Context Privacy Category & Guardrail (Pipeline 2).
File Location: tests/test_highly_personal_context.py

Verifies:
  1. General relationship question -> SAFE
  2. Mild personal relationship statement -> WARNING
  3. Detailed personal relationship history -> HIGH PRIVACY WARNING / HIGH_RISK
  4. General family question -> SAFE
  5. Detailed family/private disclosure -> HIGH PRIVACY WARNING / HIGH_RISK
  6. Password disclosure -> BLOCK (Credentials category preserved)
  7. API key disclosure -> BLOCK (Credentials category preserved)
  8. Email disclosure -> existing privacy SANITIZE/WARN behavior
  9. Normal technical question -> SAFE
  10. User chooses Review & Edit -> No automatic LLM call
  11. User chooses Continue Anyway -> Backend Pipeline 1 is executed
  12. HIGH PERSONAL RISK -> No automatic LLM call before user confirmation
  13. Explanation never repeats the user's private content
  14. Original sensitive content is not added to chat history before confirmation
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from privacy_engine.context_detector import ContextAwareEntityDetector
from pipeline.detector import PrivacyDetectionEngine, CATEGORY_PERSONAL_CONTEXT
from pipeline.risk_engine import PrivacyRiskScoringEngine
from pipeline.protection_engine import ProtectionAndDecisionEngine
from backend.services.evidence_risk import run_full_analysis, calculate_evidence_risk
from backend.main import app


client = TestClient(app)



# ── 1. General relationship question → SAFE ───────────────────────────────────
def test_01_general_relationship_question_safe():
    detector = ContextAwareEntityDetector()
    prompt = "What are common causes of relationship conflicts?"
    
    ctx = detector.detect_personal_context(prompt)
    assert ctx["level"] == "SAFE"
    assert ctx["detected"] is False
    assert ctx["requires_confirmation"] is False

    analysis = run_full_analysis(prompt)
    assert analysis["decision"] == "ALLOW"
    assert analysis["risk_score"] == 0
    assert analysis["risk_level"] == "LOW"
    assert analysis["personal_context_level"] == "SAFE"
    assert analysis["requires_user_confirmation"] is False


# ── 2. Mild personal relationship statement → WARNING ─────────────────────────
def test_02_mild_personal_relationship_statement_warning():
    detector = ContextAwareEntityDetector()
    prompt = "I have been having problems with my relationship recently."
    
    ctx = detector.detect_personal_context(prompt)
    assert ctx["level"] == "WARNING"
    assert ctx["detected"] is True
    assert ctx["requires_confirmation"] is False

    analysis = run_full_analysis(prompt)
    assert analysis["decision"] == "WARN"
    assert 30 <= analysis["risk_score"] <= 59
    assert analysis["risk_level"] == "MEDIUM"
    assert analysis["personal_context_level"] == "WARNING"
    assert analysis["requires_user_confirmation"] is False


# ── 3. Detailed personal relationship history → HIGH PRIVACY WARNING ─────────
def test_03_detailed_personal_relationship_history_high_risk():
    detector = ContextAwareEntityDetector()
    prompt = "I want to tell you everything that happened in my five-year relationship, including private events involving my partner and family."
    
    ctx = detector.detect_personal_context(prompt)
    assert ctx["level"] == "HIGH_RISK"
    assert ctx["detected"] is True
    assert ctx["requires_confirmation"] is True
    assert ctx["classification_source"] == "rule_based_precheck"

    analysis = run_full_analysis(prompt)
    assert analysis["risk_score"] >= 60
    assert analysis["risk_level"] == "HIGH"
    assert analysis["decision"] == "WARN"  # Personal context warns with confirmation, doesn't auto-block like credentials
    assert analysis["personal_context_level"] == "HIGH_RISK"
    assert analysis["requires_user_confirmation"] is True


# ── 4. General family question → SAFE ─────────────────────────────────────────
def test_04_general_family_question_safe():
    detector = ContextAwareEntityDetector()
    prompt = "How can families improve communication during conflicts?"
    
    ctx = detector.detect_personal_context(prompt)
    assert ctx["level"] == "SAFE"
    assert ctx["detected"] is False

    analysis = run_full_analysis(prompt)
    assert analysis["decision"] == "ALLOW"
    assert analysis["risk_score"] == 0
    assert analysis["risk_level"] == "LOW"


# ── 5. Detailed family/private disclosure → HIGH PRIVACY WARNING ──────────────
def test_05_detailed_family_private_disclosure_high_risk():
    detector = ContextAwareEntityDetector()
    prompt = "Let me share the intimate details of my family dispute regarding our secret inheritance and court case involving my in-laws."
    
    ctx = detector.detect_personal_context(prompt)
    assert ctx["level"] == "HIGH_RISK"
    assert ctx["detected"] is True
    assert ctx["requires_confirmation"] is True

    analysis = run_full_analysis(prompt)
    assert analysis["risk_level"] == "HIGH"
    assert analysis["requires_user_confirmation"] is True
    assert analysis["personal_context_level"] == "HIGH_RISK"


# ── 6. Password disclosure → existing BLOCK behavior preserved ────────────────
def test_06_password_disclosure_block():
    prompt = "My database password is SuperSecretPass123! and user is root"
    analysis = run_full_analysis(prompt)
    
    assert analysis["decision"] == "BLOCK"
    assert analysis["has_critical_secret"] is True
    assert analysis["risk_score"] >= 65


# ── 7. API key → existing BLOCK behavior preserved ────────────────────────────
def test_07_api_key_disclosure_block():
    prompt = "Deploy with this AWS key: AKIAIOSFODNN7EXAMPLE"
    analysis = run_full_analysis(prompt)
    
    assert analysis["decision"] == "BLOCK"
    assert analysis["has_critical_secret"] is True


# ── 8. Email → existing privacy behavior ──────────────────────────────────────
def test_08_email_disclosure_pii_sanitized():
    prompt = "Please send the report to alice.smith@enterprise.org"
    analysis = run_full_analysis(prompt)
    
    assert analysis["decision"] in ("WARN", "ALLOW")
    assert any(e["category"] == "Email Address" for e in analysis["entities"])
    assert "[EMAIL REDACTED]" in analysis["sanitized_text"] or "alice.smith" not in (analysis.get("forward_prompt") or "")


# ── 9. Normal technical question → SAFE ───────────────────────────────────────
def test_09_normal_technical_question_safe():
    prompt = "How do I sort a list of dictionaries by key in Python?"
    analysis = run_full_analysis(prompt)
    
    assert analysis["decision"] == "ALLOW"
    assert analysis["risk_score"] == 0
    assert analysis["risk_level"] == "LOW"
    assert len(analysis["entities"]) == 0


# ── 10. User chooses Review & Edit → no automatic LLM call ────────────────────
def test_10_review_and_edit_no_llm_call():
    # Chat endpoint receives HIGH_RISK prompt without confirmed_by_user
    prompt = "I want to tell you everything that happened in my five-year relationship, including private events involving my partner and family."
    
    with patch("llm_gateway.gemini_client.GeminiClient.generate_chat_response") as mock_gemini:
        res = client.post("/api/v1/chat", json={"prompt": prompt, "confirmed_by_user": False})
        assert res.status_code == 200
        data = res.json()
        
        # Intercepted before confirmation
        assert data["decision"] == "HIGH_PRIVACY_WARNING"
        assert data["action"] == "CONFIRMATION_REQUIRED"
        assert data["requires_user_confirmation"] is True
        assert mock_gemini.call_count == 0  # Gemini LLM was NEVER called


# ── 11. User chooses Continue Anyway → backend Pipeline 1 is executed ─────────
def test_11_continue_anyway_pipeline_1_executed():
    # Prompt has high personal context AND user clicks Continue Anyway (confirmed_by_user=True)
    prompt = "I want to tell you everything that happened in my five-year relationship, including private events involving my partner and family."
    
    with patch("llm_gateway.gemini_client.GeminiClient.generate_chat_response") as mock_gemini:
        mock_gemini.return_value = {"success": True, "response_text": "I understand your relationship situation."}
        
        res = client.post("/api/v1/chat", json={"prompt": prompt, "confirmed_by_user": True})
        assert res.status_code == 200
        data = res.json()
        
        # Pipeline 1 verified no credentials, allowed LLM forwarding
        assert mock_gemini.call_count == 1
        assert "I understand" in data["response"]

    # If prompt has credentials AND user clicks Continue Anyway -> Pipeline 1 MUST STILL BLOCK!
    prompt_with_password = "My password is Pass123456! and I want to share my private relationship story."
    with patch("llm_gateway.gemini_client.GeminiClient.generate_chat_response") as mock_gemini:
        res = client.post("/api/v1/chat", json={"prompt": prompt_with_password, "confirmed_by_user": True})
        assert res.status_code == 200
        data = res.json()
        
        # Pipeline 1 enforced credential BLOCK!
        assert data["decision"] == "BLOCK"
        assert mock_gemini.call_count == 0  # Still blocked from LLM!


# ── 12. HIGH PERSONAL RISK → no automatic LLM call before confirmation ─────────
def test_12_high_personal_risk_no_automatic_llm_call():
    prompt = "Let me share the intimate details of my family dispute regarding our secret inheritance and court case involving my in-laws."
    
    with patch("llm_gateway.gemini_client.GeminiClient.generate_chat_response") as mock_gemini:
        res = client.post("/api/v1/chat", json={"prompt": prompt, "confirmed_by_user": False})
        assert res.status_code == 200
        data = res.json()
        
        assert data["requires_user_confirmation"] is True
        assert mock_gemini.call_count == 0


# ── 13. Explanation never repeats the user's private content ─────────────────
def test_13_explanation_never_repeats_private_content():
    sensitive_detail = "five-year relationship involving John Doe in Seattle"
    prompt = f"I want to tell you everything that happened in my {sensitive_detail}, including private events."
    
    analysis = run_full_analysis(prompt)
    
    # Check reason and why_bullets do NOT contain the exact sensitive details
    assert "John Doe" not in analysis["reason"]
    assert "Seattle" not in analysis["reason"]
    assert "five-year" not in analysis["reason"]
    for bullet in analysis["why_bullets"]:
        assert "John Doe" not in bullet
        assert "Seattle" not in bullet
    
    # Generic safe category message
    assert "Detailed personal experiences may contain sensitive information" in analysis["reason"]


# ── 14. Original sensitive content is not added to chat history before confirmation
def test_14_chat_history_leakage_protection():
    prompt = "I want to tell you everything that happened in my five-year relationship, including private events involving my partner and family."
    
    # Live analysis endpoint verification
    live_res = client.post("/api/v1/privacy/analyze", json={"text": prompt})
    assert live_res.status_code == 200
    live_data = live_res.json()
    
    assert live_data["personal_context_level"] == "HIGH_RISK"
    assert live_data["trust_indicators"]["ai_has_received"] is False
    assert live_data["trust_indicators"]["can_review_and_edit"] is True
    assert live_data["trust_indicators"]["user_decides"] is True
    assert "Highly personal information detected" in live_data["trust_indicators"]["status_text"]
