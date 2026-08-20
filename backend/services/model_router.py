"""
AI Trust Chat — Model Router
Routes queries to appropriate LLM models based on complexity, type, and sensitivity.
File: backend/services/model_router.py
"""

import re
from typing import Dict, Any, List

# Model definitions
AVAILABLE_MODELS = {
    "gemini-3.6-flash": {
        "label": "Gemini 3.6 Flash",
        "provider": "Google Gemini",
        "capability": "fast",
        "description": "Fast general questions, simple tasks",
        "cost": "low",
        "speed": "fast",
    },
    "gemini-2.5-pro": {
        "label": "Gemini 2.5 Pro",
        "provider": "Google Gemini",
        "capability": "advanced",
        "description": "Advanced reasoning, complex analysis",
        "cost": "medium",
        "speed": "medium",
    },
    "gemini-2.5-flash-lite": {
        "label": "Gemini 2.5 Flash Lite",
        "provider": "Google Gemini",
        "capability": "standard",
        "description": "Standard tasks, document analysis",
        "cost": "low",
        "speed": "fast",
    },
    "openai-gpt-4o": {
        "label": "GPT-4o",
        "provider": "OpenAI",
        "capability": "advanced",
        "description": "OpenAI advanced model (requires API key)",
        "cost": "high",
        "speed": "medium",
        "available": False,
    },
    "claude-3-5-sonnet": {
        "label": "Claude 3.5 Sonnet",
        "provider": "Anthropic",
        "capability": "advanced",
        "description": "Anthropic advanced model (requires API key)",
        "cost": "high",
        "speed": "medium",
        "available": False,
    },
}

# Complexity indicators
COMPLEX_PATTERNS = [
    r'\banalyze\b', r'\bcompare\b', r'\bexplain.*detail\b', r'\bsummarize.*comprehensive\b',
    r'\bresearch\b', r'\bwrite.*essay\b', r'\bwrite.*report\b', r'\bright.*proof\b',
    r'\bdebug\b', r'\brefactor\b', r'\barchitect\b',
]

CODING_PATTERNS = [
    r'\bcode\b', r'\bpython\b', r'\bjavascript\b', r'\bfunction\b',
    r'\bscript\b', r'\bprogram\b', r'\bimplementation\b', r'\balgorithm\b',
    r'\bclass\b', r'\bapi\b', r'\bsql\b',
]

SIMPLE_PATTERNS = [
    r'^what is\b', r'^who is\b', r'^define\b', r'^explain\b',
    r'^tell me about\b', r'^how does\b', r'^when did\b',
]


def route_query(
    prompt: str,
    pii_detected: bool = False,
    secret_detected: bool = False,
    user_preference: str = "auto",
) -> Dict[str, Any]:
    """
    Determine the best model for a given query.

    Returns:
        model_id: the selected model ID
        model_label: human-readable model name
        reasoning: why this model was selected
        task_type: SIMPLE / COMPLEX / CODING / SENSITIVE
    """
    lower = prompt.lower().strip()

    # If sensitive data — use most private/approved model
    if pii_detected or secret_detected:
        return {
            "model_id": "gemini-2.0-flash",
            "model_label": "Gemini 2.0 Flash (Approved)",
            "task_type": "SENSITIVE",
            "reasoning": "Sensitive/PII content detected — using approved privacy model with masked prompt.",
        }

    # If user has a preference and it's available
    if user_preference != "auto" and user_preference in AVAILABLE_MODELS:
        m = AVAILABLE_MODELS[user_preference]
        if m.get("available", True):
            return {
                "model_id": user_preference,
                "model_label": m["label"],
                "task_type": "USER_SELECTED",
                "reasoning": f"User selected model: {m['label']}",
            }

    # Detect task type
    is_coding = any(re.search(p, lower) for p in CODING_PATTERNS)
    is_complex = any(re.search(p, lower) for p in COMPLEX_PATTERNS)
    is_simple = any(re.search(p, lower) for p in SIMPLE_PATTERNS) and len(prompt) < 100

    if is_coding:
        return {
            "model_id": "gemini-2.5-pro",
            "model_label": "Gemini 2.5 Pro",
            "task_type": "CODING",
            "reasoning": "Coding task detected — using advanced model for best code quality.",
        }

    if is_complex:
        return {
            "model_id": "gemini-2.5-pro",
            "model_label": "Gemini 2.5 Pro",
            "task_type": "COMPLEX",
            "reasoning": "Complex reasoning task — using advanced model.",
        }

    if is_simple:
        return {
            "model_id": "gemini-3.6-flash",
            "model_label": "Gemini 3.6 Flash",
            "task_type": "SIMPLE",
            "reasoning": "Simple factual question — using fast model.",
        }

    # Default: standard model
    return {
        "model_id": "gemini-3.6-flash",
        "model_label": "Gemini 3.6 Flash",
        "task_type": "STANDARD",
        "reasoning": "General query — using standard model.",
    }


def get_available_models() -> List[Dict[str, Any]]:
    """Return list of all models with availability status."""
    result = []
    for model_id, info in AVAILABLE_MODELS.items():
        result.append({
            "id": model_id,
            "label": info["label"],
            "provider": info["provider"],
            "description": info["description"],
            "available": info.get("available", True),
            "capability": info["capability"],
        })
    return result
