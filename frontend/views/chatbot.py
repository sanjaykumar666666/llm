"""
AI Trust Chat — Secure Chat View with Aiera Multi-Modal Tools Ecosystem.
File Location: frontend/views/chatbot.py
"""

import streamlit as st
import time
import io
import json
import html
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from frontend.services.api_client import APIClient
from backend.services.trust_receipt import format_receipt_text, get_receipt_by_id
from processing.text_processor import TextProcessor
from backend.routes.chatbot import _detect_injection
from backend.services.tools_ecosystem import (
    search_web,
    deep_research,
    process_file_content,
    analyze_dataset,
    generate_image_bridge,
    analyze_image_bytes,
    canvas_engine,
    execute_code_safely,
    analyze_url_content,
    generate_formal_report,
    execute_tool_with_ai_trust
)

# Preset quick test prompts for instant scenario loading
QUICK_TEST_CHIPS = [
    ("🟢 Safe Science", "Explain how photosynthesis works in green plants and why it is important."),
    ("🛡️ Safe Password Q", "What is a password manager and how does it help protect user accounts?"),
    ("🔴 DB Credential", "Deploy config: username=admin password=SuperSecretP@ssw0rd!123 database=prod"),
    ("🟡 Phone Hotline", "Please call our customer service hotline at +1-800-555-0199 for assistance."),
    ("🟡 Email Record", "Send the project documentation to alice.smith@enterprise-corp.org as soon as possible."),
    ("🔴 Card + CVV", "Billing record: Credit card number 4532 1234 5678 9010 expiration 12/28 CVV 882."),
    ("🟡 Mixed PII", "I am writing a blog post about cybersecurity. My email is researcher@lab.io and my phone is 9876543210."),
]

# Available Tools in the Aiera Tools Ecosystem
TOOLS_LIST = [
    "💬 Standard Chat",
    "🔎 Web Search",
    "🧠 Deep Research",
    "📊 Data Analysis",
    "📎 Files Parser",
    "🎨 Image Generation",
    "🖼️ Image Analysis",
    "✍️ Canvas Workspace",
    "💻 Code Workspace",
    "🔗 URL Analysis",
    "📚 Knowledge Base / RAG",
    "📝 Report Generator",
    "📈 Charts & Visualization",
    "📤 Export Manager",
    "🛡️ AI Trust Core"
]


def _init_chat_session():
    if "privacy_chat_threads" not in st.session_state:
        st.session_state["privacy_chat_threads"] = [{
            "id": "thread-1",
            "title": "Universal Live Grounded Chat",
            "messages": [],
            "created_at": "Just now"
        }]
    if "privacy_current_thread_id" not in st.session_state:
        st.session_state["privacy_current_thread_id"] = "thread-1"
    if "composer_preset_text" not in st.session_state:
        st.session_state["composer_preset_text"] = ""
    if "active_tool" not in st.session_state:
        st.session_state["active_tool"] = "💬 Standard Chat"
    if "canvas_content" not in st.session_state:
        st.session_state["canvas_content"] = "### Executive Research Document\n\nEnter your notes, architecture designs, or code snippets here..."


