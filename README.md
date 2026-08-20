# PrivacyShield AI - Real-Time Privacy Risk Detection & Protection System for LLM Applications

[![Python FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React Vite](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB.svg)](https://vitejs.dev)
[![Explainable AI](https://img.shields.io/badge/XAI-BERT%20%2B%20SBERT%20%2B%20SHAP-8B5CF6.svg)](https://shap.readthedocs.io)
[![Academic Status](https://img.shields.io/badge/Academic-Project%20Prototype-blue.svg)]()

> **Tagline**: Real-Time Privacy Protection Before Your Data Reaches an LLM.

---

## 🌟 Core System Highlights

1. **3-Column Real-Time Keystroke Privacy Firewall**:
   - **Left Sidebar**: Session history list, `+ New Chat`, `Search conversations` input, `Clear All Conversations` button, and main view navigation links.
   - **Center Conversation Area**: ChatGPT-style message thread, attachment tools (`📎 Attach File`, `📷 Image OCR`, `📹 Video OCR`), live input box, and a built-in **"⚡ Demo Privacy Attack"** one-click button.
   - **Right Sidebar (LIVE PRIVACY ANALYSIS Panel)**: Continuous live updates (<200ms debounced) showing Risk Status, Score (`0–100`), Confidence %, Privacy Action, Detected Categories, Sanitized Preview, and an expandable **"Why is this risky?"** explainability section with SHAP token risk heatmaps.

2. **5 Integrated System Views**:
   - 💬 **Chat**: 3-Column main conversation & live privacy panel view.
   - 🛡️ **Privacy Monitor**: Live real-time event telemetry log.
   - 📊 **Analytics**: Safe vs. Risky distribution charts, category breakdowns, and clearly labeled **Demo ML Metrics** (Accuracy 94.2%, Precision 92.5%, Recall 95.1%, F1-Score 93.8%).
   - 🏗️ **Architecture**: Interactive visual pipeline diagram rendered with connected boxes and arrows showing separate branches for Text, Image OCR, and Video keyframe OCR merging into the Unified Privacy Risk Engine.
   - 📚 **Research & Datasets**: Academic review page detailing Algorithms & Methods (Tokenization, BERT, Naïve Bayes, SBERT, Cosine Similarity, SHAP, OCR), Problem Statement & Research Gap, and Dataset SBERT Cosine Similarity cross-dataset matching visualizer.

3. **High-Risk Action Security Controls**:
   - Disables direct "Send to LLM" button when risk is **HIGH** or **CRITICAL**.
   - Displays warning alert banner: *"⚠ Privacy Risk Detected: Sensitive information detected. Do not share this information with an AI model."*
   - Offers three actions: **[Sanitize & Continue]**, **[Edit Prompt]**, **[Cancel]**.

---

## 🏗️ System Architecture & Pipeline

```
[ User Input (Text / Image OCR / Video OCR) ]
                     │
                     ▼
  [ Real-Time Keystroke & OCR Preprocessing ]
                     │
    ┌────────────────┴────────────────┐
    ▼                                 ▼
[ Span Tokenization ]       [ BERT & SBERT Embeddings ]
    │                                 │
    └────────────────┬────────────────┘
                     ▼
     [ Naïve Bayes Probabilistic Classifier ]
                     │
                     ▼
    [ UNIFIED PRIVACY RISK ENGINE (0-100) ]
                     │
                     ▼
   [ SHAP Explainability & Token Risk Heatmap ]
                     │
                     ▼
    [ Decision Gate (ALLOW / WARN / SANITIZE / BLOCK) ]
                     │
     ┌───────────────┴───────────────┐
     ▼                               ▼
 [ HIGH / CRITICAL ]         [ SAFE / SANITIZED ]
  Send Button Disabled        Forwarded to LLM Gateway
  Offer "Sanitize"            LLM Response Generated
```

---

## 🚀 Quick Start Instructions

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`

### 1. Launch FastAPI Backend Gateway
```bash
# From project root directory
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Launch React Frontend Web App
```bash
# Navigate to React client
cd frontend/client

# Start Vite dev server on http://localhost:5173
npm run dev
```

---

## 🧪 Demonstration Sequence for College Project Review

1. Open **Chat** view and click **"⚡ Demo Privacy Attack"**.
2. Input fills automatically with:
   `"My bank account number is 123456789 and my password is Sanjay123. Please analyze this."`
3. Privacy panel immediately triggers 🔴 **HIGH RISK (100/100, Action: BLOCKED)** and disables the Send button.
4. Click **[Sanitize & Continue]**.
5. Input is transformed to:
   `"My bank [FINANCIAL_ACCOUNT_REDACTED] and my password: [CREDENTIAL_REDACTED]. Please analyze this."`
6. Privacy score updates to 🟢 **SAFE (0/100)** and prompt sends safely.
7. Click **Architecture**, **Analytics**, and **Research & Datasets** in the left sidebar to demonstrate full academic presentation views.
