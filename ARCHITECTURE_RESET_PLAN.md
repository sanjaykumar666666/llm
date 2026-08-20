# Comprehensive Architecture Reset Plan

## 1. Audit of Current Architecture

The project is structured as a **Streamlit** frontend (`app.py` & `frontend/`) and a **FastAPI** backend (`backend/main.py` & `backend/routes/`).

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Streamlit Frontend                              │
│         (app.py -> frontend/views/chatbot.py & sidebar navigation)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / API Client
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Gateway                                  │
│                       (backend/routes/chatbot.py)                           │
└──────────────┬───────────────────────┬───────────────────────┬──────────────┘
               │                       │                       │
               ▼                       ▼                       ▼
┌─────────────────────────────┐ ┌───────────────┐ ┌───────────────────────────┐
│     Privacy Firewall        │ │ Query Router  │ │        MCP Engine         │
│  - DistilBERT               │ │ - Semantic    │ │ - MCP Client Manager      │
│  - Naive Bayes              │ │   Intent      │ │ - Web Search MCP Server   │
│  - Decision Gate            │ │   Classifier  │ │ - System Metrics MCP      │
└─────────────────────────────┘ └───────────────┘ └───────────────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │      LLM Gateway Client      │
                        │ (llm_gateway/gemini_client)  │
                        └──────────────────────────────┘
```

---

## 2. End-to-End Request Traces

### Trace 1: General Knowledge Query (`"Vishnu"`)

```text
USER INPUT ("Vishnu")
  │
  ▼
1. Streamlit Input Handler (frontend/views/chatbot.py)
   Captures user prompt string.
  │
  ▼
2. API Client Dispatch (frontend/services/api_client.py)
   Sends POST request to backend `/chat` endpoint.
  │
  ▼
3. Privacy Firewall Evaluation (backend/routes/chatbot.py)
   - Prompt Injection Scanner: SAFE (0 matches)
   - PII Regex Scanner: SAFE (0 matches)
   - DistilBERT + Naive Bayes Hybrid Risk Classifier: Risk Score = 5.0% (ALLOW)
  │
  ▼
4. Semantic Query Router (mcp_engine/web_search_router.py)
   - Evaluates query: "Vishnu"
   - Classifies as: GENERAL_KNOWLEDGE
   - Decision: should_search = False
  │
  ▼
5. LLM Gateway Processing (llm_gateway/gemini_client.py)
   - Sends prompt to Gemini API candidate models.
   - Executes LLM generation.
  │
  ▼
6. Response Rendering (frontend/views/chatbot.py)
   Renders natural language answer in conversation container. MCP search is NOT executed.
```

---

### Trace 2: Current Information Query (`"What is the latest news about ISRO?"`)

```text
USER INPUT ("What is the latest news about ISRO?")
  │
  ▼
1. Streamlit Input Handler (frontend/views/chatbot.py)
  │
  ▼
2. Privacy Firewall Evaluation (backend/routes/chatbot.py)
   Evaluated as SAFE (Risk = 5.0%, ALLOW).
  │
  ▼
3. Semantic Query Router (mcp_engine/web_search_router.py)
   - Detects time-sensitive pattern ("latest news").
   - Classifies as: CURRENT_INFORMATION
   - Decision: should_search = True
  │
  ▼
4. MCP Tool Execution (mcp_engine/web_search_server.py)
   - Executes tool: search_web("What is the latest news about ISRO?")
   - Fetches real search results via Wikipedia API & Google News RSS.
   - Filters prompt injection directives and SSRF targets.
  │
  ▼
5. Context Builder & LLM Synthesis (backend/routes/chatbot.py & llm_gateway/gemini_client.py)
   - Builds evidence context from retrieved web snippets.
   - LLM synthesizes natural answer + attaches '### Sources Used' clickable links.
  │
  ▼
6. Response Rendering (frontend/views/chatbot.py)
   Displays synthesized answer and source citations.
