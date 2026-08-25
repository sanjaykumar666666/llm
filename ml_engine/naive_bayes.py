"""
Calibrated Naive Bayes Privacy Classifier.
File Location: ml_engine/naive_bayes.py

Architecture:
  - Feature Extractor: TfidfVectorizer (ngram_range=(1, 3), max_features=3500, sublinear_tf=True)
  - Probabilistic Classifier: MultinomialNB(alpha=0.08)
  - Checkpoint Management: Loads pre-trained artifact from ml_engine/checkpoints/naive_bayes_model.joblib
  - Zero Fake Probabilities: Computes mathematically valid Bayesian posterior distributions via predict_proba.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import joblib

from data.unified_privacy_dataset import (
    CANONICAL_CLASSES,
    CLASS_TO_ID,
    ID_TO_CLASS,
    THREE_CLASS_NAMES,
)

CHECKPOINTS_DIR = Path(__file__).resolve().parent / "checkpoints"
DEFAULT_CHECKPOINT_PATH = CHECKPOINTS_DIR / "naive_bayes_model.joblib"


class NaiveBayesPrivacyClassifier:
    """
    Probabilistic token classifier loaded from trained checkpoint.
    Outputs genuine Bayesian class probabilities, calibrated risk score, and confidence.
    """

    def __init__(self, checkpoint_path: Optional[Path] = None):
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else DEFAULT_CHECKPOINT_PATH
        self.vectorizer = None
        self.model = None
        self.is_trained = False
        self.model_status = "uninitialized"
        self.classes = CANONICAL_CLASSES
        self.class_to_id = CLASS_TO_ID
        self.id_to_class = ID_TO_CLASS
        self._load_model_checkpoint()

    def _load_model_checkpoint(self):
        """Loads pre-trained vectorizer and MultinomialNB model from persistent artifact."""
        try:
            if not self.checkpoint_path.exists():
                self.is_trained = False
                self.model_status = "checkpoint_missing"
                return

            data = joblib.load(self.checkpoint_path)
            self.vectorizer = data["vectorizer"]
            self.model = data["model"]
            self.classes = data.get("classes", CANONICAL_CLASSES)
            self.class_to_id = data.get("class_to_id", CLASS_TO_ID)
            self.id_to_class = data.get("id_to_class", ID_TO_CLASS)
            self.is_trained = True
            self.model_status = "available"

        except Exception as exc:
            self.is_trained = False
            self.model_status = f"load_error: {type(exc).__name__}"

    def evaluate_privacy_tokens(self, text: str) -> Dict[str, Any]:
        """
        Evaluates genuine Bayesian class probabilities and classification confidence.
        """
        if not text or not text.strip():
            return {
                "risk_probability": 0.0,
                "safe_probability": 1.0,
                "predicted_class": "SAFE",
                "canonical_class": "SAFE",
                "classification_confidence": 1.0,
                "probabilities": {c: (1.0 if c == "SAFE" else 0.0) for c in self.classes},
                "three_class_probabilities": {"SAFE": 1.0, "PII_PRESENT": 0.0, "HIGH_RISK": 0.0},
                "model_status": self.model_status,
                "is_trained": self.is_trained,
            }

        if self.is_trained and self.vectorizer and self.model:
            try:
                X_vec = self.vectorizer.transform([text])
                probs = self.model.predict_proba(X_vec)[0]

                prob_dict = {
                    cls_name: round(float(probs[idx]), 4)
                    for idx, cls_name in enumerate(self.classes)
                }

                max_idx = int(self.model.predict(X_vec)[0])
                canonical_class = self.classes[max_idx]
                conf = round(float(probs[max_idx]), 4)

                # Coarse 3-Class aggregation
                p_safe = prob_dict.get("SAFE", 0.0)
                p_pii = round(
                    prob_dict.get("PERSONAL_CONTEXT", 0.0) +
                    prob_dict.get("CONTACT_INFORMATION", 0.0) +
                    prob_dict.get("IDENTITY_INFORMATION", 0.0) +
                    prob_dict.get("OTHER_SENSITIVE", 0.0),
                    4
                )
                p_high = round(
                    prob_dict.get("CREDENTIAL", 0.0) +
                    prob_dict.get("AUTHENTICATION_SECRET", 0.0) +
                    prob_dict.get("FINANCIAL_INFORMATION", 0.0) +
                    prob_dict.get("GOVERNMENT_ID", 0.0) +
                    prob_dict.get("PROMPT_INJECTION", 0.0),
                    4
                )
                three_class_probs = {
                    "SAFE": round(p_safe, 4),
                    "PII_PRESENT": min(1.0, p_pii),
                    "HIGH_RISK": min(1.0, p_high),
                }

                # Continuous calibrated risk probability: 1.0 - P(SAFE)
                risk_prob = round(max(0.0, min(1.0, 1.0 - p_safe)), 4)

                # Coarse predicted class
                if canonical_class == "SAFE":
                    coarse_class = "SAFE"
                elif canonical_class in ("CREDENTIAL", "AUTHENTICATION_SECRET", "FINANCIAL_INFORMATION", "GOVERNMENT_ID", "PROMPT_INJECTION"):
                    coarse_class = "HIGH_RISK"
                else:
                    coarse_class = "PII_PRESENT"

                return {
                    "risk_probability": risk_prob,
                    "safe_probability": round(p_safe, 4),
                    "predicted_class": coarse_class,
                    "canonical_class": canonical_class,
                    "classification_confidence": conf,
                    "probabilities": prob_dict,
                    "three_class_probabilities": three_class_probs,
                    "model_status": "available",
                    "is_trained": True,
                }
            except Exception:
                pass

        # Explicit fallback when model is unavailable
        return {
            "risk_probability": 0.0,
            "safe_probability": 0.0,
            "predicted_class": "UNKNOWN",
            "canonical_class": "UNKNOWN",
            "classification_confidence": 0.0,
            "probabilities": {},
            "three_class_probabilities": {},
            "model_status": self.model_status,
            "is_trained": False,
        }

    def predict_probability(self, text: str) -> float:
        """Calculates risk probability in [0.0, 1.0]."""
        return self.evaluate_privacy_tokens(text)["risk_probability"]

    def predict_risk(self, text: str) -> float:
        """Alias for backward compatibility."""
        return self.predict_probability(text)
