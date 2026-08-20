"""
Fast Semantic Query Router & Intent Classifier — Microsecond Query Tiering.
File: mcp_engine/web_search_router.py
"""

import re
from typing import Dict, Any, List, Optional, Tuple


# Precompiled fast regex patterns for microsecond classification (<1ms)
RE_EXPLICIT_SEARCH = re.compile(
    r"\b(search\s+the\s+web|search\s+online|look\s+up\s+online|google|search\s+internet|find\s+online|web\s+search|search\s+google|browse\s+web|look\s+on\s+the\s+web)\b",
    re.IGNORECASE,
)

RE_TIME_SENSITIVE = re.compile(
    r"\b(latest|today|yesterday|current\s+status|current\s+price|live\s+score|breaking\s+news|recent\s+news|latest\s+news|latest\s+updates?|what\s+happened\s+today|this\s+week|2026\s+update|2025\s+update|newest\s+release|stock\s+price|weather\s+today|current\s+role|who\s+is\s+the\s+current|latest\s+developments?)\b",
    re.IGNORECASE,
)

RE_RESEARCH_INTENT = re.compile(
    r"\b(deep\s+research|comprehensive\s+analysis|in-depth\s+study|exhaustive\s+review|multi-source\s+comparison|systematic\s+review|detailed\s+investigation)\b",
    re.IGNORECASE,
)

RE_MULTIMODAL_HINT = re.compile(
    r"\b(upload|uploaded\s+file|attached\s+document|run\s+this\s+code|execute\s+python|dataset|csv\s+file|generate\s+image|analyze\s+image|parse\s+pdf)\b",
    re.IGNORECASE,
)

RE_CLEAN_SEARCH_PREFIX = re.compile(
    r"^\s*(search\s+for|search\s+the\s+web\s+for|search\s+online\s+for|google\s+for|tell\s+me\s+about|find\s+out|look\s+up)\s*",
    re.IGNORECASE,
)


