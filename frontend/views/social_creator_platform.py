"""
Instagram / Social Media Creator Platform & Pre-Flight Privacy Gatekeeper.
File: frontend/views/social_creator_platform.py

Features:
  1. 🔐 Creator Login / Authentication Gateway (Session state & profile switcher).
  2. 📝 Creator Studio & Pre-Flight Privacy Audit (Images & Video Reels).
  3. 📱 Dynamic Live Instagram Feed Preview (0 initial likes/comments, live interaction).
  4. 🌐 Public Social Feed (Explore safely published posts by the community).
"""

import io
import os
import time
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
from PIL import Image
import streamlit as st

from backend.services.social_privacy_service import SocialPrivacyService
from backend.services.image_privacy_service import ImagePrivacyService
from backend.services.video_content_analyzer import VideoContentAnalyzer
from backend.services.video_privacy_service import VideoPrivacyService


def _init_social_session_state():
    """Initializes session state for Creator Auth, Public Feed, and Likes/Comments."""
    if "creator_logged_in" not in st.session_state:
        st.session_state["creator_logged_in"] = True  # Default logged in as demo creator
    if "creator_user" not in st.session_state:
        st.session_state["creator_user"] = {
            "username": "@sanjay_creator",
            "display_name": "Sanjay Kumar",
            "bio": "AI Security & Creative Media Explorer 🛡️✨",
            "avatar": "SK",
            "posts_count": 0
        }
    if "current_post_likes" not in st.session_state:
        st.session_state["current_post_likes"] = 0
    if "current_post_user_liked" not in st.session_state:
        st.session_state["current_post_user_liked"] = False
    if "current_post_comments" not in st.session_state:
        st.session_state["current_post_comments"] = []
    if "public_social_feed" not in st.session_state:
        # Default sample clean verified post in public feed
        st.session_state["public_social_feed"] = [
            {
                "id": "post_seed_1",
                "author": "@aiera_official",
                "display_name": "Aiera AI Community",
                "avatar": "AI",
                "media_type": "image",
                "media_b64": "",
                "caption": "Welcome to InstaSafe! The first social media feed where every post is verified safe from identity leaks and PII! 🛡️✨ #privacy #safecreator",
                "likes": 12,
                "comments": [{"user": "@sanjay_creator", "text": "Excited for privacy-first social sharing!", "time": "10m ago"}],
                "time_str": "1 hour ago",
                "is_verified_safe": True
            }
        ]


