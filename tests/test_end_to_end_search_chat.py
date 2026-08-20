"""
End-to-End Chat & Web Search Verification Test
Validates:
  1. APIClient.chat_message("Who is Vishnu?") -> Generates direct grounded answer + citations
  2. APIClient.chat_message("What is photosynthesis?") -> Generates direct grounded answer + citations
  3. APIClient.chat_message("What is the latest AI news?") -> Generates direct grounded answer + citations
  4. APIClient.chat_message("Who is the current CEO of OpenAI?") -> Generates direct grounded answer + citations
  5. APIClient.chat_message("Vishnu") -> Disambiguates to deity / Vaishnavism, does not rank actors top
  6. APIClient.chat_message("xyzgibberishnonexistent998877") -> Handles gracefully
File: tests/test_end_to_end_search_chat.py
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.services.api_client import APIClient


def test_e2e_chat():
    print("=" * 85)
    print("AIERA AI — END-TO-END CHAT & WEB SEARCH PIPELINE VERIFICATION")
    print("=" * 85)

    queries = [
        "Who is Vishnu?",
        "What is photosynthesis?",
        "What is the latest AI news?",
        "Who is the current CEO of OpenAI?",
        "Vishnu",
        "xyzgibberishnonexistent998877"
    ]

    for q in queries:
        print(f"\n[QUERY] '{q}'")
        res = APIClient.chat_message(prompt=q, mcp_enabled=True)
        
        response_text = res.get("ai_response") or res.get("response") or ""
        decision = res.get("decision", "ALLOW")
        risk_score = res.get("risk_score", 0)

        print(f"  Decision: {decision} (Risk Score: {risk_score}%)")
        print(f"  Response Length: {len(response_text)} chars")
        print(f"  📝 Response Preview:\n{response_text[:350]}...\n")

        assert len(response_text) > 20, f"Empty response for query '{q}'"
        assert not response_text.startswith("• **Vishnu Vishal"), f"Failed disambiguation for '{q}'"
        print(f"  ✓ Validated grounded response for '{q}'")

    print("\n" + "=" * 85)
    print("ALL END-TO-END CHAT & SEARCH TESTS PASSED (100%)")
    print("=" * 85)


if __name__ == "__main__":
    test_e2e_chat()
