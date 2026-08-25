"""
Full Application E2E Capability Audit Runner
Executes real runtime tests across all 11 user-visible application capabilities:
  1. Normal Chat / Gemini
  2. Deep Research
  3. Web Search (MCP)
  4. Image Analysis / Privacy Gate
  5. Video Analysis / Privacy Gate
  6. YouTube Analysis / Privacy Gate
  7. Text Privacy Editor / Document Inspection
  8. MCP / Tool Invocation (Tool Gateway)
  9. Real-Time Privacy Guard (Precheck)
  10. Cryptographic AI Trust Receipt
  11. Backend Analysis Routes & Policies
"""

import sys
import os
import io
import time
import json
from PIL import Image, ImageDraw

# Add project root to sys.path
sys.path.insert(0, r"c:\Users\sanja\Downloads\LLM")
sys.stdout.reconfigure(line_buffering=True)

from backend.routes.chatbot import chat_endpoint, ChatRequest
from backend.routes.live_analysis import live_typing_analysis_endpoint, LiveAnalysisRequest
from backend.services.evidence_risk import run_full_analysis, get_sanitizer
from backend.services.image_privacy_service import ImagePrivacyService
from pipeline.input_handler import MultimodalInputHandler
from mcp_engine.tool_security_gateway import secure_tool_call, get_tool_security_gateway
from llm_gateway.gemini_client import GeminiClient

results_matrix = {}

def audit_step(capability_name, test_type, payload_fn):
    print(f"\n[AUDIT] >> Capability: {capability_name} | Case: {test_type}")
    t0 = time.perf_counter()
    try:
        res = payload_fn()
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        print(f"  -> SUCCESS ({elapsed_ms}ms)")
        return {"status": "SUCCESS", "elapsed_ms": elapsed_ms, "data": res}
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        print(f"  -> ERROR ({elapsed_ms}ms): {exc}")
        return {"status": "ERROR", "elapsed_ms": elapsed_ms, "error": str(exc)}


