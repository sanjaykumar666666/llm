"""Privacy Engine Package.

Exports core privacy engine classes at the package level for easier imports.
"""

from .evaluator import AutomatedDecisionGate, PrivacyEvaluator
from .sanitizer import PIISanitizer, PrivacySanitizer, Sanitizer, PII_PATTERNS
from .context_detector import ContextAwareEntityDetector

ContextAwarePrivacyDetector = ContextAwareEntityDetector
PrivacyDetector = ContextAwareEntityDetector

def get_hybrid_classifier():
    from ml_engine.hybrid_classifier import HybridPrivacyClassifier
    return HybridPrivacyClassifier()

def get_naive_bayes_classifier():
    from ml_engine.naive_bayes import NaiveBayesPrivacyClassifier
    return NaiveBayesPrivacyClassifier()

def get_distilbert_classifier():
    from ml_engine.bert_model import DistilBERTPrivacyClassifier
    return DistilBERTPrivacyClassifier()

def run_full_analysis(text: str, *args, **kwargs):
    from backend.services.evidence_risk import analyze_privacy_risk
    res = analyze_privacy_risk(text, *args, **kwargs)
    dec = res.get("decision", "ALLOW")
    res["policy_evaluation"] = {
        "decision": dec,
        "action": dec,
        "risk_level": res.get("risk_level", "LOW"),
        "reason": res.get("reason", "Analysis complete"),
    }
    res["sanitization"] = {
        "sanitized_prompt": res.get("sanitized_text", text) or text,
        "sanitized_text": res.get("sanitized_text", text) or text,
        "entities_redacted": res.get("redacted_entities", []),
        "entities_removed": res.get("entities_removed", []),
    }
    return res


__all__ = [
    "AutomatedDecisionGate",
    "PrivacyEvaluator",
    "PrivacySanitizer",
    "PIISanitizer",
    "Sanitizer",
    "PII_PATTERNS",
    "ContextAwareEntityDetector",
    "ContextAwarePrivacyDetector",
    "PrivacyDetector",
    "get_hybrid_classifier",
    "get_naive_bayes_classifier",
    "get_distilbert_classifier",
    "run_full_analysis",
]


