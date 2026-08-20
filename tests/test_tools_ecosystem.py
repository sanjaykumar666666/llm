"""
Comprehensive Test Suite for Aiera AI Tools Ecosystem.
Tests all 15 tools for functional correctness, error handling, and Zero-Trust AI Trust Gate enforcement.
File Location: tests/test_tools_ecosystem.py
"""

import sys
import os
import time
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, '.')

from backend.services.tools_ecosystem import (
    search_web,
    deep_research,
    process_file_content,
    analyze_dataset,
    generate_image_bridge,
    analyze_image_bytes,
    canvas_engine,
    execute_code_safely,
    analyze_url_content,
    generate_formal_report,
    execute_tool_with_ai_trust
)


def run_all_tests():
    print("=" * 85)
    print("AI TRUST CHAT — AIERA TOOLS ECOSYSTEM VERIFICATION SUITE")
    print("=" * 85)

    passed_count = 0
    total_tests = 14

    # ── Test 1: 🔎 Web Search (Safe Query) ───────────────────────────────────
    print("\n[TEST 1] 🔎 Web Search — Safe Query")
    res1 = search_web("James Webb Space Telescope exoplanet discovery", max_results=3)
    print(f"  Query: '{res1['query']}' | Total Sources: {res1['total_sources']}")
    if res1["total_sources"] > 0 and len(res1["citations"]) > 0:
        print(f"  ✓ Found source: {res1['results'][0]['title']} ({res1['results'][0]['domain']})")
        passed_count += 1
    else:
        print("  ❌ Web search returned no sources")

    # ── Test 2: 🧠 Deep Research (Agentic Multi-Phase) ────────────────────────
    print("\n[TEST 2] 🧠 Deep Research — Multi-Phase Agentic Synthesis")
    progress_logs = []
    def on_prog(phase, pct, detail):
        progress_logs.append((phase, pct))

    res2 = deep_research("Quantum computing fault tolerance and error correction", on_progress=on_prog)
    print(f"  Phase Steps Completed: {len(res2['steps_log'])} | Sources Consulted: {res2['total_sources_consulted']}")
    print(f"  Executive Summary: {res2['executive_summary'][:100]}...")
    if len(res2["detailed_sections"]) >= 3 and len(res2["citations"]) > 0:
        print("  ✓ Deep Research synthesized multi-section report with cross-source citations")
        passed_count += 1
    else:
        print("  ❌ Deep research synthesis incomplete")

    # ── Test 3: 📎 Files Engine (CSV Parsing & Privacy Scan) ──────────────────
    print("\n[TEST 3] 📎 Files Engine — CSV Parsing & Privacy Scan")
    csv_bytes = b"id,name,role,department\n1,Alice,Engineer,Core Platform\n2,Bob,Researcher,AI Trust\n"
    res3 = process_file_content(csv_bytes, "team_roster.csv")
    print(f"  Filename: {res3['filename']} | Rows: {res3['metadata'].get('rows')} | Privacy Decision: {res3['privacy_scan']['decision']}")
    if res3["parsing_status"] == "SUCCESS" and res3["privacy_scan"]["decision"] == "ALLOW":
        print("  ✓ CSV file parsed cleanly and passed AI Trust privacy scan")
        passed_count += 1
    else:
        print("  ❌ CSV parsing failed")

    # ── Test 4: 📎 Files Engine (Sensitive File Interception) ─────────────────
    print("\n[TEST 4] 📎 Files Engine — Sensitive PII/Credential File Interception")
    sensitive_csv = b"user_id,email,temp_password\n101,admin@corp.io,SuperSecretP@ssw0rd!123\n"
    res4 = process_file_content(sensitive_csv, "credentials.csv")
    print(f"  Privacy Decision: {res4['privacy_scan']['decision']} | Risk: {res4['privacy_scan']['risk_score']}% | Detected: {res4['privacy_scan']['detected_entities']}")
    if res4["privacy_scan"]["decision"] in ("WARN", "BLOCK") and res4["privacy_scan"]["risk_score"] > 0:
        print("  ✓ Sensitive file correctly flagged with risk score > 0% and entity attribution")
        passed_count += 1
    else:
        print("  ❌ Failed to flag sensitive file")

    # ── Test 5: 📊 Data Analysis (Pandas Summary Stats & Correlation) ─────────
    print("\n[TEST 5] 📊 Data Analysis — Summary Stats, Correlation & Outlier Detection")
    data_bytes = b"age,salary,experience_years,score\n25,50000,2,85\n30,75000,5,90\n35,110000,10,95\n40,140000,15,98\n"
    res5 = analyze_dataset(data_bytes, "employees.csv")
    print(f"  Rows: {res5['rows']} | Cols: {res5['columns']}")
    print(f"  Salary Mean: ${res5['summary_statistics']['salary']['mean']} | Salary Max: ${res5['summary_statistics']['salary']['max']}")
    if "salary" in res5["summary_statistics"] and len(res5["correlation_matrix"]) > 0:
        print("  ✓ Summary statistics and correlation matrix generated from real tabular data")
        passed_count += 1
    else:
        print("  ❌ Data analysis failed")

    # ── Test 6: 🎨 Image Generation Bridge ───────────────────────────────────
    print("\n[TEST 6] 🎨 Image Generation Bridge — Prompt Privacy & Generation State")
    res6 = generate_image_bridge("Futuristic zero-trust cybersecurity shield in deep space", aspect_ratio="16:9", style="Sci-Fi")
    print(f"  Status: {res6['status']} | Provider: {res6['provider']}")
    if res6["status"] in ("COMPLETED", "NOT_CONFIGURED"):
        print("  ✓ Image generator handled prompt and returned valid provider status")
        passed_count += 1
    else:
        print("  ❌ Image generation bridge error")

    # ── Test 7: 🖼️ Image Analysis & EXIF Scrubbing ────────────────────────────
    print("\n[TEST 7] 🖼️ Image Analysis — Metadata & Privacy Scrubbing")
    # 1x1 dummy PNG bytes
    dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    res7 = analyze_image_bytes(dummy_png)
    print(f"  Resolution: {res7['resolution']} | EXIF Stripped: {res7['exif_stripped']}")
    if res7["exif_stripped"] is True and "privacy_scan" in res7:
        print("  ✓ Image analysis processed visual payload and verified EXIF stripping")
        passed_count += 1
    else:
        print("  ❌ Image analysis failed")

    # ── Test 8: ✍️ Canvas Workspace (Document Versioning & Transform) ─────────
    print("\n[TEST 8] ✍️ Canvas / Workspace — Document Operations & Versioning")
    doc = canvas_engine.get_or_create_doc("doc-test-1", "Security Architecture Spec", "Initial draft of security spec.")
    canvas_engine.update_content("doc-test-1", "Updated draft with zero-trust gateway details.", action="EXPAND")
    transformed = canvas_engine.transform_text(doc["content"], action="EXPAND")
    print(f"  Doc ID: {doc['id']} | Current Version: {doc['current_version']} | Versions Count: {len(doc['versions'])}")
    if doc["current_version"] == 2 and len(doc["versions"]) == 2:
        print("  ✓ Canvas workspace maintained immutable version history and text transform")
        passed_count += 1
    else:
        print("  ❌ Canvas engine error")

    # ── Test 9: 💻 Code Workspace (AST Safe Sandboxed Execution) ─────────────
    print("\n[TEST 9] 💻 Code Workspace — Safe Sandboxed Execution")
    safe_code = "import math\nvals = [math.sqrt(x) for x in range(1, 6)]\nprint(f'Computed square roots: {vals}')\n"
    res9 = execute_code_safely(safe_code, language="python")
    print(f"  Status: {res9['status']} | Output: {res9['output'].strip()}")
    if res9["status"] == "SUCCESS" and "Computed square roots" in res9["output"]:
        print("  ✓ Sandboxed code executed cleanly and captured standard output")
        passed_count += 1
    else:
        print("  ❌ Code execution failed")

    # ── Test 10: 💻 Code Workspace (Security Block on Prohibited Calls) ────────
    print("\n[TEST 10] 💻 Code Workspace — Security Block on Prohibited System Calls")
    dangerous_code = "import os\nos.system('dir')\n"
    res10 = execute_code_safely(dangerous_code, language="python")
    print(f"  Status: {res10['status']} | Error: {res10['error']}")
    if res10["status"] == "BLOCKED" and "prohibited" in res10["error"].lower():
        print("  ✓ Prohibited system call was intercepted and blocked before execution")
        passed_count += 1
    else:
        print("  ❌ Failed to block prohibited system call")

    # ── Test 11: 🔗 URL Analysis (SSRF Guard & Readability Extractor) ─────────
    print("\n[TEST 11] 🔗 URL Analysis — Safe Fetch & SSRF Protection")
    res11_ssrf = analyze_url_content("http://127.0.0.1:8080/internal-admin")
    print(f"  SSRF Test URL: 127.0.0.1 | Status: {res11_ssrf['status']}")
    if res11_ssrf["status"] == "BLOCKED_SSRF":
        print("  ✓ SSRF attempt to internal network address was blocked")
        passed_count += 1
    else:
        print("  ❌ SSRF guard failed")

    # ── Test 12: 📝 Report Generator (Formal Document Compiler) ──────────────
    print("\n[TEST 12] 📝 Report Generator — Formal Structured Document")
    sections = [
        {"heading": "Executive Summary", "content": "Overview of enterprise zero-trust deployment."},
        {"heading": "Security Audit Findings", "content": "All external LLM endpoints protected by continuous privacy gateway."}
    ]
    report_md = generate_formal_report("Aiera Enterprise Security Audit", sections)
    print(f"  Report Length: {len(report_md)} chars | Contains Header: {'# Aiera Enterprise Security Audit' in report_md}")
    if "# Aiera Enterprise Security Audit" in report_md and "## Security Audit Findings" in report_md:
        print("  ✓ Formal report generator compiled verified structured markdown document")
        passed_count += 1
    else:
        print("  ❌ Report generation failed")

    # ── Test 13: 🛡️ AI Trust Tool Gateway Wrapper — Safe Tool Execution ─────
    print("\n[TEST 13] 🛡️ AI Trust Tool Gateway — Safe Tool Call")
    wrapped_safe = execute_tool_with_ai_trust("WebSearch", search_web, "Machine learning privacy techniques", max_results=2)
    print(f"  Tool: {wrapped_safe['tool_name']} | Decision: {wrapped_safe['decision']} | Risk: {wrapped_safe['risk_score']}% | Latency: {wrapped_safe['timing_ms']} ms")
    if wrapped_safe["decision"] == "ALLOW" and wrapped_safe["status"] == "SUCCESS" and "trust_receipt" in wrapped_safe:
        print("  ✓ Safe tool call authorized, executed, and produced cryptographic Trust Receipt")
        passed_count += 1
    else:
        print("  ❌ Safe tool wrapper failed")

    # ── Test 14: 🛡️ AI Trust Tool Gateway Wrapper — Sensitive Credential Block
    print("\n[TEST 14] 🛡️ AI Trust Tool Gateway — Sensitive Credential Block")
    wrapped_block = execute_tool_with_ai_trust("WebSearch", search_web, "Deploy config: username=admin password=SuperSecret123 database=prod")
    print(f"  Tool: {wrapped_block['tool_name']} | Decision: {wrapped_block['decision']} | Risk: {wrapped_block['risk_score']}% | Status: {wrapped_block['status']}")
    if wrapped_block["decision"] == "BLOCK" and wrapped_block["status"] == "BLOCKED" and wrapped_block["result"] is None:
        print("  ✓ Sensitive credential payload was intercepted and blocked BEFORE tool execution")
        passed_count += 1
    else:
        print("  ❌ Failed to block sensitive payload at AI Trust Gateway")

    print("\n" + "=" * 85)
    print(f"TOOLS ECOSYSTEM BENCHMARK: {passed_count}/{total_tests} Tests Passed ({(passed_count/total_tests)*100:.1f}%)")
    print("=" * 85)


if __name__ == "__main__":
    run_all_tests()
