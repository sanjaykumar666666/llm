"""
Privacy & Security Classification Dataset Bridge.
File Location: ml_engine/privacy_dataset.py

Re-exports from data/unified_privacy_dataset.py (Single Source of Truth).
"""

from data.unified_privacy_dataset import (
    get_all_training_samples,
    get_benchmark_evaluation_samples,
    export_dataset_to_json,
    export_dataset_to_csv,
    SAFE_GENERAL_SAMPLES,
    SAFE_EDUCATIONAL_SECURITY_SAMPLES,
    PII_CONTACT_SAMPLES,
    PII_HEALTH_DEMOGRAPHIC_SAMPLES,
    HIGH_RISK_CREDENTIAL_SAMPLES,
    HIGH_RISK_API_KEY_SAMPLES,
    HIGH_RISK_FINANCIAL_SAMPLES,
    HIGH_RISK_GOVERNMENT_ID_SAMPLES,
    PROMPT_INJECTION_SAMPLES,
)

PRIVACY_TRAINING_CORPUS = get_all_training_samples()
CLASS_NAMES = ["SAFE", "PII_PRESENT", "HIGH_RISK"]
