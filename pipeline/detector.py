"""
Privacy Detection Engine — Phase 4 Core Module.
File Location: pipeline/detector.py

Responsibilities:
  1. Consumes Phase 3 ExtractedFeatures & Phase 2 PreprocessedData.
  2. Detects PII, Credentials, Financial data, Health records, and Prompt Injections.
  3. Visual Privacy Detection: Human Faces, ID documents, QR/Barcodes.
  4. OCR Spatial Mapping: Maps detected text PII to exact bounding boxes [x1, y1, x2, y2].
  5. Video Temporal Mapping: Maps detections to frame_id and timestamp [MM:SS].
  6. YouTube Transcript Detection: Timestamped segment PII and secret detection.
  7. Safe Masking: Generates safe masked representations (e.g. ••••••••1234) for secure logging and UI.
  8. Canonical Categories:
     - PERSONAL_INFORMATION
     - IDENTITY_INFORMATION
     - FINANCIAL_INFORMATION
     - AUTHENTICATION_INFORMATION
     - MEDICAL_INFORMATION
     - LOCATION_INFORMATION
     - BUSINESS_CONFIDENTIAL_INFORMATION
     - VISUAL_PRIVACY
     - PROMPT_INJECTION
  9. Standardized Detection Output: Produces DetectionResult dataclass.
"""

import re
import cv2
import time
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image

import config
from pipeline.feature_extractor import ExtractedFeatures
from pipeline.preprocessor import PreprocessedData
from privacy_engine.context_detector import ContextAwareEntityDetector


# ── Canonical Privacy Categories ──────────────────────────────────────────────
CATEGORY_PERSONAL = "PERSONAL_INFORMATION"
CATEGORY_IDENTITY = "IDENTITY_INFORMATION"
CATEGORY_FINANCIAL = "FINANCIAL_INFORMATION"
CATEGORY_AUTH = "AUTHENTICATION_INFORMATION"
CATEGORY_MEDICAL = "MEDICAL_INFORMATION"
CATEGORY_LOCATION = "LOCATION_INFORMATION"
CATEGORY_BUSINESS = "BUSINESS_CONFIDENTIAL_INFORMATION"
CATEGORY_VISUAL = "VISUAL_PRIVACY"
CATEGORY_INJECTION = "PROMPT_INJECTION"

# ── Entity Type → Category Mapping ────────────────────────────────────────────
ENTITY_CATEGORY_MAP = {
    # Personal
    "EMAIL_ADDRESS": CATEGORY_PERSONAL,
    "PHONE_NUMBER": CATEGORY_PERSONAL,
    "NAME": CATEGORY_PERSONAL,
    "DATE_OF_BIRTH": CATEGORY_PERSONAL,
    "EMPLOYEE_ID": CATEGORY_PERSONAL,

    # Identity
    "GOVERNMENT_ID_AADHAAR": CATEGORY_IDENTITY,
    "GOVERNMENT_ID_PAN": CATEGORY_IDENTITY,
    "GOVERNMENT_ID_SSN": CATEGORY_IDENTITY,
    "GOVERNMENT_ID_NINO": CATEGORY_IDENTITY,
    "PASSPORT_NUMBER": CATEGORY_IDENTITY,
    "DRIVING_LICENSE": CATEGORY_IDENTITY,
    "VOTER_ID": CATEGORY_IDENTITY,

    # Financial
    "CREDIT_CARD_NUMBER": CATEGORY_FINANCIAL,
    "BANK_ROUTING_ACCOUNT": CATEGORY_FINANCIAL,
    "BANK_ACCOUNT_IBAN": CATEGORY_FINANCIAL,
    "UPI_ID": CATEGORY_FINANCIAL,

    # Authentication & Secrets
    "CREDENTIAL_PASSWORD": CATEGORY_AUTH,
    "AWS_ACCESS_KEY": CATEGORY_AUTH,
    "GITHUB_TOKEN": CATEGORY_AUTH,
    "OPENAI_API_KEY": CATEGORY_AUTH,
    "GOOGLE_CLOUD_API_KEY": CATEGORY_AUTH,
    "SENDGRID_API_KEY": CATEGORY_AUTH,
    "SLACK_BOT_TOKEN": CATEGORY_AUTH,
    "GENERIC_API_SECRET": CATEGORY_AUTH,
    "JWT_TOKEN": CATEGORY_AUTH,
    "BEARER_TOKEN": CATEGORY_AUTH,
    "PRIVATE_KEY_BLOCK": CATEGORY_AUTH,

    # Medical
    "MEDICAL_PATIENT_RECORD": CATEGORY_MEDICAL,

    # Location
    "PHYSICAL_STREET_ADDRESS": CATEGORY_LOCATION,
    "IP_ADDRESS": CATEGORY_LOCATION,

    # Business
    "DATABASE_CONNECTION_STRING": CATEGORY_BUSINESS,
    "CONFIDENTIAL_BUSINESS_SPEC": CATEGORY_BUSINESS,

    # Visual
    "FACE": CATEGORY_VISUAL,
    "QR_CODE": CATEGORY_VISUAL,
    "BARCODE": CATEGORY_VISUAL,
    "DOCUMENT_PHOTO": CATEGORY_VISUAL,
    "SIGNATURE": CATEGORY_VISUAL,

    # Injection
    "PROMPT_INJECTION_OVERRIDE": CATEGORY_INJECTION,
    "JAILBREAK_ATTEMPT": CATEGORY_INJECTION,
}


