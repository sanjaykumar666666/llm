"""
Hybrid BERT - Naïve Bayes Ensemble Privacy Risk Classifier.
File Location: ml_engine/hybrid_classifier.py
"""

import time
from typing import Dict, Any
from ml_engine.bert_model import BertFeatureExtractor
from ml_engine.naive_bayes import NaiveBayesPrivacyClassifier


class HybridPrivacyClassifier:
    """
    Ensemble decision engine fusing BERT contextual embeddings, Naïve Bayes probabilistic scores,
    Shannon entropy, and entity severity weights into a unified Privacy Risk Score.
    """

    def __init__(self):
        self.bert = BertFeatureExtractor()
        self.nb = NaiveBayesPrivacyClassifier()

    def predict_privacy_risk(self, fused_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the fused multimodal payload and outputs a unified Privacy Risk Score and breakdown.
        """
        start_time = time.time()
        unified_text = fused_payload.get("unified_text", "")
        meta_feats = fused_payload.get("metadata_features", {})

        # 1. Compute Naïve Bayes probabilistic score
        nb_score = self.nb.predict_probability(unified_text)

        # 2. Compute BERT contextual risk representation
        bert_score = self.bert.predict_context_risk(unified_text)

        # 3. Entity severity & regex signal
        regex_signal = 1.0 if meta_feats.get("contains_regex_pii", 0) == 1 else 0.0
        max_severity = meta_feats.get("max_entity_severity", 0.0)
        entropy = meta_feats.get("shannon_entropy", 0.0)

        # High entropy signal (> 4.5 bits) for password/hash detection
        entropy_signal = min(1.0, max(0.0, (entropy - 4.0) / 2.0)) if len(unified_text) > 8 else 0.0

        # Weighted Ensemble Fusion:
        # Base: 35% Naïve Bayes + 25% BERT Context + 25% Severity & Regex + 15% Entropy
        weighted_score = (
            (0.35 * nb_score) +
            (0.25 * bert_score) +
            (0.25 * max(regex_signal, max_severity)) +
            (0.15 * entropy_signal)
        )

        # Zero out baseline noise when no PII is present and both ML models are low
        if regex_signal == 0 and max_severity == 0 and bert_score < 0.15 and nb_score < 0.20:
            final_risk_score = 0.0
        # Hard override for critical secrets (e.g. API Keys, AWS secrets, Private Keys)
        elif max_severity >= 0.95 or meta_feats.get("regex_pii_detected_count", 0) >= 3:
            final_risk_score = max(weighted_score, 0.88)
        elif regex_signal > 0:
            final_risk_score = max(weighted_score, 0.45)
        else:
            final_risk_score = weighted_score

        final_risk_score = round(min(max(final_risk_score, 0.0), 1.0), 4)
        elapsed_ms = (time.time() - start_time) * 1000

        # Predicted risk category
        if final_risk_score < 0.30:
            predicted_class = "SAFE"
        elif final_risk_score < 0.75:
            predicted_class = "PII_PRESENT"
        else:
            predicted_class = "HIGH_RISK"

        # Feature contribution explainability breakdown
        explainability = {
            "naive_bayes_weight": "35%",
            "bert_context_weight": "25%",
            "entity_pattern_severity": f"{int(max_severity * 100)}%",
            "shannon_entropy_rating": f"{round(entropy, 2)} bits",
        }

        return {
            "hybrid_risk_score": final_risk_score,
            "predicted_class": predicted_class,
            "nb_probability": round(nb_score, 4),
            "bert_context_score": round(bert_score, 4),
            "regex_pii_flag": int(regex_signal),
            "max_entity_severity": round(max_severity, 2),
            "shannon_entropy": round(entropy, 2),
            "inference_latency_ms": round(elapsed_ms, 2),
            "explainability": explainability,
        }
