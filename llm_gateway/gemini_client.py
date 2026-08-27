"""
AIERA GenAI Engine & LLM Gateway Client.
File Location: llm_gateway/gemini_client.py

Provides an authoritative, reliable, and transparent LLM gateway to Google Gemini.
Supports model cascades, bounded transient retries, timeout management,
and structured error reporting without fabricated/hardcoded fallback answers.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List, Tuple

import config

logger = logging.getLogger("GeminiClient")

try:
    from google import genai
    from google.genai import types as gtypes
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    gtypes = None
    GENAI_AVAILABLE = False
    logger.warning("google-genai SDK not installed.")

# ── Configuration Constants ───────────────────────────────────────────────────
DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL") or getattr(config, "DEFAULT_LLM_MODEL", "gemini-3.5-flash-lite")
TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "15.0"))
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "1"))

# Supported standard models in preferred cascade order (Active models on Google GenAI API)
STANDARD_CANDIDATE_MODELS = [
    DEFAULT_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.1-pro-preview",
]


def classify_llm_error(exc: Exception) -> Tuple[str, str, bool]:
    """
    Classifies an exception into standard (error_type, message, is_retryable).
    Standard error types:
      - LLM_AUTH_ERROR
      - LLM_INVALID_MODEL
      - LLM_QUOTA_EXCEEDED
      - LLM_RATE_LIMITED
      - LLM_TIMEOUT
      - LLM_NETWORK_ERROR
      - LLM_INVALID_RESPONSE
      - LLM_CONFIGURATION_ERROR
      - LLM_UNKNOWN_ERROR
    """
    err_str = str(exc).lower()

    # Extract clean message if available from Google SDK exception objects
    detail_msg = getattr(exc, "message", None) or str(exc)
    # Sanitize any potential key occurrences in error string
    import re
    detail_msg = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[API_KEY_REDACTED]', str(detail_msg))

    # Check Quota / Rate limits FIRST to prevent misclassifying 429 as auth error
    if any(k in err_str for k in ["resource_exhausted", "quota exceeded", "exceeded your current quota", "free_tier_requests"]):
        return ("LLM_QUOTA_EXCEEDED", "Gemini API quota has been exceeded for the configured model.", False)

    if "429" in err_str or "too many requests" in err_str or "rate limit" in err_str or "503" in err_str or "high demand" in err_str or "service unavailable" in err_str:
        return ("LLM_RATE_LIMITED", "Gemini API rate limit or capacity reached. Cascading to available model.", True)

    if any(k in err_str for k in ["api_key_invalid", "api key not valid", "unauthenticated", "401", "403", "permission_denied"]):
        return ("LLM_AUTH_ERROR", "Invalid or unauthorized Gemini API key. Please check your API key in Settings.", False)

    if any(k in err_str for k in ["404", "not_found", "no longer available", "is not supported"]):
        return ("LLM_INVALID_MODEL", f"Configured Gemini model is not available or has been updated: {detail_msg}", False)

    if isinstance(exc, (TimeoutError,)) or any(k in err_str for k in ["timed out", "timeout", "timeouterror", "deadline_exceeded"]):
        return ("LLM_TIMEOUT", "Gemini API request timed out.", True)

    if isinstance(exc, (ConnectionError, OSError)) or any(k in err_str for k in ["connection error", "connection reset", "connection refused", "connecterror", "connectionreset", "network", "getaddrinfo failed", "wsasend", "reset by peer"]):
        return ("LLM_NETWORK_ERROR", "Network connection to Gemini API failed.", True)

    if any(k in err_str for k in ["empty response", "blocked by safety", "finish_reason"]):
        return ("LLM_INVALID_RESPONSE", "Gemini returned an empty or safety-blocked response.", False)

    return ("LLM_UNKNOWN_ERROR", f"LLM generation failed: {type(exc).__name__} ({detail_msg})", False)



class GeminiClient:
    """
    Authoritative Gemini LLM Gateway Client.
    Exposes a unified contract for single-turn, multi-turn, and streaming LLM requests.
    """
    _last_working_model: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or getattr(config, "GEMINI_API_KEY", "")
        self.model_name = default_model or DEFAULT_MODEL
        self.timeout_seconds = TIMEOUT_SECONDS
        self.max_retries = MAX_RETRIES
        self.client = None

        placeholder_keys = {
            "your_gemini_api_key_here", "dummy_key",
            "your_google_gemini_api_key_here", "", "none", "null"
        }

        if not GENAI_AVAILABLE:
            logger.warning("⚠️  [GeminiClient] google-genai SDK unavailable.")
        elif not self.api_key or self.api_key.strip().lower() in placeholder_keys:
            logger.warning("⚠️  [GeminiClient] GEMINI_API_KEY is missing or placeholder.")
        else:
            try:
                self.client = genai.Client(api_key=self.api_key.strip())
                logger.info(f"✅ [GeminiClient] Initialized successfully. Primary model: {self.model_name}")
            except Exception as e:
                logger.error(f"❌ [GeminiClient] Initialization error: {e}")
                self.client = None

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Unified Authoritative LLM Gateway Contract.
        
        Returns:
          {
            "success": bool,
            "provider": "gemini",
            "model": str,
            "response": Optional[str],
            "response_text": Optional[str],
            "latency_ms": float,
            "usage": Optional[Dict[str, Any]],
            "error_type": Optional[str],
            "error_message": Optional[str],
            "error": Optional[Dict[str, Any]],
            "retry_count": int,
          }
        """
        t_start = time.perf_counter()

        if not prompt or not prompt.strip():
            return {
                "success": False,
                "status": "error",
                "provider": "gemini",
                "model": model or self.model_name,
                "response": None,
                "response_text": None,
                "latency_ms": 0.0,
                "usage": None,
                "error_type": "LLM_INVALID_RESPONSE",
                "error_message": "Prompt sent to LLM Gateway cannot be empty.",
                "error": {
                    "error_type": "LLM_INVALID_RESPONSE",
                    "message": "Prompt sent to LLM Gateway cannot be empty.",
                    "retryable": False,
                },
                "retry_count": 0,
            }

        messages = [{"role": "user", "parts": [prompt.strip()]}]
        return self.generate_chat_response(
            messages=messages,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate_response(self, sanitized_prompt: str) -> Dict[str, Any]:
        """
        Backward-compatible single-turn helper.
        """
        return self.generate(prompt=sanitized_prompt)

    def generate_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Multi-turn chat generation with bounded retries and model cascade.
        """
        t_start = time.perf_counter()

        if not messages:
            return {
                "success": False,
                "status": "error",
                "provider": "gemini",
                "model": model or self.model_name,
                "response": None,
                "response_text": None,
                "latency_ms": 0.0,
                "usage": None,
                "error_type": "LLM_INVALID_RESPONSE",
                "error_message": "Messages list cannot be empty.",
                "error": {
                    "error_type": "LLM_INVALID_RESPONSE",
                    "message": "Messages list cannot be empty.",
                    "retryable": False,
                },
                "retry_count": 0,
            }

        # Check client configuration
        if not self.client:
            latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
            err_type = "LLM_CONFIGURATION_ERROR"
            err_msg = "Gemini API key is not configured or google-genai SDK is unavailable."
            return {
                "success": False,
                "status": "error",
                "provider": "gemini",
                "model": model or self.model_name,
                "response": None,
                "response_text": None,
                "latency_ms": latency_ms,
                "usage": None,
                "error_type": err_type,
                "error_message": err_msg,
                "error": {
                    "error_type": err_type,
                    "message": err_msg,
                    "retryable": False,
                },
                "retry_count": 0,
            }

        # Build candidate model list
        target_models = []
        if model:
            target_models.append(model)
        if GeminiClient._last_working_model and GeminiClient._last_working_model not in target_models:
            target_models.append(GeminiClient._last_working_model)
        for m in STANDARD_CANDIDATE_MODELS:
            if m not in target_models:
                target_models.append(m)

        # Build SDK content structure
        def _build_contents(msgs):
            if not gtypes:
                return [m.get("parts", [""])[0] for m in msgs]
            contents = []
            for m in msgs:
                role = m.get("role", "user")
                parts = m.get("parts", [""])
                text = parts[0] if isinstance(parts, list) and parts else str(parts)
                contents.append(gtypes.Content(role=role, parts=[gtypes.Part(text=text)]))
            return contents

        contents = _build_contents(messages)

        # Optional config object
        config_kwargs = {}
        if gtypes:
            gen_config = {}
            if system_instruction:
                gen_config["system_instruction"] = system_instruction
            if temperature is not None:
                gen_config["temperature"] = float(temperature)
            if max_tokens is not None:
                gen_config["max_output_tokens"] = int(max_tokens)
            if gen_config:
                config_kwargs["config"] = gtypes.GenerateContentConfig(**gen_config)

        last_error_type = "LLM_UNKNOWN_ERROR"
        last_error_msg = "All candidate models failed."
        total_retries = 0

        for cand_model in target_models:
            for attempt in range(self.max_retries + 1):
                try:
                    logger.debug(f"[GeminiClient] Requesting model='{cand_model}' (attempt {attempt + 1})")
                    response = self.client.models.generate_content(
                        model=cand_model,
                        contents=contents,
                        **config_kwargs,
                    )

                    if response and response.text:
                        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
                        GeminiClient._last_working_model = cand_model

                        # Extract token usage if available
                        usage = None
                        if hasattr(response, "usage_metadata") and response.usage_metadata:
                            u = response.usage_metadata
                            usage = {
                                "prompt_tokens": getattr(u, "prompt_token_count", None),
                                "candidates_tokens": getattr(u, "candidates_token_count", None),
                                "total_tokens": getattr(u, "total_token_count", None),
                            }

                        return {
                            "success": True,
                            "status": "success",
                            "provider": "gemini",
                            "model": cand_model,
                            "response": response.text,
                            "response_text": response.text,
                            "latency_ms": latency_ms,
                            "usage": usage,
                            "error_type": None,
                            "error_message": None,
                            "error": None,
                            "retry_count": total_retries,
                        }
                    else:
                        last_error_type = "LLM_INVALID_RESPONSE"
                        last_error_msg = "Gemini API returned an empty text response."
                        break

                except Exception as exc:
                    err_type, err_msg, is_retryable = classify_llm_error(exc)
                    last_error_type = err_type
                    last_error_msg = err_msg

                    logger.warning(
                        f"[GeminiClient] Model '{cand_model}' attempt {attempt + 1} failed: "
                        f"{err_type} - {err_msg}"
                    )

                    # Non-retryable error (e.g. Auth, Quota exhaustion): do not loop attempt retries
                    if not is_retryable or attempt >= self.max_retries:
                        break

                    total_retries += 1
                    time.sleep(0.5)

            # If it's an Auth error, no other model will succeed with the same key
            if last_error_type == "LLM_AUTH_ERROR":
                break

        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "success": False,
            "status": "error",
            "provider": "gemini",
            "model": target_models[0] if target_models else self.model_name,
            "response": None,
            "response_text": None,
            "latency_ms": latency_ms,
            "usage": None,
            "error_type": last_error_type,
            "error_message": last_error_msg,
            "message": last_error_msg,
            "error": {
                "error_type": last_error_type,
                "message": last_error_msg,
                "retryable": False,
            },
            "retry_count": total_retries,
        }

    def stream_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
    ):
        """
        Token-by-token streaming generator from Gemini API.
        Yields text chunks in real-time. On API failure, yields an explicit status notice.
        """
        if not messages:
            yield "Error: Empty message prompt."
            return

        if not self.client:
            yield "⚠️ [Gemini Service Notice]: Gemini API client is not configured."
            return

        cand_model = GeminiClient._last_working_model or self.model_name
        try:
            contents = []
            for m in messages:
                role = m.get("role", "user")
                parts = m.get("parts", [""])
                text = parts[0] if isinstance(parts, list) and parts else str(parts)
                contents.append(gtypes.Content(role=role, parts=[gtypes.Part(text=text)]))

            config_kwargs = {}
            if system_instruction and gtypes:
                config_kwargs["config"] = gtypes.GenerateContentConfig(system_instruction=system_instruction)

            response_stream = self.client.models.generate_content_stream(
                model=cand_model,
                contents=contents,
                **config_kwargs,
            )
            has_yielded = False
            for chunk in response_stream:
                if chunk and chunk.text:
                    has_yielded = True
                    yield chunk.text

            if not has_yielded:
                yield "⚠️ [Gemini Service Notice]: Stream completed with empty output."

        except Exception as exc:
            err_type, err_msg, _ = classify_llm_error(exc)
            logger.warning(f"[GeminiClient Stream] Streaming failed: {err_type} - {err_msg}")
            if err_type == "LLM_QUOTA_EXCEEDED":
                yield "⚠️ [Gemini Quota Notice]: Gemini API quota has been exceeded for your project."
            elif err_type == "LLM_AUTH_ERROR":
                yield "⚠️ [Gemini Auth Notice]: Invalid or unauthorized API key."
            else:
                yield f"⚠️ [Gemini Error Notice]: Stream generation failed ({err_type})."


# Aliases for backward compatibility
GeminiLLMClient = GeminiClient
