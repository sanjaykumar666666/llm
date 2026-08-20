"""
Backend Processing Router and Security Gateway Controller.
File Location: backend/api.py
"""

import uuid
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import config
from backend.logger import log_privacy_audit
from processing.text_processor import TextProcessor
from processing.image_processor import ImageProcessor
from processing.video_processor import VideoProcessor
from processing.document_processor import DocumentProcessor
from ml_engine.feature_fusion import MultimodalFeatureFusion
from ml_engine.hybrid_classifier import HybridPrivacyClassifier
from privacy_engine.evaluator import PrivacyEvaluator
from privacy_engine.sanitizer import PrivacySanitizer
from llm_gateway.gemini_client import GeminiClient

# Instantiate global processing engines
text_processor = TextProcessor()
image_processor = ImageProcessor()
video_processor = VideoProcessor(max_frames_to_sample=15)
doc_processor = DocumentProcessor()
fusion_engine = MultimodalFeatureFusion()
hybrid_classifier = HybridPrivacyClassifier()
evaluator = PrivacyEvaluator()
sanitizer = PrivacySanitizer()
gemini_client = GeminiClient()


def is_meaningful_text_line(line: str) -> bool:
    """Strips out corrupted/garbage OCR noise or single character fragments."""
    if not line or len(line.strip()) < 3:
        return False
    clean = line.strip()
    words = clean.split()
    single_char_words = [w for w in words if len(w) == 1]
    if len(words) >= 3 and len(single_char_words) / len(words) > 0.5:
        return False
    alpha_num_count = sum(1 for c in clean if c.isalnum())
    return alpha_num_count >= 2


def split_text_into_readable_lines(text: str) -> List[str]:
    """Splits text into clean, readable lines."""
    if not text or not text.strip():
        return []
    initial_lines = [l.strip() for l in text.splitlines() if l.strip()]
    final_lines = []
    for line in initial_lines:
        if len(line) > 80:
            sub_parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+|(?<=\))|(?<=\})', line) if p.strip()]
            for part in sub_parts:
                if is_meaningful_text_line(part):
                    final_lines.append(part)
        else:
            if is_meaningful_text_line(line):
                final_lines.append(line)
    return final_lines


def generate_natural_story_summary(
    clean_lines: List[str],
    modality: str,
    duration_str: str,
    purpose_explanation: str,
    main_message: str
) -> str:
    """Generates a natural, human-readable narrative story/summary."""
    if clean_lines:
        narrative_parts = []
        narrative_parts.append(f"### 📖 Primary Narrative Overview\n{purpose_explanation}\n")
        narrative_parts.append("### 🎬 Key Story & Content Sequence")
        for idx, line in enumerate(clean_lines[:15], 1):
            narrative_parts.append(f"- **Content Detail #{idx}**: {line}")
        narrative_parts.append(f"\n### 📌 Conclusion\n{main_message}")
        return "\n".join(narrative_parts)

    return f"### 📖 Media Content Summary\n\n**Modality**: {modality.capitalize()}\n**Overview**: {purpose_explanation}\n**Message**: {main_message}"


