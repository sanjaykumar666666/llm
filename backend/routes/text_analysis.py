"""
Text Analysis Route — Phases 1 to 7 Complete Multimodal Pipeline.
File: backend/routes/text_analysis.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.services.evidence_risk import run_full_analysis
from pipeline.input_handler import MultimodalInputHandler
from pipeline.preprocessor import MultimodalPreprocessor
from pipeline.feature_extractor import MultimodalFeatureExtractor
from pipeline.detector import PrivacyDetectionEngine
from pipeline.hybrid_classifier import HybridClassifier
from pipeline.risk_engine import PrivacyRiskScoringEngine
from pipeline.protection_engine import ProtectionAndDecisionEngine

router = APIRouter()

# Singletons
_input_handler = MultimodalInputHandler()
_preprocessor = MultimodalPreprocessor()
_feature_extractor = MultimodalFeatureExtractor()
_detector = PrivacyDetectionEngine()
_hybrid_classifier = HybridClassifier()
_risk_engine = PrivacyRiskScoringEngine()
_protection_engine = ProtectionAndDecisionEngine()


class TextAnalysisRequest(BaseModel):
    text: str
    sanitization_mode: Optional[str] = "REDACT"


@router.post("/analyze/text")
def text_analysis_endpoint(req: TextAnalysisRequest):
    """
    Complete Multimodal Security Pipeline:
      Phase 1: Input Validation
      Phase 2: Preprocessing & Unicode Normalization
      Phase 3: Feature & Semantic Extraction (BERT)
      Phase 4: Privacy & Injection Detection
      Phase 5: Hybrid Classification (BERT + Naive Bayes)
      Phase 6: Privacy Risk Scoring Engine
      Phase 7: Protection & Decision Engine
    """
    # Phase 1: Input Validation
    std_input = _input_handler.handle_text(req.text)
    if not std_input.is_valid():
        return {
            "status": "error",
            "validation_status": "INVALID",
            "validation_errors": std_input.validation_errors,
            "standardized_input": std_input.to_summary_dict(),
        }

    # Phase 2: Preprocessing
    preprocessed = _preprocessor.preprocess(std_input)

    # Phase 3: Feature Extraction
    features = _feature_extractor.extract_features(preprocessed)

    # Phase 4: Privacy Detection
    detections = _detector.detect(features, preprocessed)

    # Phase 5: Hybrid ML Classification
    hybrid_res = _hybrid_classifier.classify(features, preprocessed)

    # Phase 6: Privacy Risk Scoring Engine
    risk_assessment = _risk_engine.calculate_risk(detections, hybrid_res)

    # Phase 7: Protection & Decision Engine
    protection_res = _protection_engine.evaluate_and_protect(
        risk=risk_assessment,
        detections=detections,
        preprocessed=preprocessed,
    )

    # Downstream Analysis using sanitized text if protection applied
    effective_text = protection_res.protected_content if (protection_res.protection_applied and protection_res.protected_content) else (preprocessed.processed or std_input.raw_text)
    result = run_full_analysis(effective_text, mode=req.sanitization_mode or "REDACT")

    # Authoritative Phase 6 & 7 overrides
    result["risk_score"] = risk_assessment.risk_score
    result["risk_level"] = risk_assessment.risk_level
    result["action"] = protection_res.decision
    result["decision"] = protection_res.decision
    result["decision_reason"] = protection_res.decision_reason
    result["sanitized_text"] = protection_res.protected_content
    result["original_allowed_downstream"] = protection_res.original_allowed_downstream
    result["protected_allowed_downstream"] = protection_res.protected_allowed_downstream

    # Attach all pipeline stage artifacts
    result["standardized_input"] = std_input.to_summary_dict()
    result["preprocessed_data"] = preprocessed.to_dict()
    result["extracted_features"] = features.to_dict()
    result["detection_result"] = detections.to_dict()
    result["hybrid_classification"] = hybrid_res.to_dict()
    result["risk_assessment"] = risk_assessment.to_dict()
    result["protection_result"] = protection_res.to_dict()

    return result
