"""
Hybrid BERT - Naive Bayes Ensemble Privacy Risk Classifier.
File Location: ml_engine/hybrid_classifier.py

Ensemble Fusion & Mathematical Combination:
  P_hybrid(c) = alpha * P_BERT(c) + (1 - alpha) * P_NB(c)
  where alpha = 0.60 by default when both models are active.
  If BERT is unavailable, alpha = 0.0 (Naive Bayes only).
  If Naive Bayes is unavailable, alpha = 1.0 (BERT only).
"""

import time
from typing import Dict, Any, Optional
from ml_engine.bert_model import BertFeatureExtractor
from ml_engine.naive_bayes import NaiveBayesPrivacyClassifier
from data.unified_privacy_dataset import CANONICAL_CLASSES


class HybridPrivacyClassifier:
    """
    Ensemble decision engine fusing DistilBERT semantic probabilities with
    Naive Bayes token n-gram posterior distributions.
    """

    def __init__(self, alpha: float = 0.60):
        self.bert = BertFeatureExtractor()
        self.nb = NaiveBayesPrivacyClassifier()
        self.alpha = float(alpha)  # Weight given to BERT (0.0 to 1.0)
        self.classes = CANONICAL_CLASSES

    def hybrid_predict(self, text: str) -> Dict[str, Any]:
        """
        Authoritative Hybrid ML prediction endpoint.
        Returns structured dictionary with per-model and combined probability distributions.
        """
        start_time = time.time()
        if not text or not text.strip():
            empty_probs = {c: (1.0 if c == "SAFE" else 0.0) for c in self.classes}
            return {
                "classification": "SAFE",
                "canonical_class": "SAFE",
                "predicted_class": "SAFE",
                "bert_probabilities": empty_probs,
                "naive_bayes_probabilities": empty_probs,
                "hybrid_probabilities": empty_probs,
                "confidence": 1.0,
                "model_status": "available",
                "classification_source": "hybrid_ml",
                "hybrid_risk_score": 0.0,
                "alpha_weight": self.alpha,
                "inference_latency_ms": 0.0,
            }

        bert_res = self.bert.evaluate_privacy_semantics(text)
        nb_res = self.nb.evaluate_privacy_tokens(text)

        bert_available = bert_res.get("is_transformer_loaded", False)
        nb_available = nb_res.get("is_trained", False)

        bert_probs = bert_res.get("probabilities", {})
        nb_probs = nb_res.get("probabilities", {})

        # Determine active classification source and dynamic alpha weight
        if bert_available and nb_available:
            classification_source = "hybrid_ml"
            active_alpha = self.alpha
            model_status = "available"
        elif bert_available and not nb_available:
            classification_source = "bert_only"
            active_alpha = 1.0
            model_status = "bert_only"
        elif not bert_available and nb_available:
            classification_source = "naive_bayes_only"
            active_alpha = 0.0
            model_status = "naive_bayes_only"
        else:
            classification_source = "unavailable"
            active_alpha = 0.0
            model_status = "unavailable"

        # Compute combined hybrid probability distribution: alpha * BERT + (1 - alpha) * NB
        hybrid_probs: Dict[str, float] = {}
        if model_status != "unavailable":
            for cls_name in self.classes:
                p_b = bert_probs.get(cls_name, 0.0) if bert_available else 0.0
                p_n = nb_probs.get(cls_name, 0.0) if nb_available else 0.0
                p_h = round(active_alpha * p_b + (1.0 - active_alpha) * p_n, 4)
                hybrid_probs[cls_name] = p_h

            # Normalize to sum to 1.0
            total_mass = sum(hybrid_probs.values())
            if total_mass > 0:
                hybrid_probs = {k: round(v / total_mass, 4) for k, v in hybrid_probs.items()}

            best_class = max(hybrid_probs.items(), key=lambda x: x[1])[0]
            confidence = hybrid_probs[best_class]
            p_safe = hybrid_probs.get("SAFE", 0.0)
            hybrid_risk = round(max(0.0, min(1.0, 1.0 - p_safe)), 4)
        else:
            best_class = "UNKNOWN"
            confidence = 0.0
            hybrid_risk = 0.0

        # Coarse predicted class
        if best_class == "SAFE":
            coarse_class = "SAFE"
        elif best_class in ("CREDENTIAL", "AUTHENTICATION_SECRET", "FINANCIAL_INFORMATION", "GOVERNMENT_ID", "PROMPT_INJECTION"):
            coarse_class = "HIGH_RISK"
        else:
            coarse_class = "PII_PRESENT"

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "classification": best_class,
            "canonical_class": best_class,
            "predicted_class": coarse_class,
            "bert_probabilities": bert_probs,
            "naive_bayes_probabilities": nb_probs,
            "hybrid_probabilities": hybrid_probs,
            "confidence": confidence,
            "model_status": model_status,
            "classification_source": classification_source,
            "hybrid_risk_score": hybrid_risk,
            "alpha_weight": active_alpha,
            "inference_latency_ms": round(elapsed_ms, 2),
        }

    def predict_privacy_risk(self, fused_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates fused multimodal payload and outputs unified Privacy Risk Score and breakdown.
        Maintains backward compatibility with legacy pipelines and tests.
        """
        start_time = time.time()
        unified_text = fused_payload.get("unified_text", "")
        meta_feats = fused_payload.get("metadata_features", {})

        pred = self.hybrid_predict(unified_text)
        nb_score = self.nb.predict_probability(unified_text)
        bert_score = self.bert.predict_context_risk(unified_text)

        regex_signal = 1.0 if meta_feats.get("contains_regex_pii", 0) == 1 else 0.0
        max_severity = meta_feats.get("max_entity_severity", 0.0)
        entropy = meta_feats.get("shannon_entropy", 0.0)
        entropy_signal = min(1.0, max(0.0, (entropy - 4.0) / 2.0)) if len(unified_text) > 8 else 0.0

        # Weighted Ensemble Fusion
        weighted_score = (
            (0.35 * nb_score) +
            (0.25 * bert_score) +
            (0.25 * max(regex_signal, max_severity)) +
            (0.15 * entropy_signal)
        )

        if regex_signal == 0 and max_severity == 0 and bert_score < 0.15 and nb_score < 0.20:
            final_risk_score = 0.0
        elif max_severity >= 0.95 or meta_feats.get("regex_pii_detected_count", 0) >= 3:
            final_risk_score = max(weighted_score, 0.88)
        elif regex_signal > 0:
            final_risk_score = max(weighted_score, 0.45)
        else:
            final_risk_score = weighted_score

        final_risk_score = round(min(max(final_risk_score, 0.0), 1.0), 4)
        elapsed_ms = (time.time() - start_time) * 1000

        if final_risk_score < 0.30:
            predicted_class = "SAFE"
        elif final_risk_score < 0.75:
            predicted_class = "PII_PRESENT"
        else:
            predicted_class = "HIGH_RISK"

        explainability = {
            "naive_bayes_weight": "35%",
            "bert_context_weight": "25%",
            "entity_pattern_severity": f"{int(max_severity * 100)}%",
            "shannon_entropy_rating": f"{round(entropy, 2)} bits",
        }

        return {
            "hybrid_risk_score": final_risk_score,
            "predicted_class": predicted_class,
            "canonical_class": pred.get("canonical_class", "SAFE"),
            "classification_source": pred.get("classification_source", "hybrid_ml"),
            "nb_probability": round(nb_score, 4),
            "bert_context_score": round(bert_score, 4),
            "regex_pii_flag": int(regex_signal),
            "max_entity_severity": round(max_severity, 2),
            "shannon_entropy": round(entropy, 2),
            "inference_latency_ms": round(elapsed_ms, 2),
            "explainability": explainability,
            "ml_analysis": pred,
        }
