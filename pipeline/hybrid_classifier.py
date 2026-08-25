"""
Hybrid Classification Engine — Phase 5 Core Module.
File Location: pipeline/hybrid_classifier.py

Responsibilities:
  1. Combines Phase 3 Feature Extraction (DistilBERT) and Naive Bayes token probabilistic modeling.
  2. Evaluates contextual risk from DistilBERT [CLS] embeddings.
  3. Evaluates token n-gram risk probabilities from Multinomial Naive Bayes.
  4. Computes Shannon entropy signal for cryptographic keys and hashes.
  5. Produces a standardized HybridClassificationResult dataclass.
"""

import time
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from pipeline.feature_extractor import ExtractedFeatures
from pipeline.preprocessor import PreprocessedData
from ml_engine.bert_model import BertFeatureExtractor
from ml_engine.naive_bayes import NaiveBayesPrivacyClassifier
from ml_engine.hybrid_classifier import HybridPrivacyClassifier


# ── Singletons ────────────────────────────────────────────────────────────────
_bert_instance: Optional[BertFeatureExtractor] = None
_nb_instance: Optional[NaiveBayesPrivacyClassifier] = None
_hybrid_instance: Optional[HybridPrivacyClassifier] = None


def get_bert() -> BertFeatureExtractor:
    global _bert_instance
    if _bert_instance is None:
        _bert_instance = BertFeatureExtractor()
    return _bert_instance


def get_naive_bayes() -> NaiveBayesPrivacyClassifier:
    global _nb_instance
    if _nb_instance is None:
        _nb_instance = NaiveBayesPrivacyClassifier()
    return _nb_instance


def get_hybrid() -> HybridPrivacyClassifier:
    global _hybrid_instance
    if _hybrid_instance is None:
        _hybrid_instance = HybridPrivacyClassifier()
    return _hybrid_instance


@dataclass
class HybridClassificationResult:
    """
    Standardized Output from Phase 5 Hybrid Classifier.
    """

    input_type: str = "text"
    source: str = "direct_input"
    predicted_class: str = "SAFE"               # "SAFE" | "PII_PRESENT" | "HIGH_RISK"
    canonical_class: str = "SAFE"
    bert_risk_score: float = 0.0               # 0.0 - 1.0
    nb_risk_probability: float = 0.0           # 0.0 - 1.0
    nb_probabilities: Dict[str, float] = field(default_factory=dict)
    hybrid_probability: float = 0.0            # Weighted probability
    shannon_entropy: float = 0.0               # bits/char
    classification_confidence: float = 0.0
    classification_source: str = "hybrid_ml"
    classification_status: str = "success"
    classification_errors: List[str] = field(default_factory=list)
    classification_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_type": self.input_type,
            "source": self.source,
            "predicted_class": self.predicted_class,
            "canonical_class": self.canonical_class,
            "bert_risk_score": self.bert_risk_score,
            "nb_risk_probability": self.nb_risk_probability,
            "nb_probabilities": self.nb_probabilities,
            "hybrid_probability": self.hybrid_probability,
            "shannon_entropy": self.shannon_entropy,
            "classification_confidence": self.classification_confidence,
            "classification_source": self.classification_source,
            "classification_status": self.classification_status,
            "classification_errors": self.classification_errors,
            "classification_time_ms": self.classification_time_ms,
        }


class HybridClassifier:
    """
    Ensemble ML Classifier combining DistilBERT contextual semantic embeddings
    with Naive Bayes n-gram token probabilities.
    """

    def __init__(self):
        self.bert = get_bert()
        self.nb = get_naive_bayes()
        self.hybrid = get_hybrid()

    @staticmethod
    def _compute_entropy(text: str) -> float:
        if not text:
            return 0.0
        freq: Dict[str, float] = {}
        for ch in text:
            freq[ch] = freq.get(ch, 0) + 1
        n = len(text)
        return round(-sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0), 2)

    def classify(
        self,
        features: ExtractedFeatures,
        preprocessed: Optional[PreprocessedData] = None,
    ) -> HybridClassificationResult:
        """
        Runs ensemble classification over text payload or extracted OCR/transcript text.
        """
        start_time = time.time()
        modality = features.input_type or "text"
        source = features.source

        # Extract text sequence
        text = ""
        if preprocessed:
            text = preprocessed.extracted_text or preprocessed.processed or ""
        if not text and isinstance(features.semantic_features, dict):
            text = features.semantic_features.get("text", "")

        if not text or not text.strip():
            return HybridClassificationResult(
                input_type=modality,
                source=source,
                predicted_class="SAFE",
                canonical_class="SAFE",
                bert_risk_score=0.0,
                nb_risk_probability=0.0,
                nb_probabilities={"SAFE": 1.0, "PII_PRESENT": 0.0, "HIGH_RISK": 0.0},
                hybrid_probability=0.0,
                shannon_entropy=0.0,
                classification_confidence=1.0,
                classification_source="hybrid_ml",
                classification_status="success",
                classification_time_ms=0.0,
            )

        try:
            hybrid_pred = self.hybrid.hybrid_predict(text)
            bert_res = self.bert.evaluate_privacy_semantics(text)
            nb_res = self.nb.evaluate_privacy_tokens(text)

            entropy = self._compute_entropy(text)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return HybridClassificationResult(
                input_type=modality,
                source=source,
                predicted_class=hybrid_pred.get("predicted_class", "SAFE"),
                canonical_class=hybrid_pred.get("canonical_class", "SAFE"),
                bert_risk_score=round(bert_res.get("risk_probability", 0.0), 4),
                nb_risk_probability=round(nb_res.get("risk_probability", 0.0), 4),
                nb_probabilities=nb_res.get("three_class_probabilities", {}),
                hybrid_probability=round(hybrid_pred.get("hybrid_risk_score", 0.0), 4),
                shannon_entropy=entropy,
                classification_confidence=round(hybrid_pred.get("confidence", 0.0), 4),
                classification_source=hybrid_pred.get("classification_source", "hybrid_ml"),
                classification_status="success",
                classification_time_ms=elapsed_ms,
            )

        except Exception as e:
            return HybridClassificationResult(
                input_type=modality,
                source=source,
                classification_status="error",
                classification_errors=[f"Hybrid classification error: {str(e)}"],
                classification_time_ms=round((time.time() - start_time) * 1000, 2),
            )
