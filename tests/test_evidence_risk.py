"""
Verification test suite for Live Explainable Privacy Detection & AI Trust Chat.
"""

import sys
import os
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, '.')

from backend.services.evidence_risk import run_full_analysis

test_cases = [
    ("1. Safe normal prompt", "Explain how photosynthesis works in green plants and why it is important."),
    ("2. 'What is a password?' (Safe question)", "What is a password and how does password hashing work?"),
    ("3. 'What is a password manager?' (Safe question)", "What is a password manager and how does it help protect user accounts?"),
    ("4. Actual password/credential (High Risk)", "Deploy config: username=admin password=SuperSecretP@ssw0rd!123 database=prod"),
    ("5. Email address (PII)", "My email is alice@company.com and please send the report there."),
    ("6. Phone number (PII)", "Please call our customer service hotline at +1-800-555-0199 for assistance."),
    ("7. Email + phone (PII)", "My email is alice@company.com and my phone is 9876543210."),
    ("8. Credit card + CVV (Actionable Financial Credentials)", "Billing record: Credit card number 4532 1234 5678 9010 expiration 12/28 CVV 882."),
    ("9. Mixed safe + sensitive prompt", "I am writing a blog post about cybersecurity. My email is researcher@lab.io and my phone is 9876543210."),
]

print("=" * 85)
print("LIVE EXPLAINABLE PRIVACY DETECTION & RISK ENGINE VERIFICATION SUITE")
print("=" * 85)

total_latency = 0.0

for idx, (label, prompt) in enumerate(test_cases, 1):
    t0 = time.time()
    res = run_full_analysis(prompt)
    lat = (time.time() - t0) * 1000
    total_latency += lat

    print(f"\n=================================================================================")
    print(f"TEST CASE {idx}: {label}")
    print(f"Prompt:         \"{prompt}\"")
    print(f"Status Banner:  {res['status_banner']}")
    print(f"Decision:       {res['decision']}")
    print(f"Risk Score:     {res['risk_score']}% ({res['risk_level']} RISK)")
    print(f"Action:         {res['action_label']}")
    print(f"BERT:           {res['bert_prediction']} (conf: {res['bert_confidence']*100:.1f}%)")
    print(f"Naive Bayes:    {res['nb_prediction']} (conf: {res['nb_confidence']*100:.1f}%)")
    
    # WHERE
    print("WHERE IS THE RISK?")
    if res['where_items']:
        for w in res['where_items']:
            print(f"  • Where: {w['exact_value']} | Type: {w['category']} | Span: {w['span']} | Severity: {w['severity']}")
    else:
        print("  • None (Clean payload)")

    # WHY
    print("WHY:")
    for b in res['why_bullets']:
        print(f"  {b}")

    print(f"Routing:        {res['routing_action']}")
    print(f"Inference Latency: {lat:.2f} ms")

avg_lat = total_latency / len(test_cases)
print("\n" + "=" * 85)
print(f"ALL {len(test_cases)} TESTS COMPLETED. Average Inference Latency: {avg_lat:.2f} ms")
print("=" * 85)
