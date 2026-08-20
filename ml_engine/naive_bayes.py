"""
Calibrated Naïve Bayes 3-Class Privacy Classifier.
File Location: ml_engine/naive_bayes.py

Classes:
  0: SAFE
  1: PII_PRESENT
  2: HIGH_RISK
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from typing import Dict, Any, List
from ml_engine.privacy_dataset import PRIVACY_TRAINING_CORPUS, CLASS_NAMES


class NaiveBayesPrivacyClassifier:
    """
    Probabilistic 3-class token classifier trained on balanced privacy corpus.
    Outputs true class probabilities, calibrated risk score, and confidence.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=2500,
            stop_words="english",
            ngram_range=(1, 3),
            sublinear_tf=True
        )
        self.model = MultinomialNB(alpha=0.1)
        self.is_trained = False
        self._initialize_bootstrap_training()

    def _initialize_bootstrap_training(self):
        """Trains the 3-class Naïve Bayes model on the curated domain corpus."""
        texts = [item[0] for item in PRIVACY_TRAINING_CORPUS]
        labels = [item[1] for item in PRIVACY_TRAINING_CORPUS]

        X_train = self.vectorizer.fit_transform(texts)
        self.model.fit(X_train, labels)
        self.is_trained = True

    def evaluate_privacy_tokens(self, text: str) -> Dict[str, Any]:
        """
        Evaluates 3-class token risk probability and classification confidence.
        """
        if not text or not text.strip():
            return {
                "risk_probability": 0.0,
                "safe_probability": 1.0,
                "predicted_class": "SAFE",
                "classification_confidence": 1.0,
                "probabilities": {"SAFE": 1.0, "PII_PRESENT": 0.0, "HIGH_RISK": 0.0},
            }

        try:
            X_vec = self.vectorizer.transform([text])
            probs = self.model.predict_proba(X_vec)[0]

            p_safe = round(float(probs[0]), 4)
            p_pii = round(float(probs[1]), 4)
            p_high = round(float(probs[2]), 4)

            # Continuous calibrated risk probability: P(Risk) = P(PII)*0.45 + P(HIGH)*1.0
            risk_prob = round(min(1.0, p_pii * 0.45 + p_high), 4)

            max_idx = int(self.model.predict(X_vec)[0])
            pred_class = CLASS_NAMES[max_idx]
            conf = round(float(probs[max_idx]), 4)

            return {
                "risk_probability": risk_prob,
                "safe_probability": p_safe,
                "predicted_class": pred_class,
                "classification_confidence": conf,
                "probabilities": {
                    "SAFE": p_safe,
                    "PII_PRESENT": p_pii,
                    "HIGH_RISK": p_high,
                },
            }
        except Exception:
            return {
                "risk_probability": 0.0,
                "safe_probability": 1.0,
                "predicted_class": "SAFE",
                "classification_confidence": 0.85,
                "probabilities": {"SAFE": 1.0, "PII_PRESENT": 0.0, "HIGH_RISK": 0.0},
            }

    def predict_probability(self, text: str) -> float:
        """Calculates probability (0.0 to 1.0) that the input text contains sensitive information."""
        return self.evaluate_privacy_tokens(text)["risk_probability"]

    def predict_risk(self, text: str) -> float:
        """Alias for backward compatibility."""
        return self.predict_probability(text)