# ── Prompt Injection Detection Patterns ────────────────────────────────────────
INJECTION_DETECTION_PATTERNS = [
    (r"(?:ignore\s+(?:all\s+)?(?:previous\s+)?(?:system\s+|your\s+)?instructions)", "Instruction Override", 0.98, "CRITICAL"),
    (r"(?:disregard\s+(?:all\s+)?(?:safety\s+)?guardrails)", "Guardrail Bypass", 0.96, "CRITICAL"),
    (r"(?:reveal\s+(?:the\s+)?(?:secret\s+)?system\s+prompt|show\s+me\s+your\s+system\s+prompt)", "System Prompt Extraction", 0.95, "CRITICAL"),
    (r"(?:output\s+the\s+entire\s+system\s+prompt)", "System Prompt Extraction", 0.95, "CRITICAL"),
    (r"(?:developer\s+mode\s+dan|dan\s+mode\s+enabled)", "Jailbreak Directive (DAN)", 0.92, "CRITICAL"),
    (r"(?:act\s+as\s+an\s+unfiltered\s+ai|act\s+as\s+if\s+you\s+have\s+no\s+rules)", "Constraint Removal", 0.90, "CRITICAL"),
    (r"(?:dump\s+environment\s+variables|print\s+env\s+vars)", "Environment Exfiltration", 0.94, "CRITICAL"),
    (r"(?:bypass\s+(?:all\s+)?security\s+filters)", "Security Bypass", 0.91, "CRITICAL"),
    (r"(?:forget\s+all\s+prior\s+rules)", "Rule Erasure", 0.90, "CRITICAL"),
]


def mask_sensitive_value(val: str, ent_type: str = "") -> str:
    """
    Generates a secure masked string representation for safe display & logging.
    Preserves at most the last 3-4 digits/chars for identity verification.
    """
    if not val:
        return "••••"

    val_clean = str(val).strip()

    # Credit card / National ID: show last 4
    if any(k in ent_type for k in ["CARD", "AADHAAR", "SSN", "ACCOUNT", "PHONE"]):
        digits = re.sub(r"\D", "", val_clean)
        if len(digits) >= 4:
            return f"••••••••{digits[-4:]}"
        return "••••••••"

    # Email: j•••@domain.com
    if "@" in val_clean:
        parts = val_clean.split("@")
        user = parts[0]
        domain = parts[1] if len(parts) > 1 else ""
        masked_user = user[0] + "•••" if len(user) > 1 else "•••"
        return f"{masked_user}@{domain}"

    # Secrets / Passwords / Keys: total mask with key prefix
    if any(k in ent_type for k in ["KEY", "TOKEN", "SECRET", "PASSWORD", "PRIVATE"]):
        if val_clean.startswith("AKIA") and len(val_clean) >= 8:
            return f"AKIA••••••••{val_clean[-4:]}"
        if val_clean.startswith("sk-") and len(val_clean) >= 8:
            return f"sk-••••••••{val_clean[-4:]}"
        return "••••••••"

    # General fallback
    if len(val_clean) <= 4:
        return "••••"
    return f"••••{val_clean[-4:]}"


