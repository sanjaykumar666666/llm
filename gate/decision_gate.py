"""
Backward-compatible wrapper for gate.decision_gate.
Delegates cleanly to privacy_engine.evaluator and privacy_engine.sanitizer.
"""

import time
from typing import Dict, Any
from privacy_engine.evaluator import PrivacyEvaluator
from privacy_engine.sanitizer import PrivacySanitizer


class AutomatedDecisionGate:
    """
    Automated Decision Gate.
    Enforces ALLOW, SANITIZE (PII Redaction), or BLOCK decisions.
    """

    def __init__(self):
        self.evaluator = PrivacyEvaluator()
        self.sanitizer = PrivacySanitizer()

    def evaluate_decision(
        self,
        text: str,
        risk_score: float,
        modality: str = "text"
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        # Collect entity matches
        sanitized_text, redacted_entities = self.sanitizer.sanitize(text)
        detected_entity_types = list(set([e["entity_type"] for e in redacted_entities]))

        eval_res = self.evaluator.evaluate_decision(
            risk_score=risk_score,
            detected_entities=detected_entity_types,
            contains_regex_pii=len(redacted_entities) > 0,
        )

        decision = eval_res["action"]

        if decision == "ALLOW":
            action_summary = "Payload classified as SAFE. Forwarding prompt untouched to Gemini LLM."
            forward_prompt = text

        elif decision == "SANITIZE":
            action_summary = f"PII detected. Redacted {len(redacted_entities)} sensitive token(s). Forwarding sanitized prompt to Gemini LLM."
            forward_prompt = sanitized_text

        else:  # BLOCK
            forward_prompt = None
            action_summary = "High privacy risk / confidential leak detected. Execution HALTED. Request BLOCKED from LLM API."

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "decision": decision,
            "risk_score": risk_score,
            "action_summary": action_summary,
            "forward_prompt": forward_prompt,
            "redacted_entities": redacted_entities,
            "original_prompt_preview": text[:150] + ("..." if len(text) > 150 else "") if text else "",
            "gate_latency_ms": round(elapsed_ms, 2)
        }
