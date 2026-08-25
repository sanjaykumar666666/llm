"""
Authoritative Tool Security Gateway & Privacy-Aware Tool Router.
File Location: mcp_engine/tool_security_gateway.py

Pipeline 6 Core Module:
  1. Authoritative Tool Execution Interceptor (`secure_tool_call`).
  2. Approved MCP / Tool Allowlist & Schema Validation.
  3. Pre-execution Privacy & Security Firewall (Pipelines 1, 3, 4, 5).
  4. Search Query Sanitization & Data Minimization.
  5. URL / SSRF Protection against Malicious Internal / Metadata Targets.
  6. External Tool Output Isolation (`trusted_as_instruction = False`).
  7. Zero Raw Sensitive Data Logging.
"""

import time
import json
import re
import ipaddress
import urllib.parse
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple

from backend.services.evidence_risk import run_full_analysis
from privacy_engine.sanitizer import get_sanitizer

logger = logging.getLogger("ToolSecurityGateway")

# ── Approved Tool Allowlist & JSON Schema Definitions ──────────────────────────
APPROVED_TOOLS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "search_web": {
        "description": "Performs real-time live web search across verified public sources.",
        "parameters": {
            "query": {"type": str, "required": True, "max_length": 500},
            "max_results": {"type": int, "required": False, "default": 3, "min": 1, "max": 10},
        },
        "handler_module": "backend.services.tools_ecosystem",
        "handler_func": "search_web",
    },
    "deep_research": {
        "description": "Agentic multi-source research synthesis and cross-verification.",
        "parameters": {
            "topic": {"type": str, "required": True, "max_length": 500},
            "max_depth": {"type": int, "required": False, "default": 2, "min": 1, "max": 5},
        },
        "handler_module": "backend.services.tools_ecosystem",
        "handler_func": "deep_research",
    },
    "analyze_url": {
        "description": "Fetches and analyzes content from a validated public web URL.",
        "parameters": {
            "url": {"type": str, "required": True, "max_length": 1000},
        },
        "handler_module": "backend.services.tools_ecosystem",
        "handler_func": "analyze_url",
    },
    "system_info": {
        "description": "Returns sanitized environment metadata.",
        "parameters": {},
        "handler_module": "backend.services.tools_ecosystem",
        "handler_func": "get_system_info",
    },
}

# ── Disallowed / Private Network Ranges for SSRF Protection ───────────────────
DISALLOWED_HOSTS = {
    "localhost", "127.0.0.1", "::1", "0.0.0.0",
    "169.254.169.254", "metadata.google.internal", "instance-data",
}
DISALLOWED_SUFFIXES = (".internal", ".local", ".corp", ".onion", ".lan")


