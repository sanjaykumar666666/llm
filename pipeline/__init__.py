"""
Pipeline Package — Multimodal Privacy Risk Detection Pipeline.
Phase 1: Standardized Input Handler.
Phase 2: Data Preprocessing Layer.
Phase 3: Feature & Semantic Extraction Layer.
Phase 4: Privacy Detection Engine.
Phase 5: Hybrid Classification Engine (BERT + Naive Bayes).
Phase 6: Privacy Risk Scoring Engine.
Phase 7: Protection & Decision Engine.
"""

from pipeline.input_handler import StandardizedInput, MultimodalInputHandler
from pipeline.preprocessor import PreprocessedData, MultimodalPreprocessor
from pipeline.feature_extractor import ExtractedFeatures, MultimodalFeatureExtractor
from pipeline.detector import PrivacyDetectionEngine, DetectionResult
from pipeline.hybrid_classifier import HybridClassifier, HybridClassificationResult
from pipeline.risk_engine import PrivacyRiskScoringEngine, RiskAssessmentResult
from pipeline.protection_engine import ProtectionAndDecisionEngine, ProtectionResult

__all__ = [
    "StandardizedInput",
    "MultimodalInputHandler",
    "PreprocessedData",
    "MultimodalPreprocessor",
    "ExtractedFeatures",
    "MultimodalFeatureExtractor",
    "PrivacyDetectionEngine",
    "DetectionResult",
    "HybridClassifier",
    "HybridClassificationResult",
    "PrivacyRiskScoringEngine",
    "RiskAssessmentResult",
    "ProtectionAndDecisionEngine",
    "ProtectionResult",
]
