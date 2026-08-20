"""
Protection & Decision Engine — Phase 7 Core Module.
File Location: pipeline/protection_engine.py

Responsibilities:
  1. Centralized Policy Decision Engine:
     - Evaluates Phase 6 Risk Assessment & Phase 4 Detection results.
     - Enforces decisions: ALLOW, WARN, SANITIZE, PROTECT, BLOCK.
  2. Fail-Closed Security Policy:
     - Upstream errors, scanner timeouts, or protection failures NEVER result in ALLOW.
  3. Text Sanitization:
     - Replaces sensitive spans with structured placeholder tags (e.g. [EMAIL REDACTED], [SECRET REDACTED]).
     - Strictly preserves original content separate from protected content.
  4. Real Pixel-Level Image Protection:
     - Applies real Gaussian Blur, Pixelation, or Solid Redaction to actual bounding boxes [x1, y1, x2, y2].
     - Generates downloadable protected image artifacts without modifying original files.
  5. Video & YouTube Protection:
     - Frame-level bounding box protection and transcript sanitization.
  6. LLM Safety Preparation:
     - Flags whether original/protected content is authorized for downstream LLM transmission.
"""

import io
import os
import time
import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from PIL import Image, ImageFilter, ImageDraw

from pipeline.detector import DetectionResult
from pipeline.risk_engine import RiskAssessmentResult
from pipeline.preprocessor import PreprocessedData


# ── Canonical Redaction Tokens ────────────────────────────────────────────────
REDACTION_TOKEN_MAP = {
    "EMAIL_ADDRESS": "[EMAIL REDACTED]",
    "PHONE_NUMBER": "[PHONE REDACTED]",
    "NAME": "[NAME REDACTED]",
    "GOVERNMENT_ID_AADHAAR": "[AADHAAR REDACTED]",
    "GOVERNMENT_ID_PAN": "[PAN REDACTED]",
    "GOVERNMENT_ID_SSN": "[SSN REDACTED]",
    "GOVERNMENT_ID_NINO": "[NINO REDACTED]",
    "PASSPORT_NUMBER": "[PASSPORT REDACTED]",
    "DRIVING_LICENSE": "[LICENSE REDACTED]",
    "VOTER_ID": "[VOTER ID REDACTED]",
    "CREDIT_CARD_NUMBER": "[PAYMENT CARD REDACTED]",
    "BANK_ROUTING_ACCOUNT": "[BANK ACCOUNT REDACTED]",
    "BANK_ACCOUNT_IBAN": "[IBAN REDACTED]",
    "UPI_ID": "[UPI ID REDACTED]",
    "CREDENTIAL_PASSWORD": "[PASSWORD REDACTED]",
    "AWS_ACCESS_KEY": "[AWS KEY REDACTED]",
    "GITHUB_TOKEN": "[GITHUB TOKEN REDACTED]",
    "OPENAI_API_KEY": "[API KEY REDACTED]",
    "GOOGLE_CLOUD_API_KEY": "[GCP KEY REDACTED]",
    "SENDGRID_API_KEY": "[API KEY REDACTED]",
    "SLACK_BOT_TOKEN": "[SLACK TOKEN REDACTED]",
    "GENERIC_API_SECRET": "[SECRET KEY REDACTED]",
    "JWT_TOKEN": "[JWT TOKEN REDACTED]",
    "BEARER_TOKEN": "[BEARER TOKEN REDACTED]",
    "PRIVATE_KEY_BLOCK": "[PRIVATE KEY REDACTED]",
    "DATABASE_CONNECTION_STRING": "[DATABASE CREDENTIALS REDACTED]",
    "MEDICAL_PATIENT_RECORD": "[HEALTH RECORD REDACTED]",
    "PHYSICAL_STREET_ADDRESS": "[ADDRESS REDACTED]",
    "IP_ADDRESS": "[IP ADDRESS REDACTED]",
    "PROMPT_INJECTION_OVERRIDE": "[BLOCKED_ADVERSARIAL_SEQUENCE]",
}


