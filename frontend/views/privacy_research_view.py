"""
Privacy Research & Empirical Benchmarking Dashboard View.
File Location: frontend/views/privacy_research_view.py

Features:
  1. Policy Mode Controls (Strict, Balanced, Utility-Focused).
  2. Live Prompt Privacy Sanitization & Redacted Output Preview.
  3. Model Ablation Study Runner (DistilBERT vs Naive Bayes vs Hybrid Ensemble).
  4. Privacy Attack & Red-Teaming Benchmark Suite.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from privacy_engine.evaluator import PolicyEvaluator, PolicyMode
from privacy_engine import run_full_analysis
from ml_engine.ablation_evaluator import ModelAblationBenchmarker
from privacy_engine.privacy_attack_bench import PrivacyAttackBenchmarker
from frontend.utils.theme_manager import get_current_theme


def render_privacy_research_view():
    st.markdown("## 🔬 LLM Prompt Privacy Research & Benchmarking Center")
    st.markdown(
        "Empirical evaluation suite for **Hybrid BERT + Naive Bayes** prompt privacy prediction, "
        "smart redaction, policy enforcement, and security attack resilience."
    )

    theme = get_current_theme()

    # ── TAB LAYOUT ────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "🛡️ Policy & Redaction Lab",
        "📊 Model Ablation Study",
        "⚡ Privacy Attack Suite"
    ])

    # ── TAB 1: POLICY & REDACTION LAB ─────────────────────────────────────────
    with tab1:
        st.markdown("### Interactive Policy Engine & Smart Redactor")
        st.markdown(
            "Test prompt privacy classification with policy presets (**Strict**, **Balanced**, **Utility-Focused**)."
        )

        col_policy, col_thresh = st.columns([1, 2])
        with col_policy:
            policy_choice = st.selectbox(
                "Select Policy Mode:",
                ["BALANCED", "STRICT", "UTILITY"],
                index=0,
                key="policy_mode_choice"
            )
            mode_enum = PolicyMode[policy_choice]
            evaluator = PolicyEvaluator(policy_mode=mode_enum)

            st.caption(
                f"**{policy_choice} Mode:** "
                + ("Blocks on any detected entity or risk." if policy_choice == "STRICT"
                   else "Redacts light PII (email/phone), blocks critical credentials." if policy_choice == "BALANCED"
                   else "Prioritizes user prompt preservation, redacts only critical secrets.")
            )

        test_prompt = st.text_area(
            "Enter prompt for live policy evaluation:",
            value="My SSN is 123-45-6789 and email is sarah.connor@cyberdyne.com. Can you review this code?",
            height=100,
            key="research_test_prompt"
        )

        if st.button("🔍 Run Full Privacy Analysis", type="primary", key="btn_run_analysis"):
            if not test_prompt.strip():
                st.warning("Please enter a non-empty prompt.")
            else:
                with st.spinner("Executing Context Detection, Hybrid ML & Policy Engine..."):
                    res = run_full_analysis(test_prompt)
                    sanit_res = res.get("sanitization", {})
                    eval_res = res.get("policy_evaluation", {})

                    st.markdown("---")
                    res_col1, res_col2, res_col3 = st.columns(3)
                    with res_col1:
                        st.metric("Final Policy Decision", eval_res.get("decision", "UNKNOWN"))
                    with res_col2:
                        st.metric("Privacy Risk Score", f"{res.get('risk_score', 0.0) * 100:.1f}%")
                    with res_col3:
                        st.metric("Hybrid Classifier", res.get("hybrid_ml", {}).get("predicted_class", "SAFE"))

                    st.markdown("#### 📝 Smart Redacted Prompt Preview")
                    st.code(sanit_res.get("sanitized_prompt", test_prompt), language="markdown")

                    entities = res.get("detected_entities", {})
                    if entities:
                        st.markdown("#### 🔍 Detected Sensitive Entities")
                        st.json(entities)

    # ── TAB 2: MODEL ABLATION STUDY ──────────────────────────────────────────
    with tab2:
        st.markdown("### Model Ablation Benchmarking Suite")
        st.markdown(
            "Measures empirical classification accuracy, F1-Score, latency, and memory memory footprints "
            "across **DistilBERT-only**, **Naive Bayes-only**, and **Hybrid Ensemble**."
        )

        if st.button("🚀 Run Empirical Ablation Experiment", key="btn_run_ablation"):
            with st.spinner("Evaluating models on canonical dataset (300+ samples)..."):
                benchmarker = ModelAblationBenchmarker()
                ablation_data = benchmarker.run_ablation_study()

                st.session_state["ablation_results"] = ablation_data

        if "ablation_results" in st.session_state:
            ab_res = st.session_state["ablation_results"]
            models = ab_res["models"]

            df_summary = pd.DataFrame({
                "Model Architecture": ["DistilBERT Only", "Naive Bayes Only", "Hybrid Ensemble (0.60/0.40)"],
                "Accuracy (%)": [models["distilbert_only"]["accuracy"], models["naive_bayes_only"]["accuracy"], models["hybrid_ensemble"]["accuracy"]],
                "F1-Score (Weighted %)": [models["distilbert_only"]["f1_weighted"], models["naive_bayes_only"]["f1_weighted"], models["hybrid_ensemble"]["f1_weighted"]],
                "F1-Score (Macro %)": [models["distilbert_only"]["f1_macro"], models["naive_bayes_only"]["f1_macro"], models["hybrid_ensemble"]["f1_macro"]],
                "Mean Latency (ms)": [models["distilbert_only"]["avg_latency_ms"], models["naive_bayes_only"]["avg_latency_ms"], models["hybrid_ensemble"]["avg_latency_ms"]],
            })

            st.markdown("#### 📈 Empirical Performance Breakdown")
            st.dataframe(df_summary, use_container_width=True)

            # Chart Comparison
            st.markdown("#### 📊 Accuracy & F1-Score Comparison")
            st.bar_chart(
                df_summary.set_index("Model Architecture")[["Accuracy (%)", "F1-Score (Weighted %)"]]
            )

            # Utility & Memory Summary
            ut = ab_res.get("data_utility", {})
            st.markdown("#### ⚡ Utility & Resource Consumption")
            u_col1, u_col2, u_col3 = st.columns(3)
            with u_col1:
                st.metric("Avg Utility Retention", f"{ut.get('avg_utility_retention_pct', 0.0)}%")
            with u_col2:
                st.metric("Leakage Prevention Rate", f"{ut.get('leakage_prevention_rate_pct', 0.0)}%")
            with u_col3:
                st.metric("Peak Memory Allocation", f"{ab_res.get('peak_memory_mb', 0.0)} MB")

    # ── TAB 3: PRIVACY ATTACK SUITE ──────────────────────────────────────────
    with tab3:
        st.markdown("### Privacy Attack & Red-Teaming Suite")
        st.markdown(
            "Subjects the privacy engine to direct PII disclosures, obfuscated PII (leetspeak, spaced digits), "
            "prompt injection attacks, and educational inquiry baseline controls."
        )

        if st.button("🛡️ Execute Privacy Attack Benchmark", key="btn_run_attack_bench"):
            with st.spinner("Running Red-Teaming & Evasion Payloads..."):
                atk_bench = PrivacyAttackBenchmarker()
                atk_res = atk_bench.run_benchmark()
                st.session_state["attack_results"] = atk_res

        if "attack_results" in st.session_state:
            atk_res = st.session_state["attack_results"]

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Total Attack Payloads", atk_res["total_tests"])
            with m2:
                st.metric("Successfully Guarded", atk_res["passed_tests"])
            with m3:
                st.metric("Guardrail Pass Rate", f"{atk_res['pass_rate_pct']}%")

            st.markdown("#### 📋 Detailed Payload Results")
            df_atk = pd.DataFrame(atk_res["test_outcomes"])
            st.dataframe(df_atk[["id", "category", "prompt", "expected", "actual_decision", "risk_score", "success"]], use_container_width=True)
