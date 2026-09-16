"""
Comprehensive Unit & Integration Tests for Upgraded LLM Prompt Privacy System.
File Location: tests/test_advanced_prompt_privacy.py
"""

import pytest
from privacy_engine.context_detector import PrivacyContextDetector
from privacy_engine.sanitizer import SmartSanitizer, RedactionStrategy
from privacy_engine.evaluator import PolicyEvaluator, PolicyMode
from privacy_engine import run_full_analysis
from ml_engine.hybrid_classifier import HybridPrivacyClassifier
from ml_engine.ablation_evaluator import ModelAblationBenchmarker
from privacy_engine.privacy_attack_bench import PrivacyAttackBenchmarker


def test_educational_query_bypass():
    detector = PrivacyContextDetector()
    res_vishnu = detector.detect_privacy_context("Vishnu")
    assert not res_vishnu["is_risk"]
    assert res_vishnu["risk_score"] == 0.0

    res_photo = detector.detect_privacy_context("What is photosynthesis?")
    assert not res_photo["is_risk"]
    assert res_photo["risk_score"] == 0.0


def test_pii_detection_categories():
    detector = PrivacyContextDetector()

    # Credit card + CVV
    res_card = detector.detect_privacy_context("Card 4532-0123-4567-8910 CVV 999 exp 12/28")
    assert res_card["is_risk"]
    assert any("FINANCIAL" in k or "CREDENTIAL" in k or "CARD" in k for k in res_card["detected_entities"])

    # SSN
    res_ssn = detector.detect_privacy_context("My SSN number is 123-45-6789")
    assert res_ssn["is_risk"]
    assert any("SSN" in k or "GOVERNMENT" in k for k in res_ssn["detected_entities"])

    # API Key
    res_api = detector.detect_privacy_context("sk-live-51Mxx9283749283749823749823")
    assert res_api["is_risk"]
    assert any("API" in k or "KEY" in k or "SECRET" in k for k in res_api["detected_entities"])


def test_stateful_smart_redaction():
    sanitizer = SmartSanitizer()
    sanitizer.reset_stateful_placeholders()

    text = "Call patient John Doe at +1-555-019-2834 or email john.doe@example.com."
    res = sanitizer.sanitize_prompt(text, strategy=RedactionStrategy.SYNTHETIC_MASK)
    sanitized = res["sanitized_prompt"]

    assert "[PHONE_1]" in sanitized
    assert "[EMAIL_1]" in sanitized



def test_policy_modes():
    evaluator_strict = PolicyEvaluator(policy_mode=PolicyMode.STRICT)
    res_strict = evaluator_strict.evaluate_policy(
        risk_score=0.45,
        is_risk=True,
        detected_entities={"EMAIL_ADDRESS": ["user@example.com"]},
        canonical_class="CONTACT_INFORMATION"
    )
    assert res_strict["decision"] in ["BLOCKED", "BLOCK"]

    evaluator_balanced = PolicyEvaluator(policy_mode=PolicyMode.BALANCED)
    res_balanced = evaluator_balanced.evaluate_policy(
        risk_score=0.45,
        is_risk=True,
        detected_entities={"EMAIL_ADDRESS": ["user@example.com"]},
        canonical_class="CONTACT_INFORMATION"
    )
    assert res_balanced["decision"] in ["PENDING_USER_DECISION", "REDACT", "WARN"]

    evaluator_utility = PolicyEvaluator(policy_mode=PolicyMode.UTILITY)
    res_utility = evaluator_utility.evaluate_policy(
        risk_score=0.30,
        is_risk=True,
        detected_entities={"EMAIL_ADDRESS": ["user@example.com"]},
        canonical_class="CONTACT_INFORMATION"
    )
    assert res_utility["decision"] in ["PENDING_USER_DECISION", "REDACT", "ALLOW"]



def test_hybrid_classifier_fusion():
    clf = HybridPrivacyClassifier(alpha=0.60)
    res = clf.hybrid_predict("Card number 4532 0123 4567 8910 CVV 123")

    assert "predicted_class" in res
    assert "hybrid_probabilities" in res
    assert res["alpha_weight"] == 0.60


def test_full_privacy_analysis_pipeline():
    res = run_full_analysis("Please assist me with my order.")
    assert res["policy_evaluation"]["decision"] == "ALLOW"
    assert res["risk_score"] == 0.0


def test_privacy_attack_benchmark():
    bench = PrivacyAttackBenchmarker()
    res = bench.run_benchmark()

    assert res["total_tests"] > 0
    assert res["pass_rate_pct"] >= 80.0


def test_automatic_blocking_high_sensitivity():
    """Verify automatic blocking for passwords, API keys, cards, and govt IDs."""
    res_pass = run_full_analysis("My password is AdminSecretPassword123!")
    assert res_pass["decision"] in ["BLOCKED", "BLOCK"]

    res_api = run_full_analysis("sk-live-51Mxx9283749283749823749823")
    assert res_api["decision"] in ["BLOCKED", "BLOCK"]

    res_card = run_full_analysis("Card 4532-0123-4567-8910 CVV 999 exp 12/28")
    assert res_card["decision"] in ["BLOCKED", "BLOCK"]


def test_user_confirmation_ordinary_personal_and_health():
    """Verify user confirmation state (PENDING_USER_DECISION) for personal health information."""
    res_health = run_full_analysis("Yesterday I suffered from fever for two days.")
    assert res_health["decision"] in ["PENDING_USER_DECISION", "WARN"]
    assert res_health["requires_user_confirmation"] is True


def test_personal_location_hometown_school_workplace_detection():
    """Regression test ensuring personal location, hometown, school, and workplace disclosures trigger privacy warning & user consent."""
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
        assert res["decision"] in ["PENDING_USER_DECISION", "WARN"], f"Failed to flag personal location info in prompt: '{prompt}'"
        assert res["risk_score"] > 0.0, f"Risk score must be > 0% for personal location prompt: '{prompt}'"
        assert res["requires_user_confirmation"] is True, f"User confirmation required for personal location prompt: '{prompt}'"


def test_allow_neutral_prompts():
    """Verify neutral educational & scientific inquiries are allowed without friction."""
    for prompt in [
        "What are the common causes of fever?",
        "Explain artificial intelligence.",
        "What is machine learning?",
    ]:
        res = run_full_analysis(prompt)
        assert res["decision"] == "ALLOW"
        assert res["risk_score"] == 0.0



def test_model_ablation_benchmarking():
    bench = ModelAblationBenchmarker()
    # Run ablation on 5 sample prompts for fast verification
    samples = [
        ("Explain photosynthesis in plants", "SAFE", "STEM"),
        ("My SSN is 123-45-6789", "GOVERNMENT_ID", "SSN"),
        ("sk-live-51Mxx9283749283749823749823", "AUTHENTICATION_SECRET", "API_KEY"),
        ("Card 4532 0123 4567 8910 exp 12/28", "FINANCIAL_INFORMATION", "CREDIT_CARD"),
        ("Call me at 555-019-2834", "CONTACT_INFORMATION", "PHONE"),
    ]
    res = bench.run_ablation_study(samples=samples)

    assert "models" in res
    assert "distilbert_only" in res["models"]
    assert "naive_bayes_only" in res["models"]
    assert "hybrid_ensemble" in res["models"]

