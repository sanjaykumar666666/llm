"""
Explicit Mock/Demo ML Engine Service for Phase 1 UI Foundation & Explainability.
File: backend/services/mock_ml_engine.py
"""

from typing import Dict, Any, List

class MockMLEngineService:
    """Provides explicitly marked mock ML predictions & LIME/SHAP explainability for Phase 1 UI development."""

    @staticmethod
    def process_explainability(modality: str = "Text", content: str = "") -> Dict[str, Any]:
        """Provides LIME & SHAP feature contributions, risk breakdowns, and non-technical explanations."""

        if modality.lower() == "image":
            return {
                "modality": "Image",
                "risk_score": 87,
                "status": "BLOCKED",
                "risk_level": "HIGH",
                "detected_risks": [
                    "Personal Information",
                    "Credential Information",
                    "Confidential Content",
                    "Document Identity Record"
                ],
                "affected_features": "OCR extracted driver license number (D9910482) and home address line from image keyframe region [120, 45, 340, 210].",
                "feature_contributions": [
                    {"rank": "#1", "type": "Supporting", "feature": "Personal Information", "weight": 0.1513, "is_risk": False},
                    {"rank": "#2", "type": "Supporting", "feature": "Driver License ID", "weight": 0.1483, "is_risk": False},
                    {"rank": "#3", "type": "Supporting", "feature": "Home Address", "weight": 0.1301, "is_risk": False},
                    {"rank": "#4", "type": "Risk Factor", "feature": "Confidential Document", "weight": 0.1022, "is_risk": True}
                ],
                "privacy_breakdown": {
                    "Personal Information": "HIGH",
                    "Credentials": "HIGH",
                    "Financial Information": "MEDIUM",
                    "Confidential Content": "LOW"
                },
                "detected_entities": ["Personal information", "Driver license ID", "Home address", "Credential"],
                "recommended_action": "BLOCK INPUT",
                "why_explanation": "The system detected privacy-sensitive information in the image scan. The detected entities contributed strongly to the overall privacy-risk score. The input was therefore classified as high risk.",
                "model_info": {
                    "model": "Hybrid BERT–Naive Bayes",
                    "detection": "Privacy Risk Classification",
                    "explainability": "LIME / SHAP"
                },
                "bottom_insights": {
                    "supporting_features": 8,
                    "risk_indicators": 2,
                    "top_contribution_weight": 0.87
                }
            }

        elif modality.lower() == "video":
            return {
                "modality": "Video",
                "risk_score": 87,
                "status": "BLOCKED",
                "risk_level": "HIGH",
                "detected_risks": [
                    "Personal Information",
                    "Credential Information",
                    "Confidential Content",
                    "Prompt Injection Risk"
                ],
                "affected_features": "Keyframe timestamp 00:11.20 contained database connection string with password token.",
                "feature_contributions": [
                    {"rank": "#1", "type": "Supporting", "feature": "Personal Information", "weight": 0.1513, "is_risk": False},
                    {"rank": "#2", "type": "Supporting", "feature": "Database Connection String", "weight": 0.1483, "is_risk": False},
                    {"rank": "#3", "type": "Supporting", "feature": "Server Password Token", "weight": 0.1301, "is_risk": False},
                    {"rank": "#4", "type": "Risk Factor", "feature": "Credential Information", "weight": 0.1022, "is_risk": True}
                ],
                "privacy_breakdown": {
                    "Personal Information": "HIGH",
                    "Credentials": "HIGH",
                    "Financial Information": "MEDIUM",
                    "Confidential Content": "LOW"
                },
                "detected_entities": ["Personal information", "Connection URL", "Server Password", "Credential"],
                "recommended_action": "BLOCK INPUT",
                "why_explanation": "The system detected privacy-sensitive information in the video frames. The detected entities contributed strongly to the overall privacy-risk score. The input was therefore classified as high risk.",
                "model_info": {
                    "model": "Hybrid BERT–Naive Bayes",
                    "detection": "Privacy Risk Classification",
                    "explainability": "LIME / SHAP"
                },
                "bottom_insights": {
                    "supporting_features": 8,
                    "risk_indicators": 2,
                    "top_contribution_weight": 0.87
                }
            }

        elif modality.lower() == "youtube":
            return {
                "modality": "YouTube",
                "risk_score": 87,
                "status": "BLOCKED",
                "risk_level": "HIGH",
                "detected_risks": [
                    "Personal Information",
                    "Credential Information",
                    "Confidential Content",
                    "Prompt Injection Risk"
                ],
                "affected_features": "Transcript timestamp [08:45] contained private secret API keys spoken during presentation.",
                "feature_contributions": [
                    {"rank": "#1", "type": "Supporting", "feature": "Personal Information", "weight": 0.1513, "is_risk": False},
                    {"rank": "#2", "type": "Supporting", "feature": "Speaker Credentials", "weight": 0.1483, "is_risk": False},
                    {"rank": "#3", "type": "Supporting", "feature": "Internal API Key", "weight": 0.1301, "is_risk": False},
                    {"rank": "#4", "type": "Risk Factor", "feature": "Credential Information", "weight": 0.1022, "is_risk": True}
                ],
                "privacy_breakdown": {
                    "Personal Information": "HIGH",
                    "Credentials": "HIGH",
                    "Financial Information": "MEDIUM",
                    "Confidential Content": "LOW"
                },
                "detected_entities": ["Personal information", "Speaker Email", "API Key", "Credential"],
                "recommended_action": "BLOCK INPUT",
                "why_explanation": "The system detected privacy-sensitive information in the YouTube transcript. The detected entities contributed strongly to the overall privacy-risk score. The input was therefore classified as high risk.",
                "model_info": {
                    "model": "Hybrid BERT–Naive Bayes",
                    "detection": "Privacy Risk Classification",
                    "explainability": "LIME / SHAP"
                },
                "bottom_insights": {
                    "supporting_features": 8,
                    "risk_indicators": 2,
                    "top_contribution_weight": 0.87
                }
            }

        # Default Text Modality
        return {
            "modality": "Text",
            "risk_score": 87,
            "status": "BLOCKED",
            "risk_level": "HIGH",
            "detected_risks": [
                "Personal Information",
                "Credential Information",
                "Confidential Content",
                "Prompt Injection Risk"
            ],
            "affected_features": "High weight tokens 'Aadhaar number', 'phone number', and 'john.doe@company.org' drove the classifier probability above the 75% cutoff.",
            "feature_contributions": [
                {"rank": "#1", "type": "Supporting", "feature": "Personal Information", "weight": 0.1513, "is_risk": False},
                {"rank": "#2", "type": "Supporting", "feature": "Phone Number", "weight": 0.1483, "is_risk": False},
                {"rank": "#3", "type": "Supporting", "feature": "Email Address", "weight": 0.1301, "is_risk": False},
                {"rank": "#4", "type": "Risk Factor", "feature": "Credential Information", "weight": 0.1022, "is_risk": True}
            ],
            "privacy_breakdown": {
                "Personal Information": "HIGH",
                "Credentials": "HIGH",
                "Financial Information": "MEDIUM",
                "Confidential Content": "LOW"
            },
            "detected_entities": ["Personal information", "Phone number", "Email", "Credential"],
            "recommended_action": "BLOCK INPUT",
            "why_explanation": "The system detected privacy-sensitive information in the input. The detected entities contributed strongly to the overall privacy-risk score. The input was therefore classified as high risk.",
            "model_info": {
                "model": "Hybrid BERT–Naive Bayes",
                "detection": "Privacy Risk Classification",
                "explainability": "LIME / SHAP"
            },
            "bottom_insights": {
                "supporting_features": 8,
                "risk_indicators": 2,
                "top_contribution_weight": 0.87
            }
        }

    @staticmethod
    def process_chat(prompt: str, mode: str = "REDACT") -> Dict[str, Any]:
        from backend.routes.chatbot import chat_endpoint, ChatRequest
        return chat_endpoint(ChatRequest(prompt=prompt, sanitization_mode=mode))

    @staticmethod
    def process_text(text: str, mode: str = "REDACT") -> Dict[str, Any]:
        from backend.services.evidence_risk import run_full_analysis
        return run_full_analysis(text, mode=mode)

    @staticmethod
    def process_youtube(url: str) -> Dict[str, Any]:
        return {
            "url": url,
            "title": "Sample AI & Data Security Tech Talk",
            "duration": "14m 20s",
            "extracted_transcript": "[00:05] Welcome to the webinar on modern enterprise security.\n[02:10] In this session, we discuss LLM security, API tokens, and preventing prompt leakage.\n[08:45] Always sanitize PII before transmitting data.",
            "key_points": [
                "Overview of enterprise multimodal LLM security risks.",
                "Best practices for API secret key storage.",
                "Implementing multi-layer privacy evaluation."
            ],
            "risk_score": 18.0,
            "status": "Safe",
            "action": "ALLOW",
            "summary": "The YouTube video provides an educational walkthrough of modern enterprise AI privacy architecture.",
            "explanation": "No sensitive PII or credentials detected in transcript.",
            "is_mock": True
        }

    @staticmethod
    def process_image(filename: str) -> Dict[str, Any]:
        has_sensitive = any(k in filename.lower() for k in ["passport", "id", "card", "tax", "secret"])
        risk = 85.0 if has_sensitive else 22.0
        action = "BLOCK" if risk >= 75.0 else ("WARN" if risk >= 40.0 else "ALLOW")
        
        return {
            "file_name": filename,
            "ocr_text": "DEPARTMENT OF MOTOR VEHICLES\nDRIVER LICENSE\nID: D9910482\nDOB: 1992-05-14\nADDRESS: 742 Evergreen Terrace",
            "detected_entities": [
                {"type": "LICENSE_NUMBER", "value": "D9910482", "risk": "HIGH"},
                {"type": "HOME_ADDRESS", "value": "742 Evergreen Terrace", "risk": "MEDIUM"}
            ] if has_sensitive else [],
            "risk_score": risk,
            "action": action,
            "status": "Block" if action == "BLOCK" else ("Warning" if action == "WARN" else "Allow"),
            "explanation": f"Optical Character Recognition (OCR) extracted text containing PII records.",
            "is_mock": True
        }

    @staticmethod
    def process_video(filename: str) -> Dict[str, Any]:
        return {
            "file_name": filename,
            "total_frames_sampled": 12,
            "ocr_analysis": "Keyframes extracted at 1.0s intervals. OCR scanned textual elements embedded in video frames.",
            "detected_frames": [
                {"timestamp": "00:02.50", "detected_text": "Welcome Presentation Slide 1", "risk": "Low"},
                {"timestamp": "00:06.00", "detected_text": "Confidential Internal Architecture Diagram", "risk": "Medium"},
                {"timestamp": "00:11.20", "detected_text": "DB Connection: postgres://user:pass123@db.internal:5432", "risk": "High"}
            ],
            "risk_score": 72.0,
            "action": "WARN",
            "status": "Warning",
            "explanation": "Detected database connection string exposure in frame timestamp 00:11.20.",
            "is_mock": True
        }

    @staticmethod
    def process_injection(prompt: str) -> Dict[str, Any]:
        lower = prompt.lower()
        is_injection = any(k in lower for k in ["ignore", "bypass", "system prompt", "jailbreak", "override", "dan"])
        risk = 94.0 if is_injection else 12.0
        status = "Malicious" if risk >= 80.0 else ("Suspicious" if risk >= 40.0 else "Safe")

        return {
            "prompt": prompt,
            "risk_score": risk,
            "status": status,
            "action": "BLOCK" if status == "Malicious" else ("WARN" if status == "Suspicious" else "ALLOW"),
            "explanation": "Detected adversarial instruction override sequence targeting system prompt boundaries." if is_injection else "No prompt injection patterns detected.",
            "matched_patterns": ["System Prompt Override Pattern", "Jailbreak Directive Keyword"] if is_injection else [],
            "is_mock": True
        }

    @staticmethod
    def process_summarize(text: str, length_option: str) -> Dict[str, Any]:
        word_count = len(text.split())
        summary_text = f"{length_option.capitalize()} Summary: Document with {word_count} words analyzed cleanly. Key takeaway: privacy risk checks verified safe."

        return {
            "summary": summary_text,
            "summary_length": length_option,
            "key_points": [
                "Core domain concepts extracted from submitted text payload.",
                "Privacy risk check performed with 0 confidential leaks identified.",
                "Structured executive takeaway points generated automatically."
            ],
            "privacy_status": "Clean",
            "is_mock": True
        }
