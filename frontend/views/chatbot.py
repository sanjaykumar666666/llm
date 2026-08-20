"""
AI Trust Chat — Secure Chat View with Aiera Multi-Modal Tools Ecosystem.
File Location: frontend/views/chatbot.py
"""

import streamlit as st
import time
import io
import json
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
    if "chat_threads" not in st.session_state:
        st.session_state["chat_threads"] = [{
            "id": "thread-1",
            "title": "Welcome Thread",
            "messages": [],
            "created_at": "Just now"
        }]
    if "current_thread_id" not in st.session_state:
        st.session_state["current_thread_id"] = "thread-1"
    if "composer_preset_text" not in st.session_state:
        st.session_state["composer_preset_text"] = ""
    if "active_tool" not in st.session_state:
        st.session_state["active_tool"] = "💬 Standard Chat"
    if "canvas_content" not in st.session_state:
        st.session_state["canvas_content"] = "### Executive Research Document\n\nEnter your notes, architecture designs, or code snippets here..."


def _compute_live_privacy_status(text: str) -> Dict[str, Any]:
    """
    Computes real-time privacy risk, detected PII entities, and policy decision
    before the user sends a message.
    """
    if not text or not text.strip():
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "decision": "ALLOW",
            "entities_label": "None (Clean)",
            "status_col": "#10B981",
            "badge_bg": "rgba(16,185,129,0.12)",
            "badge_col": "#10B981",
            "badge_border": "rgba(16,185,129,0.35)",
            "detected_list": [],
            "reason": "Input is clean and contains no sensitive entities.",
            "entities": []
        }

    # 1. Regex PII & Entropy
    tp = TextProcessor()
    proc = tp.process(text)
    entities = proc.get("detected_entities", [])
    entity_types = proc.get("detected_entity_types", [])

    # 2. Injection Check
    is_inj, inj_conf, inj_pattern = _detect_injection(text)
    if is_inj:
        entity_types.append("PROMPT_INJECTION")

    # 3. Calculate Risk Score & Decision
    if is_inj:
        risk_score = int(round(inj_conf * 100))
        risk_level = "CRITICAL"
        decision = "BLOCK"
        reason = f"Adversarial prompt injection pattern detected ('{inj_pattern}')."
    elif any(e.get("severity", 0) >= 0.90 for e in entities):
        risk_score = 92
        risk_level = "CRITICAL"
        decision = "BLOCK"
        reason = f"High-risk confidential secret / credential detected: {', '.join(entity_types)}."
    elif entities:
        max_sev = max(e.get("severity", 0.5) for e in entities)
        risk_score = int(round(max_sev * 100))
        risk_level = "HIGH" if risk_score >= 70 else "MEDIUM"
        decision = "SANITIZE"
        reason = f"Personal identifiable information (PII) detected ({', '.join(entity_types)}) — will be sanitized before LLM transmission."
    else:
        risk_score = 0
        risk_level = "LOW"
        decision = "ALLOW"
        reason = "Input is clean and safe for processing."

    # Visual tokens
    if decision == "BLOCK":
        status_col = "#EF4444"
        badge_bg = "rgba(239,68,68,0.15)"
        badge_col = "#EF4444"
        badge_border = "rgba(239,68,68,0.4)"
    elif decision == "SANITIZE":
        status_col = "#F59E0B"
        badge_bg = "rgba(245,158,11,0.15)"
        badge_col = "#F59E0B"
        badge_border = "rgba(245,158,11,0.4)"
    else:
        status_col = "#10B981"
        badge_bg = "rgba(16,185,129,0.15)"
        badge_col = "#10B981"
        badge_border = "rgba(16,185,129,0.4)"

    entities_label = ", ".join(entity_types) if entity_types else "None (Clean)"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "decision": decision,
        "entities_label": entities_label,
        "status_col": status_col,
        "badge_bg": badge_bg,
        "badge_col": badge_col,
        "badge_border": badge_border,
        "detected_list": entity_types,
        "reason": reason,
        "entities": entities,
        "entropy": proc.get("shannon_entropy", 0.0),
    }


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