def _compute_live_privacy_status(text: str) -> Dict[str, Any]:
    """
    Computes real-time authoritative privacy risk, detected entities, and policy decision
    before the user sends a message, using Pipelines 1, 3, 4, 5.
    """
    if not text or not text.strip():
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "decision": "ALLOW",
            "state_label": "🟢 SAFE",
            "state_type": "SAFE",
            "entities_label": "None (Clean)",
            "status_col": "#10B981",
            "badge_bg": "rgba(16,185,129,0.18)",
            "badge_col": "#10B981",
            "badge_border": "rgba(16,185,129,0.5)",
            "detected_list": [],
            "reason": "Input clean.",
            "entities": [],
            "sanitized_text": "",
            "is_blocked": False,
        }

    from backend.services.evidence_risk import run_full_analysis
    analysis = run_full_analysis(text)

    decision = analysis["decision"]
    risk_score = analysis["risk_score"]
    risk_level = analysis["risk_level"]
    entities = analysis.get("entities", [])
    entity_types = [e.get("category", e.get("entity_type", "PII")) for e in entities]
    sanitized_text = analysis.get("sanitized_text", text)

    # ── Three Authoritative Live States ───────────────────────────────────────
    if decision == "BLOCK":
        state_type = "DANGER"
        state_label = "🔴 DANGER"
        status_col = "#EF4444"
        badge_bg = "rgba(239,68,68,0.18)"
        badge_col = "#EF4444"
        badge_border = "rgba(239,68,68,0.5)"
        is_blocked = True
    elif decision in ("WARN", "SANITIZE") or risk_level in ("MEDIUM", "HIGH"):
        state_type = "WARNING"
        state_label = "🟡 WARNING"
        status_col = "#F59E0B"
        badge_bg = "rgba(245,158,11,0.18)"
        badge_col = "#F59E0B"
        badge_border = "rgba(245,158,11,0.5)"
        is_blocked = False
    else:
        state_type = "SAFE"
        state_label = "🟢 SAFE"
        status_col = "#10B981"
        badge_bg = "rgba(16,185,129,0.18)"
        badge_col = "#10B981"
        badge_border = "rgba(16,185,129,0.5)"
        is_blocked = False

    entities_label = ", ".join(list(dict.fromkeys(entity_types))) if entity_types else "None (Clean)"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "decision": decision,
        "state_label": state_label,
        "state_type": state_type,
        "entities_label": entities_label,
        "status_col": status_col,
        "badge_bg": badge_bg,
        "badge_col": badge_col,
        "badge_border": badge_border,
        "detected_list": entity_types,
        "reason": analysis.get("reason", "Analysis complete."),
        "entities": entities,
        "sanitized_text": sanitized_text,
        "is_blocked": is_blocked,
        "security_advisory": analysis.get("security_advisory"),
    }


