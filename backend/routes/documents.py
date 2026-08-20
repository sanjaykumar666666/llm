"""
AI Trust Chat — Document RAG API Routes
Handles upload, listing, deletion, and RAG queries.
File: backend/routes/documents.py
"""

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from backend.services.rag_engine import (
    upload_document, get_all_documents, delete_document,
    query_documents, get_document_by_id, CLASSIFICATION_LEVELS,
)

router = APIRouter()


@router.post("/documents/upload")
async def upload_doc(
    file: UploadFile = File(...),
    classification: str = Form("INTERNAL"),
    owner: str = Form("Anonymous"),
    department: str = Form("General"),
    user_role: str = Form("USER"),
):
    """Upload and index a document for RAG."""
    try:
        file_bytes = await file.read()
        if len(file_bytes) > 50 * 1024 * 1024:  # 50MB limit
            return JSONResponse(status_code=413, content={"error": "File too large. Max 50MB."})

        allowed_exts = {".pdf", ".txt", ".csv", ".docx", ".md", ".log"}
        ext = "." + file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
        if ext not in allowed_exts:
            return JSONResponse(status_code=400, content={"error": f"Unsupported file type: {ext}"})

        doc_meta = upload_document(
            file_bytes=file_bytes,
            file_name=file.filename,
            classification=classification.upper(),
            owner=owner,
            department=department,
        )

        return {
            "success": True,
            "message": f"Document '{file.filename}' uploaded and indexed successfully.",
            "document": doc_meta,
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@router.get("/documents/list")
def list_documents(user_role: str = "USER"):
    """List all available documents."""
    docs = get_all_documents()
    return {"success": True, "documents": docs, "total": len(docs)}


@router.delete("/documents/{doc_id}")
def delete_doc(doc_id: str):
    """Delete a document and its chunks."""
    success = delete_document(doc_id)
    if success:
        return {"success": True, "message": f"Document {doc_id} deleted."}
    return JSONResponse(status_code=404, content={"success": False, "error": "Document not found."})


@router.post("/documents/query")
def query_doc(request: dict):
    """RAG query against uploaded documents."""
    query = request.get("query", "")
    user_role = request.get("user_role", "USER")
    doc_id = request.get("doc_id")

    if not query.strip():
        return {"success": False, "error": "Query cannot be empty."}

    result = query_documents(query=query, user_role=user_role, doc_id=doc_id)
    return result
