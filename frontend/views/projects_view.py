"""
Aiera AI — Dedicated Projects Workspace View.
File: frontend/views/projects_view.py
"""

import streamlit as st


PROJECTS_DATA = {
    "Research": {
        "desc": "Academic literature, multimodal neural architectures, and privacy benchmark reports.",
        "icon": "🔬",
        "chats_count": 4,
        "files_count": 6,
        "notes": "Focused on DistilBERT latency optimization, token redaction algorithms, and Presidio benchmarks.",
    },
    "College Project": {
        "desc": "Final year capstone engineering project: Multimodal AI Privacy Risk Protection System.",
        "icon": "🎓",
        "chats_count": 8,
        "files_count": 12,
        "notes": "System documentation, architecture slides, video demo scripts, and evaluation metrics.",
    },
    "AI Security": {
        "desc": "Adversarial prompt injection testing, red-teaming datasets, and zero-trust firewall configurations.",
        "icon": "🛡️",
        "chats_count": 5,
        "files_count": 3,
        "notes": "DAN mode jailbreak vectors, system prompt overrides, and cryptographic receipt validation.",
    },
    "Personal": {
        "desc": "Private explorations, general knowledge searches, and experimental canvas drafts.",
        "icon": "👤",
        "chats_count": 3,
        "files_count": 1,
        "notes": "Personal notes, code experiments, and meeting summaries.",
    },
}


def render_projects_view() -> None:
    st.markdown(
        """
        <div style="padding: 10px 0 18px 0;">
            <h1 style="color:#0F172A; font-size:28px; font-weight:900; margin:0 0 6px 0;">
                📁 Projects Workspace
            </h1>
            <p style="color:#475569; font-size:14px; font-weight:500; margin:0;">
                Organize chats, uploaded files, research drafts, and canvas notes into isolated project workspaces.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    active_proj = st.session_state.get("active_project", "Research")

    # Folder Selection Tabs
    proj_names = list(PROJECTS_DATA.keys())
    selected_proj = st.radio("Select Active Project:", proj_names, index=proj_names.index(active_proj) if active_proj in proj_names else 0, horizontal=True)
    st.session_state["active_project"] = selected_proj

    proj_info = PROJECTS_DATA[selected_proj]

    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    # Project Overview Card
    st.markdown(
        f"""
        <div style="background:rgba(15,23,42,0.75); border:1px solid rgba(56,189,248,0.25); border-radius:16px; padding:20px; box-shadow:0 6px 20px rgba(0,0,0,0.3); margin-bottom:20px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:26px;">{proj_info['icon']}</span>
                    <span style="color:#FFFFFF; font-size:20px; font-weight:800;">{selected_proj} Workspace</span>
                </div>
                <span style="background:rgba(56,189,248,0.12); color:#38BDF8; border:1px solid rgba(56,189,248,0.3); font-size:11px; font-weight:700; padding:4px 12px; border-radius:20px;">
                    📁 Active Project
                </span>
            </div>
            <p style="color:#94A3B8; font-size:13.5px; margin:0 0 16px 0;">{proj_info['desc']}</p>
            <div style="display:flex; gap:20px; font-size:12.5px; border-top:1px solid rgba(255,255,255,0.06); padding-top:12px;">
                <span style="color:#E2E8F0;">💬 <strong>{proj_info['chats_count']}</strong> Saved Chats</span>
                <span style="color:#E2E8F0;">📎 <strong>{proj_info['files_count']}</strong> Documents</span>
                <span style="color:#E2E8F0;">🛡️ <strong>Zero-Trust</strong> Privacy Enabled</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Project Workspace Tools
    t_chat, t_files, t_notes, t_canvas = st.tabs([
        "💬 Project Chats",
        "📎 Attached Files",
        "📝 Research Notes",
        "✍️ Canvas Drafts"
    ])

    with t_chat:
        st.subheader(f"Chat Threads in {selected_proj}")
        st.write(f"Showing recent conversation threads associated with `{selected_proj}`:")
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.info(f"Thread: **{selected_proj} Architecture Deep Dive** (3 messages · Active)")
        with c2:
            if st.button("Open Chat →", key=f"open_proj_chat_{selected_proj}", use_container_width=True, type="primary"):
                st.session_state["selected_page"] = "Chat"
                st.rerun()

    with t_files:
        st.subheader(f"Uploaded Files & Knowledge Base ({selected_proj})")
        st.write("Documents attached to this project for retrieval-augmented generation (RAG):")
        st.markdown(
            """
            - 📄 `system_architecture_spec.pdf` (2.4 MB · Indexed)
            - 📄 `privacy_evaluation_metrics.csv` (420 KB · Indexed)
            - 📄 `research_references.docx` (1.1 MB · Indexed)
            """
        )
        if st.button("Manage Documents in Files →", key=f"proj_to_files_{selected_proj}"):
            st.session_state["selected_page"] = "Files"
            st.rerun()

    with t_notes:
        st.subheader("Project Summary & Notes")
        st.text_area("Workspace Notes:", value=proj_info["notes"], height=120, key=f"proj_notes_{selected_proj}")
        if st.button("Save Notes", key=f"save_notes_{selected_proj}"):
            st.success("Project notes updated successfully.")

    with t_canvas:
        st.subheader("Canvas Drafts")
        st.write("Open interactive writing and code scratchpad for this project:")
        if st.button("Open Project Canvas →", key=f"open_canvas_{selected_proj}", type="primary"):
            st.session_state["selected_page"] = "Canvas"
            st.rerun()