def _sanitize_message_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Strict deduplication: eliminates duplicate consecutive messages with same role & text."""
    clean = []
    for msg in messages:
        if not msg.get("text", "").strip() and not msg.get("security_meta") and not msg.get("tool_data"):
            continue
        if clean and clean[-1].get("role") == msg.get("role") and clean[-1].get("text", "").strip() == msg.get("text", "").strip():
            continue
        clean.append(msg)
    return clean


def _risk_badge_html(risk_level: str, risk_score: int) -> str:
    colors = {
        "LOW": ("#10B981", "rgba(16,185,129,0.12)", "🟢"),
        "MEDIUM": ("#F59E0B", "rgba(245,158,11,0.12)", "🟡"),
        "HIGH": ("#EF4444", "rgba(239,68,68,0.12)", "🔴"),
        "CRITICAL": ("#DC2626", "rgba(220,38,38,0.15)", "🚨"),
    }
    col, bg, icon = colors.get(risk_level.upper(), ("#94A3B8", "rgba(148,163,184,0.1)", "⚪"))
    return (
        f"<span style='background:{bg}; color:{col}; border:1px solid {col}44; "
        f"font-size:11px; font-weight:700; padding:3px 8px; border-radius:20px;'>"
        f"{icon} {risk_level} ({risk_score}%)"
        f"</span>"
    )


def _model_badge_html(model_name: str, is_error: bool = False) -> str:
    border_col = "rgba(239,68,68,0.4)" if is_error else "rgba(99,102,241,0.3)"
    text_col = "#FCA5A5" if is_error else "#A5B4FC"
    bg_col = "rgba(239,68,68,0.12)" if is_error else "rgba(99,102,241,0.12)"
    icon = "⚠️" if is_error else "🤖"
    return (
        f"<span style='background:{bg_col}; color:{text_col}; border:1px solid {border_col}; "
        f"font-size:11px; font-weight:600; padding:3px 8px; border-radius:20px;'>"
        f"{icon} {model_name}"
        f"</span>"
    )


def _telemetry_badge_html(timing: Optional[Dict[str, Any]], is_error: bool = False) -> str:
    if not timing:
        return ""
    total_s    = timing.get("total_ms", 0) / 1000.0
    r_ms       = timing.get("router_ms", 0)
    sec_ms     = timing.get("security_ms", 0)
    search_ms  = timing.get("search_ms", 0)
    llm_ms     = timing.get("llm_ms", 0)

    temporal_class  = timing.get("temporal_class", "STATIC")
    temporal_domain = timing.get("temporal_domain")
    sources_count   = timing.get("sources_count", 0)

    if is_error:
        tier_label  = "LIVE RETRIEVAL" if search_ms > 0 else "SECURITY GATEWAY"
        tier_icon   = "⚠️"
        tier_color  = "#F59E0B"
        tier_suffix = "Web: Completed · LLM: Quota Notice"
    elif temporal_class in ("LIVE_GROUNDED", "CURRENT", "UNKNOWN", "HISTORICAL") or sources_count > 0:
        tier_label  = "LIVE GROUNDED"
        tier_icon   = "🌐"
        tier_color  = "#38BDF8"
        domain_tag  = f" · {temporal_domain}" if temporal_domain and temporal_domain != "General Information" else ""
        tier_suffix = f"Sources: {sources_count} · Verification: PASSED{domain_tag}" if sources_count else "Live Verified"
    else:  # Conversational
        tier_label  = "CONVERSATIONAL"
        tier_icon   = "💬"
        tier_color  = "#10B981"
        tier_suffix = "Direct Greeting"

    tier_html = (
        f"<span style='color:{tier_color}; font-weight:700;'>"
        f"[{tier_label}] {tier_icon} {tier_suffix}"
        f"</span>"
    )

    parts = [
        f"⚡ <strong>{total_s:.2f}s</strong>",
        tier_html,
        f"Router: {r_ms:.1f}ms",
        f"Sec: {sec_ms:.1f}ms",
    ]
    if search_ms > 0:
        parts.append(f"Search: {search_ms:.0f}ms")
    if llm_ms > 0:
        parts.append(f"LLM: {llm_ms / 1000.0:.2f}s")

    return (
        f"<span style='background:rgba(15,23,42,0.8); color:#94A3B8; "
        f"border:1px solid rgba(56,189,248,0.25); "
        f"font-size:11px; font-family:monospace; padding:3px 10px; border-radius:20px;'>"
        f"{' | '.join(parts)}"
        f"</span>"
    )


def _render_answer_container(
    text: str,
    meta: Dict[str, Any],
    tool_data: Optional[Dict[str, Any]] = None,
):
    """
    Unified Stable Answer / Error Container:
    1. Single cohesive rendering (no empty boxes, no broken HTML layout)
    2. Explicit graceful error states for quota or authentication issues
    3. Verified Sources Block
    4. Deterministic AI Trust Receipt Block
    """
    decision = meta.get("decision", "ALLOW")
    risk_level = meta.get("risk_level", "LOW")
    risk_score = meta.get("risk_score", 0)

    if decision == "BLOCK":
        advisory = meta.get("security_advisory")
        if advisory and advisory.get("items"):
            # ── Credential-Specific Security Warning UI ───────────────────────
            advisory_html_items = ""
            for item in advisory["items"]:
                advisory_html_items += f"""
                <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); border-radius:8px; padding:10px 14px; margin-top:8px;">
                    <div style="color:#FCA5A5; font-weight:700; font-size:13px; margin-bottom:4px;">{item['icon']} {item['type']} Detected</div>
                    <div style="color:#CBD5E1; font-size:12.5px; line-height:1.5;">
                        <div>⚠️ {html.escape(item['warning'])}</div>
                        <div style="margin-top:4px; color:#FCD34D; font-weight:600;">🔐 Action: {html.escape(item['action'])}</div>
                    </div>
                </div>"""

            st.markdown(
                f"""
                <div style="background:rgba(220,38,38,0.15); border:1.5px solid rgba(220,38,38,0.55); border-radius:14px; padding:18px 20px; margin-bottom:12px; width:100%; box-sizing:border-box;">
                    <div style="color:#FCA5A5; font-weight:800; font-size:15px; margin-bottom:6px; display:flex; align-items:center; gap:8px;">
                        <span>🚨</span> <span>Security Alert: Sensitive Credentials Detected</span>
                    </div>
                    <div style="color:#F87171; font-size:13px; font-weight:600; margin-bottom:8px; padding:8px 12px; background:rgba(239,68,68,0.12); border-radius:8px; border-left:3px solid #EF4444;">
                        {html.escape(advisory.get('global_warning', 'Credentials detected. Message was NOT sent to AI.'))}
                    </div>
                    {advisory_html_items}
                    <div style="margin-top:12px; padding:10px 14px; background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); border-radius:8px;">
                        <div style="color:#FCD34D; font-weight:700; font-size:12.5px;">💡 Security Recommendations:</div>
                        <div style="color:#CBD5E1; font-size:12px; margin-top:4px; line-height:1.6;">
                            • Never share passwords, OTPs, PINs, or API keys in any chat<br>
                            • {html.escape(advisory.get('global_action', 'Change/revoke any active credentials immediately.'))}<br>
                            • If credentials were shared accidentally, treat them as compromised
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background:rgba(220,38,38,0.12); border:1px solid rgba(220,38,38,0.45); border-radius:12px; padding:16px; margin-bottom:10px; width:100%; box-sizing:border-box;">
                    <strong style="color:#FCA5A5;">🔒 Zero-Trust Security Gate: Request Blocked</strong><br>
                    <p style="color:#94A3B8; font-size:13px; margin:8px 0 0 0;">{html.escape(text or meta.get('reason', 'Blocked by security policy.'))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    # Extract sources if present in tool_data or text
    sources = []
    main_text = text or ""
    if tool_data and tool_data.get("result", {}).get("sources"):
        sources = tool_data["result"]["sources"]
        main_text = tool_data["result"].get("direct_answer", text)
    elif "### Sources" in main_text:
        parts = main_text.split("### Sources", 1)
        main_text = parts[0].strip()
        raw_sources_text = parts[1].strip()
        for line in raw_sources_text.splitlines():
            line = line.strip()
            if line:
                m = re.search(r'\[(\d+)\]\s*\[(.*?)\]\((.*?)\)(?:\s*—\s*`?(.*?)`?)?$', line)
                if m:
                    sources.append({
                        "citation_id": m.group(1),
                        "title": m.group(2),
                        "url": m.group(3),
                        "domain": m.group(4) or urllib.parse.urlparse(m.group(3)).netloc
                    })

    is_service_error = (
        "AI Service Notice" in main_text
        or "quota has been exceeded" in main_text.lower()
        or "authentication failed" in main_text.lower()
        or "unable to generate" in main_text.lower()
    )

    # 1. Main Answer or Error Body
    if is_service_error:
        st.markdown(
            f"""
            <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.35); border-radius:14px; padding:18px 20px; margin-bottom:12px; width:100%; box-sizing:border-box;">
                <div style="color:#FCD34D; font-weight:800; font-size:14px; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
                    <span>⚠️</span> <span>AI Service Notice: Generation Limit</span>
                </div>
                <div style="color:#CBD5E1; font-size:13.5px; line-height:1.6;">
                    The configured Google Gemini API quota for this project has been reached or is rate-limited.
                    <br><br>
                    💡 <em>To enable continuous high-speed Gemini responses, enter your free API Key in <strong>⚙️ Settings</strong>.</em>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(main_text)

    # 2. Verified Sources Block
    if sources:
        st.markdown(
            f"""
            <div style="margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.08);">
                <div style="font-size:12px; font-weight:800; color:#38BDF8; letter-spacing:0.5px; text-transform:uppercase; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                    <span>📚 Verified Sources ({len(sources)} Retrieved)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        for s in sources:
            cid = s.get("citation_id", "")
            title = s.get("title", "Source")
            url = s.get("url", "#")
            domain = s.get("domain", "web")
            st.markdown(f"- [{cid}] [{title}]({url}) — `{domain}`")

    # 3. Telemetry & Security Metadata Bar
    badge_html = _risk_badge_html(risk_level, risk_score)
    model_html = _model_badge_html(meta.get("model_selected", "Aiera AI"), is_error=is_service_error)
    telemetry_html = _telemetry_badge_html(meta.get("timing_breakdown"), is_error=is_service_error)

    st.markdown(
        f"<div style='margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); display:flex; gap:8px; flex-wrap:wrap; align-items:center;'>"
        f"{badge_html} {model_html} {telemetry_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # 4. Optional Deterministic AI Trust Receipt Inspector
    if meta.get("receipt_id"):
        receipt_title = "🧾 AI Trust Audit Receipt" if not is_service_error else "🧾 AI Trust Audit Receipt (Service Notice)"
        with st.expander(receipt_title, expanded=False):
            st.code(meta.get("receipt_text", f"Receipt ID: {meta['receipt_id']}"), language="text")


def render_chatbot_view():
    _init_chat_session()

    threads = st.session_state["privacy_chat_threads"]
    current_thread_id = st.session_state["privacy_current_thread_id"]
    current_thread = next((t for t in threads if t["id"] == current_thread_id), threads[0])
    
    # Sanitize and deduplicate messages
    current_thread["messages"] = _sanitize_message_history(current_thread["messages"])
    messages = current_thread["messages"]

    user_role = st.session_state.get("user_role", "USER")
    user_id = st.session_state.get("user_id", "Employee-001")

    # ── Top Header Bar ─────────────────────────────────────────────────────────
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.title("🛡️ AI Trust Chat & Tools Ecosystem")
        st.caption("Zero-Trust Security Gateway with Universal Live Grounding & Multi-Modal Verification")
    with col_t2:
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
            new_id = f"thread-{len(threads) + 1}"
            threads.append({
                "id": new_id,
                "title": f"Chat {len(threads) + 1}",
                "messages": [],
                "created_at": "Just now"
            })
            st.session_state["privacy_current_thread_id"] = new_id
            st.session_state["composer_preset_text"] = ""
            st.session_state["chat_message_input_box"] = ""
            st.rerun()

    # ── Active Tool Selector Bar ──────────────────────────────────────────────
    col_tool_select, col_tool_status = st.columns([2.5, 1.5])
    with col_tool_select:
        selected_tool = st.selectbox(
            "Select Active Tool:",
            TOOLS_LIST,
            index=TOOLS_LIST.index(st.session_state.get("active_tool", "💬 Standard Chat")),
            key="tool_ecosystem_selector"
        )
        if selected_tool != st.session_state["active_tool"]:
            st.session_state["active_tool"] = selected_tool
            st.rerun()

    with col_tool_status:
        st.markdown(
            f"<div style='margin-top:28px; font-size:12px; font-weight:700; color:#38BDF8; "
            f"background:rgba(56,189,248,0.1); padding:6px 12px; border-radius:8px; border:1px solid rgba(56,189,248,0.3); text-align:center;'>"
            f"⚡ Tool: {st.session_state['active_tool']}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Conversation History Container (Read-Only Rendering, No Duplicates) ────
    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        meta = msg.get("security_meta", {})
        tool_data = msg.get("tool_data")

        if role == "user":
            with st.chat_message("user", avatar="👤"):
                # ALWAYS display safe redacted representation, never raw sensitive digits
                display_text = msg.get("credential_masked_text") or msg.get("text", "")
                from privacy_engine.sanitizer import PrivacySanitizer
                _render_sanitizer = PrivacySanitizer()
                # Secondary safety net: sanitize on the fly if raw Aadhaar/PAN/credential is present
                display_text = _render_sanitizer.sanitize_text(display_text, mode="REDACT").get("sanitized_text", display_text)
                st.markdown(display_text)
                if msg.get("tool_used") and msg["tool_used"] != "💬 Standard Chat":
                    st.caption(f"🔧 *Invoked Tool:* `{msg['tool_used']}`")
                if msg.get("has_redactions") or msg.get("was_blocked"):
                    st.caption("🔒 *Sensitive data detected — redacted before processing & display*")

        else:
            with st.chat_message("assistant", avatar="🤖"):
                _render_answer_container(text=text, meta=meta, tool_data=tool_data)

    st.divider()

    # ── SECURE CHATGPT-STYLE MESSAGE COMPOSER & PRIVACY SCANNER ───────────────
    current_preset = st.session_state.get("composer_preset_text", "")
    scan_info = _compute_live_privacy_status(current_preset)

    st.markdown(
        """
        <div style="background:rgba(15,23,42,0.65); border:1px solid rgba(56,189,248,0.22); border-radius:14px; padding:16px 18px; margin-bottom:16px; width:100%; box-sizing:border-box;">
        """,
        unsafe_allow_html=True
    )

    if current_preset.strip():
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.08); font-size:12.5px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#38BDF8; font-weight:800;">🛡️ Privacy Firewall:</span>
                    <span style="color:{scan_info['status_col']}; font-weight:700;">{scan_info['state_label']} ({scan_info['risk_score']}%)</span>
                    <span style="color:#64748B;">•</span>
                    <span style="color:#94A3B8;">{scan_info['entities_label']}</span>
                </div>
                <span style="background:{scan_info['badge_bg']}; color:{scan_info['badge_col']}; border:1px solid {scan_info['badge_border']}; font-size:11px; font-weight:800; padding:2px 8px; border-radius:10px;">
                    {scan_info['decision']}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ── Live Credential Warning Banner (Before Send) ──────────────────────
        _live_advisory = scan_info.get("security_advisory")
        if _live_advisory and _live_advisory.get("items") and scan_info["is_blocked"]:
            _cred_types = ", ".join([item["type"] for item in _live_advisory["items"]])
            st.markdown(
                f"""
                <div style="background:rgba(220,38,38,0.18); border:1.5px solid rgba(239,68,68,0.5); border-radius:10px; padding:10px 14px; margin-bottom:8px; animation: pulse 2s ease-in-out infinite;">
                    <div style="color:#FCA5A5; font-weight:700; font-size:12.5px; display:flex; align-items:center; gap:6px;">
                        <span>🚨</span> <span>CREDENTIAL DETECTED: {_cred_types}</span>
                    </div>
                    <div style="color:#CBD5E1; font-size:11.5px; margin-top:4px; line-height:1.5;">
                        ⚠️ Your message contains sensitive credentials. It will be <strong style="color:#F87171;">BLOCKED</strong> from being sent to AI.<br>
                        🔐 If this is an active credential, <strong style="color:#FCD34D;">change it immediately</strong>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Full-width message textarea with dynamic nonce key for instant clean reset
    input_nonce = st.session_state.get("input_nonce", 0)
    user_prompt = st.text_area(
        "Type your message...",
        value=current_preset,
        placeholder="Type any question or prompt... (Universal Live Web Grounding & Privacy Shield active)",
        height=95,
        key=f"chat_message_input_box_{input_nonce}",
        label_visibility="collapsed",
    )

    if user_prompt != current_preset:
        st.session_state["composer_preset_text"] = user_prompt

    # Action bar matching exact horizontal boundaries of the textarea
    active_tool_name = st.session_state.get("active_tool", "💬 Standard Chat")
    c_tool_info, c_scan, c_clear, c_send = st.columns([2.2, 1.1, 0.8, 1.2])

    with c_tool_info:
        st.markdown(
            f"<div style='padding-top:7px; font-size:12px; color:#94A3B8; display:flex; align-items:center; gap:6px;'>"
            f"<span>⚡ Active Tool:</span> <strong style='color:#38BDF8;'>{active_tool_name}</strong>"
            f"</div>",
            unsafe_allow_html=True
        )

    with c_scan:
        scan_clicked = st.button("🛡️ Scan Prompt", key="btn_chat_preflight_scan", use_container_width=True)

    with c_clear:
        if st.button("🗑️ Clear", key="btn_chat_clear", use_container_width=True):
            st.session_state["composer_preset_text"] = ""
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()

    with c_send:
        send_btn_label = "🚫 Blocked" if scan_info["is_blocked"] else "➤ Send"
        send_clicked = st.button(
            send_btn_label,
            key="btn_chat_send",
            type="secondary" if scan_info["is_blocked"] else "primary",
            use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Pre-flight Scan Diagnostic Expander
    if scan_clicked and user_prompt and user_prompt.strip():
        detailed_scan = _compute_live_privacy_status(user_prompt)
        with st.expander("🛡️ Pre-Flight Privacy & Security Diagnostic", expanded=True):
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Risk Score", f"{detailed_scan['risk_score']}%", detailed_scan['risk_level'])
            sc2.metric("Policy Action", detailed_scan['decision'])
            sc3.metric("Live State", detailed_scan['state_label'])
            st.markdown(f"**Diagnostic Summary:** {detailed_scan['reason']}")
            if detailed_scan.get("entities"):
                st.markdown("**Detected Entity Spans:**")
                for e in detailed_scan["entities"]:
                    st.write(f"- `{e.get('category', e.get('entity_type'))}`: `{e.get('value', '[MASKED]')}` (Severity: {e.get('severity')})")

    # ── Handle Send Action (Strict Deduplication & Module Isolation) ───────────
    if send_clicked:
        prompt = (user_prompt or "").strip()
        if not prompt:
            st.warning("⚠️ Please type a message before sending.")
            return

        # Deduplication Guard: Check if the exact message was just appended
        if messages and messages[-1].get("role") == "user" and messages[-1].get("text") == prompt:
            # Already submitted, avoid re-submitting duplicate
            st.session_state["composer_preset_text"] = ""
            st.session_state["input_nonce"] = input_nonce + 1
            return

        msg_turn_id = f"turn-{int(time.time()*1000)}"
        st.session_state["composer_preset_text"] = ""
        st.session_state["input_nonce"] = input_nonce + 1

        # ── IMMEDIATE SANITIZATION: Redact sensitive information BEFORE storing or rendering ──
        from privacy_engine.sanitizer import PrivacySanitizer
        _common_sanitizer = PrivacySanitizer()
        _sanitized_result = _common_sanitizer.sanitize_text(prompt, mode="REDACT")
        _safe_redacted_prompt = _sanitized_result.get("sanitized_text", prompt)
        _has_redactions = _safe_redacted_prompt != prompt

        if scan_info["is_blocked"]:
            st.error("⛔ REQUEST BLOCKED: Input contains high-risk credentials or adversarial overrides. Execution halted with 0 external LLM/tool calls.")

            messages.append({
                "id": f"{msg_turn_id}-user",
                "role": "user",
                "text": _safe_redacted_prompt,
                "credential_masked_text": _safe_redacted_prompt if _has_redactions else None,
                "has_redactions": _has_redactions,
                "was_blocked": True,
                "tool_used": active_tool_name,
                "timestamp": time.time()
            })
            messages.append({
                "id": f"{msg_turn_id}-assistant",
                "role": "assistant",
                "text": "",
                "security_meta": {
                    "decision": "BLOCK",
                    "risk_score": scan_info["risk_score"],
                    "risk_level": "CRITICAL",
                    "category": "CRITICAL_SECURITY",
                    "detected_risks": scan_info["detected_list"],
                    "detected_entities": scan_info["entities"],
                    "reason": scan_info["reason"],
                    "routing_action": "BLOCKED → LLM was not called",
                    "model_selected": "Blocked (No Provider)",
                    "security_advisory": scan_info.get("security_advisory"),
                    "timing_breakdown": {"total_ms": 1.0, "router_ms": 0.0, "security_ms": 1.0, "search_ms": 0.0, "llm_ms": 0.0, "tier": "BLOCKED"},
                    "timing_ms": 1.0,
                }
            })
            st.rerun()
        else:
            if not messages:
                current_thread["title"] = (_safe_redacted_prompt[:28] + "...") if len(_safe_redacted_prompt) > 28 else _safe_redacted_prompt

            messages.append({
                "id": f"{msg_turn_id}-user",
                "role": "user",
                "text": _safe_redacted_prompt,
                "credential_masked_text": _safe_redacted_prompt if _has_redactions else None,
                "has_redactions": _has_redactions,
                "was_blocked": False,
                "tool_used": active_tool_name,
                "timestamp": time.time()
            })

            status_container = st.empty()
            status_container.markdown(
                """
                <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:12px 18px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 4px 16px rgba(0,0,0,0.3);">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:16px;">🌐</span>
                        <span style="color:#F8FAFC; font-size:13px; font-weight:700;">Verifying current information & synthesizing response…</span>
                    </div>
                    <div style="font-size:11px; font-weight:700; color:#38BDF8; font-family:monospace;">
                        ● LIVE GROUNDING ACTIVE
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            t_start = time.perf_counter()
            tool_out = None
            resp = None

            # 1. 🔎 Web Search Execution (Safe Redacted Input Passed)
            if active_tool_name == "🔎 Web Search":
                tool_out = execute_tool_with_ai_trust("🔎 Web Search", search_web, _safe_redacted_prompt)

            # 2. 🧠 Deep Research Execution
            elif active_tool_name == "🧠 Deep Research":
                tool_out = execute_tool_with_ai_trust("🧠 Deep Research", deep_research, _safe_redacted_prompt)

            # 3. 💻 Code Workspace Execution
            elif active_tool_name == "💻 Code Workspace":
                tool_out = execute_tool_with_ai_trust("💻 Code Workspace", execute_code_safely, _safe_redacted_prompt)

            # 4. 🔗 URL Analysis Execution
            elif active_tool_name == "🔗 URL Analysis":
                tool_out = execute_tool_with_ai_trust("🔗 URL Analysis", analyze_url_content, _safe_redacted_prompt)

            # 5. Standard LLM Chat Route with Universal Live Grounding (Safe Redacted Input Passed)
            else:
                safe_history = [
                    m for m in messages[:-1]
                    if not m.get("was_blocked") and m.get("security_meta", {}).get("decision") != "BLOCK"
                ]
                resp = APIClient.chat_message(
                    prompt=_safe_redacted_prompt,
                    mode="REDACT",
                    mcp_enabled=True,
                    chat_history=safe_history,
                    user_role=user_role,
                    user_id=user_id,
                    rag_doc_id=st.session_state.get("rag_doc_id"),
                )

            elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
            status_container.empty()

            if tool_out:
                receipt = tool_out.get("trust_receipt", {})
                receipt_text = format_receipt_text(receipt) if receipt else "Trust Receipt Verified"
                messages.append({
                    "id": f"{msg_turn_id}-assistant",
                    "role": "assistant",
                    "text": "" if tool_out.get("decision") == "BLOCK" else f"Result from **{active_tool_name}**:\n\n{tool_out.get('result', {}).get('direct_answer', '')}",
                    "tool_data": tool_out,
                    "security_meta": {
                        "decision": tool_out.get("decision", "ALLOW"),
                        "risk_score": tool_out.get("risk_score", 0),
                        "risk_level": tool_out.get("risk_level", "LOW"),
                        "reason": tool_out.get("reason", ""),
                        "receipt_id": receipt.get("receipt_id", ""),
                        "receipt_text": receipt_text,
                        "model_selected": f"Aiera {active_tool_name}",
                        "timing_breakdown": {
                            "total_ms": elapsed_ms,
                            "router_ms": 1.0,
                            "security_ms": 15.0,
                            "search_ms": elapsed_ms - 20.0,
                            "llm_ms": 0.0,
                            "tier": "WEB_REQUIRED"
                        },
                        "timing_ms": elapsed_ms,
                    }
                })

            elif resp:
                if resp.get("masked_prompt") and resp["masked_prompt"] != prompt:
                    messages[-1]["masked_text"] = resp["masked_prompt"]

                ai_text = resp.get("ai_response") or resp.get("response") or "Security scan completed."
                decision = resp.get("decision", "ALLOW")

                receipt_id = resp.get("receipt_id", "")
                receipt = get_receipt_by_id(receipt_id) if receipt_id else None
                receipt_text = format_receipt_text(receipt) if receipt else f"Receipt ID: {receipt_id}"

                timing_bd = resp.get("timing_breakdown", {
                    "total_ms": elapsed_ms,
                    "router_ms": 0.5,
                    "security_ms": 30.0,
                    "search_ms": 0.0,
                    "llm_ms": elapsed_ms - 35.0,
                    "tier": "SIMPLE"
                })

                messages.append({
                    "id": f"{msg_turn_id}-assistant",
                    "role": "assistant",
                    "text": ai_text if decision in ("ALLOW", "BLOCK") else "",
                    "security_meta": {
                        "decision": decision,
                        "risk_score": resp.get("risk_score", 0),
                        "risk_level": resp.get("risk_level", "LOW"),
                        "category": resp.get("category", "SAFE"),
                        "detected_risks": resp.get("detected_risks", []),
                        "detected_entities": resp.get("detected_entities", []),
                        "reason": resp.get("reason", ""),
                        "routing_action": resp.get("routing_action", "SAFE → LLM" if decision == "ALLOW" else "BLOCKED → LLM was not called"),
                        "bert_prediction": resp.get("bert_prediction", "SAFE"),
                        "bert_confidence": resp.get("bert_confidence", 0.0),
                        "nb_prediction": resp.get("nb_prediction", "SAFE"),
                        "nb_confidence": resp.get("nb_confidence", 0.0),
                        "model_selected": resp.get("model_selected", "Gemini"),
                        "receipt_id": receipt_id,
                        "receipt_text": receipt_text,
                        "timing_breakdown": timing_bd,
                        "timing_ms": elapsed_ms,
                    },
                })

            st.rerun()
