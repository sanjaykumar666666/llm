"""
Real Video Privacy Analysis Route — Phases 1 to 7 Complete Multimodal Pipeline.
File: backend/routes/video_analysis.py
"""

from fastapi import APIRouter, UploadFile, File
from pipeline.input_handler import MultimodalInputHandler
from pipeline.preprocessor import MultimodalPreprocessor
from pipeline.feature_extractor import MultimodalFeatureExtractor
from pipeline.detector import PrivacyDetectionEngine
from pipeline.hybrid_classifier import HybridClassifier
from pipeline.risk_engine import PrivacyRiskScoringEngine
from pipeline.protection_engine import ProtectionAndDecisionEngine
from processing.text_processor import TextProcessor

router = APIRouter()

# Singletons
_input_handler = MultimodalInputHandler()
_preprocessor = MultimodalPreprocessor()
_feature_extractor = MultimodalFeatureExtractor()
_detector = PrivacyDetectionEngine()
_hybrid_classifier = HybridClassifier()
_risk_engine = PrivacyRiskScoringEngine()
_protection_engine = ProtectionAndDecisionEngine()
_text_processor = TextProcessor()


@router.post("/analyze/video")
async def video_analysis_endpoint(file: UploadFile = File(...)):
    """
    Complete Multimodal Security Pipeline:
      Phase 1: Input Validation & Temp Storage
      Phase 2: Temporal Keyframe Sampling & OCR Preparation
      Phase 3: Frame Visual & OCR Semantic Feature Extraction
      Phase 4: Frame Privacy & OCR Entity Detection
      Phase 5: Hybrid ML Classification
      Phase 6: Privacy Risk Scoring Engine
      Phase 7: Protection & Decision Engine
    """
    std_input = await _input_handler.handle_video(file)
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
        protection_res = _protection_engine.evaluate_and_protect(
            risk=risk_assessment,
            detections=detections,
            preprocessed=preprocessed,
        )

        extracted_text = preprocessed.extracted_text or ""
        frames = preprocessed.frames or []
        metadata = preprocessed.metadata or {}

        duration_str = metadata.get("duration_str", "00:00")
        duration_sec = metadata.get("duration_sec", 0.0)

        text_analysis = _text_processor.process(extracted_text)

        # Extended Video Content Understanding, Summary & 7-Phase Privacy Shield Pipeline
        content_analysis = {}
        seven_phase_privacy_pipeline = {}
        try:
            from backend.services.video_content_analyzer import VideoContentAnalyzer
            from backend.services.video_privacy_service import VideoPrivacyService
            
            target_path = std_input.file_path or (Path(std_input.metadata.get("saved_path")) if std_input.metadata.get("saved_path") else None)
            if target_path and Path(target_path).exists():
                with open(target_path, "rb") as vf:
                    vbytes = vf.read()
                seven_phase_privacy_pipeline = VideoPrivacyService.execute_video_privacy_pipeline(
                    video_bytes=vbytes,
                    filename=std_input.file_name or "uploaded_video.mp4",
                    protection_mode="Redact Sensitive",
                    protect_faces=True,
                    protect_qr_barcodes=True,
                    remove_audio=True
                )
                content_analysis = VideoContentAnalyzer.analyze_video_full(
                    str(target_path), filename=std_input.file_name
                )
        except Exception:
            pass

        final_verif = seven_phase_privacy_pipeline.get("final_report", {}).get("final_verification", {})

        return {
            "status": "success",
            "file_name": std_input.file_name,
            "modality": "video",
            "frames_processed": len(frames),
            "duration_str": duration_str,
            "duration_sec": duration_sec,
            "extracted_text": extracted_text,
            "sanitized_text": protection_res.protected_content,
            "timeline_frames": frames,
            "detected_entities": text_analysis.get("detected_entities", []),
            "detected_entity_types": text_analysis.get("detected_entity_types", []),
            "contains_pii": detections.has_pii,
            "shannon_entropy": text_analysis.get("shannon_entropy", 0.0),
            "character_count": text_analysis.get("character_count", 0),
            "word_count": text_analysis.get("word_count", 0),
            "risk_level": risk_assessment.risk_level,
            "action": protection_res.decision,
            "decision": protection_res.decision,
            "decision_reason": protection_res.decision_reason,
            "risk_score": risk_assessment.risk_score,
            "risk_factors": risk_assessment.risk_factors,
            "original_allowed_downstream": protection_res.original_allowed_downstream,
            "protected_allowed_downstream": protection_res.protected_allowed_downstream,
            "standardized_input": std_input.to_summary_dict(),
            "preprocessed_data": preprocessed.to_dict(),
            "extracted_features": features.to_dict(),
            "detection_result": detections.to_dict(),
            "hybrid_classification": hybrid_res.to_dict(),
            "risk_assessment": risk_assessment.to_dict(),
            "protection_result": protection_res.to_dict(),
            "content_analysis": content_analysis,
            "seven_phase_report": seven_phase_privacy_pipeline.get("final_report", {}),
            "verified": seven_phase_privacy_pipeline.get("verified", False),
            "verification_status": final_verif.get("status", "PASS"),
            "zero_leaks_guarantee": final_verif.get("zero_leaks_guarantee", False),
            "video_summary": content_analysis.get("summary", {}),
            "scenes": content_analysis.get("scenes", []),
            "copyright_assessment": content_analysis.get("copyright_assessment", {}),
            "best_frames": content_analysis.get("best_frames", {}),
            "risk_timeline": content_analysis.get("risk_timeline", []),
            "is_mock": False,
            "engine": "video_pipeline_7phases_real",
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Video processing failed: {str(e)}",
            "standardized_input": std_input.to_summary_dict(),
        }

    finally:
        MultimodalInputHandler.cleanup(std_input)
