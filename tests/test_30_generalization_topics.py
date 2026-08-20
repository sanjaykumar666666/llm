"""
30-Topic Generalization Test Suite.
Verifies that the chatbot generates contextually relevant responses for 30+ completely unseen topics without hardcoded topic dictionaries or generic template strings ("Definition & Context", "information technology").
File: tests/test_30_generalization_topics.py
"""

import pytest
from llm_gateway.gemini_client import GeminiClient
from backend.routes.chatbot import chat_endpoint, ChatRequest


# The 30 Test Topics requested by user
BENCHMARK_30_TOPICS = [
    ("Garuda", ["garuda", "bird", "mount", "mythology", "vishnu"]),
    ("Krishna", ["krishna", "gita", "avatar", "vishnu", "deity"]),
    ("Shiva", ["shiva", "mahadeva", "destroyer", "deity", "trishula"]),
    ("Tea", ["tea", "camellia", "beverage", "leaves", "brew"]),
    ("Coffee", ["coffee", "beans", "caffeine", "beverage", "roast"]),
    ("Python", ["python", "language", "code", "programming", "script"]),
    ("Java", ["java", "programming", "code", "language", "jvm"]),
    ("Photosynthesis", ["photosynthesis", "plants", "light", "chlorophyll", "energy"]),
    ("Gravity", ["gravity", "force", "mass", "einstein", "attraction"]),
    ("Black holes", ["black hole", "singularity", "event horizon", "gravity", "space"]),
    ("Indian history", ["india", "history", "civilization", "empire", "dynasty"]),
    ("Machine learning", ["machine learning", "data", "model", "algorithm", "ai"]),
    ("Blockchain", ["blockchain", "ledger", "crypto", "decentralized", "block"]),
    ("Economics", ["economics", "market", "supply", "demand", "economy"]),
    ("Psychology", ["psychology", "mind", "behavior", "mental", "brain"]),
    ("Cooking", ["cooking", "food", "recipe", "culinary", "ingredients"]),
    ("Travel", ["travel", "destination", "tourism", "journey", "explore"]),
    ("Mathematics", ["mathematics", "math", "numbers", "algebra", "calculus"]),
    ("Programming", ["programming", "code", "software", "developer", "algorithm"]),
    ("Geography", ["geography", "earth", "continents", "maps", "regions"]),
    ("Music", ["music", "melody", "rhythm", "sound", "harmony"]),
    ("Sports", ["sports", "game", "athletes", "match", "competition"]),
    ("Medicine-related general information", ["medicine", "health", "clinical", "treatment", "medical"]),
    ("Engineering", ["engineering", "design", "structures", "technology", "systems"]),
    ("Space", ["space", "cosmos", "universe", "astronomy", "planets"]),
    ("Environment", ["environment", "ecosystem", "climate", "nature", "conservation"]),
    ("Business", ["business", "company", "market", "strategy", "enterprise"]),
    ("Education", ["education", "learning", "knowledge", "school", "teaching"]),
    ("Quantum computing", ["quantum", "qubit", "computation", "superposition", "computing"]),
    ("How do optical fibers transmit light signals over long distances?", ["optical", "fiber", "light", "reflection", "signal"])
]


@pytest.mark.parametrize("topic,expected_keywords", BENCHMARK_30_TOPICS)
def test_generalization_topic_response(topic, expected_keywords):
    client = GeminiClient()
    res = client.generate_response(topic)

    assert res["success"] is True
    assert "response_text" in res
    text = res["response_text"]
    assert text is not None and len(text) > 30

    # Critical Assertion 1: Must NOT contain generic filler template phrases
    assert "Definition & Context: The topic involves fundamental principles of information technology" not in text
    assert "information technology, domain analysis, or general knowledge" not in text

    # Critical Assertion 2: Response text should contain relevant domain concepts or topic title
    lower_text = text.lower()
    topic_words = [w.lower() for w in topic.split() if len(w) > 3]
    has_relevance = any(kw in lower_text for kw in expected_keywords) or any(tw in lower_text for tw in topic_words)
    assert has_relevance, f"Response for topic '{topic}' was not relevant to query terms: {text[:150]}"


def test_chatbot_endpoint_generalization_integration():
    req = ChatRequest(prompt="Explain the principles of aerodynamics in aviation.", mcp_enabled=True)
    resp = chat_endpoint(req)

    assert resp["success"] is True
    assert resp["decision"] == "ALLOW"
    assert resp["response"] is not None
    assert "Definition & Context: The topic involves fundamental principles of information technology" not in resp["response"]
