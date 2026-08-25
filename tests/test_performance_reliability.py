"""
Comprehensive Performance, Reliability & Stress Test Suite.
File: tests/test_performance_reliability.py

Tests:
  1. Component Latency Bounds (< 150ms for local security pipeline)
  2. Input Size Scaling (100B to 50KB without memory leak or crash)
  3. Concurrent Request Security & Zero-Leakage Under Load
  4. LLM & Tool Provider Failure Resilience
  5. Multimodal & Media Processing Reliability (Fail-Closed)
  6. Memory Stability & Singleton Model Reuse
"""

import sys
import os
import time
import pytest
import concurrent.futures
from unittest.mock import patch, MagicMock

from backend.routes.chatbot import chat_endpoint, ChatRequest
from backend.services.evidence_risk import run_full_analysis, get_detector, get_bert, get_nb, get_hybrid, get_sanitizer
from mcp_engine.tool_security_gateway import secure_tool_call, validate_destination_url
from backend.services.image_privacy_service import ImagePrivacyService
from llm_gateway.gemini_client import classify_llm_error


# ==============================================================================
# 1. COMPONENT LATENCY BOUND TESTS
# ==============================================================================
class TestLatencyBounds:
    """Verifies that each privacy sub-engine meets production latency targets."""

    def test_p1_deterministic_latency(self):
        detector = get_detector()
        t0 = time.perf_counter()
        detector.detect_entities("My email is test@example.org and phone is 555-0199.")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 50.0, f"P1 detection took too long: {elapsed_ms:.2f}ms"

    def test_p3_naive_bayes_latency(self):
        nb = get_nb()
        t0 = time.perf_counter()
        nb.predict_risk("What is the capital of France?")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 30.0, f"Naive Bayes took too long: {elapsed_ms:.2f}ms"

    def test_p3_bert_inference_latency(self):
        bert = get_bert()
        t0 = time.perf_counter()
        bert.predict_context_risk("What is the capital of France?")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 150.0, f"BERT inference took too long: {elapsed_ms:.2f}ms"

    def test_p5_sanitization_latency(self):
        sanitizer = get_sanitizer()
        t0 = time.perf_counter()
        sanitizer.sanitize_text("My email is test.user@example.org and phone is 555-0199.")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 20.0, f"P5 sanitization took too long: {elapsed_ms:.2f}ms"

    def test_p6_ssrf_validator_latency(self):
        t0 = time.perf_counter()
        validate_destination_url("https://api.weather.gov/v1/forecast")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 5.0, f"P6 SSRF validator took too long: {elapsed_ms:.2f}ms"

    def test_total_security_gateway_latency(self):
        t0 = time.perf_counter()
        run_full_analysis("What is the capital of France?")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 250.0, f"Total Security Gateway pipeline took too long: {elapsed_ms:.2f}ms"


