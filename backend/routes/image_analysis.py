"""
Real Image Privacy Analysis Route — Phases 1 to 7 Complete Multimodal Pipeline.
File: backend/routes/image_analysis.py
"""

from fastapi import APIRouter, UploadFile, File, Form
from backend.services.image_privacy_service import ImagePrivacyService
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


@router.post("/analyze/image")
async def image_analysis_endpoint(
    file: UploadFile = File(...),
    protection_mode: str = Form("GAUSSIAN_BLUR")
):
    """
    Complete Multimodal Security Pipeline:
      Phase 1: Input Validation & Temp Storage
      Phase 2: Preprocessing & OCR Preparation
      Phase 3: Visual & OCR Semantic Feature Extraction
      Phase 4: Visual & OCR Privacy Detection
      Phase 5: Hybrid ML Classification
      Phase 6: Privacy Risk Scoring Engine
      Phase 7: Real Pixel-Level Protection (Blur/Pixelate/Redact) & Decision Engine
    """
    std_input = await _input_handler.handle_image(file)
    if not std_input.is_valid():
        return {
            "status": "error",
            "validation_status": "INVALID",
            "validation_errors": std_input.validation_errors,
            "standardized_input": std_input.to_summary_dict(),
        }

    try:
        preprocessed = _preprocessor.preprocess(std_input)
        features = _feature_extractor.extract_features(preprocessed)
        detections = _detector.detect(features, preprocessed)
        hybrid_res = _hybrid_classifier.classify(features, preprocessed)
        risk_assessment = _risk_engine.calculate_risk(detections, hybrid_res)

        # Phase 7: Real pixel protection
        protection_res = _protection_engine.evaluate_and_protect(
            risk=risk_assessment,
            detections=detections,
            preprocessed=preprocessed,
            protection_mode=protection_mode,
        )

        with open(std_input.file_path, "rb") as f:
            contents = f.read()

        result = ImagePrivacyService.process_image(
            contents,
            std_input.file_name or "uploaded_image.png",
            protection_mode
        )

        # Authoritative Phase 6 & 7 overrides
        result["risk_score"] = risk_assessment.risk_score
        result["risk_level"] = risk_assessment.risk_level
        result["risk_factors"] = risk_assessment.risk_factors
        result["decision"] = protection_res.decision
        result["action"] = protection_res.decision
        result["decision_reason"] = protection_res.decision_reason
        result["protected_image_b64"] = protection_res.protected_data_url or result.get("protected_image_b64")
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

    finally:
        MultimodalInputHandler.cleanup(std_input)
