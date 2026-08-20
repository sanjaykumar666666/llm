"""
Unified Core Privacy Intelligence Evaluation Suite.
Tests the entire dataset against all categories in data/unified_privacy_dataset.py.
File Location: tests/evaluate_pipeline.py
"""

import sys
import os
import time
from typing import List, Tuple, Dict, Any

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, '.')

from backend.services.evidence_risk import run_full_analysis, warmup_models
from data.unified_privacy_dataset import get_benchmark_evaluation_samples

EVALUATION_DATASET = get_benchmark_evaluation_samples()


def run_evaluation():
    print("=" * 85)
    print("AI TRUST CHAT — UNIFIED PRIVACY INTELLIGENCE EVALUATION SUITE")
    print(f"Total Unified Test Prompts: {len(EVALUATION_DATASET)}")
    print("=" * 85)

    # Warm up first
    t_w0 = time.time()
    warmup_models()
    warmup_time = (time.time() - t_w0) * 1000
    print(f"Model Warmup Completed in: {warmup_time:.2f} ms\n")

    # Metrics accumulators
    tp = 0  # True Positive (Risk correctly identified as Risk)
    fp = 0  # False Positive (Safe incorrectly flagged as Risk)
    tn = 0  # True Negative (Safe correctly identified as Safe)
    fn = 0  # False Negative (Risk incorrectly passed as Safe)

    decision_matches = 0
    pii_correct = 0
    pii_total = 0
    cred_correct = 0
    cred_total = 0

    latencies = []
    category_metrics: Dict[str, Dict[str, int]] = {}

    for idx, (prompt, expected_is_risk, expected_decision, sub_cat) in enumerate(EVALUATION_DATASET, 1):
        if sub_cat not in category_metrics:
            category_metrics[sub_cat] = {"total": 0, "correct": 0}
        category_metrics[sub_cat]["total"] += 1

        t0 = time.time()
        res = run_full_analysis(prompt)
        lat = (time.time() - t0) * 1000
        latencies.append(lat)

        actual_decision = res["decision"]
        actual_is_risk = (actual_decision in ("WARN", "BLOCK")) or (res["risk_score"] > 0)

        # Binary Classification Evaluation
        if expected_is_risk and actual_is_risk:
            tp += 1
            is_correct = True
        elif not expected_is_risk and not actual_is_risk:
            tn += 1
            is_correct = True
        elif not expected_is_risk and actual_is_risk:
            fp += 1
            is_correct = False
        else:  # expected_is_risk and not actual_is_risk
            fn += 1
            is_correct = False

        if not is_correct:
            category_metrics[sub_cat]["correct"] += 0
            print(f"FAILED [{sub_cat}]: expected_risk={expected_is_risk}, actual_decision={actual_decision}, actual_score={res['risk_score']}%, prompt: '{prompt}'")
        else:
            category_metrics[sub_cat]["correct"] += 1

        # Decision Evaluation (ALLOW vs WARN vs BLOCK)
        if actual_decision == expected_decision or (expected_decision in ("WARN", "BLOCK") and actual_decision in ("WARN", "BLOCK")):
            decision_matches += 1

        # Sub-category accuracy tracking
        if "PII" in sub_cat:
            pii_total += 1
            if actual_decision in ("WARN", "BLOCK"):
                pii_correct += 1
        elif any(k in sub_cat for k in ("Credential", "Secret", "Financial", "Govt ID", "Security")):
            cred_total += 1
            if actual_decision in ("WARN", "BLOCK"):
                cred_correct += 1

    total_samples = len(EVALUATION_DATASET)
    accuracy = (tp + tn) / total_samples
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    mean_lat = sum(latencies) / len(latencies)
    latencies_sorted = sorted(latencies)
    p50_lat = latencies_sorted[len(latencies_sorted) // 2]
    p95_lat = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    min_lat = latencies_sorted[0]
    max_lat = latencies_sorted[-1]

    # Print Detailed Evaluation Report
    print("\n" + "=" * 85)
    print("UNIFIED PERFORMANCE & ACCURACY BENCHMARK")
    print("=" * 85)
    print(f"Total Unified Samples Evaluated:  {total_samples}")
    print(f"True Positives (TP):               {tp}")
    print(f"True Negatives (TN):               {tn}")
    print(f"False Positives (FP):              {fp}")
    print(f"False Negatives (FN):              {fn}")
    print("-" * 85)
    print(f"Accuracy:                         {accuracy * 100:.2f}%")
    print(f"Precision:                        {precision * 100:.2f}%")
    print(f"Recall:                           {recall * 100:.2f}%")
    print(f"F1 Score:                         {f1 * 100:.2f}%")
    print(f"False Positive Rate (FPR):        {fpr * 100:.2f}%")
    print(f"False Negative Rate (FNR):        {fnr * 100:.2f}%")
    print("-" * 85)
    print("CONFUSION MATRIX:")
    print(f"                 Actual Safe      Actual Risk")
    print(f"Predicted Safe     TN = {tn:2d}         FN = {fn:2d}")
    print(f"Predicted Risk     FP = {fp:2d}         TP = {tp:2d}")
    print("-" * 85)
    print("SUB-ENGINE ACCURACY:")
    if pii_total > 0:
        print(f"  • PII Detection Accuracy:        {pii_correct}/{pii_total} ({pii_correct/pii_total * 100:.1f}%)")
    if cred_total > 0:
        print(f"  • Credential/Secret Detection:   {cred_correct}/{cred_total} ({cred_correct/cred_total * 100:.1f}%)")
    print(f"  • Decision Routing Match:        {decision_matches}/{total_samples} ({decision_matches/total_samples * 100:.1f}%)")
    print("-" * 85)
    print(f"INFERENCE LATENCY BENCHMARKS ({total_samples} queries):")
    print(f"  • Mean Latency:                  {mean_lat:.2f} ms")
    print(f"  • P50 (Median) Latency:          {p50_lat:.2f} ms")
    print(f"  • P95 Latency:                   {p95_lat:.2f} ms")
    print(f"  • Min / Max Latency:             {min_lat:.2f} ms / {max_lat:.2f} ms")
    print("=" * 85)


if __name__ == "__main__":
    run_evaluation()