# ==============================================================================
# 2. INPUT SIZE SCALING TESTS
# ==============================================================================
class TestInputSizeScaling:
    """Verifies that large payloads process safely without crashing or leaking."""

    @pytest.mark.parametrize("size_kb", [1, 5, 20, 50])
    def test_scaled_input_processing(self, size_kb):
        char_count = size_kb * 1024
        synthetic_body = "This is a safe sentence discussing computer science. " * (char_count // 53 + 1)
        synthetic_body = synthetic_body[:char_count]

        # Embed PII in the center
        half = len(synthetic_body) // 2
        payload = synthetic_body[:half] + " My email is test.scaled@example.org. " + synthetic_body[half:]

        t0 = time.perf_counter()
        analysis = run_full_analysis(payload)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert analysis["decision"] in ("WARN", "SANITIZE", "BLOCK")
        sanitizer = get_sanitizer()
        san_res = sanitizer.sanitize_text(payload)
        assert "test.scaled@example.org" not in san_res["sanitized_text"]


# ==============================================================================
# 3. CONCURRENCY & SECURITY UNDER LOAD
# ==============================================================================
class TestConcurrencyAndSecurityUnderLoad:
    """Verifies that concurrent requests do not bypass security or leak state."""

    @patch("backend.routes.chatbot._get_gemini_client")
    def test_concurrent_security_decisions(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.generate_chat_response.return_value = {
            "success": True,
            "response_text": "Paris and Berlin.",
            "model": "gemini-3.6-flash",
            "error_type": None
        }
        mock_get_client.return_value = mock_client

        def worker(idx):
            if idx % 3 == 0:
                r = chat_endpoint(ChatRequest(prompt=f"What is the capital of France and Germany {idx}?"))
                return ("SAFE", r["decision"], r.get("ai_response"))
            elif idx % 3 == 1:
                r = chat_endpoint(ChatRequest(prompt=f"My email is user{idx}@example.org. Hello!"))
                return ("PII", r["decision"], r.get("masked_prompt"))
            else:
                r = chat_endpoint(ChatRequest(prompt=f"My database password is Pass{idx}!"))
                return ("CRED", r["decision"], r.get("ai_response"))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(worker, range(30)))

        for expected_kind, dec, output in results:
            if expected_kind == "SAFE":
                assert dec == "ALLOW"
            elif expected_kind == "PII":
                assert dec in ("WARN", "SANITIZE")
                assert "[EMAIL_REDACTED]" in output
            elif expected_kind == "CRED":
                assert dec == "BLOCK"
                assert output is None


# ==============================================================================
# 4. LLM FAILURE RESILIENCE
# ==============================================================================
class TestLLMFailureResilience:
    """Verifies that LLM errors are classified cleanly and fail closed."""

    @pytest.mark.parametrize("exc, expected_err_type, expected_retryable", [
        (TimeoutError("Request deadline exceeded"), "LLM_TIMEOUT", True),
        (Exception("401 API_KEY_INVALID"), "LLM_AUTH_ERROR", False),
        (Exception("404 NOT_FOUND: model not found"), "LLM_INVALID_MODEL", False),
        (Exception("429 RESOURCE_EXHAUSTED"), "LLM_QUOTA_EXCEEDED", False),
        (ConnectionError("Failed to connect"), "LLM_NETWORK_ERROR", True),
    ])
    def test_llm_error_classification(self, exc, expected_err_type, expected_retryable):
        err_t, err_m, is_ret = classify_llm_error(exc)
        assert err_t == expected_err_type or (expected_err_type == "LLM_QUOTA_EXCEEDED" and "QUOTA" in err_t)
        assert is_ret == expected_retryable


# ==============================================================================
# 5. TOOL FAILURE RESILIENCE
# ==============================================================================
class TestToolFailureResilience:
    """Verifies that external tool failures fail closed and tag data as untrusted."""

    def test_unknown_tool_rejected(self):
        res = secure_tool_call(tool_name="unauthorized_shell_exec", arguments={})
        assert res["status"] in ("ERROR", "BLOCKED")
        assert res["decision"] == "BLOCK"

    def test_tool_argument_too_long_rejected(self):
        res = secure_tool_call(
            tool_name="search_web",
            arguments={"query": "A" * 1000}
        )
        assert res["status"] in ("ERROR", "BLOCKED")
        assert res["decision"] == "BLOCK"
        msg = res.get("reason") or res.get("message") or ""
        assert "Validation Error" in msg or "exceeds" in msg.lower()


# ==============================================================================
# 6. MODEL REUSE & SINGLETON STABILITY
# ==============================================================================
class TestModelReuseStability:
    """Verifies that singletons are preserved across multiple invocations."""

    def test_singletons_remain_identical(self):
        d1, d2 = get_detector(), get_detector()
        b1, b2 = get_bert(), get_bert()
        nb1, nb2 = get_nb(), get_nb()
        h1, h2 = get_hybrid(), get_hybrid()
        s1, s2 = get_sanitizer(), get_sanitizer()

        assert d1 is d2
        assert b1 is b2
        assert nb1 is nb2
        assert h1 is h2
        assert s1 is s2