def validate_destination_url(url: str) -> Tuple[bool, str]:
    """
    Validates external URL against SSRF, internal network probing, and malicious schemes.
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL."

    parsed = urllib.parse.urlparse(url.strip())
    scheme = parsed.scheme.lower()

    # 1. Scheme Validation (Only HTTP and HTTPS allowed)
    if scheme not in ("http", "https"):
        return False, f"Prohibited URL scheme '{scheme}'. Only HTTP and HTTPS are permitted."

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return False, "URL missing valid hostname."

    # 2. Disallowed Hostnames & Cloud Metadata IPs
    if hostname in DISALLOWED_HOSTS or any(hostname.endswith(sfx) for sfx in DISALLOWED_SUFFIXES):
        return False, f"SSRF Security Violation: Access to internal / metadata host '{hostname}' is blocked."

    # 3. IP Address Range Validation (Reject Private / Loopback / Link-Local IP ranges)
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False, f"SSRF Security Violation: Access to private/reserved IP '{hostname}' is prohibited."
    except ValueError:
        # Not a raw IP literal (valid standard domain name)
        pass

    return True, "URL validated safe."


def sanitize_and_minimize_search_query(raw_query: str) -> str:
    """
    Sanitizes PII from search query and removes extraneous personal disclosure clauses.
    Example: "What is latest news about Apple? My email is john@test.com" -> "What is latest news about Apple? [EMAIL_REDACTED]"
    """
    if not raw_query:
        return ""

    sanitizer = get_sanitizer()
    san_res = sanitizer.sanitize_text(raw_query)
    sanitized = san_res["sanitized_text"]

    # Strip clean search prefixes if present (e.g. "search the web for ...")
    clean_prefix = re.compile(r"^\s*(?:search\s+(?:the\s+web|online|google)?\s+for|look\s+up|find\s+out\s+about|tell\s+me\s+about)\s*", re.IGNORECASE)
    minimized = clean_prefix.sub("", sanitized).strip()

    return minimized if minimized else sanitized


class ToolSecurityGateway:
    """
    Authoritative Tool Security Gateway.
    Guarantees that no external tool or search provider receives unverified or sensitive user data.
    """

    def __init__(self):
        self.allowed_tools = APPROVED_TOOLS_REGISTRY
        self.sanitizer = get_sanitizer()

    def validate_tool_arguments(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validates tool arguments against schema definitions."""
        if tool_name not in self.allowed_tools:
            return False, f"Security Alert: Unknown or unauthorized tool '{tool_name}' is not in the approved allowlist.", {}

        spec = self.allowed_tools[tool_name]
        param_defs = spec.get("parameters", {})
        validated_args = {}

        for p_name, p_rules in param_defs.items():
            req = p_rules.get("required", False)
            expected_type = p_rules.get("type", str)

            if p_name not in args:
                if req:
                    return False, f"Missing required parameter '{p_name}' for tool '{tool_name}'.", {}
                validated_args[p_name] = p_rules.get("default")
            else:
                val = args[p_name]
                if not isinstance(val, expected_type):
                    return False, f"Invalid type for parameter '{p_name}': expected {expected_type.__name__}, got {type(val).__name__}.", {}

                # String length check
                if expected_type == str and "max_length" in p_rules and len(val) > p_rules["max_length"]:
                    return False, f"Parameter '{p_name}' exceeds maximum allowed length of {p_rules['max_length']} characters.", {}

                # Numeric range check
                if expected_type == int:
                    if "min" in p_rules and val < p_rules["min"]:
                        val = p_rules["min"]
                    if "max" in p_rules and val > p_rules["max"]:
                        val = p_rules["max"]

                validated_args[p_name] = val

        return True, "Arguments validated.", validated_args

    def secure_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes external tool calls under Zero-Trust Privacy & Security Governance:
          1. Validates tool name against approved allowlist.
          2. Validates parameters against JSON schema.
          3. Evaluates arguments through Privacy Pipelines (Pipelines 1, 3, 4, 5).
          4. If BLOCK: Halts execution immediately, external_request_count = 0.
          5. If SANITIZE / WARN: Sanitizes parameters before tool invocation.
          6. If tool is URL-based: Performs strict SSRF validation.
          7. Executes tool handler and wraps response in untrusted data container.
        """
        t_start = time.time()
        user_context = user_context or {}
        confirmed_by_user = user_context.get("confirmed_by_user", False)

        # ── 1. Allowlist & Schema Validation ──────────────────────────────────
        is_valid, validation_msg, clean_args = self.validate_tool_arguments(tool_name, arguments)
        if not is_valid:
            logger.warning(f"🚫 Tool call '{tool_name}' rejected: {validation_msg}")
            return {
                "success": False,
                "status": "BLOCKED",
                "decision": "BLOCK",
                "tool_name": tool_name,
                "reason": validation_msg,
                "trusted_as_instruction": False,
                "security_status": "untrusted_data",
                "external_request_count": 0,
                "result": None,
                "timing_ms": round((time.time() - t_start) * 1000, 2),
            }

        # ── 2. Privacy & Security Pre-Check (Pipelines 1, 3, 4, 5) ─────────────
        arg_text_repr = " ".join([str(v) for v in clean_args.values() if isinstance(v, (str, int, float))])
        privacy_scan = run_full_analysis(arg_text_repr)

        # INVARIANT 1: Critical Credentials / Prompt Injections STRICTLY PROHIBIT Tool Calls
        if privacy_scan["decision"] == "BLOCK":
            logger.warning(f"🚫 Tool '{tool_name}' BLOCKED by Privacy Firewall: {privacy_scan['reason']}")
            return {
                "success": False,
                "status": "BLOCKED",
                "decision": "BLOCK",
                "tool_name": tool_name,
                "risk_score": privacy_scan["risk_score"],
                "risk_level": privacy_scan["risk_level"],
                "reason": f"Tool execution blocked for security: {privacy_scan['reason']}",
                "detected_entities": [e.get("category", "Sensitive Data") for e in privacy_scan.get("entities", [])],
                "trusted_as_instruction": False,
                "security_status": "untrusted_data",
                "external_request_count": 0,
                "result": None,
                "timing_ms": round((time.time() - t_start) * 1000, 2),
            }

        # Check for High Personal Context requiring user confirmation
        is_personal_high = (
            privacy_scan.get("requires_user_confirmation", False)
            or privacy_scan.get("personal_context_level") == "HIGH_RISK"
        )
        if is_personal_high and not confirmed_by_user:
            return {
                "success": False,
                "status": "CONFIRMATION_REQUIRED",
                "decision": "WARN",
                "tool_name": tool_name,
                "risk_score": privacy_scan["risk_score"],
                "risk_level": privacy_scan["risk_level"],
                "reason": "Detailed personal context requires user confirmation before external tool invocation.",
                "requires_user_confirmation": True,
                "trusted_as_instruction": False,
                "security_status": "untrusted_data",
                "external_request_count": 0,
                "result": None,
                "timing_ms": round((time.time() - t_start) * 1000, 2),
            }

        # ── 3. Query Sanitization & Data Minimization (Pipeline 5) ────────────
        sanitized_args = {}
        for k, v in clean_args.items():
            if isinstance(v, str):
                if k == "query":
                    sanitized_args[k] = sanitize_and_minimize_search_query(v)
                else:
                    san_res = self.sanitizer.sanitize_text(v)
                    sanitized_args[k] = san_res["sanitized_text"]
            else:
                sanitized_args[k] = v

        # ── 4. URL / SSRF Protection ──────────────────────────────────────────
        if "url" in sanitized_args:
            target_url = sanitized_args["url"]
            url_valid, url_reason = validate_destination_url(target_url)
            if not url_valid:
                logger.warning(f"🚫 URL tool call blocked: {url_reason}")
                return {
                    "success": False,
                    "status": "BLOCKED",
                    "decision": "BLOCK",
                    "tool_name": tool_name,
                    "reason": url_reason,
                    "trusted_as_instruction": False,
                    "security_status": "untrusted_data",
                    "external_request_count": 0,
                    "result": None,
                    "timing_ms": round((time.time() - t_start) * 1000, 2),
                }

        # ── 5. Safe Tool Execution ────────────────────────────────────────────
        external_request_count = 1
        raw_result = None
        execution_status = "SUCCESS"

        try:
            if tool_name == "search_web":
                from backend.services.tools_ecosystem import search_web
                raw_result = search_web(
                    query=sanitized_args["query"],
                    max_results=sanitized_args.get("max_results", 3)
                )
            elif tool_name == "deep_research":
                from backend.services.tools_ecosystem import deep_research
                raw_result = deep_research(
                    topic=sanitized_args["topic"],
                    max_depth=sanitized_args.get("max_depth", 2)
                )
            elif tool_name == "analyze_url":
                from backend.services.tools_ecosystem import analyze_url
                raw_result = analyze_url(url=sanitized_args["url"])
            elif tool_name == "system_info":
                raw_result = {"status": "active", "environment": "Aiera AI Trust Ecosystem", "version": "2.0"}
            else:
                raw_result = {"error": f"Handler not mapped for tool '{tool_name}'"}
                execution_status = "FAILED"
        except Exception as e:
            logger.error(f"Error executing external tool '{tool_name}': {e}")
            raw_result = {"error": f"Tool execution failed: {str(e)}"}
            execution_status = "ERROR"

        # ── 6. Tool Output Sanitization & Untrusted Data Isolation ────────────
        # Scan output for sensitive data leaks or prompt injection
        output_str = json.dumps(raw_result, default=str)
        output_analysis = run_full_analysis(output_str)

        sanitized_content = output_str
        if output_analysis.get("sanitized_text"):
            sanitized_content = output_analysis["sanitized_text"]

        elapsed_ms = round((time.time() - t_start) * 1000, 2)

        # INVARIANT 4: External Output is strictly marked UNTRUSTED DATA
        return {
            "success": execution_status == "SUCCESS",
            "status": execution_status,
            "decision": privacy_scan["decision"],
            "tool_name": tool_name,
            "sanitized_arguments": sanitized_args,
            "risk_score": privacy_scan["risk_score"],
            "risk_level": privacy_scan["risk_level"],
            "source": "external_tool",
            "trusted_as_instruction": False,
            "security_status": "untrusted_data",
            "external_request_count": external_request_count,
            "content": sanitized_content,
            "raw_result": raw_result,
            "direct_answer": raw_result.get("direct_answer", "") if isinstance(raw_result, dict) else "",
            "sources": raw_result.get("sources", []) if isinstance(raw_result, dict) else [],
            "citations": raw_result.get("citations", []) if isinstance(raw_result, dict) else [],
            "timing_ms": elapsed_ms,
        }


# Singleton Global Gateway
_GLOBAL_TOOL_GATEWAY = ToolSecurityGateway()


def get_tool_security_gateway() -> ToolSecurityGateway:
    return _GLOBAL_TOOL_GATEWAY


def secure_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Authoritative API entry point for all tool executions."""
    return _GLOBAL_TOOL_GATEWAY.secure_tool_call(
        tool_name=tool_name,
        arguments=arguments,
        user_context=user_context
    )
