"""
Prompt Injection Detector Route — Real Phase 4 Injection Detection.
File: backend/routes/injection_detector.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from pipeline.input_handler import MultimodalInputHandler
from pipeline.preprocessor import MultimodalPreprocessor
from pipeline.feature_extractor import MultimodalFeatureExtractor
from pipeline.detector import PrivacyDetectionEngine

router = APIRouter()

# Singletons
_input_handler = MultimodalInputHandler()
_preprocessor = MultimodalPreprocessor()
_feature_extractor = MultimodalFeatureExtractor()
_detector = PrivacyDetectionEngine()


class InjectionRequest(BaseModel):
    prompt: str


@router.post("/detect/injection")
def injection_detector_endpoint(req: InjectionRequest):
    """
    Real Phase 4 Prompt Injection Detector:
    Analyzes input prompt for adversarial instruction overrides, system prompt reveal attempts, and jailbreaks.
    """
    std_input = _input_handler.handle_text(req.prompt)
    preprocessed = _preprocessor.preprocess(std_input)
    features = _feature_extractor.extract_features(preprocessed)
    detection_res = _detector.detect(features, preprocessed)

    # Filter prompt injection detections
    injection_dets = [
        d for d in detection_res.detections
        if d.get("category") == "PROMPT_INJECTION" or "INJECTION" in d.get("type", "")
    ]

    is_injection = len(injection_dets) > 0
    risk_score = 94 if is_injection else 12
    status = "Malicious" if is_injection else "Safe"
    action = "BLOCK" if is_injection else "ALLOW"

    matched_patterns = [d.get("reason", "Adversarial Pattern") for d in injection_dets]

    return {
        "prompt": req.prompt,
        "is_injection": is_injection,
        "risk_score": risk_score,
        "status": status,
        "action": action,
        "detections": injection_dets,
        "matched_patterns": matched_patterns,
        "detection_result": detection_res.to_dict(),
        "is_mock": False,
        "engine": "real_privacy_detection_engine_v4",
    }
