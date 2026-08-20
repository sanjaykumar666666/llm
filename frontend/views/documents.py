"""
AI Trust Chat — Document Library View (RAG)
File: frontend/views/documents.py
"""

import streamlit as st
from backend.services.rag_engine import (
    get_all_documents, upload_document, delete_document,
    CLASSIFICATION_LEVELS, ROLE_ACCESS,
)

CLASSIFICATION_COLORS = {
    "PUBLIC":       ("#10B981", "rgba(16,185,129,0.12)"),
    "INTERNAL":     ("#06B6D4", "rgba(6,182,212,0.12)"),
    "CONFIDENTIAL": ("#F59E0B", "rgba(245,158,11,0.12)"),
    "RESTRICTED":   ("#EF4444", "rgba(239,68,68,0.12)"),
}


def render_documents_view() -> None:
    user_role = st.session_state.get("user_role", "USER")
    user_id = st.session_state.get("user_id", "Employee-001")

    st.markdown(
        "<h1 style='margin-bottom:4px;'>📁 Document Library</h1>"
        "<p style='color:#94A3B8; font-size:14px; margin-top:0;'>"
        "Upload and manage documents for RAG-based Q&amp;A with access-controlled retrieval.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Access control info ────────────────────────────────────────────────────
    accessible = ROLE_ACCESS.get(user_role.upper(), ["PUBLIC"])
    st.markdown(
        f"<div style='background:rgba(6,182,212,0.08); border:1px solid rgba(6,182,212,0.2); "
        f"border-radius:10px; padding:12px; margin-bottom:16px;'>"
        f"<strong style='color:#06B6D4;'>Your Access Level ({user_role})</strong><br>"
        f"<span style='color:#94A3B8; font-size:13px;'>You can access: "
        f"<code>{' · '.join(accessible)}</code></span></div>",
        unsafe_allow_html=True,
    )

    # ── Upload Section ─────────────────────────────────────────────────────────
    with st.expander("📤 Upload New Document", expanded=True):
        col_file, col_meta = st.columns([2, 1])
        with col_file:
            uploaded = st.file_uploader(
                "Select document (PDF, TXT, DOCX, CSV, MD):",
                type=["pdf", "txt", "docx", "csv", "md"],
                key="doc_lib_upload",
            )
        with col_meta:
            classification = st.selectbox("Classification", CLASSIFICATION_LEVELS, index=1, key="doc_class")
            department = st.text_input("Department", value="General", key="doc_dept")

        if uploaded:
            if st.button("📤 Upload & Index", type="primary", key="do_upload_doc"):
                with st.spinner(f"Indexing {uploaded.name}..."):
                    doc_bytes = uploaded.read()
                    meta = upload_document(
                        file_bytes=doc_bytes,
                        file_name=uploaded.name,
                        classification=classification,
                        owner=user_id,
                        department=department,
                    )
                st.success(f"✅ **{uploaded.name}** uploaded! {meta['chunk_count']} chunks indexed.")
                st.rerun()

    # ── Document List ──────────────────────────────────────────────────────────
    docs = get_all_documents()
    st.subheader(f"📚 Indexed Documents ({len(docs)} total)")

    if not docs:
        st.info("No documents uploaded yet. Upload a document above to get started.")
        return

    for doc in docs:
        cls = doc["classification"]
        cls_color, cls_bg = CLASSIFICATION_COLORS.get(cls, ("#94A3B8", "rgba(148,163,184,0.12)"))
        can_access = cls in ROLE_ACCESS.get(user_role.upper(), [])

        with st.container():
            st.markdown(
                f"<div style='background:rgba(11,39,66,0.5); border:1px solid rgba(59,130,246,0.15); "
                f"border-radius:12px; padding:16px; margin-bottom:10px;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:start;'>"
                f"<div>"
                f"<strong style='color:#E2E8F0; font-size:15px;'>📄 {doc['file_name']}</strong><br>"
                f"<span style='font-size:12px; color:#64748B;'>"
                f"Owner: {doc['owner']} · Dept: {doc['department']} · "
                f"{doc['chunk_count']} chunks · {doc['size_bytes']:,} bytes · {doc['uploaded_at']}"
                f"</span>"
                f"</div>"
                f"<span style='background:{cls_bg}; border:1px solid {cls_color}44; color:{cls_color}; "
                f"font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px;'>{cls}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            col_access, col_preview, col_chat, col_del = st.columns([1.5, 1.5, 2, 1])
            with col_access:
                if can_access:
                    st.markdown("<span style='color:#10B981; font-size:12px;'>✅ You have access</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:#EF4444; font-size:12px;'>🔒 Access denied ({cls} requires higher role)</span>", unsafe_allow_html=True)

            with col_preview:
                if st.button("👁️ Preview", key=f"preview_{doc['id']}", help="View text preview"):
                    st.session_state[f"show_preview_{doc['id']}"] = not st.session_state.get(f"show_preview_{doc['id']}", False)

            with col_chat:
                if can_access:
                    if st.button("💬 Chat with this document", key=f"chat_doc_{doc['id']}", type="primary"):
                        st.session_state["rag_doc_id"] = doc["id"]
                        st.session_state["rag_doc_name"] = doc["file_name"]
                        st.session_state["selected_page"] = "AI Trust Chat"
                        st.rerun()
                else:
                    st.markdown(f"<span style='color:#64748B; font-size:12px;'>Requires {cls} access</span>", unsafe_allow_html=True)

            with col_del:
                if st.button("🗑️", key=f"del_doc_{doc['id']}", help="Delete document"):
                    delete_document(doc["id"])
                    st.success("Document deleted.")
                    st.rerun()

            if st.session_state.get(f"show_preview_{doc['id']}"):
                st.text_area("Document Preview:", value=doc.get("text_preview", ""), height=120, key=f"prev_ta_{doc['id']}", disabled=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ── Classification Guide ───────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Classification Guide")
    guide_data = {
        "PUBLIC":       ("🟢", "Accessible by all users", "Marketing materials, public docs"),
        "INTERNAL":     ("🔵", "Accessible by all employees (USER+)", "Internal policies, guidelines"),
        "CONFIDENTIAL": ("🟡", "Accessible by MANAGER+ and AUDITOR", "Financial reports, strategies"),
        "RESTRICTED":   ("🔴", "Accessible by ADMIN only", "CEO salary, trade secrets, PII databases"),
    }
    for cls, (icon, desc, examples) in guide_data.items():
        cls_color, cls_bg = CLASSIFICATION_COLORS[cls]
        st.markdown(
            f"<div style='display:flex; gap:12px; align-items:center; margin-bottom:8px;'>"
            f"<span style='background:{cls_bg}; border:1px solid {cls_color}44; color:{cls_color}; "
            f"font-size:11px; font-weight:700; padding:3px 12px; border-radius:20px; min-width:100px; "
            f"text-align:center;'>{icon} {cls}</span>"
            f"<div><strong style='color:#E2E8F0; font-size:13px;'>{desc}</strong> "
            f"<span style='color:#64748B; font-size:12px;'>— e.g. {examples}</span></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