def run_full_audit():
    print("=" * 80)
    print("STARTING FULL APPLICATION CAPABILITY E2E AUDIT")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # 1. NORMAL CHAT / GEMINI
    # --------------------------------------------------------------------------
    # Safe
    r1_safe = audit_step("1. Normal Chat", "SAFE", lambda: chat_endpoint(ChatRequest(
        prompt="What is the capital of France?",
        deep_research=False,
        web_search=False
    )))
    # PII
    r1_pii = audit_step("1. Normal Chat", "PII", lambda: chat_endpoint(ChatRequest(
        prompt="My email is john.audit@example.org and phone is +1-555-0199. Explain gravity.",
        deep_research=False,
        web_search=False
    )))
    # Critical Credential
    r1_cred = audit_step("1. Normal Chat", "CREDENTIAL", lambda: chat_endpoint(ChatRequest(
        prompt="My database password is AuditSecret99! and API key is AIzaSyD3xAmPlE1234567890123456789012345.",
        deep_research=False,
        web_search=False
    )))

    # --------------------------------------------------------------------------
    # 2. DEEP RESEARCH
    # --------------------------------------------------------------------------
    r2_safe = audit_step("2. Deep Research", "SAFE", lambda: chat_endpoint(ChatRequest(
        prompt="Synthesize the latest developments in quantum error correction.",
        deep_research=True,
        web_search=False
    )))
    r2_cred = audit_step("2. Deep Research", "CREDENTIAL", lambda: chat_endpoint(ChatRequest(
        prompt="Deep research DB password admin:SuperSecretKey99! on internal server.",
        deep_research=True,
        web_search=False
    )))

    # --------------------------------------------------------------------------
    # 3. WEB SEARCH (MCP)
    # --------------------------------------------------------------------------
    r3_safe = audit_step("3. Web Search", "SAFE", lambda: chat_endpoint(ChatRequest(
        prompt="Search the web for recent James Webb space telescope findings.",
        deep_research=False,
        web_search=True
    )))
    r3_pii = audit_step("3. Web Search", "PII", lambda: chat_endpoint(ChatRequest(
        prompt="Search python tutorials for employee sarah.connor@cyberdyne.org.",
        deep_research=False,
        web_search=True
    )))
    r3_ssrf = audit_step("3. Web Search", "SSRF_ATTACK", lambda: secure_tool_call(
        tool_name="search_web",
        arguments={"query": "fetch http://169.254.169.254/latest/meta-data/"}
    ))

    # --------------------------------------------------------------------------
    # 4. IMAGE ANALYSIS / PRIVACY GATE
    # --------------------------------------------------------------------------
    # Generate a synthetic image in memory
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Secret ID: 9918-4019-2011", fill=(0, 0, 0))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_raw = img_bytes.getvalue()

    img_service = ImagePrivacyService()
    r4_safe = audit_step("4. Image Analysis", "SAFE", lambda: img_service.analyze_image_bytes(
        image_bytes=img_raw,
        filename="test_id.png"
    ))

    # --------------------------------------------------------------------------
    # 5. VIDEO ANALYSIS / PRIVACY GATE
    # --------------------------------------------------------------------------
    inp_h = UnifiedInputHandler()
    prep = UnifiedPreprocessor()
    det = UnifiedDetector()

    r5_video = audit_step("5. Video Analysis", "SYNTHETIC_VIDEO", lambda: inp_h.handle_video(
        file_bytes=b"FAKE_MP4_HEADER_DATA_1234567890",
        file_name="corrupt.mp4"
    ))

    # --------------------------------------------------------------------------
    # 6. YOUTUBE ANALYSIS / PRIVACY GATE
    # --------------------------------------------------------------------------
    r6_safe = audit_step("6. YouTube Analysis", "SAFE_URL", lambda: inp_h.handle_youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
    r6_malformed = audit_step("6. YouTube Analysis", "MALFORMED_URL", lambda: inp_h.handle_youtube("https://attacker.com/evil?v=12345"))

    # --------------------------------------------------------------------------
    # 7. TEXT PRIVACY EDITOR / DOCUMENT INSPECTION
    # --------------------------------------------------------------------------
    sanitizer = get_sanitizer()
    r7_safe = audit_step("7. Text Privacy Editor", "SAFE_DOC", lambda: sanitizer.sanitize_text(
        "This is an executive project summary regarding Q3 cloud architecture."
    ))
    r7_pii = audit_step("7. Text Privacy Editor", "PII_DOC", lambda: sanitizer.sanitize_text(
        "Employee: Alice Smith, Email: alice@example.org, Aadhaar: 9918-4019-2011, SSN: 000-12-3456."
    ))

    # --------------------------------------------------------------------------
    # 8. MCP / TOOL INVOCATION GATEWAY
    # --------------------------------------------------------------------------
    r8_safe = audit_step("8. MCP Tool Gateway", "VALID_CALL", lambda: secure_tool_call(
        tool_name="search_web",
        arguments={"query": "latest AI regulations"}
    ))
    r8_unauth = audit_step("8. MCP Tool Gateway", "UNAUTHORIZED_TOOL", lambda: secure_tool_call(
        tool_name="bash_execute",
        arguments={"cmd": "rm -rf /"}
    ))

    # --------------------------------------------------------------------------
    # 9. REAL-TIME PRIVACY GUARD (PRECHECK)
    # --------------------------------------------------------------------------
    r9_safe = audit_step("9. Real-Time Precheck", "SAFE_PRECHECK", lambda: live_typing_analysis_endpoint(LiveAnalysisRequest(
        text="What is machine learning?"
    )))
    r9_cred = audit_step("9. Real-Time Precheck", "CREDENTIAL_PRECHECK", lambda: live_typing_analysis_endpoint(LiveAnalysisRequest(
        text="My database password is SuperSecretAdminKey123!"
    )))

    # --------------------------------------------------------------------------
    # 10. CRYPTOGRAPHIC AI TRUST RECEIPT
    # --------------------------------------------------------------------------
    # Verified in chat response
    r10_receipt = r1_safe["data"].get("trust_receipt") or r1_safe["data"].get("audit_meta")
    print(f"\n[AUDIT] >> Capability: 10. Trust Receipt Verification")
    print(f"  -> Generated Receipt Keys: {list(r10_receipt.keys()) if isinstance(r10_receipt, dict) else r10_receipt}")

    # --------------------------------------------------------------------------
    # 11. EXPOSED BACKEND ROUTES & POLICIES
    # --------------------------------------------------------------------------
    r11_analysis = audit_step("11. Evidence Risk Route", "DIRECT_ANALYSIS", lambda: run_full_analysis(
        "My AWS Secret Key is wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    ))

    print("\n" + "=" * 80)
    print("ALL 11 CAPABILITIES AUDITED VIA LIVE RUNTIME EXECUTION")
    print("=" * 80)

    audit_summary = {
        "chat_safe": r1_safe,
        "chat_pii": r1_pii,
        "chat_cred": r1_cred,
        "research_safe": r2_safe,
        "research_cred": r2_cred,
        "web_search_safe": r3_safe,
        "web_search_pii": r3_pii,
        "web_search_ssrf": r3_ssrf,
        "image_analysis": r4_safe,
        "video_analysis": r5_video,
        "youtube_analysis": (r6_safe, r6_malformed),
        "text_editor": (r7_safe, r7_pii),
        "mcp_gateway": (r8_safe, r8_unauth),
        "realtime_precheck": (r9_safe, r9_cred),
        "evidence_risk": r11_analysis
    }

    with open("scratch/audit_runtime_data.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, default=str, indent=2)
    print("Saved raw audit telemetry to scratch/audit_runtime_data.json")

if __name__ == "__main__":
    run_full_audit()
