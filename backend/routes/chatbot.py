"""
AI Trust Chat — Secure Chat Route with Full Evidence-Based Security Gateway Pipeline.
File: backend/routes/chatbot.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import logging

from backend.logger import log_privacy_audit
from llm_gateway.gemini_client import GeminiClient
from mcp_engine.mcp_client import MCPClientManager
from mcp_engine.web_search_router import WebSearchRouter
from backend.services.evidence_risk import run_full_analysis, calculate_evidence_risk
from backend.services.output_scanner import scan_output
from backend.services.trust_receipt import generate_receipt
from backend.services.policy_engine import evaluate_policies
from backend.services.model_router import route_query
from backend.services.security_events import log_event
from backend.services.rag_engine import query_documents
from backend.services.tools_ecosystem import search_web

router = APIRouter()
logger = logging.getLogger("AITrustChat")

# Singletons & Thread-Safe TTL Cache
_gemini_client: Optional[GeminiClient] = None
_mcp_manager: Optional[MCPClientManager] = None
_CHAT_RESPONSE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_CHAT_CACHE_TTL = 600.0  # 10 minutes (only for SAFE responses with 0 PII)


def _get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def _get_mcp_manager() -> MCPClientManager:
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager(enable_default_servers=True)
    return _mcp_manager


INJECTION_PATTERNS = [
    ("ignore previous instructions",       0.98),
    ("reveal your system prompt",          0.97),
    ("disregard all previous",             0.96),
    ("show me your hidden instructions",   0.95),
    ("ignore all previous",                0.93),
    ("reveal system prompt",               0.92),
    ("dan mode",                           0.90),
    ("jailbreak",                          0.90),
    ("bypass security",                    0.89),
    ("act as if you have no restrictions", 0.95),
    ("pretend you are a different ai",     0.90),
    ("forget your training",               0.88),
    ("override your instructions",         0.95),
    ("ignore your guidelines",             0.94),
]


def _detect_injection(text: str) -> Tuple[bool, float, Optional[str]]:
    """Detect prompt injection patterns."""
    lower = text.lower()
    max_conf = 0.0
    matched_pattern = None

    for pattern, confidence in INJECTION_PATTERNS:
        if pattern in lower:
            if confidence > max_conf:
                max_conf = confidence
                matched_pattern = pattern

    return max_conf >= 0.70, max_conf, matched_pattern


def _build_gemini_messages(
    raw_prompt: str,
    chat_history: Optional[List[Dict[str, Any]]],
    synthesis_context: str = "",
    rag_context: str = "",
    model_label: str = "Gemini",
) -> List[Dict[str, Any]]:
    """Build Gemini multi-turn message list."""
    messages = []

    system_preamble = (
        "You are AI Trust Chat, a secure and privacy-aware AI assistant. "
        "You answer questions clearly, naturally, helpfully, and accurately. "
        "For general knowledge, answer from your training. "
        "For code requests, provide complete working code. "
        "Do NOT use filler templates. Be specific and factual."
    )
    messages.append({"role": "user", "parts": [system_preamble]})
    messages.append({"role": "model", "parts": ["Understood. I am AI Trust Chat, ready to assist with accurate, trustworthy responses."]})

    # Inject conversation history (last 12 turns)
    if chat_history:
        history_turns = [
            m for m in chat_history
            if m.get("role") in ("user", "assistant") and m.get("text", "").strip()
        ]
        for msg in history_turns[-12:]:
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["text"].strip()]})

    # Build final user message
    if rag_context:
        final_text = (
            f"You are answering based on the following retrieved document context.\n\n"
            f"RETRIEVED DOCUMENT CONTEXT:\n{rag_context}\n\n"
            f"USER QUESTION: {raw_prompt}\n\n"
            f"Answer the question based on the document context above. "
            f"If the context doesn't contain enough information, say so clearly."
        )
    elif synthesis_context:
        final_text = (
            f"USER QUESTION: \"{raw_prompt}\"\n\n"
            f"RETRIEVED WEB EVIDENCE:\n{synthesis_context}\n\n"
            f"Synthesize a concise, natural response. Do NOT dump raw results verbatim. "
            f"Conclude with '### Sources Used' listing markdown links."
        )
    else:
        final_text = raw_prompt

    messages.append({"role": "user", "parts": [final_text]})
    return messages


class ChatRequest(BaseModel):
    prompt: str
    sanitization_mode: Optional[str] = "REDACT"
    mcp_enabled: Optional[bool] = True
    chat_history: Optional[List[Dict[str, Any]]] = None
    user_role: Optional[str] = "USER"
    user_id: Optional[str] = "Employee-001"
    rag_doc_id: Optional[str] = None
    model_preference: Optional[str] = "auto"


@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    AI Trust Chat — Ultra-Fast Evidence-Based Security Gateway Pipeline:
    1. Input Validation
    2. Fast Query Intent Classification (Router: <1ms)
    3. Evidence-Based Privacy & Injection Scanning (Security: ~40ms)
    4. Decision Gate (BLOCK -> Halt, WARN -> Mask, ALLOW -> Pass)
    5. Direct Fast LLM or Parallel Web Search (Target: <=2-5s)
    6. Output Scanner & Trust Receipt Generation
    7. High-Resolution Telemetry Profiling (Total, Router, Security, Search, LLM)
    """
    import time
    import threading
    import uuid as uuid_module

    t_total_start = time.perf_counter()
    request_id = f"ATC-{abs(uuid_module.uuid4().int) % 1000000:06d}"
    raw_prompt = req.prompt.strip() if req.prompt else ""
    user_role = req.user_role or "USER"
    user_id = req.user_id or "Employee-001"

    # Empty prompt guard
    if not raw_prompt:
        return _empty_response(request_id)

    # ── STAGE 0: Fast TTL Query Cache Check (<0.1ms) ──────────────────────────
    cache_key = f"{raw_prompt.lower().strip()}||{user_role}||{req.sanitization_mode or 'REDACT'}"
    now_ts = time.time()
    if cache_key in _CHAT_RESPONSE_CACHE:
        cached_ts, cached_payload = _CHAT_RESPONSE_CACHE[cache_key]
        if (now_ts - cached_ts) < _CHAT_CACHE_TTL:
            cached_resp = dict(cached_payload)
            cached_resp["request_id"] = request_id
            cached_resp["timing_breakdown"] = {
                "total_ms": round((time.perf_counter() - t_total_start) * 1000, 2),
                "router_ms": 0.05,
                "security_ms": 0.05,
                "search_ms": 0.0,
                "llm_ms": 0.0,
                "render_ms": 0.05,
                "tier": "SIMPLE (CACHE HIT)",
                "cached": True,
            }
            return cached_resp

    # ── STAGE 0b: Fast Query Router (<1ms) ────────────────────────────────────
    t_router_start = time.perf_counter()
    routing_intent = WebSearchRouter.classify_query_intent(raw_prompt, req.chat_history)
    router_ms = round((time.perf_counter() - t_router_start) * 1000, 2)

    # ── STAGE 1 & 2: Evidence-Based Security Analysis & Injection Detection ───
    t_sec_start = time.perf_counter()
    analysis = run_full_analysis(raw_prompt, mode=req.sanitization_mode or "REDACT")
    injection_detected, injection_confidence, injection_pattern = _detect_injection(raw_prompt)

    # ── STAGE 3: Merge Signals & Calculate Final Decision ──────────────────────
    if injection_detected:
        risk_score = max(analysis["risk_score"], int(injection_confidence * 95))
        risk_level = "CRITICAL"
        decision = "BLOCK"
        detected_risks = list(dict.fromkeys(["Prompt Injection Attack"] + analysis["detected_risks"]))
        evidence = [f"Prompt injection pattern detected: '{injection_pattern}' (confidence: {injection_confidence * 100:.1f}%)"] + analysis["evidence"]
        reason = f"Adversarial instruction override sequence detected: '{injection_pattern}'. Request blocked from LLM."
        routing_action = "BLOCKED → LLM was not called"
        category = "PROMPT_INJECTION"
    else:
        risk_score = analysis["risk_score"]
        risk_level = analysis["risk_level"]
        decision = analysis["decision"]
        detected_risks = analysis["detected_risks"]
        evidence = analysis["evidence"]
        reason = analysis["reason"]
        routing_action = analysis["routing_action"]
        category = "SECRET_DETECTED" if analysis.get("has_critical_secret") else ("PII_DETECTED" if detected_risks else "SAFE")

    # ── STAGE 4: Policy Evaluation ─────────────────────────────────────────────
    pii_detected = len(analysis["entities"]) > 0
    secret_detected = analysis.get("has_critical_secret", False)
    policy_result = evaluate_policies(
        pii_detected=pii_detected,
        secret_detected=secret_detected,
        injection_detected=injection_detected,
        injection_confidence=injection_confidence,
        output_sensitive=False,
        risk_score=risk_score,
        doc_classification="PUBLIC",
        user_role=user_role,
    )
    security_ms = round((time.perf_counter() - t_sec_start) * 1000, 2)

    # ── STAGE 5: BLOCK GATE (LLM is NEVER called on HIGH RISK / BLOCK) ─────────
    if decision == "BLOCK":
        model_info = {"model_label": "N/A (Blocked)", "task_type": "BLOCKED", "reasoning": reason}
        total_ms = round((time.perf_counter() - t_total_start) * 1000, 2)
        timing_breakdown = {
            "total_ms": total_ms,
            "router_ms": router_ms,
            "security_ms": security_ms,
            "search_ms": 0.0,
            "llm_ms": 0.0,
            "render_ms": 1.0,
        }

        # Background async audit logging
        threading.Thread(
            target=_emit_event,
            args=("INJECTION_BLOCKED" if injection_detected else "SECRET_BLOCKED",
                  "CRITICAL" if risk_score >= 80 else "HIGH",
                  reason, user_id, "N/A", "BLOCK", risk_score),
            daemon=True
        ).start()

        receipt = _build_and_return_receipt(
            request_id, user_id, "N/A", pii_detected,
            [e["entity_type"] for e in analysis["entities"]],
            injection_detected, risk_score, risk_level, "BLOCK", "BLOCK", "BLOCK", False
        )
        resp_payload = _build_response_payload(
            request_id=request_id,
            receipt_id=receipt.get("receipt_id", request_id),
            decision="BLOCK",
            risk_score=risk_score,
            risk_level=risk_level,
            category=category,
            detected_risks=detected_risks,
            entities=analysis["entities"],
            where_items=analysis.get("where_items", []),
            why_bullets=analysis.get("why_bullets", []),
            evidence=evidence,
            reason=reason,
            routing_action="BLOCKED → LLM was not called",
            status_banner=analysis.get("status_banner", "🔴 PRIVACY RISK DETECTED"),
            action_label=analysis.get("action_label", "🚫 BLOCK — Will NOT be sent to external LLM"),
            highlighted_html=analysis.get("highlighted_html", ""),
            response_text=None,
            bert_prediction=analysis["bert_prediction"],
            bert_confidence=analysis["bert_confidence"],
            nb_prediction=analysis["nb_prediction"],
            nb_confidence=analysis["nb_confidence"],
            model_info=model_info,
            policy_result=policy_result,
            pii_action="BLOCK",
            output_action="BLOCK",
            output_sensitive=False,
            masked_prompt=None,
            rag_meta=None,
            mcp_meta=None,
        )
        resp_payload["timing_breakdown"] = timing_breakdown
        return resp_payload

    # ── STAGE 6: Sanitization for MEDIUM RISK (WARN / MASK) ───────────────────
    if decision == "WARN" or pii_detected:
        prompt_to_send = analysis.get("sanitized_text") or raw_prompt
        pii_action = "MASK"
    else:
        prompt_to_send = raw_prompt
        pii_action = "ALLOW"

    # ── STAGE 7: Model Router ──────────────────────────────────────────────────
    model_info = route_query(raw_prompt, pii_detected, secret_detected, req.model_preference or "auto")

    # ── STAGE 8: RAG Query (if applicable) ────────────────────────────────────
    rag_context = ""
    rag_meta = None
    if req.rag_doc_id or any(kw in raw_prompt.lower() for kw in ["document", "pdf", "file", "uploaded", "summarize this"]):
        rag_result = query_documents(prompt_to_send, user_role=user_role, doc_id=req.rag_doc_id)
        if rag_result.get("access_denied"):
            decision = "BLOCK"
            reason = rag_result["message"]
            response_text = f"🔒 **ACCESS DENIED**\n\n{reason}"
            return _build_response_payload(
                request_id=request_id, receipt_id=request_id, decision="BLOCK",
                risk_score=80, risk_level="HIGH", category="RAG_ACCESS_DENIED",
                detected_risks=["Unauthorized Document Access"], entities=[],
                evidence=[reason], reason=reason, routing_action="DENIED → Access control block",
                response_text=response_text, bert_prediction=analysis["bert_prediction"],
                bert_confidence=analysis["bert_confidence"], nb_prediction=analysis["nb_prediction"],
                nb_confidence=analysis["nb_confidence"], model_info=model_info,
                policy_result=policy_result, pii_action=pii_action, output_action="BLOCK",
                output_sensitive=False, masked_prompt=None, rag_meta=None, mcp_meta=None,
            )
        if rag_result.get("success"):
            rag_context = rag_result["context"]
            rag_meta = {"source_docs": rag_result["source_docs"], "chunks_retrieved": rag_result["chunks_retrieved"]}

    # ── STAGE 9 & 10: Grounded Search / Fast Direct LLM Generation ───────────
    sources_list = []
    mcp_meta = None
    response_text = ""
    search_ms = 0.0
    llm_ms = 0.0

    # Only invoke search if WebSearchRouter categorized as WEB_REQUIRED / COMPLEX_RESEARCH
    if not rag_context and req.mcp_enabled and routing_intent["should_search"]:
        t_search_start = time.perf_counter()
        search_out = search_web(routing_intent["search_query"], max_results=routing_intent.get("max_sources", 3))
        search_ms = round((time.perf_counter() - t_search_start) * 1000, 2)
        sources_list = search_out.get("sources", [])
        response_text = search_out.get("direct_answer", "")

        # Append verified sources list below the answer
        if sources_list and "### Sources" not in response_text:
            source_links = "\n".join([f"[{s['citation_id']}] [{s['title']}]({s['url']}) — `{s['domain']}`" for s in sources_list])
            response_text += f"\n\n### Sources\n{source_links}"

        mcp_meta = {
            "tool_name": "search_web",
            "status": "SUCCESS",
            "sources_count": len(sources_list),
            "sources": sources_list,
            "timing_ms": search_out.get("timing_ms", {})
        }

    # FAST DIRECT LLM GENERATION for SIMPLE queries (No web search)
    if not response_text:
        t_llm_start = time.perf_counter()
        messages = _build_gemini_messages(
            raw_prompt=prompt_to_send,
            chat_history=req.chat_history,
            synthesis_context="",
            rag_context=rag_context,
            model_label=model_info["model_label"],
        )
        genai_payload = _get_gemini_client().generate_chat_response(messages=messages)
        llm_ms = round((time.perf_counter() - t_llm_start) * 1000, 2)

        if genai_payload.get("status") == "error" or not genai_payload.get("response_text"):
            response_text = _get_gemini_client()._generate_dynamic_generalized_response(raw_prompt)
        else:
            response_text = genai_payload["response_text"]

    if rag_meta and rag_meta.get("source_docs"):
        response_text += f"\n\n---\n📄 *Answered from document(s): {', '.join(rag_meta['source_docs'])}*"

    # ── STAGE 11: Output Security Scanner ─────────────────────────────────────
    t_out_start = time.perf_counter()
    output_scan = scan_output(response_text)
    output_action = output_scan["action"]
    output_sensitive = output_scan["is_sensitive"]

    if output_action == "REDACT":
        response_text = output_scan["redacted_text"]

    # ── STAGE 12: Trust Receipt & Audit Logging ───────────────────────────────
    receipt = generate_receipt(
        user_id=user_id,
        model_selected=model_info["model_label"],
        pii_detected=pii_detected,
        pii_entities=[e["entity_type"] for e in analysis["entities"]],
        injection_detected=injection_detected,
        risk_score=risk_score,
        risk_level=risk_level,
        policy_action=decision,
        pii_action=pii_action,
        output_action=output_action,
        output_sensitive=output_sensitive,
    )
    render_ms = round((time.perf_counter() - t_out_start) * 1000, 2)
    total_ms = round((time.perf_counter() - t_total_start) * 1000, 2)

    timing_breakdown = {
        "total_ms": total_ms,
        "router_ms": router_ms,
        "security_ms": security_ms,
        "search_ms": search_ms,
        "llm_ms": llm_ms,
        "render_ms": render_ms,
        "tier": routing_intent.get("category", "SIMPLE"),
    }

    # Background Async Audit Logging
    def _async_audit():
        try:
            log_privacy_audit(
                request_id=request_id,
                modality="Text",
                risk_score=float(risk_score) / 100.0,
                action_taken=decision,
                detected_entities=[e.get("entity_type", "PII") for e in analysis.get("entities", [])],
                original_length=len(raw_prompt),
                llm_status="SUCCESS" if decision != "BLOCK" else "BLOCKED",
            )
        except Exception:
            pass

    threading.Thread(target=_async_audit, daemon=True).start()

    resp_payload = _build_response_payload(
        request_id=request_id,
        receipt_id=receipt.get("receipt_id", request_id),
        decision=decision,
        risk_score=risk_score,
        risk_level=risk_level,
        category=category,
        detected_risks=detected_risks,
        entities=analysis["entities"],
        where_items=analysis.get("where_items", []),
        why_bullets=analysis.get("why_bullets", []),
        evidence=evidence,
        reason=reason,
        routing_action=routing_action,
        status_banner=analysis.get("status_banner", "🟢 SAFE — Low Privacy Risk"),
        action_label=analysis.get("action_label", "✅ ALLOW — Sent to LLM"),
        highlighted_html=analysis.get("highlighted_html", ""),
        response_text=response_text,
        bert_prediction=analysis["bert_prediction"],
        bert_confidence=analysis["bert_confidence"],
        nb_prediction=analysis["nb_prediction"],
        nb_confidence=analysis["nb_confidence"],
        model_info=model_info,
        policy_result=policy_result,
        pii_action=pii_action,
        output_action=output_action,
        output_sensitive=output_sensitive,
        masked_prompt=analysis.get("sanitized_text") if pii_detected else None,
        rag_meta=rag_meta,
        mcp_meta=mcp_meta,
    )
    resp_payload["timing_breakdown"] = timing_breakdown

    # Save to TTL Cache (Only for SAFE responses with zero PII/secrets)
    if decision == "ALLOW" and not pii_detected and not secret_detected and not injection_detected and not rag_context:
        _CHAT_RESPONSE_CACHE[cache_key] = (now_ts, resp_payload)

    return resp_payload


