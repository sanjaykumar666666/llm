"""
Ablation Evaluator & Empirical Performance Benchmarking Engine.
File Location: ml_engine/ablation_evaluator.py

Compares:
1. DistilBERT-only classifier
2. Naive Bayes-only classifier
3. Hybrid BERT + Naive Bayes Classifier

Metrics computed:
- Accuracy, Precision, Recall, F1-Score (Macro & Weighted)
- Average Inference Latency (ms)
- Data Utility Retention Score (%)
- Privacy Leakage Prevention Rate (%)
"""

import time
import tracemalloc
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.metrics import classification_report, precision_recall_fscore_support, accuracy_score

from data.unified_privacy_dataset import get_canonical_dataset, CANONICAL_CLASSES
from ml_engine.hybrid_classifier import HybridPrivacyClassifier
from privacy_engine.sanitizer import SmartSanitizer, RedactionStrategy


class ModelAblationBenchmarker:
    """
    Empirical research benchmarker for DistilBERT, Naive Bayes, and Hybrid Ensemble models.
    """

    def __init__(self, hybrid_classifier: Optional[HybridPrivacyClassifier] = None):
        if hybrid_classifier is not None:
            self.hybrid_model = hybrid_classifier
        else:
            self.hybrid_model = HybridPrivacyClassifier(alpha=0.60)
        self.sanitizer = SmartSanitizer()

    def run_ablation_study(self, samples: Optional[List[Tuple[str, str, str]]] = None) -> Dict[str, Any]:
        """
        Executes an empirical ablation experiment across all 3 model variants:
        1. DistilBERT Only
        2. Naive Bayes Only
        3. Hybrid Ensemble (BERT 0.60 + NB 0.40)
        """
        if samples is None:
            samples = get_canonical_dataset()

        prompts = [s[0] for s in samples]
        y_true = [s[1] for s in samples]

        y_pred_bert = []
        y_pred_nb = []
        y_pred_hybrid = []

        latencies_bert = []
        latencies_nb = []
        latencies_hybrid = []

        # Peak memory tracking
        tracemalloc.start()

        for prompt in prompts:
            # 1. DistilBERT evaluation
            t0 = time.perf_counter()
            bert_res = self.hybrid_model.bert.evaluate_privacy_semantics(prompt)
            t1 = time.perf_counter()
            pred_b = bert_res.get("predicted_class", "SAFE")
            y_pred_bert.append(pred_b)
            latencies_bert.append((t1 - t0) * 1000.0)

            # 2. Naive Bayes evaluation
            t2 = time.perf_counter()
            nb_res = self.hybrid_model.nb.evaluate_privacy_tokens(prompt)
            t3 = time.perf_counter()
            pred_nb = nb_res.get("canonical_class", "SAFE")
            y_pred_nb.append(pred_nb)
            latencies_nb.append((t3 - t2) * 1000.0)

            # 3. Hybrid Ensemble evaluation
            t4 = time.perf_counter()
            hyb_res = self.hybrid_model.hybrid_predict(prompt)
            t5 = time.perf_counter()
            pred_hyb = hyb_res.get("predicted_class", "SAFE")
            y_pred_hybrid.append(pred_hyb)
            latencies_hybrid.append((t5 - t4) * 1000.0)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Compute classification metrics
        def _calc_metrics(y_real, y_pred, lats):
            acc = float(accuracy_score(y_real, y_pred))
            prec, rec, f1, _ = precision_recall_fscore_support(
                y_real, y_pred, average="weighted", zero_division=0
            )
            macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(
                y_real, y_pred, average="macro", zero_division=0
            )
            return {
                "accuracy": round(acc * 100, 2),
                "precision_weighted": round(float(prec) * 100, 2),
                "recall_weighted": round(float(rec) * 100, 2),
                "f1_weighted": round(float(f1) * 100, 2),
                "f1_macro": round(float(macro_f1) * 100, 2),
                "avg_latency_ms": round(float(np.mean(lats)), 2),
                "p95_latency_ms": round(float(np.percentile(lats, 95)), 2),
            }

        metrics_bert = _calc_metrics(y_true, y_pred_bert, latencies_bert)
        metrics_nb = _calc_metrics(y_true, y_pred_nb, latencies_nb)
        metrics_hybrid = _calc_metrics(y_true, y_pred_hybrid, latencies_hybrid)

        # Compute Utility Retention & Leakage Metrics
        utility_res = self.calculate_data_utility_retention(prompts)

        return {
            "num_test_samples": len(prompts),
            "models": {
                "distilbert_only": metrics_bert,
                "naive_bayes_only": metrics_nb,
                "hybrid_ensemble": metrics_hybrid,
            },
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 2),
            "data_utility": utility_res,
        }

    def calculate_data_utility_retention(self, prompts: List[str]) -> Dict[str, float]:
        """
        Measures Data Utility Preservation (%) vs Information Redaction Ratio.
        Utility = Ratio of non-PII token preservation after smart redaction.
        """
        retained_ratios = []
        redacted_counts = 0

        for text in prompts:
            res = self.sanitizer.sanitize_prompt(text, strategy=RedactionStrategy.SYNTHETIC_MASK)
            sanitized_text = res.get("sanitized_prompt", text)
            entities = res.get("entities_redacted", [])

            orig_words = [w for w in text.split() if w]
            sanit_words = [w for w in sanitized_text.split() if w]

            if not orig_words:
                retained_ratios.append(100.0)
                continue

            if len(entities) > 0:
                redacted_counts += 1

            # Simple word overlap count for non-placeholder words
            non_mask_words = [w for w in sanit_words if not (w.startswith("[") and w.endswith("]"))]
            overlap = sum(1 for w in non_mask_words if w in orig_words)
            ratio = (overlap / max(1, len(orig_words))) * 100.0
            retained_ratios.append(min(100.0, ratio))

        avg_utility = round(float(np.mean(retained_ratios)), 2)
        leakage_prevention_rate = round((redacted_counts / max(1, len(prompts))) * 100.0, 2)

        return {
            "avg_utility_retention_pct": avg_utility,
            "leakage_prevention_rate_pct": leakage_prevention_rate,
            "total_evaluated_prompts": len(prompts),
        }
