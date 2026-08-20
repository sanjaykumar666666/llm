"""
AI Trust Chat — FastAPI Backend Application Entrypoint.
File: backend/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import (
    chatbot,
    text_analysis,
    live_analysis,
    youtube_analysis,
    image_analysis,
    video_analysis,
    injection_detector,
    summarizer,
    dashboard,
    history,
    settings,
    explainability,
    mcp,
    documents,
    policies,
)

app = FastAPI(
    title="AI Trust Chat — Secure GenAI Platform API",
    description=(
        "REST API Gateway for AI Trust Chat: Secure Generative AI Chatbot with "
        "Privacy-Preserving Data Protection, Prompt Injection Detection, RAG, and Policy Engine."
    ),
    version="2.0.0"
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Chat & Security Gateway
app.include_router(chatbot.router, prefix="/api/v1", tags=["AI Trust Chat"])
app.include_router(documents.router, prefix="/api/v1", tags=["RAG Documents"])
app.include_router(policies.router, prefix="/api/v1", tags=["Policies & Security"])

# Analysis & MCP Tools
app.include_router(live_analysis.router, prefix="/api/v1", tags=["Real-Time Analysis"])
app.include_router(explainability.router, prefix="/api/v1", tags=["Explainability"])
app.include_router(mcp.router, prefix="/api/v1", tags=["MCP"])
app.include_router(text_analysis.router, prefix="/api/v1", tags=["Text Analysis"])
app.include_router(youtube_analysis.router, prefix="/api/v1", tags=["YouTube"])
app.include_router(image_analysis.router, prefix="/api/v1", tags=["Image Analysis"])
app.include_router(video_analysis.router, prefix="/api/v1", tags=["Video Analysis"])
app.include_router(injection_detector.router, prefix="/api/v1", tags=["Injection Detector"])
app.include_router(summarizer.router, prefix="/api/v1", tags=["Summarizer"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(history.router, prefix="/api/v1", tags=["Audit History"])
app.include_router(settings.router, prefix="/api/v1", tags=["Settings"])


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Trust Chat — Secure GenAI Platform",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