def _model_badge_html(model_name: str) -> str:
    return (
        f"<span style='background:rgba(99,102,241,0.12); color:#A5B4FC; border:1px solid rgba(99,102,241,0.3); "
        f"font-size:11px; font-weight:600; padding:3px 8px; border-radius:20px;'>"
        f"🤖 {model_name}"
        f"</span>"
    )


def _telemetry_badge_html(timing: Optional[Dict[str, Any]]) -> str:
    if not timing:
        return ""
    total_s = timing.get("total_ms", 0) / 1000.0
    r_ms = timing.get("router_ms", 0)
    sec_ms = timing.get("security_ms", 0)
    search_ms = timing.get("search_ms", 0)
    llm_ms = timing.get("llm_ms", 0)
    tier = timing.get("tier", "SIMPLE")

    tier_color = "#38BDF8" if tier == "SIMPLE" else ("#F59E0B" if tier == "WEB_REQUIRED" else "#A78BFA")

    parts = [f"⚡ <strong>{total_s:.2f}s</strong>", f"<span style='color:{tier_color};'>[{tier}]</span>", f"Router: {r_ms:.1f}ms", f"Sec: {sec_ms:.1f}ms"]
    if search_ms > 0:
        parts.append(f"Search: {search_ms:.0f}ms")
    if llm_ms > 0:
        parts.append(f"LLM: {llm_ms/1000.0:.2f}s")

    return (
        f"<span style='background:rgba(15,23,42,0.8); color:#94A3B8; border:1px solid rgba(56,189,248,0.25); "
        f"font-size:11px; font-family:monospace; padding:3px 10px; border-radius:20px;'>"
        f"{' | '.join(parts)}"
        f"</span>"
    )


