"""
Regression & Verification Test Suite for Personal Location, Hometown, School, Workplace, Health & Neutral Inquiries.
File Location: tests/test_location_and_personal_privacy.py
"""

import pytest
from privacy_engine import run_full_analysis


def test_hometown_and_location_disclosures():
    """Verify self-disclosed hometown and location disclosures trigger privacy warning (PENDING_USER_DECISION) with non-zero risk score."""
    location_prompts = [
        "My home town is Veppanapalli.",
        "I live in Veppanapalli.",
        "My address is 742 Evergreen Terrace.",
        "I am from Chennai.",
        "My school is St. Joseph Higher Secondary School.",
        "My workplace is Microsoft Corporation.",
    ]

    for prompt in location_prompts:
        res = run_full_analysis(prompt)
        assert res["decision"] in ["PENDING_USER_DECISION", "WARN"], f"Prompt '{prompt}' failed: expected PENDING_USER_DECISION, got '{res['decision']}'"
        assert res["risk_score"] > 0.0, f"Prompt '{prompt}' failed: expected risk_score > 0, got {res['risk_score']}"
        assert res["requires_user_confirmation"] is True, f"Prompt '{prompt}' failed: expected requires_user_confirmation == True"
        # Ensure '100% Zero Privacy Risk' is NOT displayed
        assert res["status_banner"] != "🟢 NO PRIVACY RISK"


def test_health_information_disclosures():
    """Verify self-disclosed health information triggers privacy warning (PENDING_USER_DECISION)."""
    health_prompts = [
        "Yesterday I suffered from fever for two days.",
        "I was diagnosed with Type 2 Diabetes last month.",
    ]

    for prompt in health_prompts:
        res = run_full_analysis(prompt)
        assert res["decision"] in ["PENDING_USER_DECISION", "WARN"]
        assert res["risk_score"] > 0.0
        assert res["requires_user_confirmation"] is True


def test_neutral_questions_allowed():
    """Verify neutral educational & general inquiries evaluate to ALLOW with 0% risk score."""
    neutral_prompts = [
        "What are the common causes of fever?",
        "Explain artificial intelligence.",
        "What is machine learning?",
    ]

    for prompt in neutral_prompts:
        res = run_full_analysis(prompt)
        assert res["decision"] == "ALLOW", f"Prompt '{prompt}' failed: expected ALLOW, got '{res['decision']}'"
        assert res["risk_score"] == 0.0, f"Prompt '{prompt}' failed: expected risk_score == 0, got {res['risk_score']}"
