"""
AI Trust Chat — RAG Engine
TF-IDF based document retrieval with role-based access control.
Supports PDF, DOCX, TXT, CSV file types.
File: backend/services/rag_engine.py
"""

import io
import re
import math
import uuid
import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

# Try optional parsers
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pypdf as PyPDF2
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# In-memory document store
_documents: List[Dict[str, Any]] = []
_chunks: List[Dict[str, Any]] = []

CLASSIFICATION_LEVELS = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]

ROLE_ACCESS = {
    "ADMIN":          ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
    "SECURITY_ADMIN": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
    "MANAGER":        ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
    "USER":           ["PUBLIC", "INTERNAL"],
    "AUDITOR":        ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
}


def _extract_text(file_bytes: bytes, file_name: str) -> str:
    """Extract text from uploaded file."""
    ext = file_name.lower().rsplit(".", 1)[-1]

    if ext == "txt" or ext == "md" or ext == "log":
        try:
            return file_bytes.decode("utf-8", errors="replace")
        except Exception:
            return ""

    elif ext == "pdf":
        if not PDF_AVAILABLE:
            return "[PDF parsing unavailable — install pypdf2 or pypdf]"
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages)
        except Exception as e:
            return f"[PDF extraction error: {e}]"

    elif ext == "docx":
        if not DOCX_AVAILABLE:
            return "[DOCX parsing unavailable — install python-docx]"
        try:
            doc = DocxDocument(io.BytesIO(file_bytes))
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        except Exception as e:
            return f"[DOCX extraction error: {e}]"

    elif ext == "csv":
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            # Simple CSV text extraction
            return text.replace(",", " ").replace('"', "")
        except Exception:
            return ""

    return f"[Unsupported file type: {ext}]"


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer — lowercase, remove punctuation, split words."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return [t for t in text.split() if len(t) > 2]


def _tf_idf_score(query_tokens: List[str], chunk_text: str, all_chunks: List[str]) -> float:
    """Compute TF-IDF similarity score between query and chunk."""
    chunk_tokens = _tokenize(chunk_text)
    chunk_freq = Counter(chunk_tokens)
    total_chunks = len(all_chunks)

    score = 0.0
    for token in query_tokens:
        # TF: frequency in chunk
        tf = chunk_freq.get(token, 0) / max(len(chunk_tokens), 1)

        # IDF: inverse document frequency across all chunks
        docs_with_token = sum(1 for c in all_chunks if token in _tokenize(c))
        idf = math.log((total_chunks + 1) / (docs_with_token + 1)) + 1

        score += tf * idf

    return score


def upload_document(
    file_bytes: bytes,
    file_name: str,
    classification: str = "INTERNAL",
    owner: str = "Anonymous",
    department: str = "General",
    allowed_roles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Upload and index a document."""
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    # Extract text
    full_text = _extract_text(file_bytes, file_name)
    if not full_text.strip():
        full_text = f"[Document: {file_name}] — No text could be extracted."

    # Chunk text
    chunks = _chunk_text(full_text)

    # Store document metadata
    doc_meta = {
        "id": doc_id,
        "file_name": file_name,
        "classification": classification.upper(),
        "owner": owner,
        "department": department,
        "allowed_roles": allowed_roles or ROLE_ACCESS.get("USER", ["PUBLIC"]),
        "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "size_bytes": len(file_bytes),
        "chunk_count": len(chunks),
        "text_preview": full_text[:300] + "..." if len(full_text) > 300 else full_text,
    }
    _documents.append(doc_meta)

    # Store chunks
    for idx, chunk in enumerate(chunks):
        _chunks.append({
            "chunk_id": f"{doc_id}_chunk_{idx}",
            "doc_id": doc_id,
            "text": chunk,
            "classification": classification.upper(),
        })

    return doc_meta


def check_access(doc_classification: str, user_role: str) -> bool:
    """Check if user role has access to document classification."""
    allowed = ROLE_ACCESS.get(user_role.upper(), ["PUBLIC"])
    return doc_classification.upper() in allowed


def query_documents(
    query: str,
    user_role: str = "USER",
    doc_id: Optional[str] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Retrieve relevant chunks from documents, enforcing access control.
    Returns context text and access status.
    """
    if not _documents:
        return {
            "success": False,
            "access_denied": False,
            "context": "",
            "source_docs": [],
            "message": "No documents uploaded yet.",
        }

    query_tokens = _tokenize(query)

    # Filter accessible documents
    accessible_docs = []
    denied_docs = []

    for doc in _documents:
        if doc_id and doc["id"] != doc_id:
            continue
        if check_access(doc["classification"], user_role):
            accessible_docs.append(doc)
        else:
            denied_docs.append(doc)

    if not accessible_docs and denied_docs:
        return {
            "success": False,
            "access_denied": True,
            "context": "",
            "source_docs": [],
            "denied_docs": [d["file_name"] for d in denied_docs],
            "message": f"ACCESS DENIED — You do not have permission to access {len(denied_docs)} document(s). Your role ({user_role}) does not grant access to {denied_docs[0]['classification']} classified documents.",
        }

    # Get chunks for accessible docs
    accessible_chunk_texts = []
    accessible_chunk_data = []
    for doc in accessible_docs:
        for chunk in _chunks:
            if chunk["doc_id"] == doc["id"]:
                accessible_chunk_texts.append(chunk["text"])
                accessible_chunk_data.append(chunk)

    if not accessible_chunk_data:
        return {
            "success": False,
            "access_denied": False,
            "context": "",
            "source_docs": [],
            "message": "No document content found.",
        }

    # Score and rank chunks
    scored = []
    for chunk_data in accessible_chunk_data:
        score = _tf_idf_score(query_tokens, chunk_data["text"], accessible_chunk_texts)
        scored.append((score, chunk_data))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored[:top_k]

    # Build context
    context_parts = []
    source_docs = set()
    for score, chunk in top_chunks:
        if score > 0:
            context_parts.append(chunk["text"])
            source_docs.add(chunk["doc_id"])

    context = "\n\n---\n\n".join(context_parts)

    # Get source doc names
    source_doc_names = [d["file_name"] for d in _documents if d["id"] in source_docs]

    return {
        "success": bool(context),
        "access_denied": False,
        "context": context,
        "source_docs": source_doc_names,
        "chunks_retrieved": len(context_parts),
        "message": f"Retrieved {len(context_parts)} relevant chunk(s) from {len(source_doc_names)} document(s).",
    }


def get_all_documents() -> List[Dict[str, Any]]:
    return list(reversed(_documents))


def delete_document(doc_id: str) -> bool:
    global _documents, _chunks
    before = len(_documents)
    _documents = [d for d in _documents if d["id"] != doc_id]
    _chunks = [c for c in _chunks if c["doc_id"] != doc_id]
    return len(_documents) < before


def get_document_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    for d in _documents:
        if d["id"] == doc_id:
            return d
    return None
