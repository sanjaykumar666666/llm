# Aiera React Client (`frontend/client/`)

## Status: Future UI Layer (Currently Inactive)

This directory contains a **Vite + React 19** frontend client for Aiera.
It is **not currently running** — the primary running UI is the **Streamlit app** (`app.py`).

## What's Here

| File/Dir | Description |
|----------|-------------|
| `src/components/Header.jsx` | Top navigation bar with BERT/NB status badges |
| `src/index.css` | Complete production-grade design system (599 lines) |
| `index.html` | Vite entry point |
| `vite.config.js` | Vite build config |
| `package.json` | React 19 + lucide-react + Vite dependencies |

## To Start the React Dev Server

```bash
cd frontend/client
npm install     # if node_modules missing
npm run dev     # starts at http://localhost:5173
```

The React client is designed to call the **FastAPI backend** directly at:
`http://localhost:8000/api/v1/chat`

## Architecture Role

```
                     ┌──────────────────────┐
       Browser ─────►│  React Client (Vite) │  ← future primary chat UI
                     │  localhost:5173       │
                     └──────────┬───────────┘
                                │ REST API calls
                     ┌──────────▼───────────┐
       Streamlit ───►│  FastAPI Backend      │  ← running now
                     │  localhost:8000       │
                     └──────────────────────┘
```

## Migration Path

Phase 1 (Current): Streamlit handles all UI
Phase 2 (Future): React client replaces Streamlit for chat view only
Phase 3 (Future): React client becomes the primary full application

The `src/index.css` design system (dark navy, cyan accent, glassmorphism)
is intentionally aligned with `frontend/styles.css` (Streamlit injection).
