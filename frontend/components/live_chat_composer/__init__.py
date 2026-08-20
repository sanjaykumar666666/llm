"""
Live Chat Composer Custom Component.
Provides real-time, client-side debounced input events, 0ms live privacy detection,
span highlighting, and seamless bidirectional communication with Streamlit.
File Location: frontend/components/live_chat_composer/__init__.py
"""

import os
import streamlit.components.v1 as components

_component_dir = os.path.dirname(os.path.abspath(__file__))
_live_chat_composer = components.declare_component(
    "live_chat_composer",
    path=_component_dir
)


def render_live_chat_composer(initial_text: str = "", key: str = "live_chat_composer_widget"):
    """
    Renders the canonical single input message composer with real-time privacy analysis.
    Returns dict: {"text": str, "action": "send" | "clear", "timestamp": int} or None.
    """
    return _live_chat_composer(
        initial_text=initial_text,
        key=key,
        default=None
    )
