"""
Privacy Guarded MCP Wrapper Component.
File: mcp_engine/privacy_mcp_wrapper.py
"""

from typing import Dict, Any, Optional
import json
import logging
from processing.text_processor import TextProcessor
from ml_engine.hybrid_classifier import HybridPrivacyClassifier
from gate.decision_gate import AutomatedDecisionGate

logger = logging.getLogger("PrivacyMCPWrapper")


class PrivacyMCPWrapper:
    """
    Wraps MCP Tool & Resource interactions with real-time Privacy Shield Firewall protection.
    Intercepts tool calls and resource payloads to prevent PII leakage and adversarial injections.
    """

    def __init__(self):
        self.text_processor = TextProcessor()
        self.hybrid_classifier = HybridPrivacyClassifier()
        self.decision_gate = AutomatedDecisionGate()

    def evaluate_tool_call_safety(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scans tool arguments for PII, credentials, or prompt injection risks before executing the tool.
        """
        # Serialize arguments to JSON string for textual inspection
        arg_str = json.dumps(arguments)

        # 1. Process text features
        processed = self.text_processor.process(arg_str)
        detected_entities = processed.get("detected_entities", [])

        # 2. Check for Prompt Injection pattern
        lower_str = arg_str.lower()
        injection_keywords = ["ignore previous", "reveal prompt", "bypass security", "system prompt", "jailbreak"]
        has_injection = any(k in lower_str for k in injection_keywords)

        if has_injection:
            return {
                "safe": False,
                "action": "BLOCK",
                "risk_score": 95.0,
                "reason": f"Security Alert: MCP Tool '{tool_name}' arguments contain adversarial prompt injection attempt.",
                "detected_entities": ["Prompt Injection"]
            }

        # 3. Check for raw PII / credentials in parameters
        if processed.get("contains_regex_pii") or detected_entities:
            entity_names = [e.get("entity_type", str(e)) if isinstance(e, dict) else str(e) for e in detected_entities]
            return {
                "safe": False,
                "action": "BLOCK",
                "risk_score": 85.0,
                "reason": f"Privacy Warning: MCP Tool '{tool_name}' arguments contain sensitive PII ({', '.join(entity_names)}). Execution blocked.",
                "detected_entities": entity_names
            }

        return {
            "safe": True,
            "action": "ALLOW",
            "risk_score": 5.0,
            "reason": "MCP tool arguments verified clean by Privacy Firewall.",
            "detected_entities": []
        }

    def sanitize_tool_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspects output produced by MCP tool execution and sanitizes sensitive data fields.
        """
        if isinstance(result, dict):
            sanitized_dict = {}
            contains_pii = False
            for k, v in result.items():
                if isinstance(v, str):
                    processed = self.text_processor.process(v)
                    if processed.get("contains_regex_pii"):
                        s_text, _ = self.decision_gate.sanitizer.sanitize(v)
                        sanitized_dict[k] = s_text
                        contains_pii = True
                    else:
                        sanitized_dict[k] = v
                else:
                    sanitized_dict[k] = v
            if contains_pii:
                sanitized_dict["_privacy_notice"] = "Tool output contained PII and was automatically sanitized."
            return sanitized_dict

        result_str = str(result)
        processed = self.text_processor.process(result_str)
        if processed.get("contains_regex_pii"):
            sanitized_text, _ = self.decision_gate.sanitizer.sanitize(result_str)
            return {"sanitized_output": sanitized_text, "_privacy_notice": "Tool output contained PII."}
        return result
