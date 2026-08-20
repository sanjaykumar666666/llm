"""
Privacy & Routing Analysis Panel Component.
Renders structured evidence-based privacy intelligence with real ML signals.
File: frontend/components/analysis_panel.py
"""

import streamlit as st
from typing import Dict, Any, Optional

DECISION_COLORS = {
    "ALLOW": ("#10B981", "rgba(16,185,129,0.12)", "🟢"),
    "WARN":  ("#F59E0B", "rgba(245,158,11,0.12)", "🟡"),
    "MASK":  ("#06B6D4", "rgba(6,182,212,0.12)", "🛡️"),
    "BLOCK": ("#EF4444", "rgba(239,68,68,0.12)", "🔴"),
}


def render_live_analysis_panel(data: Optional[Dict[str, Any]] = None) -> None:
    """
    Renders structured Privacy & Routing Analysis:
      - Decision (ALLOW / WARN / BLOCK)
      - Risk Score (calculated %, 0% for clean)
      - BERT Result + Confidence
      - Naive Bayes Result + Confidence
      - Detected Risks
      - Evidence
      - Reason
      - Routing Action
    """
    st.markdown(
        "<div style='font-size:13px; font-weight:800; color:#94A3B8; "
        "letter-spacing:0.08em; margin-bottom:8px;'>PRIVACY & ROUTING ANALYSIS</div>",
        unsafe_allow_html=True,
    )

    if not data:
        st.info("Enter or load content to evaluate privacy risk.")
        return

    # Extract fields with safe defaults
    score = int(data.get("risk_score", data.get("risk_score_pct", 0)))
    decision = data.get("decision", data.get("action", "ALLOW")).upper()
    color, bg, icon = DECISION_COLORS.get(decision, ("#94A3B8", "rgba(148,163,184,0.12)", "⚪"))

    bert_pred = data.get("bert_prediction", "SAFE")
    bert_conf = data.get("bert_confidence", data.get("bert_score", 0.0))
    nb_pred = data.get("nb_prediction", "SAFE")
    nb_conf = data.get("nb_confidence", data.get("nb_score", 0.0))

    detected_risks = data.get("detected_risks", [])
    if not detected_risks:
        # Fallback to entities if detected_risks is not explicitly formatted
        ents = data.get("entities", data.get("detected_entities", data.get("sensitive_entities", [])))
        if ents:
            detected_risks = list(dict.fromkeys([
                e.get("category", e.get("entity_type", e.get("type", str(e)))) if isinstance(e, dict) else str(e)
                for e in ents
            ]))

    evidence = data.get("evidence", [])
    reason = data.get("reason", data.get("explanation", ""))
    if not reason:
        if decision == "ALLOW" or score == 0:
            reason = "No privacy-sensitive information was detected."
        elif decision == "BLOCK":
            reason = "The prompt contains high-risk authentication or sensitive information."
        else:
            reason = "Sensitive personal information was detected in the prompt."

    routing_action = data.get("routing_action", "")
    if not routing_action:
        if decision == "ALLOW":
            routing_action = "SAFE → LLM"
        elif decision == "BLOCK":
            routing_action = "BLOCKED → LLM was not called"
        else:
            routing_action = "SANITIZE → Masked payload to LLM"

    # ── Top Summary Card ───────────────────────────────────────────────────────
    st.markdown(
        f"<div style='background:{bg}; border:1px solid {color}44; border-radius:10px; "
        f"padding:12px; margin-bottom:12px;'>"
        f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
        f"<div><span style='font-size:11px; color:#94A3B8; font-weight:700;'>DECISION</span><br>"
        f"<strong style='color:{color}; font-size:16px;'>{icon} {decision}</strong></div>"
        f"<div style='text-align:right;'><span style='font-size:11px; color:#94A3B8; font-weight:700;'>RISK SCORE</span><br>"
        f"<strong style='color:{color}; font-size:18px;'>{score}%</strong></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # ── ML Models Breakdown ───────────────────────────────────────────────────
    st.markdown(
        "<div style='background:rgba(11,39,66,0.5); border:1px solid rgba(59,130,246,0.15); "
        "border-radius:10px; padding:10px 12px; margin-bottom:10px; font-size:12px;'>"
        f"<div style='margin-bottom:4px;'><strong style='color:#E2E8F0;'>BERT:</strong> "
        f"<span style='color:{'#10B981' if bert_pred == 'SAFE' else '#EF4444'}; font-weight:700;'>{bert_pred}</span> "
        f"<span style='color:#64748B;'>(conf: {bert_conf * 100:.1f}%)</span></div>"
        f"<div><strong style='color:#E2E8F0;'>Naive Bayes:</strong> "
        f"<span style='color:{'#10B981' if nb_pred == 'SAFE' else '#EF4444'}; font-weight:700;'>{nb_pred}</span> "
        f"<span style='color:#64748B;'>(conf: {nb_conf * 100:.1f}%)</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Detected Risks ────────────────────────────────────────────────────────
    st.markdown("**Detected Risks:**")
    if detected_risks:
        for r in detected_risks:
            st.markdown(f"- ⚠️ <span style='color:#FCA5A5; font-size:13px;'>{r}</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#10B981; font-size:13px;'>None</span>", unsafe_allow_html=True)

    # ── Evidence ──────────────────────────────────────────────────────────────
    if evidence:
        st.markdown("**Evidence:**")
        for ev in evidence:
            st.markdown(f"<div style='color:#94A3B8; font-size:11px; margin-bottom:2px;'>• {ev}</div>", unsafe_allow_html=True)

    # ── Reason ────────────────────────────────────────────────────────────────
    st.markdown("**Reason:**")
    st.markdown(f"<div style='color:#CBD5E1; font-size:12px;'>{reason}</div>", unsafe_allow_html=True)

    # ── Routing Action ────────────────────────────────────────────────────────
    st.markdown("**Routing:**")
    st.markdown(
        f"<div style='background:rgba(255,255,255,0.05); border:1px solid {color}33; "
        f"color:{color}; font-size:12px; font-weight:700; padding:6px 10px; border-radius:8px;'>"
        f"{routing_action}</div>",
        unsafe_allow_html=True,
    )