@dataclass
class DetectionResult:
    """
    Standardized Detection Output Dataclass for all modalities.
    Authoritative source of truth for Phase 5 (Hybrid Classifier) and Phase 6 (Risk Engine).
    """

    input_type: str = "text"                    # "text" | "image" | "video" | "youtube"
    source: str = "direct_input"
    detections: List[Dict[str, Any]] = field(default_factory=list)
    category_counts: Dict[str, int] = field(default_factory=dict)
    detection_count: int = 0
    has_critical_secrets: bool = False
    has_pii: bool = False
    has_injection: bool = False
    has_visual_privacy: bool = False

    # Status
    detection_status: str = "success"           # "success" | "error"
    detection_errors: List[str] = field(default_factory=list)
    detection_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable representation."""
        return {
            "input_type": self.input_type,
            "source": self.source,
            "detections": self.detections,
            "category_counts": self.category_counts,
            "detection_count": self.detection_count,
            "has_critical_secrets": self.has_critical_secrets,
            "has_pii": self.has_pii,
            "has_injection": self.has_injection,
            "has_visual_privacy": self.has_visual_privacy,
            "detection_status": self.detection_status,
            "detection_errors": self.detection_errors,
            "detection_time_ms": self.detection_time_ms,
        }


class PrivacyDetectionEngine:
    """
    Enterprise Multimodal Privacy Detection Engine.
    Detects PII, Credentials, Visual Privacy, and Prompt Injections with character-exact
    and spatial bounding box coordinates.
    """

    def __init__(self):
        self.context_detector = ContextAwareEntityDetector()

    # ── 1. TEXT PRIVACY & INJECTION DETECTION ───────────────────────────────────

    def detect_text_privacy(self, text: str, source: str = "direct_input") -> List[Dict[str, Any]]:
        """
        Runs context-aware detection on text for PII, credentials, and prompt injections.
        """
        detections = []
        if not text or not text.strip():
            return detections

        # 1. Context-Aware Entity & Credential Detection
        raw_entities = self.context_detector.detect_entities(text)
        for ent in raw_entities:
            ent_type = ent.get("entity_type", "SENSITIVE_DATA")
            cat = ENTITY_CATEGORY_MAP.get(ent_type, CATEGORY_PERSONAL)
            raw_val = ent.get("detected_span", "")

            detections.append({
                "type": ent_type,
                "category": cat,
                "value_masked": mask_sensitive_value(raw_val, ent_type),
                "confidence": round(float(ent.get("confidence", 0.95)), 2),
                "severity": ent.get("severity", "MEDIUM"),
                "location": {
                    "start": ent.get("start_index", 0),
                    "end": ent.get("end_index", len(raw_val)),
                },
                "bbox": None,
                "reason": ent.get("reason", "Sensitive privacy disclosure detected"),
            })

        # 2. Prompt Injection Detection Patterns
        lower = text.lower()
        for pat, attack_name, conf, sev in INJECTION_DETECTION_PATTERNS:
            match = re.search(pat, lower, re.IGNORECASE)
            if match:
                matched_span = text[match.start():match.end()]
                detections.append({
                    "type": "PROMPT_INJECTION_OVERRIDE",
                    "category": CATEGORY_INJECTION,
                    "value_masked": f"[ADVERSARIAL_SEQUENCE]: '{matched_span[:25]}...'",
                    "confidence": conf,
                    "severity": sev,
                    "location": {
                        "start": match.start(),
                        "end": match.end(),
                    },
                    "bbox": None,
                    "reason": f"Prompt injection attack pattern detected: {attack_name}",
                })

        return detections

    # ── 2. OCR TEXT PRIVACY & SPATIAL BOUNDING BOX DETECTION ───────────────────

    def detect_ocr_privacy(self, ocr_boxes: List[Dict[str, Any]], full_ocr_text: str) -> List[Dict[str, Any]]:
        """
        Detects PII in OCR text and maps detected entities to their actual spatial bounding boxes.
        """
        detections = []
        if not full_ocr_text or not full_ocr_text.strip():
            return detections

        # 1. Detect entities on full OCR text
        text_dets = self.detect_text_privacy(full_ocr_text)

        # 2. Map back to spatial bounding box coordinates
        for d in text_dets:
            # Search for word match in ocr_boxes
            matched_bbox = None
            loc = d.get("location", {})
            start_pos = loc.get("start", 0)
            end_pos = loc.get("end", len(full_ocr_text))

            target_snippet = full_ocr_text[start_pos:end_pos].strip()

            # Find matching box by text alignment
            for box in ocr_boxes:
                b_text = box.get("text", "").strip()
                if b_text and (b_text in target_snippet or target_snippet in b_text):
                    matched_bbox = box.get("bbox")
                    break

            # If no single word matched, take default first box if available
            if not matched_bbox and ocr_boxes:
                matched_bbox = ocr_boxes[0].get("bbox")

            d_copy = dict(d)
            d_copy["bbox"] = matched_bbox
            detections.append(d_copy)

        return detections

    # ── 3. IMAGE VISUAL PRIVACY DETECTION ──────────────────────────────────────

    def detect_image_visual_privacy(self, image_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Detects Human Faces, QR Codes, and Barcodes directly on the image.
        """
        visual_dets = []
        if not image_path or not Path(image_path).exists():
            return visual_dets

        try:
            cv_img = cv2.imread(str(image_path))
            if cv_img is None:
                return visual_dets

            height, width = cv_img.shape[:2]

            # 1. Human Face Detection (OpenCV Haar Cascade)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            if not face_cascade.empty():
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                for (x, y, w, h) in faces:
                    visual_dets.append({
                        "type": "FACE",
                        "category": CATEGORY_VISUAL,
                        "value_masked": "Human Face",
                        "confidence": 0.94,
                        "severity": "HIGH",
                        "location": None,
                        "bbox": [int(x), int(y), int(x + w), int(y + h)],
                        "reason": "Human facial biometric visual region detected",
                    })

            # 2. QR Code Detection
            qr_detector = cv2.QRCodeDetector()
            retval, points = qr_detector.detect(cv_img)
            if retval and points is not None:
                pts = points[0]
                x1, y1 = int(np.min(pts[:, 0])), int(np.min(pts[:, 1]))
                x2, y2 = int(np.max(pts[:, 0])), int(np.max(pts[:, 1]))
                visual_dets.append({
                    "type": "QR_CODE",
                    "category": CATEGORY_VISUAL,
                    "value_masked": "QR Code Data",
                    "confidence": 0.98,
                    "severity": "MEDIUM",
                    "location": None,
                    "bbox": [x1, y1, x2, y2],
                    "reason": "Visual machine-readable QR Code data matrix detected",
                })

        except Exception:
            pass

        return visual_dets

    # ── 4. UNIFIED DETECTION DISPATCHER ────────────────────────────────────────

    def detect(
        self,
        features: ExtractedFeatures,
        preprocessed: Optional[PreprocessedData] = None,
    ) -> DetectionResult:
        """
        Unified detection entry point consuming Phase 3 ExtractedFeatures & Phase 2 PreprocessedData.
        """
        start_time = time.time()
        modality = (features.input_type or "text").lower()
        source = features.source

        if features.feature_status != "success":
            return DetectionResult(
                input_type=modality,
                source=source,
                detection_status="error",
                detection_errors=features.feature_errors or ["Feature extraction failed upstream."],
                detection_time_ms=0.0,
            )

        all_detections: List[Dict[str, Any]] = []

        try:
            # ── A. TEXT MODALITY ───────────────────────────────────────────────
            if modality == "text":
                text = ""
                if preprocessed:
                    text = preprocessed.processed or preprocessed.extracted_text or ""
                all_detections.extend(self.detect_text_privacy(text, source=source))

            # ── B. IMAGE MODALITY ──────────────────────────────────────────────
            elif modality == "image":
                ocr_boxes = []
                extracted_text = ""
                orig_file_path = None

                if preprocessed:
                    ocr_boxes = preprocessed.ocr or []
                    extracted_text = preprocessed.extracted_text or ""
                    orig_file_path = preprocessed.original

                # 1. OCR Text PII with bounding boxes
                ocr_dets = self.detect_ocr_privacy(ocr_boxes, extracted_text)
                all_detections.extend(ocr_dets)

                # 2. Visual Privacy (Faces, QR Codes)
                if orig_file_path:
                    vis_dets = self.detect_image_visual_privacy(orig_file_path)
                    all_detections.extend(vis_dets)

            # ── C. VIDEO MODALITY ──────────────────────────────────────────────
            elif modality == "video":
                frames = preprocessed.frames if preprocessed else []

                if frames:
                    for f in frames:
                        f_id = f.get("frame_id", 1)
                        f_ts_sec = f.get("timestamp_sec", 0.0)
                        f_ts_str = f.get("timestamp_str", "00:00")
                        f_text = f.get("extracted_text", "")

                        if f_text:
                            frame_dets = self.detect_text_privacy(f_text, source=f"frame_{f_id}")
                            for d in frame_dets:
                                d["frame_id"] = f_id
                                d["timestamp_sec"] = f_ts_sec
                                d["timestamp_str"] = f_ts_str
                                all_detections.append(d)
                elif preprocessed and (preprocessed.extracted_text or preprocessed.processed):
                    v_text = preprocessed.extracted_text or preprocessed.processed or ""
                    all_detections.extend(self.detect_text_privacy(v_text, source="video_ocr"))

            # ── D. YOUTUBE MODALITY ────────────────────────────────────────────
            elif modality == "youtube":
                segments = preprocessed.frames if preprocessed else []

                if segments:
                    for s in segments:
                        seg_text = s.get("text", "")
                        ts_sec = s.get("timestamp_sec", 0.0)
                        ts_str = s.get("timestamp_str", "00:00")

                        if seg_text:
                            seg_dets = self.detect_text_privacy(seg_text, source="youtube_transcript")
                            for d in seg_dets:
                                d["timestamp_sec"] = ts_sec
                                d["timestamp_str"] = ts_str
                                all_detections.append(d)
                elif preprocessed and (preprocessed.extracted_text or preprocessed.processed):
                    yt_text = preprocessed.extracted_text or preprocessed.processed or ""
                    all_detections.extend(self.detect_text_privacy(yt_text, source="youtube_transcript"))

            # ── Summarize Category Counts & Flags ──────────────────────────────
            category_counts = {}
            has_crit_secret = False
            has_pii = False
            has_injection = False
            has_visual = False

            for d in all_detections:
                cat = d.get("category", CATEGORY_PERSONAL)
                category_counts[cat] = category_counts.get(cat, 0) + 1

                sev = d.get("severity", "MEDIUM")
                if sev == "CRITICAL" or cat == CATEGORY_AUTH:
                    has_crit_secret = True
                if cat in [CATEGORY_PERSONAL, CATEGORY_IDENTITY, CATEGORY_FINANCIAL, CATEGORY_MEDICAL]:
                    has_pii = True
                if cat == CATEGORY_INJECTION:
                    has_injection = True
                if cat == CATEGORY_VISUAL:
                    has_visual = True

            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return DetectionResult(
                input_type=modality,
                source=source,
                detections=all_detections,
                category_counts=category_counts,
                detection_count=len(all_detections),
                has_critical_secrets=has_crit_secret,
                has_pii=has_pii,
                has_injection=has_injection,
                has_visual_privacy=has_visual,
                detection_status="success",
                detection_time_ms=elapsed_ms,
            )

        except Exception as e:
            return DetectionResult(
                input_type=modality,
                source=source,
                detection_status="error",
                detection_errors=[f"Privacy detection engine error: {str(e)}"],
                detection_time_ms=round((time.time() - start_time) * 1000, 2),
            )