```

---

## 3. Empirical Performance & Response Time Audit

### Benchmark Timing Results
- **Simple Query (`"Vishnu"`)**: **3.6813s**
- **Web Search Query (`"What is the latest news about ISRO?"`)**: **3.6193s**

### Bottleneck Analysis
1. **Gemini Candidate Model Retry Chain**: When `GEMINI_API_KEY` is unauthenticated or set to placeholder string, `GeminiClient` attempts HTTP POST calls to deprecated model endpoints (`gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) sequentially. Each HTTP 404 response introduces ~0.6s latency before falling back to local generation.
2. **HuggingFace Hub Network Verification**: At startup, `DistilBertModel` executes network HEAD requests to HuggingFace Hub to verify model configuration weights (~6s initial load).
3. **Heavy Privacy Firewall on Simple Text**: DistilBERT tensor matrix multiplications run synchronously on CPU for every single prompt.

---

## 4. Disconnected / Duplicate / Broken Generation Paths

1. **Fallback Template Residue**: Residual string formatting functions in legacy routes attempted to inject boilerplate text (`"Information on Latest verified updates on"`).
2. **Duplicate Client Instantiations**: `GeminiClient()` was instantiated multiple times per request instead of maintaining a single initialized client instance.
3. **Implicit Tool Invocation inside LLM Fallback**: Gemini Client fallback previously contained logic invoking `WebSearchMCPServer` directly, bypassing the Query Router decision.

---

## 5. Strict Model & Architecture Responsibilities

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TARGET RESPONSIBILITY MAP                          │
├───────────────────┬─────────────────────────────────────────────────────────┤
│ Component         │ Strict Allowed Responsibilities                         │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ LLM Gateway       │ - General Q&A, conversation, reasoning, code generation  │
│                   │ - Natural language synthesis from RAG / MCP evidence    │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ BERT + Naive Bayes│ - ONLY privacy risk scoring, PII entity detection,      │
│                   │   adversarial prompt injection classification          │
│                   │ - NO text generation                                    │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ MCP Engine        │ - External tool execution layer (Web search, system)    │
│                   │ - NO direct answer generation                           │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ RAG Engine        │ - Document chunk retrieval & knowledge base querying    │
└───────────────────┴─────────────────────────────────────────────────────────┘
```

---

## 6. Target Primary Application Architecture

### Core Execution Flow
```text
                         USER QUESTION
                               ↓
                      INPUT PROCESSOR
                               ↓
                   LIGHTWEIGHT PRIVACY CHECK
            (Adversarial Regex & PII Fast-Path)
                               ↓
                      SEMANTIC QUERY ROUTER
                               ↓
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
   GENERAL KNOWLEDGE    TIME-SENSITIVE INFO     DOCUMENT / RAG
          ↓                    ↓                    ↓
      DIRECT LLM       MCP search_web TOOL     RAG RETRIEVER
          ↓                    ↓                    ↓
          └────────────────────┼────────────────────┘
                               ↓
                       CONTEXT BUILDER
                               ↓
                    generate_chat_response()
                               ↓
                        LLM RESPONSE
                               ↓
                    USER DISPLAY (+ SOURCES)
```

---

## 7. Implementation Roadmap & Action Items

### Phase 1: Centralized Chat Pipeline (`generate_chat_response`)
- Refactor backend to use ONE authoritative function:
  ```python
  generate_chat_response(messages, context=None, tools=None)
  ```
- Remove all alternate / secondary answer generation paths.

### Phase 2: Lightweight Fast-Path & Lazy Component Execution
- Implement lightweight PII/regex fast-path for safe conversational queries so simple text prompts skip heavy BERT tensor operations.
- Update `GeminiClient` to use active, supported Gemini model IDs (`gemini-1.5-flash`, `gemini-2.0-flash-exp`) to eliminate 404 retry delays.

### Phase 3: UI Simplification & Diagnostic Dashboard Shift
- Re-orient sidebar around **Aiera (Primary AI Assistant)**.
- Move top-bar badges (`BERT: ONLINE`, `NAIVE BAYES: ONLINE`, `RISK ENGINE: ACTIVE`) out of the primary chat UI and place them inside the **Dashboard** view.
- Hide privacy analysis details behind clean, collapsed expanders in the chat view.
