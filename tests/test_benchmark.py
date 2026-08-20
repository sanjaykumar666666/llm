"""
Performance Benchmark Suite for Privacy Shield AI.
File Location: tests/test_benchmark.py
"""

import sys
import time
from pathlib import Path

# Add project root directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.api import process_firewall_request
from evaluation.metrics import PrivacyEvaluationMetrics


def run_performance_benchmark():
    print("=" * 70)
    print("   PRIVACY SHIELD AI -- SYSTEM PERFORMANCE & BENCHMARK SUITE   ")
    print("=" * 70)

    test_cases = [
        # Safe queries (Expected 0)
        ("What is quantum entanglement?", "text", 0),
        ("Explain the water cycle for students.", "text", 0),
        ("Write a Python script for binary search.", "text", 0),
        ("Summarize the plot of Hamlet.", "text", 0),
        ("What is the speed of light in vacuum?", "text", 0),

        # Sensitive queries (Expected 1 or 2)
        ("My phone number is 9876543210 call me tomorrow.", "text", 1),
        ("Contact admin at john@privacy-corp.com for info.", "text", 1),
        ("Card number 4532 1234 5678 9010 security code 999", "text", 2),
        ("SSN 123-45-6789 email user@test.com phone 555-0199", "text", 2),
        ("Secret key AKIAIOSFODNN7EXAMPLE login password SuperSecret!", "text", 2),
    ]

    y_true = []
    y_pred = []
    latencies = []

    print("\nExecuting benchmark requests...")
    for idx, (content, modality, expected_cat) in enumerate(test_cases, 1):
        t0 = time.time()
        res = process_firewall_request(modality=modality, text_content=content)
        latency = (time.time() - t0) * 1000
        latencies.append(latency)

        action = res.get("action", "ALLOW")
        pred_cat = 0 if action == "ALLOW" else (1 if action == "SANITIZE" else 2)

        y_true.append(expected_cat)
        y_pred.append(pred_cat)

        status = "OK" if pred_cat == expected_cat else "MISMATCH"
        print(f"Test #{idx:02d} | Modality: {modality:<6} | Expected: {expected_cat} | Got: {pred_cat} ({action:<8}) | Latency: {latency:5.1f} ms | [{status}]")

    metrics = PrivacyEvaluationMetrics.calculate_classifier_metrics(y_true, y_pred)
    avg_latency = sum(latencies) / len(latencies)

    print("\n" + "=" * 70)
    print(f"   BENCHMARK METRICS SUMMARY")
    print("=" * 70)
    print(f"   - Accuracy             : {metrics['accuracy'] * 100:.1f}%")
    print(f"   - Precision            : {metrics['precision']:.3f}")
    print(f"   - Recall               : {metrics['recall']:.3f}")
    print(f"   - F1-Score             : {metrics['f1_score']:.3f}")
    print(f"   - False Positive Rate  : {metrics['false_positive_rate']:.3f}")
    print(f"   - False Negative Rate  : {metrics['false_negative_rate']:.3f}")
    print(f"   - Average Latency      : {avg_latency:.2f} ms")
    print("=" * 70)


if __name__ == "__main__":
    run_performance_benchmark()