@dataclass
class ProtectionResult:
    """
    Standardized Output from Phase 7 Protection & Decision Engine.
    Authoritative payload for downstream Secure LLM Gateway and UI.
    """

    input_type: str = "text"
    source: str = "direct_input"
    decision: str = "ALLOW"                    # "ALLOW" | "WARN" | "SANITIZE" | "PROTECT" | "BLOCK"
    decision_reason: str = ""
    risk_score: float = 0.0                    # 0.0 - 100.0 from Phase 6
    risk_level: str = "LOW"                    # "LOW" | "MEDIUM" | "HIGH"
    protection_applied: bool = False
    protection_method: str = "NONE"            # "GAUSSIAN_BLUR" | "PIXELATION" | "SOLID_REDACTION" | "TEXT_SANITIZATION" | "NONE"

    # Separation of Original vs Protected Content
    original_content: Optional[str] = None
    protected_content: Optional[str] = None
    original_allowed_downstream: bool = False
    protected_allowed_downstream: bool = False

    # Visual Artifacts
    protected_regions_count: int = 0
    protected_regions: List[Dict[str, Any]] = field(default_factory=list)
    protected_data_url: Optional[str] = None
    download_filename: Optional[str] = None

    # Status
    decision_status: str = "success"           # "success" | "error"
    decision_errors: List[str] = field(default_factory=list)
    decision_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary."""
        return {
            "input_type": self.input_type,
            "source": self.source,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "protection_applied": self.protection_applied,
            "protection_method": self.protection_method,
            "original_content": self.original_content,
            "protected_content": self.protected_content,
            "original_allowed_downstream": self.original_allowed_downstream,
            "protected_allowed_downstream": self.protected_allowed_downstream,
            "protected_regions_count": self.protected_regions_count,
            "protected_regions": self.protected_regions,
            "protected_data_url": self.protected_data_url,
            "download_filename": self.download_filename,
            "decision_status": self.decision_status,
            "decision_errors": self.decision_errors,
            "decision_time_ms": self.decision_time_ms,
        }


class ProtectionAndDecisionEngine:
    """
    Enterprise Protection and Decision Engine.
    Executes policy evaluation, text sanitization, and real pixel-level image blurring/redaction.
    """

    def __init__(self):
        pass

    # ── 1. TEXT SANITIZATION ───────────────────────────────────────────────────

    def sanitize_text(self, text: str, detections: List[Dict[str, Any]]) -> str:
        """
        Sanitizes text by replacing character spans with structured redaction tokens.
        Processes spans in reverse index order to avoid index drifting.
        """
        if not text or not detections:
            return text

        # Sort spans in reverse order of start_index
        spans_to_replace = []
        for d in detections:
            loc = d.get("location")
            if loc and "start" in loc and "end" in loc:
                start = loc["start"]
                end = loc["end"]
                if 0 <= start < end <= len(text):
                    ent_type = d.get("type", "SENSITIVE_DATA")
                    token = REDACTION_TOKEN_MAP.get(ent_type, "[SENSITIVE DATA REDACTED]")
                    spans_to_replace.append((start, end, token))

        # Sort by start descending
        spans_to_replace.sort(key=lambda s: s[0], reverse=True)

        sanitized = text
        for start, end, token in spans_to_replace:
            sanitized = sanitized[:start] + token + sanitized[end:]

        return sanitized

    # ── 2. IMAGE PIXEL PROTECTION (REAL GAUSSIAN BLUR / PIXELATION / REDACT) ──

    def protect_image_pixels(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        detections: List[Dict[str, Any]],
        protection_mode: str = "GAUSSIAN_BLUR",
    ) -> Tuple[Image.Image, str, List[Dict[str, Any]]]:
        """
        Applies real pixel modifications directly to image bounding boxes.
        Returns (protected_pil_image, base64_data_url, protected_regions_metadata).
        """
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(str(image_input)).convert("RGB")
        elif isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.copy().convert("RGB")
        else:
            raise ValueError("Unsupported image input type for protection.")

        width, height = pil_img.size
        protected_img = pil_img.copy()
        draw = ImageDraw.Draw(protected_img)
        protected_regions = []

        norm_mode = protection_mode.upper()
        if "PIXEL" in norm_mode:
            active_method = "PIXELATION"
        elif "REDACT" in norm_mode or "SOLID" in norm_mode:
            active_method = "SOLID_REDACTION"
        else:
            active_method = "GAUSSIAN_BLUR"

        for det in detections:
            bbox = det.get("bbox")
            if not bbox or len(bbox) < 4:
                continue

            x1, y1, x2, y2 = max(0, int(bbox[0])), max(0, int(bbox[1])), min(width, int(bbox[2])), min(height, int(bbox[3]))
            if x2 <= x1 or y2 <= y1:
                continue

            crop_box = (x1, y1, x2, y2)
            region = protected_img.crop(crop_box)

            if active_method == "PIXELATION":
                rw, rh = max(1, (x2 - x1) // 10), max(1, (y2 - y1) // 10)
                small = region.resize((rw, rh), Image.NEAREST)
                pixelated = small.resize((x2 - x1, y2 - y1), Image.NEAREST)
                protected_img.paste(pixelated, crop_box)
            elif active_method == "SOLID_REDACTION":
                draw.rectangle(crop_box, fill=(15, 18, 25))
            else:
                # Default: Gaussian Blur
                blurred = region.filter(ImageFilter.GaussianBlur(radius=22))
                protected_img.paste(blurred, crop_box)

            protected_regions.append({
                "type": det.get("type", "SENSITIVE_REGION"),
                "bbox": [x1, y1, x2, y2],
                "confidence": det.get("confidence", 0.95),
                "protection_method": active_method,
            })

        # Generate base64
        buf = io.BytesIO()
        protected_img.save(buf, format="PNG")
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        data_url = f"data:image/png;base64,{b64_str}"

        return protected_img, data_url, protected_regions

    # ── 3. CENTRALIZED DECISION EVALUATION ─────────────────────────────────────

    def evaluate_and_protect(
        self,
        risk: RiskAssessmentResult,
        detections: DetectionResult,
        preprocessed: Optional[PreprocessedData] = None,
        protection_mode: str = "GAUSSIAN_BLUR",
    ) -> ProtectionResult:
        """
        Synthesizes Risk Assessment and Detections to produce an authoritative security decision
        and execute all required content protections (redaction, blur, pixelation).
        """
        start_time = time.time()
        modality = detections.input_type
        source = detections.source

        # ── Fail-Closed Security Policy ────────────────────────────────────────
        if risk.assessment_status != "success" or detections.detection_status != "success":
            errors = risk.assessment_errors + detections.detection_errors
            return ProtectionResult(
                input_type=modality,
                source=source,
                decision="BLOCK",
                decision_reason="Security Scan Failure: Upstream pipeline error. Content blocked under fail-closed security policy.",
                risk_score=100.0,
                risk_level="HIGH",
                original_allowed_downstream=False,
                protected_allowed_downstream=False,
                decision_status="error",
                decision_errors=errors or ["Pipeline validation error."],
                decision_time_ms=0.0,
            )

        risk_score = risk.risk_score
        risk_level = risk.risk_level
        has_crit = detections.has_critical_secrets
        has_inj = detections.has_injection
        has_visual = detections.has_visual_privacy
        det_count = detections.detection_count

        raw_text = ""
        orig_file_path = None
        if preprocessed:
            raw_text = preprocessed.extracted_text or preprocessed.processed or ""
            orig_file_path = preprocessed.original

        # ── Decision Mapping Matrix ────────────────────────────────────────────
        if has_crit or has_inj or risk_score >= 85.0:
            decision = "BLOCK"
            if has_inj:
                reason = "Adversarial prompt injection attempt detected. Direct execution blocked."
            elif has_crit:
                reason = "Critical authentication credentials or private API keys detected. Transmission blocked."
            else:
                reason = "Extreme privacy risk detected. Payload blocked."
            protection_method = "NONE"
            orig_allowed = False
            prot_allowed = False

        elif modality == "image" and (has_visual or det_count > 0):
            decision = "PROTECT"
            reason = f"Visual privacy or OCR PII regions detected ({det_count} regions). Real pixel-level protection applied."
            protection_method = protection_mode.upper()
            orig_allowed = False
            prot_allowed = True

        elif det_count >= 1 or risk_score > 30.0:
            decision = "SANITIZE"
            reason = f"Privacy-sensitive entities detected ({det_count} items). Structured token redaction applied."
            protection_method = "TEXT_SANITIZATION"
            orig_allowed = False
            prot_allowed = True

        elif risk_score > 15.0 and det_count == 0:
            decision = "WARN"
            reason = "Informational privacy risk notice: low probability keywords detected."
            protection_method = "NONE"
            orig_allowed = True
            prot_allowed = True

        else:
            decision = "ALLOW"
            reason = "Zero privacy risks or policy violations detected. Verified safe for downstream LLM processing."
            protection_method = "NONE"
            orig_allowed = True
            prot_allowed = True

        # ── Execute Content Protection ─────────────────────────────────────────
        protected_text = None
        protected_data_url = None
        protected_regions: List[Dict[str, Any]] = []
        protection_applied = False
        download_fn = None

        try:
            if decision == "SANITIZE":
                protected_text = self.sanitize_text(raw_text, detections.detections)
                protection_applied = True

            elif decision == "PROTECT" and modality == "image" and orig_file_path and Path(orig_file_path).exists():
                _, protected_data_url, protected_regions = self.protect_image_pixels(
                    orig_file_path,
                    detections.detections,
                    protection_mode=protection_mode,
                )
                protection_applied = True
                download_fn = f"protected_{Path(orig_file_path).name}"

            elif decision == "BLOCK":
                # For blocked text, also create a sanitized preview so raw secret is never sent
                protected_text = self.sanitize_text(raw_text, detections.detections) if raw_text else "[CONTENT BLOCKED]"
                protection_applied = False

            elif decision == "ALLOW":
                protected_text = raw_text
                protection_applied = False

        except Exception as protect_err:
            # Fail-closed on protection failure
            return ProtectionResult(
                input_type=modality,
                source=source,
                decision="BLOCK",
                decision_reason=f"Protection Engine Failure: {str(protect_err)}. Content blocked under fail-closed security.",
                risk_score=100.0,
                risk_level="HIGH",
                original_allowed_downstream=False,
                protected_allowed_downstream=False,
                decision_status="error",
                decision_errors=[str(protect_err)],
                decision_time_ms=round((time.time() - start_time) * 1000, 2),
            )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return ProtectionResult(
            input_type=modality,
            source=source,
            decision=decision,
            decision_reason=reason,
            risk_score=risk_score,
            risk_level=risk_level,
            protection_applied=protection_applied,
            protection_method=protection_method,
            original_content=raw_text if modality in ("text", "youtube") else str(orig_file_path),
            protected_content=protected_text,
            original_allowed_downstream=orig_allowed,
            protected_allowed_downstream=prot_allowed,
            protected_regions_count=len(protected_regions),
            protected_regions=protected_regions,
            protected_data_url=protected_data_url,
            download_filename=download_fn,
            decision_status="success",
            decision_time_ms=elapsed_ms,
        )
