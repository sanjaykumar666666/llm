# AIERA Chat Rebuild & Architecture Blueprint

This plan outlines the complete rebuild of **Aiera** into a modern **Generative AI Chatbot** with background privacy protection, persistent conversation history, a universal message composer, and semantic query routing.

---

## 1. Primary Product Experience & UI Reset

### 1.1 Direct Landing on AIERA Chat
- The application (`app.py` & `frontend/views/chatbot.py`) opens **directly into the Chatbot UI**.
- Technical diagnostic banners (`AI PRIVACY CORE`, pipeline diagrams) and status badges (`BERT: ONLINE`, `NAIVE BAYES: ONLINE`, `RISK ENGINE: ACTIVE`) are moved to the **Security Dashboard** view.
- Privacy inspection runs automatically in the background.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SIDEBAR                  │ MAIN AIERA CHAT AREA                             │
│                          │                                                  │
│ + New Chat               │                 AIERA ASSISTANT                  │
│                          │    "Your privacy-aware AI assistant"             │
│ CHATS                    │                                                  │
│ Today                    │  User: Who is Vishnu?                            │
│  └─ Hindu Mythology      │  Aiera: Vishnu is a major deity in Hindu...       │
│  └─ Python Recursion     │                                                  │
│ Yesterday                │  User: What are his major teachings?             │
│  └─ ISRO Launch Updates  │  Aiera: In the Bhagavad Gita, Krishna...         │
│                          │                                                  │
│ TOOLS                    │  ─────────────────────────────────────────────   │
│  - Privacy Tools         │  [+] Message Aiera...                   [Send]   │
│  - Multimodal Engine     │                                                  │
│ DASHBOARD                │                                                  │
└──────────────────────────┴──────────────────────────────────────────────────┘
```

---

## 2. ChatGPT-Style Interaction Model & Sidebar Redesign

### 2.1 Sidebar Organization ([frontend/components/sidebar.py](file:///c:/Users/sanja/Downloads/LLM/frontend/components/sidebar.py))
- **Primary Section**:
  - `+ New Chat` button (clears current conversation container, initializes a fresh thread).
  - Conversation History categorized by `Today`, `Yesterday`, `Previous 7 Days`.
  - Supports conversation renaming, thread switching, and deletion.
- **Secondary Tools Section**:
  - `Privacy Analysis`, `Multimodal Analysis`, `Documents & RAG`, `MCP Tools`.
- **System Section**:
  - `Security Dashboard` (contains full BERT/Naive Bayes metrics & pipeline diagnostic badges), `Model Evaluation`, `Audit History`, `Settings`.

### 2.2 Conversational State & Memory
- Persistent `st.session_state["conversations"]` dictionary holding multi-turn message history (`role`, `content`, `timestamp`, `privacy_meta`).
- Context resolver automatically retains history for pronoun disambiguation (`"his teachings"`, `"what about it"`).

---

## 3. Universal Message Composer & Automatic Modality Detection

### 3.1 Integrated Bottom Composer ([frontend/views/chatbot.py](file:///c:/Users/sanja/Downloads/LLM/frontend/views/chatbot.py))
- Single rounded input bar at the bottom: `"Message Aiera..."`.
- Attachment button (`[ + Attach ]`) supporting:
  - **Images** (`.png`, `.jpg`, `.jpeg`, `.webp`)
  - **Documents / PDFs** (`.pdf`, `.csv`, `.json`, `.txt`, `.md`)
  - **Video Files** (`.mp4`, `.avi`, `.mov`)
  - **Audio Files** (`.mp3`, `.wav`)
- Automatically detects input modality without requiring prepended radio buttons.

---

## 4. Semantic Query Routing & Model Responsibilities

```text
                                USER MESSAGE
                                     │
                                     ▼
                          LIGHTWEIGHT PRIVACY CHECK
                 (PII & Prompt Injection Regex Fast-Path)
                                     │
                                     ▼
                            SEMANTIC QUERY ROUTER
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                          ▼
  GENERAL KNOWLEDGE          TIME-SENSITIVE INFO        MULTIMODAL / RAG
   (Vishnu, Tea, Java,        ("latest ISRO news",       (PDF, Images, Video,
    Python, Gravity, etc.)     "what happened today")     Audio attachments)
          │                          │                          │
          ▼                          ▼                          ▼
      DIRECT LLM              MCP search_web             VISION / RAG
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     ▼
                             CONTEXT BUILDER
                                     │
                                     ▼
                          generate_chat_response()
                                     │
                                     ▼
                          CHATBOT RESPONSE DISPLAY
                        (+ Sources if Web search used)
```

---

## 5. Background Privacy Protection & User Experience

### 5.1 Safe Inputs
- Normal queries (`"Who is Vishnu?"`, `"Explain Java inheritance"`) render standard conversational message bubbles instantly.
- Technical privacy breakdown metrics (risk score, confidence, model execution time) are hidden inside a collapsed `▼ Analysis Details` expander.

### 5.2 Sensitive Inputs & PII Warning Cards
- If PII (Aadhaar, Email, Credit Card) is detected:
  - Displays a clean warning card: `🛡️ Privacy Warning: Sensitive personal information detected`.
  - Provides `[Protect & Sanitize]` and `[Send Anyway]` action buttons.

### 5.3 Blocked Inputs
- If adversarial jailbreak or severe risk is detected:
  - Displays: `🛡️ Message Blocked: High privacy / security risk detected`.
  - Prompts are halted immediately before reaching the external LLM.

---

## 6. Implementation Strategy & File Changes

### 1. [frontend/app.py](file:///c:/Users/sanja/Downloads/LLM/frontend/app.py) & [frontend/components/sidebar.py](file:///c:/Users/sanja/Downloads/LLM/frontend/components/sidebar.py)
- Set default landing page to **Aiera (Primary Chat)**.
- Re-architect sidebar to prioritize `+ New Chat` and conversation history threads. Move pipeline diagrams to **Dashboard**.

### 2. [frontend/views/chatbot.py](file:///c:/Users/sanja/Downloads/LLM/frontend/views/chatbot.py)
- Redesign into a full ChatGPT-like chat container with message bubbles, action buttons (Copy, Regenerate, Retry), and a bottom composer with attachment popover.

### 3. [backend/routes/chatbot.py](file:///c:/Users/sanja/Downloads/LLM/backend/routes/chatbot.py)
- Implement centralized `generate_chat_response(messages, context=None, tools=None)` backend handler.
- Integrate fast-path privacy check for conversational prompts.

---

## 7. Mandatory 13 Acceptance Tests

1. **Default Landing**: App opens directly to Aiera Chat UI.
2. **"Vishnu"**: Direct LLM response about Vishnu; NO MCP search.
3. **"Garuda"**: Direct LLM response about Garuda; NO MCP search.
4. **"Tea"**: Direct LLM response about Tea; NO MCP search.
5. **"Explain Java inheritance"**: Technical explanation + clean code block.
6. **"Write Python factorial program"**: Clean python code block.
7. **"What is the latest ISRO update?"**: Triggers MCP search_web; displays synthesized answer + clickable sources.
8. **Image Upload**: Upload image -> Chat displays OCR & privacy analysis inside conversation.
9. **PDF Upload**: Upload document -> Chat answers questions via RAG.
10. **Video Upload**: Video sampled & analyzed in-line.
11. **Sensitive Input**: Aadhaar/Email triggers `🛡️ Privacy Warning`.
12. **Follow-up Conversation**: *"Who is Krishna?"* followed by *"What are his teachings?"* resolves pronoun memory correctly.
13. **Unseen Topics**: Arbitrary topics generate natural answers without generic templates.
