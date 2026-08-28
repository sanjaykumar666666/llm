"""
Social Media Privacy Pre-Flight & Instagram Post Safety Gatekeeper.
File: backend/services/social_privacy_service.py

Validates photos, reels, and video posts before publishing to Instagram, TikTok, YouTube, or X.
Determines whether a person can safely upload the media or if it contains privacy leaks.
"""

import io
import os
import re
import time
import base64
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

from backend.services.image_privacy_service import ImagePrivacyService
from backend.services.video_content_analyzer import VideoContentAnalyzer
from backend.services.privacy_twin_service import PrivacyTwinService


class SocialPrivacyService:
    """
    Social Media Privacy Gatekeeper & Pre-Flight Post Analyzer.
    """

    @classmethod
    def analyze_caption_text(cls, caption: str) -> Dict[str, Any]:
        """Scans caption and hashtags for PII leaks and sensitive text."""
        findings = []
        # Phone
        if re.search(r'(?:\+?91[-\s]?)?[6-9]\d{9}|\b\d{10}\b', caption):
            findings.append({"type": "PHONE_NUMBER", "severity": "HIGH", "detail": "Phone number detected in caption."})
        # Email
        if re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', caption):
            findings.append({"type": "EMAIL_ADDRESS", "severity": "HIGH", "detail": "Email address detected in caption."})
        # UPI
        if re.search(r'[a-zA-Z0-9._-]+@[a-zA-Z]{3,}', caption) and any(k in caption.lower() for k in ["upi", "pay", "gpay", "phonepe"]):
            findings.append({"type": "UPI_ID", "severity": "CRITICAL", "detail": "UPI ID in caption may expose banking link."})
        # Govt ID / Aadhaar / PAN
        if re.search(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}\b', caption) or re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', caption):
            findings.append({"type": "GOVERNMENT_ID", "severity": "CRITICAL", "detail": "National ID number disclosed in caption."})
        # Address / Pin
        if re.search(r'\b\d{6}\b', caption) and any(k in caption.lower() for k in ["pin", "house", "sector", "flat", "street", "road"]):
            findings.append({"type": "ADDRESS_PIN", "severity": "HIGH", "detail": "Residential location / PIN code in caption."})

        return {
            "has_caption_leaks": len(findings) > 0,
            "findings": findings,
            "leak_count": len(findings)
        }

    @classmethod
    def evaluate_social_post(
        cls,
        media_bytes: bytes,
        filename: str,
        media_type: str = "image",  # "image" or "video"
        caption: str = "",
        target_platform: str = "Instagram",
        author_username: str = "creator_user",
        user_consent_given: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive Pre-Flight Social Media Privacy Audit.
        Answers: 'Can a person safely upload this post on Instagram / Social Media?'
        """
        t_start = time.perf_counter()
        caption_res = cls.analyze_caption_text(caption)
        
        media_findings: List[Dict[str, Any]] = []
        privacy_score = 100.0  # 100 = perfectly safe, 0 = critical leak
        is_safe_to_upload = True
        verdict = "SAFE_TO_UPLOAD"
        badge = "🟢 SAFE TO UPLOAD — NO PRIVACY LEAKS"
        recommendations = []
        sanitized_media_bytes = None

        if media_type == "image":
            # Process image through ImagePrivacyService
            img_res = ImagePrivacyService.process_image(
                image_bytes=media_bytes,
                filename=filename,
                protection_mode="REDACT_SENSITIVE",
                protect_faces=True,
                protect_qr_barcodes=True
            )
            detections = img_res.get("detections", [])
            sanitized_media_bytes = img_res.get("protected_image_bytes")
            
            for d in detections:
                dtype = d.get("type", "UNKNOWN")
                dcat = d.get("category", "UNKNOWN")
                prio = d.get("priority", "MEDIUM")

                if prio == "CRITICAL" or dtype in ["AADHAAR_NUMBER", "PAN_NUMBER", "BANK_ACCOUNT", "CREDIT_CARD", "PASSWORD", "API_KEY", "RESIDENTIAL_ADDRESS", "IDENTITY_QR_CODE"]:
                    privacy_score -= 35.0
                    media_findings.append({
                        "category": dcat,
                        "type": dtype,
                        "severity": "CRITICAL",
                        "where": d.get("where", "Visible in Image"),
                        "why": d.get("why", "Critical private identifier visible in background/foreground."),
                        "what_could_happen": d.get("what_could_happen", "Public exposure can lead to identity theft, financial fraud, or physical stalking."),
                        "what_to_do": d.get("what_to_do", "Redact this entity before publishing.")
                    })
                elif dtype in ["POSTAL_PIN_CODE", "PHONE_NUMBER", "EMAIL_ADDRESS", "DATE_OF_BIRTH", "PERSON_NAME"]:
                    privacy_score -= 15.0
                    media_findings.append({
                        "category": dcat,
                        "type": dtype,
                        "severity": "HIGH",
                        "where": d.get("where", "Visible in Image"),
                        "why": d.get("why", "Personal contact or location detail visible."),
                        "what_could_happen": d.get("what_could_happen", "Exposes private contact or personal details to followers and strangers."),
                        "what_to_do": d.get("what_to_do", "Mask or crop personal info.")
                    })
                elif dtype == "HUMAN_FACE":
                    # Single face is creator, multiple faces = bystander privacy check
                    face_count = sum(1 for x in detections if x.get("type") == "HUMAN_FACE")
                    if face_count > 1:
                        privacy_score -= 10.0
                        media_findings.append({
                            "category": "BIOMETRIC_FACE",
                            "type": "BYSTANDER_FACE",
                            "severity": "MEDIUM",
                            "where": d.get("where", "Background faces visible"),
                            "why": "Multiple persons / bystanders visible in the photo without explicit consent.",
                            "what_could_happen": "Posting pictures of non-consenting bystanders in public spaces may violate privacy rights.",
                            "what_to_do": "Blur bystander faces before posting to social media."
                        })

        else:
            # Process video through VideoContentAnalyzer
            vid_res = VideoContentAnalyzer.analyze_video_full(
                video_bytes_or_path=media_bytes,
                filename=filename
            )
            priv_summary = vid_res.get("privacy_assessment", {})
            copy_summary = vid_res.get("copyright_assessment", {})
            
            p_level = priv_summary.get("privacy_risk_level", "LOW")
            c_level = copy_summary.get("copyright_risk_level", "LOW")

            if p_level == "CRITICAL" or p_level == "HIGH":
                privacy_score -= 45.0
                for f in vid_res.get("analyzed_frames", []):
                    if f.get("privacy_risk") == "HIGH":
                        media_findings.append({
                            "category": "VIDEO_PRIVACY",
                            "type": f.get("detected_summary", "Sensitive Artifact"),
                            "severity": "CRITICAL",
                            "where": f.get("where", "In video timeline"),
                            "why": f.get("why", "Sensitive artifact displayed in video frames."),
                            "what_could_happen": f.get("what_could_happen", "Followers and web scrapers can capture private data from video frames."),
                            "what_to_do": f.get("what_to_do", "Cut this segment or blur the sensitive region.")
                        })
            elif p_level == "MEDIUM":
                privacy_score -= 20.0

            if c_level == "HIGH":
                privacy_score -= 25.0
                media_findings.append({
                    "category": "COPYRIGHT",
                    "type": "MUSIC_OR_VIDEO_COPYRIGHT",
                    "severity": "HIGH",
                    "where": "Audio / Visual Track",
                    "why": copy_summary.get("copyright_reason", "Potential commercial music or watermarked content detected."),
                    "what_could_happen": "Instagram / Meta may mute audio, block monetization, or remove the reel for copyright strike.",
                    "what_to_do": "Replace audio with Instagram royalty-free audio library track."
                })

        # Add caption leak penalties
        if caption_res["has_caption_leaks"]:
            privacy_score -= (caption_res["leak_count"] * 20.0)
            for c_leak in caption_res["findings"]:
                media_findings.append({
                    "category": "CAPTION_LEAK",
                    "type": c_leak["type"],
                    "severity": c_leak["severity"],
                    "where": "Post Caption & Hashtags",
                    "why": c_leak["detail"],
                    "what_could_happen": "Caption text is indexed by search engines and AI scrapers.",
                    "what_to_do": "Remove phone numbers, emails, or IDs from the caption text."
                })

        privacy_score = max(0.0, min(100.0, round(privacy_score, 1)))

        # Determine Final Verdict for the Person Uploading
        if privacy_score >= 85.0:
            is_safe_to_upload = True
            verdict = "SAFE_TO_UPLOAD"
            badge = "🟢 SAFE TO UPLOAD ON INSTAGRAM"
            recommendations.append("✅ Post is clean. Zero privacy leaks or copyright violations detected.")
            recommendations.append("🚀 You can post this directly to Instagram Feed, Stories, or Reels.")
        elif privacy_score >= 50.0:
            is_safe_to_upload = False
            verdict = "WARNING_REDACTION_RECOMMENDED"
            badge = "🟡 CAUTION: REDACTION RECOMMENDED BEFORE POSTING"
            recommendations.append("⚠️ Contains minor privacy leaks (e.g., bystander faces, contact info, or background text).")
            recommendations.append("🛡️ Click 'Auto-Sanitize Post' to blur background leaks before sharing.")
        else:
            is_safe_to_upload = False
            verdict = "BLOCKED_DANGEROUS_LEAK"
            badge = "🔴 DO NOT UPLOAD — CRITICAL PRIVACY LEAK"
            recommendations.append("🛑 High-risk personal identifiers detected (Aadhaar/Govt ID/Bank info/Address).")
            recommendations.append("❌ Sharing this publicly on Instagram exposes you or others to fraud and identity theft.")

        proc_ms = round((time.perf_counter() - t_start) * 1000, 2)

        return {
            "success": True,
            "filename": filename,
            "media_type": media_type,
            "target_platform": target_platform,
            "author_username": author_username,
            "privacy_score": privacy_score,
            "is_safe_to_upload": is_safe_to_upload,
            "verdict": verdict,
            "badge": badge,
            "total_issues_found": len(media_findings),
            "findings": media_findings,
            "recommendations": recommendations,
            "caption_analysis": caption_res,
            "sanitized_media_bytes": sanitized_media_bytes,
            "processing_ms": proc_ms,
            "instagram_guidelines_passed": is_safe_to_upload
        }
