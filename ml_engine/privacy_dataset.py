"""
Privacy & Security Classification Dataset Bridge.
File Location: ml_engine/privacy_dataset.py

Re-exports from data/unified_privacy_dataset.py (Single Source of Truth).
"""

from data.unified_privacy_dataset import (
    CANONICAL_CLASSES,
    CLASS_TO_ID,
    ID_TO_CLASS,
    THREE_CLASS_NAMES,
    CANONICAL_TO_THREE_CLASS,
    get_canonical_dataset,
    get_multiclass_training_samples,
    get_all_training_samples,
    get_benchmark_evaluation_samples,
    export_dataset_to_json,
    export_dataset_to_csv,
    SAFE_GENERAL_SAMPLES,
    PERSONAL_CONTEXT_SAMPLES,
    IDENTITY_INFORMATION_SAMPLES,
    CONTACT_INFORMATION_SAMPLES,
    FINANCIAL_INFORMATION_SAMPLES,
    CREDENTIAL_SAMPLES,
    GOVERNMENT_ID_SAMPLES,
    AUTHENTICATION_SECRET_SAMPLES,
    PROMPT_INJECTION_SAMPLES,
    OTHER_SENSITIVE_SAMPLES,
)

# Canonical 10-Class definitions
CANONICAL_PRIVACY_CLASSES = CANONICAL_CLASSES

# 3-Class Coarse Corpus for backward compatibility
PRIVACY_TRAINING_CORPUS = get_all_training_samples()
CLASS_NAMES = THREE_CLASS_NAMES