def render_chatbot_view():
    _init_chat_session()

    current_thread_id = st.session_state["current_thread_id"]
    current_thread = next(
        (t for t in st.session_state["chat_threads"] if t["id"] == current_thread_id),
        st.session_state["chat_threads"][0]
    )
    messages = current_thread["messages"]

    user_role = st.session_state.get("user_role", "USER")
    user_id = st.session_state.get("user_id", "Employee-001")

    # ── Top Header Bar ─────────────────────────────────────────────────────────
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.title("🛡️ AI Trust Chat & Tools Ecosystem")
        st.caption("Zero-Trust Security Gateway with Real Multi-Modal Tools Execution")
    with col_t2:
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
            new_id = f"thread-{len(st.session_state['chat_threads']) + 1}"
            st.session_state["chat_threads"].append({
                "id": new_id,
                "title": f"Chat {len(st.session_state['chat_threads']) + 1}",
                "messages": [],
                "created_at": "Just now"
            })
            st.session_state["current_thread_id"] = new_id
            st.session_state["composer_preset_text"] = ""
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

    # ── Welcome empty state ───────────────────────────────────────────────────
    if not messages:
        st.markdown(
            "<div style='background:rgba(15,23,42,0.6); border:1px solid rgba(59,130,246,0.2); "
            "border-radius:14px; padding:18px; margin-bottom:16px;'>"
            "<h4 style='margin:0 0 8px 0; color:#F8FAFC;'>🔒 Zero-Trust AI Assistant & Multi-Modal Tools</h4>"
            "<p style='color:#94A3B8; font-size:13px; margin:0;'>"
            "Select any tool from the dropdown above or type in the composer below. "
            "Every tool invocation is protected by character-level live privacy scans and cryptographic Trust Receipts."
            "</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("**🧪 Quick Test Prompts (Click to Load):**")
        chip_cols = st.columns(4)
        for i, (label, prompt_sample) in enumerate(QUICK_TEST_CHIPS[:4]):
            with chip_cols[i % 4]:
                if st.button(label, key=f"chip_{i}", use_container_width=True):
                    st.session_state["composer_preset_text"] = prompt_sample
                    st.rerun()

        chip_cols2 = st.columns(3)
        for i, (label, prompt_sample) in enumerate(QUICK_TEST_CHIPS[4:]):
            with chip_cols2[i % 3]:
                if st.button(label, key=f"chip_row2_{i}", use_container_width=True):
                    st.session_state["composer_preset_text"] = prompt_sample
                    st.rerun()

        st.divider()

    # ── Conversation History Container ─────────────────────────────────────────
    for idx, msg in enumerate(messages):
        role = msg["role"]
        text = msg["text"]
        meta = msg.get("security_meta", {})
        tool_data = msg.get("tool_data")

        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(text)
                if msg.get("tool_used") and msg["tool_used"] != "💬 Standard Chat":
                    st.caption(f"🔧 *Invoked Tool:* `{msg['tool_used']}`")
                if msg.get("masked_text") and msg["masked_text"] != text:
                    st.caption(f"🛡️ *Sent to AI (masked):* `{msg['masked_text'][:120]}...`")

        else:
            decision = meta.get("decision", "ALLOW")
            risk_level = meta.get("risk_level", "LOW")
            risk_score = meta.get("risk_score", 0)

            with st.chat_message("assistant", avatar="🤖"):

                # ── Tool Result Renderers ─────────────────────────────────────
                if tool_data:
                    t_name = tool_data.get("tool_name")

                    # 1. 🔎 Web Search Card
                    if t_name == "🔎 Web Search" and tool_data.get("result"):
                        res = tool_data["result"]
                        timing = res.get("timing_ms", {})
                        
                        st.markdown(
                            f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>"
                            f"<h3 style='margin:0; color:#38BDF8;'>🔎 Web Search: <em>'{res.get('query')}'</em></h3>"
                            f"<span style='font-size:11px; color:#94A3B8; background:rgba(56,189,248,0.1); padding:3px 8px; border-radius:12px; border:1px solid rgba(56,189,248,0.3);'>"
                            f"⚡ {timing.get('total_ms', 0)} ms (Search: {timing.get('search_ms', 0)}ms | Answer: {timing.get('generation_ms', 0)}ms)"
                            f"</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                        # Direct Grounded Answer
                        st.markdown("#### Answer")
                        st.markdown(res.get("direct_answer", ""))

                        # Verified Sources & Evidence
                        if res.get("sources"):
                            st.markdown("#### Sources")
                            for s in res["sources"]:
                                st.markdown(
                                    f"**[{s['citation_id']}] [{s['title']}]({s['url']})** (`{s['domain']}`) — "
                                    f"<span style='color:#10B981; font-size:12px; font-weight:600;'>{s.get('relevance_score', '')} Match</span>",
                                    unsafe_allow_html=True
                                )
                                with st.expander(f"📖 View Retrieved Passage Evidence for [{s['citation_id']}]", expanded=False):
                                    st.write(s.get("retrieved_passage", s.get("snippet", "")))

                    # 2. 🧠 Deep Research Card
                    elif t_name == "🧠 Deep Research" and tool_data.get("result"):
                        res = tool_data["result"]
                        st.markdown(f"### 🧠 Deep Research Report: *'{res.get('query')}'*")
                        
                        with st.status("🔬 Agentic Research Workflow Completed", state="complete"):
                            for step in res.get("steps_log", []):
                                st.write(f"✓ **{step['phase']}** ({step['progress']}%) — {step['detail']}")

                        st.markdown("#### Executive Summary")
                        st.info(res.get("executive_summary", ""))

                        st.markdown("#### Key Findings")
                        for kf in res.get("key_findings", []):
                            st.markdown(f"- {kf}")

                        with st.expander("📖 Comprehensive Analysis Sections", expanded=False):
                            for sec in res.get("detailed_sections", []):
                                st.markdown(f"**{sec['heading']}**")
                                st.markdown(sec["content"])
                                st.divider()

                        if res.get("citations"):
                            st.markdown("#### Sources Consulted")
                            for cit in res["citations"]:
                                st.markdown(f"- {cit['id']} **[{cit['title']}]({cit['url']})** ({cit['domain']})")

                    # 3. 📊 Data Analysis Card
                    elif t_name == "📊 Data Analysis" and tool_data.get("result"):
                        res = tool_data["result"]
                        st.markdown(f"### 📊 Tabular Data Analytics: *'{res.get('filename')}'*")
                        st.markdown(f"**Dimensions:** {res.get('rows')} rows × {len(res.get('columns', []))} columns | **Missing Values:** {res.get('total_missing_values')}")
                        
                        # Summary stats dataframe
                        if res.get("summary_statistics"):
                            st.markdown("#### Numeric Summary Statistics")
                            st.dataframe(pd.DataFrame(res["summary_statistics"]).T, use_container_width=True)

                        # Preview records
                        if res.get("preview_records"):
                            with st.expander("👀 View Dataset Records", expanded=False):
                                st.dataframe(pd.DataFrame(res["preview_records"]), use_container_width=True)

                    # 4. 💻 Code Workspace Card
                    elif t_name == "💻 Code Workspace" and tool_data.get("result"):
                        res = tool_data["result"]
                        st.markdown("### 💻 Sandboxed Code Execution Result")
                        if res.get("status") == "SUCCESS":
                            st.code(res.get("output", ""), language="python")
                            st.caption(f"⚡ Execution Latency: {res.get('execution_time_ms')} ms")
                        else:
                            st.error(f"Execution Status: {res.get('status')} — {res.get('error', 'Execution halted.')}")

                    # 5. 🔗 URL Analysis Card
                    elif t_name == "🔗 URL Analysis" and tool_data.get("result"):
                        res = tool_data["result"]
                        st.markdown(f"### 🔗 URL Content Analysis: [{res.get('domain')}]({res.get('url')})")
                        st.markdown(f"**Page Title:** *{res.get('title')}*")
                        st.info(res.get("content_preview", "")[:600] + "...")

                    # 6. Generic Text Output
                    elif text:
                        st.markdown(text)

                # ── Standard AI Chat / Security Output ────────────────────────
                elif decision == "BLOCK":
                    st.markdown(
                        f"<div style='background:rgba(220,38,38,0.1); border:1px solid rgba(220,38,38,0.4); "
                        f"border-radius:12px; padding:16px;'>"
                        f"<strong style='color:#FCA5A5;'>🔒 Zero-Trust Security Gate: Request Blocked</strong><br>"
                        f"<p style='color:#94A3B8; font-size:13px; margin:8px 0 0 0;'>{text or meta.get('reason', 'Blocked by security policy.')}</p>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(text)

                # ── Security & Telemetry Metadata Bar ──────────────────────────
                if meta:
                    badge_html = _risk_badge_html(risk_level, risk_score)
                    model_html = _model_badge_html(meta.get("model_selected", "Aiera AI"))
                    telemetry_html = _telemetry_badge_html(meta.get("timing_breakdown"))
                    st.markdown(
                        f"<div style='margin-top:8px; display:flex; gap:8px; flex-wrap:wrap; align-items:center;'>"
                        f"{badge_html} {model_html} {telemetry_html}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # ── Trust Receipt Expander ─────────────────────────────────────
                if meta.get("receipt_id"):
                    with st.expander("🧾 Cryptographic AI Trust Receipt", expanded=False):
                        st.code(meta.get("receipt_text", f"Receipt ID: {meta['receipt_id']}"), language="text")

    # ── Specialized Tool Modals (File Upload / Canvas / Code Editor) ───────────
    active_tool_name = st.session_state.get("active_tool", "💬 Standard Chat")
    
    # ── Upload Drawer for Files / Data Analysis / Image Analysis ───────────────
    if active_tool_name in ("📎 Files Parser", "📊 Data Analysis", "🖼️ Image Analysis", "📚 Knowledge Base / RAG"):
        with st.expander(f"📁 Upload File for {active_tool_name}", expanded=True):
            uploaded_file = st.file_uploader(
                f"Select file to process with {active_tool_name}:",
                type=["csv", "xlsx", "pdf", "docx", "txt", "json", "png", "jpg"],
                key="ecosystem_file_uploader"
            )
            if uploaded_file and st.button(f"⚡ Execute {active_tool_name} on File", type="primary", key="exec_file_tool_btn"):
                with st.spinner(f"Running {active_tool_name} with Zero-Trust AI Privacy Gate..."):
                    file_bytes = uploaded_file.read()
                    
                    if active_tool_name == "📊 Data Analysis":
                        tool_out = execute_tool_with_ai_trust("📊 Data Analysis", analyze_dataset, file_bytes, uploaded_file.name)
                    elif active_tool_name == "🖼️ Image Analysis":
                        tool_out = execute_tool_with_ai_trust("🖼️ Image Analysis", analyze_image_bytes, file_bytes)
                    else:
                        tool_out = execute_tool_with_ai_trust("📎 Files Parser", process_file_content, file_bytes, uploaded_file.name)

                    # Append to chat
                    messages.append({
                        "role": "user",
                        "text": f"[{active_tool_name}] Processed file: {uploaded_file.name}",
                        "tool_used": active_tool_name
                    })

                    receipt = tool_out.get("trust_receipt", {})
                    receipt_text = format_receipt_text(receipt) if receipt else "Trust Receipt Verified"

                    messages.append({
                        "role": "assistant",
                        "text": f"Completed execution for **{active_tool_name}**.",
                        "tool_data": tool_out,
                        "security_meta": {
                            "decision": tool_out.get("decision", "ALLOW"),
                            "risk_score": tool_out.get("risk_score", 0),
                            "risk_level": tool_out.get("risk_level", "LOW"),
                            "receipt_id": receipt.get("receipt_id", ""),
                            "receipt_text": receipt_text,
                            "model_selected": f"Aiera {active_tool_name}"
                        }
                    })
                    st.rerun()

    # ── Canvas Interactive Document Editor ─────────────────────────────────────
    elif active_tool_name == "✍️ Canvas Workspace":
        with st.expander("✍️ Canvas Interactive Workspace", expanded=True):
            st.session_state["canvas_content"] = st.text_area(
                "Document Scratchpad:",
                value=st.session_state.get("canvas_content", ""),
                height=180,
                key="canvas_text_area"
            )
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1:
                if st.button("✨ Rewrite", key="canvas_rewrite"):
                    st.session_state["canvas_content"] = canvas_engine.transform_text(st.session_state["canvas_content"], "REWRITE")
                    st.rerun()
            with col_c2:
                if st.button("✂️ Shorten", key="canvas_shorten"):
                    st.session_state["canvas_content"] = canvas_engine.transform_text(st.session_state["canvas_content"], "SHORTEN")
                    st.rerun()
            with col_c3:
                if st.button("📖 Expand", key="canvas_expand"):
                    st.session_state["canvas_content"] = canvas_engine.transform_text(st.session_state["canvas_content"], "EXPAND")
                    st.rerun()
            with col_c4:
                if st.button("💎 Improve", key="canvas_improve"):
                    st.session_state["canvas_content"] = canvas_engine.transform_text(st.session_state["canvas_content"], "IMPROVE")
                    st.rerun()

    st.divider()

    # ── SECURE CHATGPT-STYLE MESSAGE COMPOSER & PRIVACY SCANNER ───────────────
    # Read preset text if any (e.g. from test chips or dashboard)
    current_preset = st.session_state.get("composer_preset_text", "")

    # Compute live privacy analysis for the current text
    scan_info = _compute_live_privacy_status(current_preset)

    # 1. Real-time Live Security Status Strip
    st.markdown(
        f"""
        <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(56,189,248,0.25); border-radius:12px; padding:10px 16px; margin-bottom:8px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; box-shadow:0 4px 14px rgba(0,0,0,0.25);">
            <div style="display:flex; align-items:center; gap:10px; font-size:12.5px; flex-wrap:wrap;">
                <span style="color:#38BDF8; font-weight:800; display:flex; align-items:center; gap:4px;">🛡️ AI TRUST</span>
                <span style="color:#64748B;">|</span>
                <span style="color:{scan_info['status_col']}; font-weight:700;">Risk: {scan_info['risk_score']}% ({scan_info['risk_level']})</span>
                <span style="color:#64748B;">|</span>
                <span style="color:#CBD5E1;">Detected: <strong style="color:#F1F5F9;">{scan_info['entities_label']}</strong></span>
            </div>
            <span style="background:{scan_info['badge_bg']}; color:{scan_info['badge_col']}; border:1px solid {scan_info['badge_border']}; font-size:11px; font-weight:800; padding:3px 10px; border-radius:12px;">
                ● {scan_info['decision']}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Main Secure Composer Form & Action Bar
    with st.container():
        # Large message input area
        user_prompt = st.text_area(
            "Type your secure message...",
            value=current_preset,
            placeholder="Type your secure message... (real-time privacy scan and zero-trust gateway active)",
            height=90,
            key="chat_message_input_box",
            label_visibility="collapsed",
        )

        # Synchronize preset text if user edited
        if user_prompt != current_preset:
            st.session_state["composer_preset_text"] = user_prompt

        # Action bar with Tool Indicator, Scan, Clear, and Send Button
        c_tool_info, c_scan, c_clear, c_send = st.columns([2.5, 1.1, 0.8, 1.2])

        with c_tool_info:
            st.markdown(
                f"<div style='padding-top:8px; font-size:12px; color:#94A3B8; display:flex; align-items:center; gap:6px;'>"
                f"<span>⚡ Active Tool:</span> <strong style='color:#38BDF8;'>{active_tool_name}</strong>"
                f"</div>",
                unsafe_allow_html=True
            )

        with c_scan:
            scan_clicked = st.button("🛡️ Scan Prompt", key="btn_chat_preflight_scan", use_container_width=True)

        with c_clear:
            if st.button("🗑️ Clear", key="btn_chat_clear", use_container_width=True):
                st.session_state["composer_preset_text"] = ""
                st.rerun()

        with c_send:
            send_clicked = st.button("➤ Send", key="btn_chat_send", type="primary", use_container_width=True)

    # 3. Optional Pre-flight Scan Detailed Inspection
    if scan_clicked and user_prompt and user_prompt.strip():
        detailed_scan = _compute_live_privacy_status(user_prompt)
        with st.expander("🛡️ Pre-Flight Privacy & Security Diagnostic", expanded=True):
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Risk Score", f"{detailed_scan['risk_score']}%", detailed_scan['risk_level'])
            sc2.metric("Policy Action", detailed_scan['decision'])
            sc3.metric("Shannon Entropy", f"{detailed_scan.get('entropy', 0.0):.2f} bits")
            st.markdown(f"**Diagnostic Summary:** {detailed_scan['reason']}")
            if detailed_scan.get("entities"):
                st.markdown("**Detected Entity Spans:**")
                for e in detailed_scan["entities"]:
                    st.write(f"- `{e['entity_type']}`: `{e['value']}` (Severity: {e['severity']})")

    # 4. Handle Send Action
    if send_clicked:
        prompt = (user_prompt or "").strip()
        if not prompt:
            st.warning("⚠️ Please type a secure message before sending.")
        else:
            # Clear preset text so it won't duplicate on next turn
            st.session_state["composer_preset_text"] = ""

            if not messages:
                current_thread["title"] = (prompt[:28] + "...") if len(prompt) > 28 else prompt

            messages.append({"role": "user", "text": prompt, "tool_used": active_tool_name})

            # Live Processing Status Banner
            status_container = st.empty()
            status_container.markdown(
                """
                <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:10px 14px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:16px;">⚡</span>
                        <span style="color:#F8FAFC; font-size:12.5px; font-weight:700;">Zero-Trust Security Gateway Processing...</span>
                    </div>
                    <div style="display:flex; gap:8px; font-size:11px; font-weight:700;">
                        <span style="color:#06B6D4;">● Router</span> ➔
                        <span style="color:#10B981;">● Security</span> ➔
                        <span style="color:#A78BFA;">● Reasoning</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            t_start = time.perf_counter()
            tool_out = None
            resp = None

            # 1. 🔎 Web Search Execution
            if active_tool_name == "🔎 Web Search":
                tool_out = execute_tool_with_ai_trust("🔎 Web Search", search_web, prompt)

            # 2. 🧠 Deep Research Execution
            elif active_tool_name == "🧠 Deep Research":
                tool_out = execute_tool_with_ai_trust("🧠 Deep Research", deep_research, prompt)

            # 3. 💻 Code Workspace Execution
            elif active_tool_name == "💻 Code Workspace":
                tool_out = execute_tool_with_ai_trust("💻 Code Workspace", execute_code_safely, prompt)

            # 4. 🔗 URL Analysis Execution
            elif active_tool_name == "🔗 URL Analysis":
                tool_out = execute_tool_with_ai_trust("🔗 URL Analysis", analyze_url_content, prompt)

            # 5. 🎨 Image Generation Bridge
            elif active_tool_name == "🎨 Image Generation":
                tool_out = execute_tool_with_ai_trust("🎨 Image Generation", generate_image_bridge, prompt)

            # 6. Standard LLM Chat Route (Ultra-Fast)
            else:
                resp = APIClient.chat_message(
                    prompt=prompt,
                    mode="REDACT",
                    mcp_enabled=True,
                    chat_history=messages,
                    user_role=user_role,
                    user_id=user_id,
                    rag_doc_id=st.session_state.get("rag_doc_id"),
                )

            elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
            status_container.empty()

            # Handle Tool Response
            if tool_out:
                receipt = tool_out.get("trust_receipt", {})
                receipt_text = format_receipt_text(receipt) if receipt else "Trust Receipt Verified"

                timing_bd = {
                    "total_ms": elapsed_ms,
                    "router_ms": 1.0,
                    "security_ms": 15.0,
                    "search_ms": elapsed_ms - 20.0 if "Search" in active_tool_name else 0.0,
                    "llm_ms": 0.0,
                    "tier": "MULTIMODAL" if "Search" not in active_tool_name else "WEB_REQUIRED"
                }

                messages.append({
                    "role": "assistant",
                    "text": "" if tool_out.get("decision") == "BLOCK" else f"Result from **{active_tool_name}**:",
                    "tool_data": tool_out,
                    "security_meta": {
                        "decision": tool_out.get("decision", "ALLOW"),
                        "risk_score": tool_out.get("risk_score", 0),
                        "risk_level": tool_out.get("risk_level", "LOW"),
                        "reason": tool_out.get("reason", ""),
                        "receipt_id": receipt.get("receipt_id", ""),
                        "receipt_text": receipt_text,
                        "model_selected": f"Aiera {active_tool_name}",
                        "timing_breakdown": timing_bd,
                        "timing_ms": elapsed_ms,
                    }
                })

            # Handle Standard LLM Response
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

                security_meta = {
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
                }

                messages.append({
                    "role": "assistant",
                    "text": ai_text if decision in ("ALLOW", "BLOCK") else "",
                    "security_meta": security_meta,
                })

            st.rerun()