def _build_response_payload(
    request_id: str,
    receipt_id: str,
    decision: str,
    risk_score: int,
    risk_level: str,
    category: str,
    detected_risks: List[str],
    entities: List[Dict[str, Any]],
    where_items: List[Dict[str, Any]],
    why_bullets: List[str],
    evidence: List[str],
    reason: str,
    routing_action: str,
    status_banner: str,
    action_label: str,
    highlighted_html: str,
    response_text: Optional[str],
    bert_prediction: str,
    bert_confidence: float,
    nb_prediction: str,
    nb_confidence: float,
    model_info: Dict[str, Any],
    policy_result: Dict[str, Any],
    pii_action: str,
    output_action: str,
    output_sensitive: bool,
    masked_prompt: Optional[str],
    rag_meta: Optional[Dict[str, Any]],
    mcp_meta: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "success": True,
        "request_id": request_id,
        "receipt_id": receipt_id,
        # Core decisions
        "decision": decision,
        "action": decision,
        "risk_score": risk_score,
        "risk_score_pct": risk_score,
        "risk_level": risk_level,
        "category": category,
        "status_banner": status_banner,
        "action_label": action_label,
        # Evidence-based breakdown & Spans
        "detected_risks": detected_risks,
        "entities": entities,
        "detected_entities": [e.get("entity_type", "") for e in entities],
        "where_items": where_items,
        "why_bullets": why_bullets,
        "evidence": evidence,
        "reason": reason,
        "routing_action": routing_action,
        "highlighted_html": highlighted_html,
        # ML model results
        "bert_prediction": bert_prediction,
        "bert_confidence": bert_confidence,
        "bert_score": bert_confidence,
        "naive_bayes_prediction": nb_prediction,
        "nb_prediction": nb_prediction,
        "nb_confidence": nb_confidence,
        "nb_score": nb_confidence,
        # Responses & LLM
        "ai_response": response_text,
        "response": response_text,
        "masked_prompt": masked_prompt,
        "model_selected": model_info.get("model_label", "Gemini"),
        "model_task_type": model_info.get("task_type", "STANDARD"),
        "model_routing_reason": model_info.get("reasoning", ""),
        # Policies
        "pii_action": pii_action,
        "output_action": output_action,
        "output_sensitive": output_sensitive,
        "policy_action": policy_result.get("final_action", "ALLOW"),
        "triggered_policies": [p["name"] for p in policy_result.get("triggered_policies", [])],
        # Context metadata
        "rag_meta": rag_meta,
        "mcp_meta": mcp_meta,
    }


