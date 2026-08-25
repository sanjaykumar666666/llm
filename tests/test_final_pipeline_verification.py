"""
Mandatory Architecture Verification Test Suite.
File: tests/test_final_pipeline_verification.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.routes.chatbot import chat_endpoint, ChatRequest
from mcp_engine.web_search_router import WebSearchRouter

def run_mandatory_tests():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("MANDATORY ARCHITECTURE & ROUTING TESTS (1 to 8)")
    print("=" * 70)

    forbidden_templates = [
        "Information on Latest verified updates on",
        "Current status and verified documentation regarding",
        "Latest verified updates on",
        "comprehensive breakdown",
        "Knowledge & Insights",
        "Definition & Context",
        "Core Concept & Definition",
        "Key Facets",
        "Global Impact",
        "Practical Value"
    ]

    mandatory_test_cases = [
        ("TEST 1: Vishnu", "Vishnu", False),
        ("TEST 2: Garuda", "Garuda", False),
        ("TEST 3: Tea", "Tea", False),
        ("TEST 4: Java", "Java", False),
        ("TEST 5: What is Vishnu?", "What is Vishnu?", False),
        ("TEST 6: Tell me about Krishna.", "Tell me about Krishna.", False),
        ("TEST 7: Latest ISRO news", "What is the latest news about ISRO?", True),
        ("TEST 8: What happened in Delhi today?", "What happened in Delhi today?", True),
    ]

    results_summary = []

    for label, query, expected_search in mandatory_test_cases:
        # Check router intent decision
        intent = WebSearchRouter.evaluate_search_intent(query)
        actual_search = intent["should_search"]

        # Run full backend API pipeline endpoint
        req = ChatRequest(prompt=query, mcp_enabled=True)
        resp = chat_endpoint(req)
        ans = resp["response"]

        mcp_called = resp.get("mcp_meta") is not None

        # Assert search decision matches expectation
        assert actual_search == expected_search, f"[{label}] Expected search={expected_search}, but got {actual_search} (Reason: {intent['reason']})"
        assert mcp_called == expected_search, f"[{label}] Expected MCP executed={expected_search}, but got {mcp_called}"

        # Assert no generic boilerplate template text exists
        for bad in forbidden_templates:
            assert bad not in ans, f"[{label}] Forbidden template string '{bad}' found in answer!"

        status_str = "SUCCESS (MCP NOT CALLED)" if not expected_search else "SUCCESS (MCP CALLED)"
        print(f"\n✓ {label}")
        print(f"  Prompt: '{query}'")
        print(f"  Router Intent: {intent['intent_type']} | Search Required: {actual_search}")
        print(f"  MCP Executed: {mcp_called}")
        print(f"  Generated Answer:\n  {ans[:160]}...")

        results_summary.append({
            "label": label,
            "query": query,
            "expected_mcp": expected_search,
            "actual_mcp": mcp_called,
            "status": status_str,
            "sample_answer": ans[:180]
        })

    print("\n" + "=" * 70)
    print("ALL 8 MANDATORY ARCHITECTURE TESTS PASSED 100% CLEANLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_mandatory_tests()