def generate_mandatory_schema_payload(
    extracted_text: str,
    modality: str,
    frames_count: int,
    duration_str: str,
    detected_entities: List[str],
    risk_score: float,
    action: str,
    decision_reason: str,
    timeline_frames: List[Dict[str, Any]],
    file_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates the mandatory 7-property backend response schema."""
    clean_lines = split_text_into_readable_lines(extracted_text)
    lower_text = extracted_text.lower() if extracted_text else ""

    purpose_explanation = f"Evaluated {modality.capitalize()} payload for security, privacy, and compliance."
    main_message = f"Multimodal privacy inspection completed across {len(clean_lines)} text segments."

    video_overview = {
        "title": file_name if file_name else f"Uploaded {modality.capitalize()} Payload",
        "duration": duration_str,
        "purpose": purpose_explanation,
        "main_message": main_message
    }

    summary_text = generate_natural_story_summary(
        clean_lines=clean_lines,
        modality=modality,
        duration_str=duration_str,
        purpose_explanation=purpose_explanation,
        main_message=main_message
    )

    important_moments = []
    if timeline_frames:
        for idx, tf in enumerate(timeline_frames):
            ts = tf.get("timestamp_str", "00:00")
            txt = tf.get("extracted_text", "")
            important_moments.append({
                "timestamp": ts,
                "title": f"Frame Moment #{idx+1}",
                "description": txt if (txt and is_meaningful_text_line(txt)) else "Visual keyframe scene segment."
            })

    if not important_moments:
        important_moments = [
            {"timestamp": "00:00", "title": "Start", "description": f"Initial {modality} inspection frame."},
            {"timestamp": duration_str, "title": "End", "description": f"Final {modality} evaluation frame."}
        ]

    privacy_findings = []
    if detected_entities:
        for ent in detected_entities:
            privacy_findings.append({
                "type": ent,
                "timestamp": "00:00 - 00:15",
                "description": f"Unmasked token detected matching pattern for {ent}.",
                "risk": "HIGH" if ent in ["CREDIT_CARD", "GOVERNMENT_ID_SSN", "AWS_KEY", "OPENAI_API_KEY", "PRIVATE_KEY_BLOCK"] else "MEDIUM"
            })
        privacy_explanation = f"Detected {len(detected_entities)} sensitive entity type(s): {', '.join(detected_entities)}."
        privacy_level = "HIGH" if risk_score >= 0.75 else "MEDIUM"
    else:
        privacy_explanation = "No significant personal or sensitive information detected."
        privacy_level = "LOW"

    privacy_analysis = {
        "risk_score": risk_score,
        "risk_level": privacy_level,
        "decision": action,
        "findings": privacy_findings,
        "explanation": privacy_explanation
    }

    security_findings = []
    has_secret = any(kw in lower_text for kw in ["api_key", "password", "sk_live", "token", "secret", "private key", "akias"])
    if has_secret:
        security_findings.append({
            "type": "Authentication Secret",
            "timestamp": "00:00 - 00:05",
            "description": "Exposed credential token or API secret detected in payload.",
            "risk": "HIGH"
        })
        security_explanation = "Exposed credential tokens or authentication secrets were detected."
        security_level = "HIGH"
    else:
        security_explanation = "No credentials, API keys, passwords, or critical security secrets detected."
        security_level = "LOW"

    security_analysis = {
        "risk_level": security_level,
        "findings": security_findings,
        "explanation": security_explanation
    }

    final_decision = {
        "decision": action,
        "score": risk_score,
        "reason": decision_reason if decision_reason else "Evaluated against enterprise privacy policies."
    }

    if action == "ALLOW":
        final_recommendation = "SAFE TO SHARE — No significant sensitive content detected."
    elif action == "SANITIZE":
        final_recommendation = "SAFE AFTER REDACTION — Sensitive entities detected and redacted before LLM transmission."
    else:
        final_recommendation = "DO NOT SHARE — Critical privacy or security information detected. Execution halted."

    return {
        "video_overview": video_overview,
        "summary": summary_text,
        "important_moments": important_moments,
        "privacy_analysis": privacy_analysis,
        "security_analysis": security_analysis,
        "final_decision": final_decision,
        "final_recommendation": final_recommendation
    }


def analyze_extracted_lines(extracted_text: str) -> Dict[str, Any]:
    """Cleans text, filter noise, and classifies lines as SAFE (Green) or SENSITIVE (Red)."""
    cleaned_lines = split_text_into_readable_lines(extracted_text)
    if not cleaned_lines:
        return {"total_lines": 0, "safe_count": 0, "sensitive_count": 0, "lines": []}

    analyzed_lines = []
    safe_count = 0
    sensitive_count = 0

    for line in cleaned_lines:
        line_analysis = text_processor.process(line)
        entities = line_analysis["detected_entity_types"]
        if entities:
            sensitive_count += 1
            analyzed_lines.append({
                "line_text": line,
                "status": "SENSITIVE",
                "badge": "🔴 SENSITIVE PII",
                "entities": entities
            })
        else:
            safe_count += 1
            analyzed_lines.append({
                "line_text": line,
                "status": "SAFE",
                "badge": "🟢 SAFE CONTENT",
                "entities": []
            })

    return {
        "total_lines": len(analyzed_lines),
        "safe_count": safe_count,
        "sensitive_count": sensitive_count,
        "lines": analyzed_lines
    }


def process_firewall_request(
    modality: str,
    text_content: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    file_name: Optional[str] = None,
    sanitization_mode: str = "REDACT",
) -> Dict[str, Any]:
    """Unified entry point for inspecting multimodal requests (Text, Image, Video, Document)."""
    request_start_time = time.time()
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    saved_file_path = None

    try:
        if modality not in ["text", "image", "video", "document"]:
            raise ValueError(f"Invalid modality type: '{modality}'")

        raw_text_prompt = ""
        ocr_extracted_text = ""
        frames_count = 0
        input_length = 0
        duration_str = "00:05"
        timeline_frames = []
        doc_metadata = {}

        # Stage 1: Ingestion & Feature Extraction
        t0 = time.time()
        if modality == "text":
            if not text_content or not text_content.strip():
                raise ValueError("Text prompt cannot be empty.")
            raw_text_prompt = text_content
            input_length = len(text_content)

        elif modality == "image":
            if not file_bytes or not file_name:
                raise ValueError("No image file provided.")

            ext = Path(file_name).suffix.lower()
            if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError(f"Unsupported image format '{ext}'. Allowed: {config.ALLOWED_IMAGE_EXTENSIONS}")

            saved_file_path = config.TEMP_UPLOAD_DIR / f"{request_id}_{file_name}"
            with open(saved_file_path, "wb") as f:
                f.write(file_bytes)

            input_length = len(file_bytes)
            image_result = image_processor.process(file_bytes)
            ocr_extracted_text = image_result["extracted_text"]

        elif modality == "video":
            if not file_bytes or not file_name:
                raise ValueError("No video file provided.")

            ext = Path(file_name).suffix.lower()
            if ext not in config.ALLOWED_VIDEO_EXTENSIONS:
                raise ValueError(f"Unsupported video format '{ext}'. Allowed: {config.ALLOWED_VIDEO_EXTENSIONS}")

            saved_file_path = config.TEMP_UPLOAD_DIR / f"{request_id}_{file_name}"
            with open(saved_file_path, "wb") as f:
                f.write(file_bytes)

            input_length = len(file_bytes)
            video_result = video_processor.process(saved_file_path)
            ocr_extracted_text = video_result["extracted_text"]
            frames_count = video_result["frames_processed"]
            duration_str = video_result.get("duration_str", "00:00")
            timeline_frames = video_result.get("timeline_frames", [])

        elif modality == "document":
            if not file_bytes or not file_name:
                raise ValueError("No document file provided.")

            ext = Path(file_name).suffix.lower()
            if ext not in config.ALLOWED_DOCUMENT_EXTENSIONS:
                raise ValueError(f"Unsupported document format '{ext}'. Allowed: {config.ALLOWED_DOCUMENT_EXTENSIONS}")

            input_length = len(file_bytes)
            doc_result = doc_processor.process_file_bytes(file_bytes, file_name)
            ocr_extracted_text = doc_result["extracted_text"]
            doc_metadata = doc_result["doc_metadata"]

        stage1_ms = round((time.time() - t0) * 1000, 2)

        # Stage 2: Feature Fusion & Text Analysis
        t1 = time.time()
        combined_text_for_summary = ocr_extracted_text if ocr_extracted_text else raw_text_prompt
        line_analysis_report = analyze_extracted_lines(combined_text_for_summary)

        fused_payload = fusion_engine.fuse_features(
            modality=modality,
            text_content=raw_text_prompt,
            ocr_text=ocr_extracted_text,
            frames_processed=frames_count,
            doc_metadata=doc_metadata,
        )
        stage2_ms = round((time.time() - t1) * 1000, 2)

        # Stage 3: ML Hybrid Classifier Inference
        t2 = time.time()
        ml_analysis = hybrid_classifier.predict_privacy_risk(fused_payload)
        risk_score = ml_analysis["hybrid_risk_score"]
        unified_text = fused_payload["unified_text"]
        detected_entities = fused_payload["detected_entity_types"]
        max_severity = fused_payload.get("max_entity_severity", 0.0)
        stage3_ms = round((time.time() - t2) * 1000, 2)

        # Stage 4: Privacy Evaluator Gate
        t3 = time.time()
        decision = evaluator.evaluate_decision(
            risk_score=risk_score,
            detected_entities=detected_entities,
            contains_regex_pii=bool(fused_payload["metadata_features"].get("contains_regex_pii", 0)),
            max_severity=max_severity,
        )

        action = decision["action"]
        risk_level = decision["risk_level"]
        stage4_ms = round((time.time() - t3) * 1000, 2)

        # Stage 5: Mandatory Schema Construction
        schema_payload = generate_mandatory_schema_payload(
            extracted_text=combined_text_for_summary,
            modality=modality,
            frames_count=frames_count,
            duration_str=duration_str,
            detected_entities=detected_entities,
            risk_score=risk_score,
            action=action,
            decision_reason=decision["reason"],
            timeline_frames=timeline_frames,
            file_name=file_name
        )

        # Stage 6: Action Execution & LLM Gateway
        t4 = time.time()
        if action == "BLOCK":
            sanitized_prompt = None
            llm_response = f"🚫 [BLOCKED BY FIREWALL]: Prompt halted. Risk level: {risk_level} ({risk_score:.2f}). Reason: {decision['reason']}"
            llm_status = "BLOCKED_BY_FIREWALL"

        elif action == "SANITIZE":
            sanitization_result = sanitizer.sanitize_text(unified_text, mode=sanitization_mode)
            sanitized_prompt = sanitization_result["sanitized_text"]
            if not sanitized_prompt or not sanitized_prompt.strip():
                sanitized_prompt = "[SANITIZED PROMPT]: All sensitive tokens were redacted."

            llm_payload = gemini_client.generate_response(sanitized_prompt)
            llm_response = llm_payload["response_text"]
            llm_status = llm_payload["status"]

        else:  # ALLOW
            sanitized_prompt = unified_text if unified_text else f"Safe content from {modality}"
            llm_payload = gemini_client.generate_response(sanitized_prompt)
            llm_response = llm_payload["response_text"]
            llm_status = llm_payload["status"]
        stage6_ms = round((time.time() - t4) * 1000, 2)

        total_latency_ms = round((time.time() - request_start_time) * 1000, 2)

        # Stage 7: Privacy Audit Logging
        log_privacy_audit(
            request_id=request_id,
            modality=modality,
            risk_score=risk_score,
            action_taken=action,
            detected_entities=detected_entities,
            original_length=input_length,
            llm_status=llm_status,
        )

        return {
            "status": "success",
            "request_id": request_id,
            "modality": modality,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "action": action,
            "reason": decision["reason"],
            "ml_breakdown": ml_analysis,
            "detected_entities": detected_entities,
            "extracted_text": unified_text,
            "frames_processed": frames_count,
            "duration_str": duration_str,
            "sanitized_prompt": sanitized_prompt,
            "llm_response": llm_response,
            "total_latency_ms": total_latency_ms,
            "latency_breakdown_ms": {
                "ingestion": stage1_ms,
                "fusion": stage2_ms,
                "ml_classifier": stage3_ms,
                "evaluator_gate": stage4_ms,
                "llm_gateway": stage6_ms,
            },
            "video_overview": schema_payload["video_overview"],
            "summary": schema_payload["summary"],
            "important_moments": schema_payload["important_moments"],
            "privacy_analysis": schema_payload["privacy_analysis"],
            "security_analysis": schema_payload["security_analysis"],
            "final_decision": schema_payload["final_decision"],
            "final_recommendation": schema_payload["final_recommendation"],
            "total_lines": line_analysis_report["total_lines"],
            "safe_count": line_analysis_report["safe_count"],
            "sensitive_count": line_analysis_report["sensitive_count"],
            "line_highlights": line_analysis_report["lines"]
        }

    except Exception as e:
        log_privacy_audit(
            request_id=request_id,
            modality=modality,
            risk_score=1.0,
            action_taken="ERROR_BLOCK",
            detected_entities=["SYSTEM_ERROR"],
            original_length=0,
            llm_status="FAILED",
        )
        return {
            "status": "error",
            "request_id": request_id,
            "error_message": str(e),
        }

    finally:
        if saved_file_path and saved_file_path.exists():
            try:
                saved_file_path.unlink()
            except Exception:
                pass