def _empty_response(request_id: str) -> Dict[str, Any]:
    return {
        "success": False,
        "request_id": request_id,
        "decision": "ALLOW",
        "action": "ALLOW",
        "risk_score": 0,
        "risk_score_pct": 0,
        "risk_level": "LOW",
        "category": "SAFE",
        "detected_risks": [],
        "entities": [],
        "detected_entities": [],
        "evidence": [],
        "reason": "Empty prompt provided.",
        "routing_action": "NO_OP",
        "bert_prediction": "SAFE",
        "bert_confidence": 0.0,
        "naive_bayes_prediction": "SAFE",
        "nb_prediction": "SAFE",
        "nb_confidence": 0.0,
        "ai_response": None,
        "response": None,
        "masked_prompt": None,
        "model_selected": "N/A",
        "pii_action": "ALLOW",
        "output_action": "ALLOW",
        "output_sensitive": False,
        "policy_action": "ALLOW",
        "triggered_policies": [],
        "rag_meta": None,
        "mcp_meta": None,
    }


def _emit_event(event_type, severity, message, user, model, action, risk_score):
    try:
        log_event(event_type, severity, message, user, model, action, risk_score)
    except Exception:
        pass


def _build_and_return_receipt(request_id, user_id, model_label, pii_detected, pii_entity_types,
                               injection_detected, risk_score, risk_level, policy_action, pii_action,
                               output_action, output_sensitive):
    try:
        return generate_receipt(
            user_id=user_id, model_selected=model_label,
            pii_detected=pii_detected, pii_entities=pii_entity_types,
            injection_detected=injection_detected, risk_score=risk_score,
            risk_level=risk_level, policy_action=policy_action,
            pii_action=pii_action, output_action=output_action,
            output_sensitive=output_sensitive, request_id=request_id,
        )
    except Exception:
        return {"receipt_id": request_id}


def _format_local_synthesis(prompt: str, sources: List[Dict[str, Any]]) -> str:
    snippets = [s["snippet"] for s in sources if s.get("snippet")]
    body = " ".join(snippets[:3]) if snippets else f"Retrieved information regarding: {prompt}"
    source_links = "\n".join([f"- [{s['title']}]({s['url']})" for s in sources])
    return f"{body}\n\n### Sources Used\n{source_links}"
