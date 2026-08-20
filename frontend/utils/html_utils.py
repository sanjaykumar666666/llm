"""
HTML Helper Utilities for Streamlit.
File: frontend/utils/html_utils.py
"""

import streamlit as st

def clean_html(html_str: str) -> str:
    """
    Strips all leading/trailing whitespace and newlines from an HTML string
    so Streamlit's Markdown parser never interprets it as a preformatted code block.
    """
    return "".join(line.strip() for line in html_str.splitlines())

def render_html(html_str: str) -> None:
    """
    Renders clean, unindented HTML in Streamlit without raw text code blocks.
    """
    st.markdown(clean_html(html_str), unsafe_allow_html=True)