class WebSearchRouter:
    """
    Fast Query Router & Intent Classifier:
    Microsecond classification into 4 primary tiers:
      - SIMPLE: Direct LLM / Knowledge Engine (Target: 2-3s, NO web search)
      - WEB_REQUIRED: Live parallel search with minimum evidence (Target: <=5s)
      - COMPLEX_RESEARCH: Stream initial answer + background enrichment
      - MULTIMODAL: Multi-modal tool execution
    """

    @classmethod
    def classify_query_intent(
        cls,
        prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        forced_tool: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classifies query into execution tier.
        Returns:
          - category: "SIMPLE" | "WEB_REQUIRED" | "COMPLEX_RESEARCH" | "MULTIMODAL"
          - should_search: bool
          - search_query: str
          - reason: str
          - max_sources: int
          - early_stop: bool
          - execution_mode: "DIRECT_LLM" | "PARALLEL_SEARCH" | "RESEARCH_ENRICHMENT" | "TOOL"
        """
        raw_prompt = (prompt or "").strip()
        lower = raw_prompt.lower()

        # 0. Forced tool overrides
        if forced_tool and forced_tool != "💬 Standard Chat":
            if "Web Search" in forced_tool:
                return {
                    "category": "WEB_REQUIRED",
                    "should_search": True,
                    "search_query": raw_prompt,
                    "reason": "Explicit tool selector set to Web Search.",
                    "max_sources": 3,
                    "early_stop": True,
                    "execution_mode": "PARALLEL_SEARCH",
                }
            elif "Deep Research" in forced_tool:
                return {
                    "category": "COMPLEX_RESEARCH",
                    "should_search": True,
                    "search_query": raw_prompt,
                    "reason": "Explicit tool selector set to Deep Research.",
                    "max_sources": 5,
                    "early_stop": False,
                    "execution_mode": "RESEARCH_ENRICHMENT",
                }
            else:
                return {
                    "category": "MULTIMODAL",
                    "should_search": False,
                    "search_query": raw_prompt,
                    "reason": f"Tool route: {forced_tool}",
                    "max_sources": 0,
                    "early_stop": True,
                    "execution_mode": "TOOL",
                }

        # 1. Resolve follow-up query context if any
        resolved_query, _ = cls._resolve_followup_context(raw_prompt, chat_history)

        # 2. Check for explicit Deep Research pattern
        if RE_RESEARCH_INTENT.search(resolved_query):
            return {
                "category": "COMPLEX_RESEARCH",
                "should_search": True,
                "search_query": resolved_query,
                "reason": "Complex in-depth research requested.",
                "max_sources": 4,
                "early_stop": False,
                "execution_mode": "RESEARCH_ENRICHMENT",
            }

        # 3. Check for Multimodal / File hints
        if RE_MULTIMODAL_HINT.search(resolved_query):
            return {
                "category": "MULTIMODAL",
                "should_search": False,
                "search_query": resolved_query,
                "reason": "Multimodal / document context detected.",
                "max_sources": 0,
                "early_stop": True,
                "execution_mode": "TOOL",
            }

        # 4. Check for explicit search command
        if RE_EXPLICIT_SEARCH.search(resolved_query):
            clean_q = RE_CLEAN_SEARCH_PREFIX.sub("", RE_EXPLICIT_SEARCH.sub("", resolved_query)).strip(" .?,")
            clean_q = clean_q or resolved_query
            return {
                "category": "WEB_REQUIRED",
                "should_search": True,
                "search_query": clean_q,
                "reason": "Explicit user command requesting web search.",
                "max_sources": 3,
                "early_stop": True,
                "execution_mode": "PARALLEL_SEARCH",
            }

        # 5. Check for time-sensitive keywords
        if RE_TIME_SENSITIVE.search(resolved_query):
            return {
                "category": "WEB_REQUIRED",
                "should_search": True,
                "search_query": resolved_query,
                "reason": "Query contains time-sensitive / current news keywords.",
                "max_sources": 3,
                "early_stop": True,
                "execution_mode": "PARALLEL_SEARCH",
            }

        # 6. Default: ALL GENERAL KNOWLEDGE ("Vishnu", "What is BERT?", "What is Python?", "Photosynthesis", etc.)
        # FAST ANSWER MODE -> DIRECT LLM / KNOWLEDGE ENGINE (NO WEB SEARCH)
        return {
            "category": "SIMPLE",
            "should_search": False,
            "search_query": resolved_query,
            "reason": "General knowledge query routed directly to Fast LLM without Web Search.",
            "max_sources": 0,
            "early_stop": True,
            "execution_mode": "DIRECT_LLM",
        }

    @classmethod
    def evaluate_search_intent(
        cls,
        prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Backward-compatible helper returning should_search and metadata."""
        classified = cls.classify_query_intent(prompt, chat_history)
        return {
            "should_search": classified["should_search"],
            "reason": classified["reason"],
            "search_query": classified["search_query"],
            "intent_type": classified["category"],
            "execution_mode": classified["execution_mode"],
        }

    @classmethod
    def _resolve_followup_context(
        cls,
        prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, bool]:
        """Resolves ambiguous pronouns ('it', 'his', 'her') against chat history."""
        if not chat_history or len(chat_history) < 2:
            return prompt, False

        lower_prompt = prompt.lower()
        followup_pronouns = ["when did it happen", "where did it happen", "what about it", "tell me more about it", "who led it", "his teachings", "her teachings", "his", "her"]
        contains_ambiguous = any(p in lower_prompt for p in followup_pronouns)

        if not contains_ambiguous:
            return prompt, False

        for msg in reversed(chat_history):
            text = msg.get("text", "")
            if text and len(text) > 3 and msg.get("role") == "user":
                subject = text.split("?")[0].strip()
                return f"{prompt} (regarding {subject[:40]})", True

        return prompt, False