def render_social_creator_platform_view() -> None:
    _init_social_session_state()
    creator = st.session_state["creator_user"]
    is_logged_in = st.session_state["creator_logged_in"]

    # ── 1. Header & Creator Login Status Bar ───────────────────────────────────
    st.markdown(
        """
        <div style="padding: 4px 0 12px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <div>
                    <h1 style="font-size:26px; font-weight:900; margin:0 0 4px 0; color:#F8FAFC; letter-spacing:0.02em;">
                        📱 InstaSafe — Social Media Creator & Privacy Gatekeeper
                    </h1>
                    <p style="color:#94A3B8; font-size:13.5px; margin:0;">
                        Public social platform with pre-flight privacy verification. Scan photos and video reels before sharing to Instagram.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Creator Authentication Ribbon ──────────────────────────────────────────
    with st.expander(f"🔐 Creator Account: {creator['username']} ({creator['display_name']}) — Click to Switch User / Login", expanded=not is_logged_in):
        c_l1, c_l2, c_l3 = st.columns([1.5, 1.2, 1])
        with c_l1:
            inp_user = st.text_input("Creator Username / Handle:", value=creator["username"], key="auth_inp_user")
            inp_name = st.text_input("Display Name:", value=creator["display_name"], key="auth_inp_name")
        with c_l2:
            quick_persona = st.selectbox(
                "Quick Login Persona Switcher:",
                [
                    "@sanjay_creator (Sanjay Kumar)",
                    "@tech_traveler (Aero Explorer)",
                    "@privacy_advocate (Priya V.)",
                    "@creative_lens (Ananya D.)"
                ],
                key="auth_quick_persona"
            )
        with c_l3:
            st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
            if st.button("🔑 UPDATE / LOGIN AS CREATOR", type="primary", use_container_width=True, key="btn_auth_login"):
                p_user = quick_persona.split(" ")[0].strip()
                p_name = quick_persona.split("(")[1].replace(")", "").strip() if "(" in quick_persona else inp_name
                st.session_state["creator_user"] = {
                    "username": p_user if p_user.startswith("@") else inp_user,
                    "display_name": p_name,
                    "bio": "AI & Content Creator 🛡️",
                    "avatar": p_user.replace("@", "")[:2].upper(),
                    "posts_count": creator.get("posts_count", 0)
                }
                st.session_state["creator_logged_in"] = True
                st.success(f"Logged in as {p_user}!")
                st.rerun()

    # ── 2. Top Navigation Tabs: Creator Studio vs Public Social Feed ───────────
    tab_create, tab_feed = st.tabs([
        "📝 1. Creator Studio & Pre-Flight Privacy Audit",
        f"🌐 2. Public Social Feed ({len(st.session_state['public_social_feed'])} Safe Posts)"
    ])

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 1: CREATOR STUDIO & INSTAGRAM PREVIEW
    # ──────────────────────────────────────────────────────────────────────────
    with tab_create:
        col_composer, col_preview = st.columns([1.1, 1])

        with col_composer:
            st.markdown(
                f"""
                <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:16px; margin-bottom:14px;">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
                        <div style="font-size:14px; font-weight:800; color:#F8FAFC;">
                            📝 COMPOSE NEW SOCIAL POST / REEL
                        </div>
                        <div style="font-size:12px; color:#38BDF8; font-weight:700;">
                            Posting as: {creator['username']}
                        </div>
                    </div>
                """,
                unsafe_allow_html=True
            )

            media_type = st.radio("Select Media Type:", ["📷 Photo Post", "🎥 Video Reel / Short"], horizontal=True, key="soc_media_type")
            is_video = "Video" in media_type

            c_plat1, c_plat2 = st.columns([1.2, 1])
            with c_plat1:
                target_platform = st.selectbox("Target Social Platform:", ["Instagram", "YouTube Shorts", "TikTok", "X / Twitter"], key="soc_platform")
            with c_plat2:
                visibility = st.selectbox("Post Visibility:", ["Public Community", "Followers Only", "Private Draft"], key="soc_visibility")

            up_media = st.file_uploader(
                "Upload Photo or Video Reel:",
                type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "avi"] if is_video else ["png", "jpg", "jpeg", "webp"],
                key="soc_media_uploader"
            )

            preset_choice = st.selectbox(
                "Or Test with Creator Sample Preset:",
                [
                    "🌿 Clean Travel Video / Photo (Safe to Upload)",
                    "⚠️ Photo with Leaked ID Card / Aadhaar in Background",
                    "💳 Reel with Visible Credit Card & Bank Detail",
                    "👥 Public Event Photo with Bystander Faces",
                    "None (Use Uploaded Media)"
                ],
                key="soc_preset_choice"
            )

            caption_text = st.text_area(
                "Post Caption & Hashtags:",
                value="Enjoying the weekend vibes! 🌴✨ Catch me live or DM for collaborations! #travel #lifestyle",
                height=75,
                key="soc_caption_text"
            )

            st.markdown("</div>", unsafe_allow_html=True)

            # Process / Load Media Bytes
            media_bytes = b""
            filename = "post.mp4" if is_video else "post.png"

            if up_media is not None:
                media_bytes = up_media.getvalue()
                filename = up_media.name
                actual_type = "video" if any(filename.lower().endswith(ext) for ext in [".mp4", ".mov", ".avi", ".webm"]) else "image"
            else:
                actual_type = "video" if is_video else "image"
                if is_video:
                    if "Clean Travel" in preset_choice:
                        media_bytes, filename = VideoPrivacyService.generate_sample_video("🟢 Clean Landscape Video (Zero PII)")
                    elif "Credit Card" in preset_choice:
                        media_bytes, filename = VideoPrivacyService.generate_sample_video("💳 Financial Video (Bank & Credit Card)")
                    else:
                        media_bytes, filename = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")
                else:
                    from frontend.views.image_analyzer import _generate_sample_image
                    if "Clean Travel" in preset_choice:
                        media_bytes, filename = _generate_sample_image("🌿 Clean Photo (Zero Leaks)")
                    elif "Leaked ID" in preset_choice:
                        media_bytes, filename = _generate_sample_image("🪪 Identity Card (Aadhaar & PAN)")
                    else:
                        media_bytes, filename = _generate_sample_image("💳 Credit Card & Bank Account")

            # Run Safety Gatekeeper Button
            if st.button("🛡️ AUDIT POST PRIVACY & CAN I UPLOAD?", type="primary", use_container_width=True, key="btn_run_soc_audit"):
                with st.spinner("🤖 Scanning visual frames, caption text, bystander faces, and copyright risk…"):
                    audit_res = SocialPrivacyService.evaluate_social_post(
                        media_bytes=media_bytes,
                        filename=filename,
                        media_type=actual_type,
                        caption=caption_text,
                        target_platform=target_platform,
                        author_username=creator["username"]
                    )
                    st.session_state["active_social_audit"] = audit_res

        # ── RIGHT COLUMN: LIVE INSTAGRAM POST SIMULATOR ───────────────────────
        with col_preview:
            st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-bottom:8px;'>📱 LIVE INSTAGRAM POST PREVIEW (NEW POST DRAFT)</div>", unsafe_allow_html=True)

            media_b64 = base64.b64encode(media_bytes).decode("utf-8") if media_bytes else ""
            if actual_type == "video":
                media_html = f"""<video src="data:video/mp4;base64,{media_b64}" controls autoplay muted loop style="width:100%; max-height:380px; background:#000000; display:block; object-fit:contain; border-top:1px solid rgba(255,255,255,0.1); border-bottom:1px solid rgba(255,255,255,0.1);"></video>"""
            else:
                media_html = f"""<img src="data:image/png;base64,{media_b64}" alt="Instagram Post" style="width:100%; max-height:380px; background:#000000; display:block; object-fit:contain; border-top:1px solid rgba(255,255,255,0.1); border-bottom:1px solid rgba(255,255,255,0.1);" />"""

            clean_cap = caption_text[:110] + ("..." if len(caption_text) > 110 else "")
            likes_count = st.session_state["current_post_likes"]
            user_liked = st.session_state["current_post_user_liked"]
            comments_list = st.session_state["current_post_comments"]
            
            # Dynamic realistic like label (starts at 0 / No likes yet)
            if likes_count == 0:
                likes_label = "<span style='color:#94A3B8; font-weight:500;'>No likes yet • Be the first to like this post</span>"
            elif likes_count == 1 and user_liked:
                likes_label = "<span style='color:#FFFFFF; font-weight:800;'>1 like (You liked this)</span>"
            else:
                likes_label = f"<span style='color:#FFFFFF; font-weight:800;'>{likes_count} likes</span>"

            # Render Instagram Card
            st.markdown(
                f"""<div style="background:#050505; border:1.5px solid rgba(255,255,255,0.18); border-radius:18px; overflow:hidden; max-width:440px; margin:0 auto 12px auto; box-shadow:0 14px 40px rgba(0,0,0,0.65);">
<!-- Header -->
<div style="padding:12px 14px; display:flex; align-items:center; justify-content:space-between; background:#0A0A0A;">
<div style="display:flex; align-items:center; gap:10px;">
<div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(45deg, #F58529, #DD2A7B, #8134AF); padding:2.5px; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
<div style="width:100%; height:100%; border-radius:50%; background:#1E293B; display:flex; align-items:center; justify-content:center; color:#FFFFFF; font-size:12px; font-weight:900;">
{creator['avatar']}
</div>
</div>
<div>
<div style="color:#FFFFFF; font-weight:800; font-size:13px; line-height:1.2;">{creator['username']}</div>
<div style="color:#94A3B8; font-size:10.5px;">Original Audio • {target_platform}</div>
</div>
</div>
<div style="color:#94A3B8; font-size:18px; cursor:pointer; padding-right:4px;">•••</div>
</div>

<!-- Media (Image / Video) -->
{media_html}

<!-- Footer Actions & Caption -->
<div style="padding:12px 14px; background:#0A0A0A;">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; color:#FFFFFF; font-size:20px;">
<div style="display:flex; align-items:center; gap:14px;">
<span>{'❤️' if user_liked else '🤍'}</span>
<span>💬</span>
<span>✈️</span>
</div>
<span>🔖</span>
</div>
<div style="font-size:12.5px; margin-bottom:5px;">{likes_label}</div>
<div style="color:#CBD5E1; font-size:12px; line-height:1.4;">
<strong style="color:#FFFFFF; margin-right:6px;">{creator['username']}</strong><span>{clean_cap}</span>
</div>
<div style="color:#64748B; font-size:10.5px; margin-top:6px;">
{f'View all {len(comments_list)} comments' if comments_list else 'No comments yet. Start the conversation...'} • Just now
</div>
</div>
</div>""",
                unsafe_allow_html=True
            )

            # Interactive Live Like & Comment Row
            c_lk, c_cm = st.columns([1, 2])
            with c_lk:
                btn_heart_label = "💔 Unlike" if user_liked else "❤️ Like Post"
                if st.button(btn_heart_label, key="btn_toggle_like", use_container_width=True):
                    if user_liked:
                        st.session_state["current_post_likes"] = max(0, st.session_state["current_post_likes"] - 1)
                        st.session_state["current_post_user_liked"] = False
                    else:
                        st.session_state["current_post_likes"] += 1
                        st.session_state["current_post_user_liked"] = True
                    st.rerun()

            with c_cm:
                new_comment_text = st.text_input("Add a comment as creator:", placeholder="Write a comment...", key="inp_add_comment", label_visibility="collapsed")
                if st.button("💬 Post Comment", key="btn_post_comment", use_container_width=True):
                    if new_comment_text.strip():
                        st.session_state["current_post_comments"].append({
                            "user": creator["username"],
                            "text": new_comment_text.strip(),
                            "time": "Just now"
                        })
                        st.rerun()

        # ── BOTTOM SECTION: CAN I UPLOAD? PRE-FLIGHT VERDICT ──────────────────
        audit = st.session_state.get("active_social_audit")
        if audit and audit.get("success"):
            p_score = audit.get("privacy_score", 100.0)
            is_safe = audit.get("is_safe_to_upload", True)
            badge = audit.get("badge", "")
            findings = audit.get("findings", [])
            proc_ms = audit.get("processing_ms", 0)

            banner_bg = "rgba(16,185,129,0.12)" if is_safe else ("rgba(245,158,11,0.12)" if p_score >= 50 else "rgba(239,68,68,0.15)")
            banner_border = "#10B981" if is_safe else ("#F59E0B" if p_score >= 50 else "#EF4444")
            banner_color = "#34D399" if is_safe else ("#FBBF24" if p_score >= 50 else "#F87171")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"""<div style="background:{banner_bg}; border:2px solid {banner_border}; border-radius:12px; padding:16px 20px; margin-bottom:16px;">
<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
<div>
<div style="font-size:17px; font-weight:900; color:{banner_color}; margin-bottom:4px;">
{badge}
</div>
<div style="font-size:12.5px; color:#CBD5E1;">
Safety Assessment Score: <strong>{p_score}/100</strong> • Scanned in <strong>{proc_ms}ms</strong> for {target_platform}.
</div>
</div>
<div style="font-size:24px; font-weight:900; color:{banner_color};">
{'✅ READY TO POST' if is_safe else ('⚠️ CAUTION' if p_score >= 50 else '🛑 BLOCKED')}
</div>
</div>
</div>""",
                unsafe_allow_html=True
            )

            # Publish to Public Feed Button
            if is_safe:
                if st.button("🚀 PUBLISH POST TO PUBLIC SOCIAL FEED", type="primary", use_container_width=True, key="btn_publish_public"):
                    new_public_post = {
                        "id": f"post_{int(time.time())}",
                        "author": creator["username"],
                        "display_name": creator["display_name"],
                        "avatar": creator["avatar"],
                        "media_type": actual_type,
                        "media_b64": media_b64,
                        "caption": caption_text,
                        "likes": st.session_state["current_post_likes"],
                        "comments": list(st.session_state["current_post_comments"]),
                        "time_str": "Just now",
                        "is_verified_safe": True
                    }
                    st.session_state["public_social_feed"].insert(0, new_public_post)
                    st.session_state["current_post_likes"] = 0
                    st.session_state["current_post_user_liked"] = False
                    st.session_state["current_post_comments"] = []
                    st.success("🎉 Post successfully verified and published to the Public Social Feed!")
                    st.rerun()

            # Findings & Explanations List
            if findings:
                st.markdown("<div style='font-size:14px; font-weight:800; color:#F8FAFC; margin-bottom:8px;'>🔍 DETECTED PRIVACY ISSUES & WHAT YOU SHOULD DO</div>", unsafe_allow_html=True)
                for idx, item in enumerate(findings):
                    sev_color = "#EF4444" if item.get("severity") == "CRITICAL" else "#F59E0B"
                    st.markdown(
                        f"""<div style="background:rgba(15,23,42,0.8); border-left:4px solid {sev_color}; border-radius:8px; padding:12px 16px; margin-bottom:8px;">
<div style="color:{sev_color}; font-weight:800; font-size:13px; margin-bottom:4px;">
🔴 {item.get('type')} ({item.get('category')}) — Severity: {item.get('severity')}
</div>
<div style="font-size:12px; color:#E2E8F0; margin-bottom:2px;">
📍 <strong>Where:</strong> {item.get('where')}
</div>
<div style="font-size:12px; color:#CBD5E1; margin-bottom:2px;">
❓ <strong>Why is it private:</strong> {item.get('why')}
</div>
<div style="font-size:12px; color:#FCA5A5; margin-bottom:2px;">
⚠️ <strong>What could happen if posted:</strong> {item.get('what_could_happen')}
</div>
<div style="font-size:12px; color:#6EE7B7;">
🛡️ <strong>What you should do:</strong> {item.get('what_to_do')}
</div>
</div>""",
                        unsafe_allow_html=True
                    )

            # One-Click Auto-Sanitize
            if not is_safe and audit.get("sanitized_media_bytes"):
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                st.download_button(
                    label="🛡️ DOWNLOAD AUTO-SANITIZED SAFE MEDIA (READY TO POST)",
                    data=audit["sanitized_media_bytes"],
                    file_name=f"safe_instagram_{filename}",
                    mime="image/png",
                    type="primary",
                    use_container_width=True
                )

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 2: PUBLIC SOCIAL FEED (COMMUNITY WALL)
    # ──────────────────────────────────────────────────────────────────────────
    with tab_feed:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px 16px; margin-bottom:16px; font-size:12.5px; color:#CBD5E1;">
                🌐 <strong>Public Social Media Wall:</strong> Every post in this public feed has passed <strong>AI Privacy Shield Pre-Flight Verification</strong> (zero leaked PII, no unredacted IDs or addresses).
            </div>
            """,
            unsafe_allow_html=True
        )

        feed_posts = st.session_state["public_social_feed"]
        if not feed_posts:
            st.info("No public posts published yet. Be the first to publish in Tab 1!")
        else:
            for p_idx, post in enumerate(feed_posts):
                p_id = post["id"]
                p_author = post["author"]
                p_avatar = post["avatar"]
                p_cap = post["caption"]
                p_likes = post["likes"]
                p_comments = post.get("comments", [])
                p_time = post["time_str"]
                p_b64 = post["media_b64"]
                p_type = post.get("media_type", "image")

                # Media render inside public card
                if p_b64:
                    if p_type == "video":
                        p_media_html = f"""<video src="data:video/mp4;base64,{p_b64}" controls style="width:100%; max-height:360px; background:#000000; display:block; object-fit:contain;"></video>"""
                    else:
                        p_media_html = f"""<img src="data:image/png;base64,{p_b64}" alt="Post" style="width:100%; max-height:360px; background:#000000; display:block; object-fit:contain;" />"""
                else:
                    p_media_html = """<div style="background:linear-gradient(135deg, #1E293B, #0F172A); height:160px; display:flex; align-items:center; justify-content:center; color:#94A3B8; font-size:13px;">🛡️ AI Privacy Shield Verified Media Post</div>"""

                # Render each Public Feed Post
                st.markdown(
                    f"""<div style="background:#050505; border:1.5px solid rgba(255,255,255,0.16); border-radius:18px; overflow:hidden; max-width:460px; margin:0 auto 16px auto; box-shadow:0 10px 30px rgba(0,0,0,0.6);">
<!-- Post Header -->
<div style="padding:12px 14px; display:flex; align-items:center; justify-content:space-between; background:#0A0A0A;">
<div style="display:flex; align-items:center; gap:10px;">
<div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(45deg, #F58529, #DD2A7B, #8134AF); padding:2px; display:flex; align-items:center; justify-content:center;">
<div style="width:100%; height:100%; border-radius:50%; background:#1E293B; display:flex; align-items:center; justify-content:center; color:#FFFFFF; font-size:12px; font-weight:900;">
{p_avatar}
</div>
</div>
<div>
<div style="color:#FFFFFF; font-weight:800; font-size:13px; display:flex; align-items:center; gap:6px;">
<span>{p_author}</span>
<span style="background:rgba(16,185,129,0.2); color:#34D399; border:1px solid rgba(16,185,129,0.4); border-radius:10px; padding:1px 6px; font-size:9.5px; font-weight:800;">✓ VERIFIED SAFE</span>
</div>
<div style="color:#94A3B8; font-size:10.5px;">Public Feed • {p_time}</div>
</div>
</div>
<div style="color:#94A3B8; font-size:16px;">•••</div>
</div>

<!-- Media -->
{p_media_html}

<!-- Actions & Comments -->
<div style="padding:12px 14px; background:#0A0A0A;">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; color:#FFFFFF; font-size:19px;">
<div style="display:flex; align-items:center; gap:12px;">
<span>❤️</span>
<span>💬</span>
<span>✈️</span>
</div>
<span>🔖</span>
</div>
<div style="color:#FFFFFF; font-weight:800; font-size:12px; margin-bottom:4px;">{p_likes} likes</div>
<div style="color:#CBD5E1; font-size:12px; line-height:1.4;">
<strong style="color:#FFFFFF; margin-right:6px;">{p_author}</strong><span>{p_cap}</span>
</div>
</div>
</div>""",
                    unsafe_allow_html=True
                )

                # Public Comments and Like button for this post
                c_p1, c_p2 = st.columns([1, 2])
                with c_p1:
                    if st.button(f"❤️ Like ({p_likes})", key=f"btn_feed_like_{p_id}", use_container_width=True):
                        post["likes"] += 1
                        st.rerun()
                with c_p2:
                    pub_cm_text = st.text_input(f"Comment on {p_author}:", placeholder="Write a comment...", key=f"inp_feed_cm_{p_id}", label_visibility="collapsed")
                    if st.button(f"💬 Send Comment", key=f"btn_send_cm_{p_id}", use_container_width=True):
                        if pub_cm_text.strip():
                            if "comments" not in post:
                                post["comments"] = []
                            post["comments"].append({
                                "user": creator["username"],
                                "text": pub_cm_text.strip(),
                                "time": "Just now"
                            })
                            st.rerun()

                # Display existing comments for this post
                if p_comments:
                    with st.expander(f"💬 View Comments ({len(p_comments)})", expanded=False):
                        for c in p_comments:
                            st.markdown(f"**{c.get('user', 'User')}**: {c.get('text', '')} *(<span style='color:#94A3B8; font-size:10px;'>{c.get('time', '')}</span>)*", unsafe_allow_html=True)
                st.markdown("<div style='height:1px; background:rgba(255,255,255,0.08); margin:12px 0 20px 0;'></div>", unsafe_allow_html=True)
