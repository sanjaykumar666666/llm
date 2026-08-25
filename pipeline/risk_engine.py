"""
Privacy Risk Scoring Engine — Phase 6 Core Module.
File Location: pipeline/risk_engine.py

Responsibilities:
  1. Consumes Phase 4 DetectionResult & Phase 5 HybridClassificationResult.
  2. Synthesizes ML probabilities, entity severity weights, visual privacy detections,
     and prompt injection signals into an authoritative Privacy Risk Score (0–100) and Level.
  3. Risk Levels:
     - LOW: 0.0 - 30.0%
     - MEDIUM: 31.0 - 74.0%
     - HIGH: 75.0 - 100.0%
  4. Provides structured category-level risk breakdowns and concrete risk factors.
  5. Does NOT enforce block/redact decisions (reserved for Phase 7 Decision Gate).
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from pipeline.detector import DetectionResult
from pipeline.hybrid_classifier import HybridClassificationResult


# ── Severity Multipliers ──────────────────────────────────────────────────────
SEVERITY_WEIGHTS = {
    "CRITICAL": 1.00,
    "HIGH": 0.85,
    "MEDIUM": 0.50,
    "LOW": 0.20,
}


@dataclass
class RiskAssessmentResult:
    """
    Standardized Output from Phase 6 Privacy Risk Scoring Engine.
    Authoritative source of truth for Phase 7 (Decision Gate).
    """

    input_type: str = "text"
    source: str = "direct_input"
    risk_score: float = 0.0                     # 0.0 to 100.0
    risk_score_normalized: float = 0.0          # 0.0 to 1.0
    risk_level: str = "LOW"                     # "LOW" | "MEDIUM" | "HIGH"
    risk_factors: List[str] = field(default_factory=list)
    risk_breakdown: Dict[str, str] = field(default_factory=dict)
    category_scores: Dict[str, float] = field(default_factory=dict)

    # Personal Context Fields
    has_personal_context: bool = False
    personal_context_level: str = "SAFE"        # "SAFE" | "WARNING" | "HIGH_RISK"
    requires_user_confirmation: bool = False
    classification_source: str = "rule_based_precheck"

    # Component Scores
    ml_hybrid_score: float = 0.0
    entity_severity_score: float = 0.0
    visual_privacy_score: float = 0.0
    injection_risk_score: float = 0.0

    # Status
    assessment_status: str = "success"          # "success" | "error"
    assessment_errors: List[str] = field(default_factory=list)
    assessment_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable dictionary."""
        return {
            "input_type": self.input_type,
            "source": self.source,
            "risk_score": self.risk_score,
            "risk_score_normalized": self.risk_score_normalized,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "risk_breakdown": self.risk_breakdown,
            "category_scores": self.category_scores,
            "has_personal_context": self.has_personal_context,
            "personal_context_level": self.personal_context_level,
            "requires_user_confirmation": self.requires_user_confirmation,
            "classification_source": self.classification_source,
            "ml_hybrid_score": self.ml_hybrid_score,
            "entity_severity_score": self.entity_severity_score,
            "visual_privacy_score": self.visual_privacy_score,
            "injection_risk_score": self.injection_risk_score,
            "assessment_status": self.assessment_status,
            "assessment_errors": self.assessment_errors,
            "assessment_time_ms": self.assessment_time_ms,
        }


