# Phase 1 — Complete Project Audit Report

## 1. Current Architecture
The project is an **AI-Powered Multimodal Privacy Risk Detection & Protection System** built with a **Streamlit** frontend (`frontend/app.py`) and a **FastAPI** backend API gateway (`backend/main.py`).

### High-Level Architecture Overview
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Streamlit Frontend UI                             │
│                  (frontend/app.py & frontend/views/*)                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / Local API Client
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI REST Gateway                             │
│                         (backend/main.py & routes)                          │
└──────────────┬───────────────────────┬───────────────────────┬──────────────┘
               │                       │                       │
               ▼                       ▼                       ▼
┌─────────────────────────────┐ ┌───────────────┐ ┌───────────────────────────┐
│     Multimodal Ingestion    │ │ Privacy Engine│ │        MCP Engine         │
│  - Text Processor           │ │ - BERT Model  │ │ - MCP Client Manager      │
│  - Document Processor       │ │ - Naive Bayes │ │ - Web Search MCP Server   │
│  - Image OCR (PyTesseract)  │ │ - Decision    │ │ - System Metrics MCP      │
│  - Video Frame Sampler      │ │   Gate        │ │ - Audit History MCP       │
└─────────────────────────────┘ └───────────────┘ └───────────────────────────┘
```

---

## 2. Current Request Flow
When a user enters a query (e.g. `"Krishna"`) into the Chatbot view:

1. **User Input**: Entered in `frontend/views/chatbot.py`.
2. **API Client Dispatch**: Sent via `APIClient.chat_message(prompt)` in `frontend/services/api_client.py`.
3. **Backend Route**: Received by `chat_endpoint()` in `backend/routes/chatbot.py`.
4. **Privacy Firewall Inspection**:
   - Scanned for adversarial prompt injection patterns (`injection_patterns`).
   - Scanned for regex PII entities (email, phone, credentials).
   - Evaluated by `HybridPrivacyClassifier` combining **DistilBERT** embeddings and **Naive Bayes** keyword probabilities.
5. **Decision Gate Evaluation**:
   - If `BLOCK` (risk >= 0.75 or injection/PII detected) -> Execution halts immediately; LLM is **NOT** invoked.
   - If `ALLOW` -> Proceed to LLM / MCP engine.
6. **Query Intent Routing**:
   - `WebSearchRouter.evaluate_search_intent(prompt)` checks if real-time web search is required.
7. **LLM Gateway Processing**:
   - Prompt sent to `GeminiClient().generate_response(prompt)` in `llm_gateway/gemini_client.py`.
8. **Response Generation**:
   - Returned text displayed in Streamlit conversation container alongside a live analysis panel.

---

## 3. Exact Cause of the "Krishna" Wrong Answer

### Root Cause Identification
- **Target File**: [llm_gateway/gemini_client.py](file:///c:/Users/sanja/Downloads/LLM/llm_gateway/gemini_client.py)
- **Target Function**: `GeminiClient.generate_response()` and `GeminiClient._generate_smart_aiera_response()`
- **Line Numbers**: Lines 28-36, 47-76, 178-192

### Why It Happens
1. **API Key Status**: In [.env](file:///c:/Users/sanja/Downloads/LLM/.env), `GEMINI_API_KEY` is set to the placeholder string `your_google_gemini_api_key_here` (or `your_gemini_api_key_here`).
2. **Client Initialization Failure**: In `GeminiClient.__init__()` (line 31), the `google-genai` client is **NOT initialized** because the key is detected as a placeholder:
   ```python
   if GENAI_AVAILABLE and self.api_key and self.api_key not in ["your_gemini_api_key_here", "dummy_key", "your_google_gemini_api_key_here"]:
       self.client = genai.Client(api_key=self.api_key)
   ```
   Result: `self.client` evaluates to `None`.
3. **Silent Fallback Execution**: In `generate_response()` (line 47), `if self.client:` evaluates to `False`. The code skips the real Gemini LLM API call entirely and falls through to step 2 (line 71):
   ```python
   return {
       "status": "aiera_genai_engine",
       "success": True,
       "model": f"{self.model_name} (Knowledge Engine)",
       "response_text": self._generate_smart_aiera_response(sanitized_prompt),
   }
   ```
4. **Template Fallthrough**: Inside `_generate_smart_aiera_response(prompt)`:
   If an incoming prompt (such as `"Krishna"`) did not match an exact string `if "..." in p_lower:` condition previously, it executed lines 178-192:
   ```python
   cleaned_topic = prompt.strip().rstrip("?.!")
   formatted_topic = cleaned_topic.capitalize()

   return (
       f"### 📚 Knowledge & Insights on \"{formatted_topic}\"\n\n"
       f"Here is a comprehensive breakdown regarding **{cleaned_topic}**:\n\n"
       f"1. **Core Concept & Definition**: **{formatted_topic}** represents a fundamental domain topic involving systematic principles, historical development, or analytical study.\n\n"
       f"2. **Key Facets & Structural Components**:\n"
       f"   - **Fundamental Principles**: Understood through foundational frameworks, established facts, and domain observations.\n"
       f"   - **Applications & Relevance**: Crucial in modern analytical research, educational learning, and practical real-world execution.\n"
       f"   - **Global Impact**: Influences contemporary understanding, problem-solving methodologies, and strategic development.\n\n"
       f"3. **Summary & Perspective**: Exploring **{cleaned_topic}** provides deeper domain awareness and facilitates informed decision-making.\n\n"
   )
   ```
   This generic filler template produced the unrelated "information technology / domain analysis" output regardless of the actual user query topic.

---

## 4. Chatbot Architecture Classification
The current chatbot is classified as:
**E. An LLM with a broken fallback + D. A template-based / hardcoded fallback system.**

- **Intended Design**: An LLM-powered chatbot utilizing Google Gemini (`google-genai` SDK).
- **Actual Runtime State**: Operates as a keyword-matching and template fallback script due to unauthenticated / placeholder API key status.

---

## 5. LLM Status
- **SDK**: `google-genai` Python library (`from google import genai`).
- **Configured Models**: `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-1.5-flash` (in `config.py`).
- **API Key Configuration**: Placeholder key (`GEMINI_API_KEY=your_google_gemini_api_key_here`).
- **Runtime Execution**: Live API requests fail / are bypassed due to placeholder key status.

---

## 6. BERT Status
- **File**: [ml_engine/bert_model.py](file:///c:/Users/sanja/Downloads/LLM/ml_engine/bert_model.py)
- **Model Architecture**: HuggingFace `DistilBertModel` (`distilbert-base-uncased`).
- **Role**: Extracts 768-dimensional token feature vectors and calculates contextual similarity for privacy risk scoring.
- **Classification vs Generation**: Used **strictly for classification / feature extraction**. NOT used for text generation.
- **Runtime Status**: REAL, operational PyTorch model running in local CPU memory.

---

## 7. Naive Bayes Status
- **File**: [ml_engine/naive_bayes.py](file:///c:/Users/sanja/Downloads/LLM/ml_engine/naive_bayes.py)
- **Model Architecture**: `scikit-learn` `MultinomialNB` with `CountVectorizer`.
- **Role**: Calculates n-gram term probability distributions for PII and sensitive tokens.
- **Classification vs Generation**: Used **strictly for probability classification**. NOT used for text generation.
- **Runtime Status**: REAL, operational model trained on seed samples in memory.

---

## 8. Risk Engine Status
- **File**: [ml_engine/hybrid_classifier.py](file:///c:/Users/sanja/Downloads/LLM/ml_engine/hybrid_classifier.py) and [gate/decision_gate.py](file:///c:/Users/sanja/Downloads/LLM/gate/decision_gate.py)
- **Logic**: Combines BERT semantic embeddings (40% weight) + Naive Bayes keyword probability (30% weight) + Metadata / Regex PII flags (30% weight).
- **Thresholds**:
  - `ALLOW`: Risk Score < 0.30
  - `SANITIZE`: Risk Score 0.30 - 0.74
  - `BLOCK`: Risk Score >= 0.75
- **Runtime Status**: Fully ACTIVE and functional.

---

## 9. XAI Status
- **File**: [backend/routes/explainability.py](file:///c:/Users/sanja/Downloads/LLM/backend/routes/explainability.py) and [frontend/views/explainability.py](file:///c:/Users/sanja/Downloads/LLM/frontend/views/explainability.py)
- **Logic**: Provides feature contribution ranking and privacy breakdown charts.
- **Runtime Status**: Partially heuristic / simulated feature contribution weights based on regex entity detection and risk score bands.

---

## 10. Training/Fine-tuning Status
- **Training Datasets**: No offline `.pt` or `.bin` fine-tuned BERT checkpoint exists in the repository.
- **Naive Bayes**: Trained dynamically at startup on 15 seed sentences in `naive_bayes.py`.
- **BERT**: Loads stock pre-trained weights (`distilbert-base-uncased`) directly from HuggingFace Hub.
- **Model Fine-Tuning**: No custom PyTorch training loop or domain-specific fine-tuning script is present.

---

## 11. RAG Status
- **Vector Database**: No external vector database (ChromaDB, FAISS, Qdrant, Pinecone) is installed.
- **Resource Context**: Basic static resource strings (`mcp://knowledge/gdpr_pii_rules`) are exposed via MCP, but full document chunking and vector retrieval are absent.

---

## 12. Web Search Status
- **File**: [mcp_engine/web_search_server.py](file:///c:/Users/sanja/Downloads/LLM/mcp_engine/web_search_server.py)
- **Implementation**: `WebSearchMCPServer` exposing the `search_web(query, max_results)` tool.
- **Search Backend**: DuckDuckGo HTML endpoint parser with fallback to structured news/domain knowledge when offline.
- **Security Protections**:
  - SSRF URL filtering (`_is_safe_url()`) blocking `localhost`, `127.0.0.1`, `169.254.169.254`, and private subnets.
  - Scraped content prompt injection filter (`_sanitize_web_content()`).
- **Runtime Status**: Fully implemented.

---

## 13. MCP Status
- **Files**: [mcp_engine/](file:///c:/Users/sanja/Downloads/LLM/mcp_engine/) (`mcp_server.py`, `mcp_client.py`, `privacy_mcp_wrapper.py`, `web_search_server.py`)
- **Architecture**: MCP 1.0 Client-Server pattern.
- **Registered MCP Servers**:
  1. `SystemMetricsMCPServer`: System health & model status tools.
  2. `PrivacyAuditMCPServer`: Firewall audit log query tools.
  3. `KnowledgeBaseMCPServer`: Compliance rulebook resources and tools.
  4. `WebSearchMCPServer`: Live web search and content retrieval.
- **Privacy Enforcement**: `PrivacyMCPWrapper` evaluates tool parameters and output payloads before execution.
- **Runtime Status**: Fully implemented and functional.

---

## 14. Text Analysis Status
- **Status**: **WORKING**
- **Files**: `processing/text_processor.py`, `backend/routes/text_analysis.py`, `frontend/views/text_analyzer.py`.
- **Capabilities**: Detects emails, phone numbers, SSNs, Aadhaar numbers, API keys, passwords, and calculates Shannon entropy.

---

## 15. Image Analysis Status
- **Status**: **WORKING**
- **Files**: `ocr/image_ocr.py`, `backend/services/image_privacy_service.py`, `frontend/views/image_analyzer.py`.
- **Capabilities**: Extracts text via `pytesseract` / OpenCV, detects PII, and applies blurring/redaction to image regions.

---

## 16. Video Analysis Status
- **Status**: **PARTIALLY WORKING / SIMULATED KEYFRAMES**
- **Files**: `ocr/video_frame.py`, `processing/video_processor.py`, `frontend/views/video_analyzer.py`.
- **Capabilities**: Samples video keyframes and extracts OCR text from video frames.

---

## 17. Audio Analysis Status
- **Status**: **NOT IMPLEMENTED / PLACEHOLDER**
- **Details**: No audio transcription library (Whisper, Vosk, SpeechRecognition) is included in `requirements.txt`.

---

## 18. URL Analysis Status
- **Status**: **PARTIALLY WORKING (YOUTUBE TRANSCRIPTS)**
- **Files**: `backend/routes/youtube_analysis.py`, `frontend/views/youtube_analyzer.py`.
- **Capabilities**: Fetches YouTube video metadata and transcript summaries for privacy inspection.

---

## 19. Dashboard Status Verification
- **Header Badges**: `SYSTEM ONLINE`, `BERT: ONLINE`, `NAIVE BAYES: ONLINE`, `RISK ENGINE: ACTIVE`, `XAI: READY`.
- **Verification Result**:
  - `BERT`: Real DistilBERT model loaded in PyTorch -> **CONFIRMED ONLINE**.
  - `NAIVE BAYES`: Real scikit-learn model trained in memory -> **CONFIRMED ONLINE**.
  - `RISK ENGINE`: Real hybrid risk calculator -> **CONFIRMED ACTIVE**.
  - `XAI`: Heuristic explanation engine -> **PARTIALLY REAL**.

---

## 20. Security Findings
1. **SSRF Defense**: `WebSearchMCPServer` validates URLs against private IP ranges (`10.x`, `172.16-31.x`, `192.168.x`, `127.0.0.1`, `169.254.169.254`).
2. **Web Content Jailbreak Filter**: Scraped web content passes through prompt injection regex filters before context injection.
3. **File Upload Security**: `InputValidator` checks file extension whitelists and file size constraints (max 50 MB).
4. **API Key Security**: Keys stored in `.env` and loaded via `python-dotenv`.

---

## 21. Files That Need Modification (For Phase 2 Chatbot Upgrade)
- `llm_gateway/gemini_client.py`: Upgrade LLM caller and replace generic template fallback.
- `.env`: Ensure valid API key or local LLM endpoint configuration.
- `backend/routes/chatbot.py`: Refine query synthesis and RAG context integration.

---

## 22. Files That Must Be Preserved
- `ml_engine/bert_model.py` (BERT feature extraction)
- `ml_engine/naive_bayes.py` (Naive Bayes classifier)
- `ml_engine/hybrid_classifier.py` (Hybrid risk classification)
- `gate/decision_gate.py` (ALLOW / SANITIZE / BLOCK decision gate)
- `privacy_engine/evaluator.py` & `privacy_engine/sanitizer.py` (PII redaction)
- `mcp_engine/` (MCP infrastructure, servers, and security wrapper)

---

## 23. Recommended Target Architecture
```text
                    USER QUESTION
                          ↓
                PRIVACY FIREWALL GATE
       (DistilBERT + Naive Bayes + Regex PII)
                          ↓
            ┌─────────────┴─────────────┐
            ↓                           ↓
      [HIGH RISK]                   [SAFE]
            ↓                           ↓
       BLOCK / WARN               QUERY ROUTER
                                        ↓
                       ┌────────────────┴────────────────┐
                       ↓                                 ↓
               GENERAL KNOWLEDGE                 REAL-TIME / WEB / RAG
                       ↓                                 ↓
                   LLM ENGINE                    MCP TOOLS / SEARCH
                       ↓                                 ↓
                       └────────────────┬────────────────┘
                                        ↓
                                  LLM SYNTHESIS
                                        ↓
                            NATURAL ANSWER + SOURCES
```

---

## 24. Phase 2 Implementation Plan Overview
1. **LLM Connection Fix**: Configure valid LLM gateway credentials or robust local LLM provider.
2. **Eliminate Generic Template**: Replace hardcoded `Knowledge & Insights` string templates with real LLM generation across all prompt categories.
3. **Strict Separation of Concerns**: Keep BERT + Naive Bayes dedicated 100% to privacy risk classification, while delegating all natural language answer generation to the LLM.
4. **End-to-End Testing**: Test general-purpose Q&A on arbitrary unseen prompts (Krishna, Garuda, Shiva, Tea, Java, Photosynthesis, Python factorial, etc.).
