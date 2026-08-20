# Runtime Diagnostic Report

## 1. RUNNING PROCESS
- **Process ID**: `29064`
- **Executable**: `C:\Users\sanja\AppData\Local\Programs\Python\Python313\python.exe`
- **Script Command**: `"C:\Users\sanja\AppData\Local\Programs\Python\Python313\Scripts\streamlit.exe" run app.py`
- **Port**: `8501` (Owned by PID `29064`)
- **Number of Active Streamlit Processes**: `1`

---

## 2. PROJECT PATH
- **Absolute Path**: `c:\Users\sanja\Downloads\LLM`
- **Working Directory**: `C:\Users\sanja\Downloads\LLM`
- **Entry File**: [app.py](file:///c:/Users/sanja/Downloads/LLM/app.py) -> [frontend/app.py](file:///c:/Users/sanja/Downloads/LLM/frontend/app.py)

---

## 3. CHAT HANDLER
- **Frontend Handler**: `render_chatbot_view()` in [frontend/views/chatbot.py](file:///c:/Users/sanja/Downloads/LLM/frontend/views/chatbot.py)
- **API Dispatcher**: `APIClient.chat_message()` in [frontend/services/api_client.py](file:///c:/Users/sanja/Downloads/LLM/frontend/services/api_client.py)
- **Backend Route Handler**: `chat_endpoint()` in [backend/routes/chatbot.py](file:///c:/Users/sanja/Downloads/LLM/backend/routes/chatbot.py)

---

## 4. GENERIC RESPONSE SOURCE
- **Historical Template Strings Found**:
  - `tests/test_rebuilt_aiera_chatbot.py`
  - `tests/test_final_pipeline_verification.py`
- **Web Search Server Fallback Generator**:
  - [mcp_engine/web_search_server.py](file:///c:/Users/sanja/Downloads/LLM/mcp_engine/web_search_server.py): `_handle_search_web()` calls `_perform_real_web_search()` which queries Wikipedia API & Google News RSS.

---

## 5. LLM STATUS
- **Configured Provider**: Google Gemini (`google-genai` SDK)
- **Configured Models**: `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-1.5-flash` in [config.py](file:///c:/Users/sanja/Downloads/LLM/config.py)
- **API Key Configuration**: Placeholder string `your_google_gemini_api_key_here` in [.env](file:///c:/Users/sanja/Downloads/LLM/.env)
- **Client Initialization**: `self.client` evaluates to `None` due to placeholder key check in [llm_gateway/gemini_client.py](file:///c:/Users/sanja/Downloads/LLM/llm_gateway/gemini_client.py)
- **API Call Result**: Real HTTP API call is **bypassed**, triggering `_generate_dynamic_generalized_response()` in fallback mode.

---

## 6. MCP STATUS
- **Router Logic**: [mcp_engine/web_search_router.py](file:///c:/Users/sanja/Downloads/LLM/mcp_engine/web_search_router.py) `evaluate_search_intent()`
- **Execution Status**:
  - For `Vishnu`, `Krishna`, `Garuda`, `Tea`, `Java`: Router returns `should_search = False` (MCP NOT executed).
  - For `What is the latest news about ISRO?`, `What happened in Delhi today?`: Router returns `should_search = True` (MCP `search_web` tool executed).

---

## 7. ROUTING STATUS
- **Semantic Intent Classifier**: `WebSearchRouter` evaluates prompts against `EXPLICIT_SEARCH_TERMS` and `TIME_SENSITIVE_PATTERNS`.
- **Default Category**: General knowledge prompts fall back to `GENERAL_KNOWLEDGE` (`should_search = False`).

---

## 8. CACHE STATUS
- **Streamlit Caching**: No `@st.cache_data` or `@st.cache_resource` decorators are applied to chatbot route responses.
- **Session State**: Session state maintains `conversations` dictionary and `chat_history` list in `st.session_state`.
- **Stale Browser Cache**: If the browser tab was opened prior to process updates, Streamlit's websocket connection retains old session state in browser memory until refreshed (`Ctrl + F5` or hard refresh).

---

## 9. DUPLICATE PROJECTS
- **Duplicate Projects Found**: **NO** duplicate Streamlit `app.py` projects found under `C:\Users\sanja\Downloads`.
- **Existing Directories**: `C:\Users\sanja\Downloads\projject` (backend venv only, no Streamlit app.py), `C:\Users\sanja\Downloads\Privacy` (Flask venv only).

---

## 10. VISHNU TRACE

```text
User Input ("Vishnu")
  ↓
render_chatbot_view() [frontend/views/chatbot.py]
  ↓
APIClient.chat_message() [frontend/services/api_client.py]
  ↓
chat_endpoint() [backend/routes/chatbot.py]
  ↓
WebSearchRouter.evaluate_search_intent("Vishnu") -> should_search = False
  ↓
Privacy Firewall (DistilBERT + Naive Bayes) -> ALLOW (Risk: 5.0%)
  ↓
MCP search_web -> BYPASSED (Not executed)
  ↓
GeminiClient.generate_response("Vishnu")
  ↓
Gemini API Key is Placeholder -> Executed _generate_dynamic_generalized_response()
  ↓
Natural Vishnu paragraph returned directly
  ↓
Formatted message bubble rendered in Streamlit Chat container
```

---

## 11. ROOT CAUSE

1. **Unauthenticated / Placeholder Gemini API Key**:
   In [.env](file:///c:/Users/sanja/Downloads/LLM/.env), `GEMINI_API_KEY` is set to placeholder `"your_google_gemini_api_key_here"`. Real Gemini API calls are bypassed, forcing `GeminiClient` to run local fallback synthesis.

2. **Streamlit Websocket / Session State Persistence**:
   Streamlit keeps in-memory tab state (`st.session_state["chat_history"]`) active across hot reloads. Unless a user clicks `➕ New Chat` or performs a hard refresh (`Ctrl + F5`), previous responses rendered in session state remain visible in the browser UI.