class PrivacyRiskScoringEngine:
    """
    Enterprise Privacy Risk Engine.
    Fuses deterministic entity detections, visual privacy markers, prompt injection signals,
    and ML ensemble probabilities into an authoritative numerical risk score.
    """

    def __init__(self):
        pass

    def calculate_risk(
        self,
        detections: DetectionResult,
        hybrid_result: Optional[HybridClassificationResult] = None,
    ) -> RiskAssessmentResult:
        """
        Synthesizes detection evidence and ML signals into an exact risk score [0, 100] and risk level.
        """
        start_time = time.time()
        modality = detections.input_type
        source = detections.source

        if detections.detection_status != "success":
            return RiskAssessmentResult(
                input_type=modality,
                source=source,
                assessment_status="error",
                assessment_errors=detections.detection_errors or ["Privacy detection failed upstream."],
                assessment_time_ms=0.0,
            )

        risk_factors: List[str] = []
        category_scores: Dict[str, float] = {}

        # ── 1. Calculate Entity Severity Component ─────────────────────────────
        max_entity_sev = 0.0
        entity_count = detections.detection_count

        for d in detections.detections:
            sev_str = d.get("severity", "MEDIUM")
            weight = SEVERITY_WEIGHTS.get(sev_str, 0.50)
            if weight > max_entity_sev:
                max_entity_sev = weight

            cat = d.get("category", "PERSONAL_INFORMATION")
            category_scores[cat] = max(category_scores.get(cat, 0.0), round(weight * 100, 1))

            # Record human-readable risk factor (ensure no private content is echoed)
            d_type = d.get("type", "SENSITIVE_DATA")
            if "PERSONAL_CONTEXT" in d_type or cat == "HIGHLY_PERSONAL_CONTEXT":
                risk_factors.append(d.get("reason", "Personal context disclosed in message."))
            else:
                d_type_clean = d_type.replace("_", " ").title()
                d_masked = d.get("value_masked", "")
                risk_factors.append(f"{d_type_clean} detected ({d_masked}) [Severity: {sev_str}]")

        entity_score_pct = round(max_entity_sev * 100.0, 1)

        # ── 2. Calculate ML Hybrid Score Component ─────────────────────────────
        ml_score_pct = 0.0
        if hybrid_result and hybrid_result.classification_status == "success":
            ml_score_pct = round(hybrid_result.hybrid_probability * 100.0, 1)

        # ── 3. Visual & Injection Signals ──────────────────────────────────────
        visual_score_pct = 85.0 if detections.has_visual_privacy else 0.0
        injection_score_pct = 95.0 if detections.has_injection else 0.0

        if detections.has_injection:
            risk_factors.append("Adversarial prompt injection sequence identified [Severity: CRITICAL]")

        # ── 4. Unified Synthesis & Personal Context Enforcements ──────────────
        requires_confirmation = False
        pers_level = getattr(detections, "personal_context_level", "SAFE")
        has_pers_ctx = getattr(detections, "has_personal_context", False)

        if entity_count == 0 and not detections.has_injection and not detections.has_visual_privacy and ml_score_pct < 65.0:
            final_risk = 0.0
        elif detections.has_critical_secrets or detections.has_injection:
            # Critical secrets or injection force high risk (>= 88%)
            base_score = max(entity_score_pct, injection_score_pct, ml_score_pct)
            final_risk = max(base_score, 88.0)
        elif has_pers_ctx and pers_level == "HIGH_RISK":
            # Highly personal context without credentials triggers confirmation
            final_risk = max(65.0, entity_score_pct)
            requires_confirmation = True
        elif has_pers_ctx and pers_level == "WARNING":
            final_risk = max(35.0, min(55.0, entity_score_pct))
        elif entity_count >= 2:
            # Multiple PII entities elevate risk to HIGH (>= 75%)
            final_risk = max(75.0, entity_score_pct + (entity_count * 3.0))
        elif entity_count == 1:
            # Single standard PII entity is MEDIUM risk [45% - 59%]
            final_risk = max(45.0, min(59.0, entity_score_pct))
        elif detections.has_visual_privacy:
            final_risk = max(55.0, visual_score_pct)
        else:
            final_risk = ml_score_pct

        final_risk = round(min(100.0, max(0.0, final_risk)), 1)
        norm_score = round(final_risk / 100.0, 4)

        # ── 5. Risk Level Mapping ──────────────────────────────────────────────
        if final_risk < 30.0:
            risk_level = "LOW"
        elif final_risk < 75.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # ── 6. Category Breakdown Rating ───────────────────────────────────────
        risk_breakdown = {}
        for cat, score in category_scores.items():
            readable_cat = cat.replace("_", " ").title()
            if score >= 75.0:
                risk_breakdown[readable_cat] = "HIGH"
            elif score >= 30.0:
                risk_breakdown[readable_cat] = "MEDIUM"
            else:
                risk_breakdown[readable_cat] = "LOW"

        if not risk_factors:
            risk_factors.append("No sensitive privacy entities or adversarial patterns detected.")

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return RiskAssessmentResult(
            input_type=modality,
            source=source,
            risk_score=final_risk,
            risk_score_normalized=norm_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            risk_breakdown=risk_breakdown,
            category_scores=category_scores,
            has_personal_context=has_pers_ctx,
            personal_context_level=pers_level,
            requires_user_confirmation=requires_confirmation,
            classification_source="evidence_based_risk_engine",
            ml_hybrid_score=ml_score_pct,
            entity_severity_score=entity_score_pct,
            visual_privacy_score=visual_score_pct,
            injection_risk_score=injection_score_pct,
            assessment_status="success",
            assessment_time_ms=elapsed_ms,
        )

