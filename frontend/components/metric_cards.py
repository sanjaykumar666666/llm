"""
Metric Cards Component.
File: frontend/components/metric_cards.py
"""

import streamlit as st

def render_metric_card(val, label: str, color: str = "#38BDF8") -> None:
    """Renders styled metric card container."""
    st.markdown(f"""
    <div class="ps-metric-card">
        <div class="ps-metric-val" style="color: {color};">{val}</div>
        <div class="ps-metric-lbl">{label}</div>
    </div>
    """, unsafe_allow_html=True)
