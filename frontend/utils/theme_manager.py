"""
Multi-Palette Theme Engine for AI Privacy Shield.
Provides 8 aesthetic color themes for Privacy Chat, Dashboard, Sidebar, and all modules.
File: frontend/utils/theme_manager.py
"""

from typing import Dict, Any
import streamlit as st

COLOR_THEMES: Dict[str, Dict[str, Any]] = {
    "🌈 Rainbow Aurora": {
        "id": "rainbow_aurora",
        "name": "Rainbow Aurora",
        "description": "Hyper-vibrant 6-color iridescent rainbow spectrum & neon glow",
        "is_dark": True,
        "bg_void": "#050814",
        "bg_surface": "#090f26",
        "bg_card": "linear-gradient(135deg, rgba(13, 20, 42, 0.92), rgba(18, 12, 38, 0.90))",
        "bg_card_subtle": "rgba(16, 28, 49, 0.75)",
        "accent_primary": "#FF007A",
        "accent_secondary": "#00D9F6",
        "accent_tertiary": "#FFAE00",
        "accent_quaternary": "#00F5A0",
        "accent_violet": "#7928CA",
        "gradient": "linear-gradient(135deg, #FF007A 0%, #FF5E3A 20%, #FFAE00 40%, #00F5A0 60%, #00D9F6 80%, #7928CA 100%)",
        "border_sidebar": "linear-gradient(180deg, #FF007A 0%, #FF7A00 20%, #FFD600 40%, #00F5A0 60%, #00D9F6 80%, #7928CA 100%)",
        "border_card": "rgba(255, 255, 255, 0.14)",
        "glow": "0 0 35px rgba(0, 217, 246, 0.4), 0 0 50px rgba(255, 0, 122, 0.3)",
        "user_bubble_bg": "linear-gradient(135deg, rgba(255, 0, 122, 0.18) 0%, rgba(121, 40, 202, 0.22) 100%)",
        "user_bubble_border": "rgba(255, 0, 122, 0.45)",
        "assistant_bubble_bg": "linear-gradient(135deg, rgba(13, 20, 42, 0.90) 0%, rgba(9, 15, 38, 0.90) 100%)",
        "assistant_bubble_border": "rgba(0, 217, 246, 0.35)",
        "badge_bg": "linear-gradient(135deg, rgba(255, 0, 122, 0.15), rgba(0, 217, 246, 0.15))",
        "badge_border": "rgba(0, 217, 246, 0.45)",
        "badge_color": "#00D9F6",
        "text_pure": "#F8FAFC",
        "text_muted": "#94A3B8",
        "preview_colors": ["#FF007A", "#FF7A00", "#00F5A0", "#00D9F6", "#7928CA"]
    },
    "🌌 Cyberpunk Neon": {
        "id": "cyberpunk_neon",
        "name": "Cyberpunk Neon",
        "description": "High-contrast Electric Cyan, Hot Pink, and Laser Purple synthwave aesthetic",
        "is_dark": True,
        "bg_void": "#080811",
        "bg_surface": "#0f0f24",
        "bg_card": "linear-gradient(135deg, rgba(15, 15, 36, 0.92), rgba(24, 10, 40, 0.90))",
        "bg_card_subtle": "rgba(20, 20, 48, 0.75)",
        "accent_primary": "#00F0FF",
        "accent_secondary": "#FF0055",
        "accent_tertiary": "#FFE600",
        "accent_quaternary": "#7000FF",
        "accent_violet": "#D946EF",
        "gradient": "linear-gradient(135deg, #00F0FF 0%, #7000FF 50%, #FF0055 100%)",
        "border_sidebar": "linear-gradient(180deg, #00F0FF 0%, #7000FF 50%, #FF0055 100%)",
        "border_card": "rgba(0, 240, 255, 0.25)",
        "glow": "0 0 35px rgba(0, 240, 255, 0.45), 0 0 50px rgba(255, 0, 85, 0.35)",
        "user_bubble_bg": "linear-gradient(135deg, rgba(0, 240, 255, 0.18) 0%, rgba(112, 0, 255, 0.24) 100%)",
        "user_bubble_border": "rgba(0, 240, 255, 0.5)",
        "assistant_bubble_bg": "linear-gradient(135deg, rgba(15, 15, 36, 0.92) 0%, rgba(24, 10, 40, 0.90) 100%)",
        "assistant_bubble_border": "rgba(255, 0, 85, 0.35)",
        "badge_bg": "linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(255, 0, 85, 0.15))",
        "badge_border": "rgba(0, 240, 255, 0.5)",
        "badge_color": "#00F0FF",
        "text_pure": "#FFFFFF",
        "text_muted": "#A5B4FC",
        "preview_colors": ["#00F0FF", "#7000FF", "#FF0055", "#FFE600"]
    },
    "🔮 Amethyst Galaxy": {
        "id": "amethyst_galaxy",
        "name": "Amethyst Galaxy",
        "description": "Deep Royal Violet, Lavender Nebula, and Cosmic Fuchsia glow",
        "is_dark": True,
        "bg_void": "#0B071A",
        "bg_surface": "#140D2E",
        "bg_card": "linear-gradient(135deg, rgba(20, 13, 46, 0.92), rgba(32, 16, 68, 0.90))",
        "bg_card_subtle": "rgba(28, 18, 60, 0.75)",
        "accent_primary": "#8B5CF6",
        "accent_secondary": "#D946EF",
        "accent_tertiary": "#C084FC",
        "accent_quaternary": "#6366F1",
        "accent_violet": "#A855F7",
        "gradient": "linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #D946EF 100%)",
        "border_sidebar": "linear-gradient(180deg, #6366F1 0%, #8B5CF6 50%, #D946EF 100%)",
        "border_card": "rgba(139, 92, 246, 0.3)",
        "glow": "0 0 35px rgba(139, 92, 246, 0.45), 0 0 50px rgba(217, 70, 239, 0.35)",
        "user_bubble_bg": "linear-gradient(135deg, rgba(139, 92, 246, 0.20) 0%, rgba(217, 70, 239, 0.22) 100%)",
        "user_bubble_border": "rgba(139, 92, 246, 0.5)",
        "assistant_bubble_bg": "linear-gradient(135deg, rgba(20, 13, 46, 0.92) 0%, rgba(32, 16, 68, 0.90) 100%)",
        "assistant_bubble_border": "rgba(217, 70, 239, 0.35)",
        "badge_bg": "linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(217, 70, 239, 0.15))",
        "badge_border": "rgba(139, 92, 246, 0.5)",
        "badge_color": "#C084FC",
        "text_pure": "#FAF5FF",
        "text_muted": "#D8B4FE",
        "preview_colors": ["#6366F1", "#8B5CF6", "#C084FC", "#D946EF"]
    },
    "🌊 Oceanic Azure": {
        "id": "oceanic_azure",
        "name": "Oceanic Azure",
        "description": "Marine Cobalt, Electric Cyan, and Deep Sapphire ocean currents",
        "is_dark": True,
        "bg_void": "#030C1B",
        "bg_surface": "#071830",
        "bg_card": "linear-gradient(135deg, rgba(7, 24, 48, 0.92), rgba(11, 35, 70, 0.90))",
        "bg_card_subtle": "rgba(10, 32, 64, 0.75)",
        "accent_primary": "#06B6D4",
        "accent_secondary": "#3B82F6",
        "accent_tertiary": "#38BDF8",
        "accent_quaternary": "#0284C7",
        "accent_violet": "#6366F1",
        "gradient": "linear-gradient(135deg, #06B6D4 0%, #3B82F6 50%, #1D4ED8 100%)",
        "border_sidebar": "linear-gradient(180deg, #06B6D4 0%, #3B82F6 50%, #1D4ED8 100%)",
        "border_card": "rgba(6, 182, 212, 0.3)",
        "glow": "0 0 35px rgba(6, 182, 212, 0.45), 0 0 50px rgba(59, 130, 246, 0.35)",
        "user_bubble_bg": "linear-gradient(135deg, rgba(6, 182, 212, 0.20) 0%, rgba(59, 130, 246, 0.24) 100%)",
        "user_bubble_border": "rgba(6, 182, 212, 0.5)",
        "assistant_bubble_bg": "linear-gradient(135deg, rgba(7, 24, 48, 0.92) 0%, rgba(11, 35, 70, 0.90) 100%)",
        "assistant_bubble_border": "rgba(59, 130, 246, 0.35)",
        "badge_bg": "linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(59, 130, 246, 0.15))",
        "badge_border": "rgba(6, 182, 212, 0.5)",
        "badge_color": "#38BDF8",
        "text_pure": "#F0F9FF",
        "text_muted": "#7DD3FC",
        "preview_colors": ["#06B6D4", "#38BDF8", "#3B82F6", "#1D4ED8"]
    },
    "🌲 Emerald Matrix": {
        "id": "emerald_matrix",
        "name": "Emerald Matrix",
        "description": "Mint Green, Jade Matrix, and Cyber Emerald terminal energy",
        "is_dark": True,
        "bg_void": "#040D0A",
        "bg_surface": "#081A14",
        "bg_card": "linear-gradient(135deg, rgba(8, 26, 20, 0.92), rgba(12, 40, 30, 0.90))",
        "bg_card_subtle": "rgba(10, 34, 26, 0.75)",
        "accent_primary": "#00F5A0",
        "accent_secondary": "#10B981",
        "accent_tertiary": "#34D399",
        "accent_quaternary": "#059669",
        "accent_violet": "#0D9488",
        "gradient": "linear-gradient(135deg, #00F5A0 0%, #10B981 50%, #059669 100%)",
        "border_sidebar": "linear-gradient(180deg, #00F5A0 0%, #10B981 50%, #059669 100%)",
        "border_card": "rgba(0, 245, 160, 0.3)",
        "glow": "0 0 35px rgba(0, 245, 160, 0.45), 0 0 50px rgba(16, 185, 129, 0.35)",
        "user_bubble_bg": "linear-gradient(135deg, rgba(0, 245, 160, 0.18) 0%, rgba(16, 185, 129, 0.22) 100%)",
        "user_bubble_border": "rgba(0, 245, 160, 0.5)",
        "assistant_bubble_bg": "linear-gradient(135deg, rgba(8, 26, 20, 0.92) 0%, rgba(12, 40, 30, 0.90) 100%)",
        "assistant_bubble_border": "rgba(16, 185, 129, 0.35)",
        "badge_bg": "linear-gradient(135deg, rgba(0, 245, 160, 0.15), rgba(16, 185, 129, 0.15))",
        "badge_border": "rgba(0, 245, 160, 0.5)",
        "badge_color": "#00F5A0",
        "text_pure": "#F0FDF4",
        "text_muted": "#86EFAC",
        "preview_colors": ["#00F5A0", "#34D399", "#10B981", "#059669"]
    },
    "🌅 Sunset Solar": {
        "id": "sunset_solar",
        "name": "Sunset Solar",
        "description": "Crimson Rose, Solar Amber, and Warm Blood Orange twilight horizon",
        "is_dark": True,
        "bg_void": "#12080D",
        "bg_surface": "#1F0F17",
        "bg_card": "linear-gradient(135deg, rgba(31, 15, 23, 0.92), rgba(48, 20, 32, 0.90))",
        "bg_card_subtle": "rgba(40, 18, 28, 0.75)",
        "accent_primary": "#FF5E3A",
        "accent_secondary": "#FFAE00",
        "accent_tertiary": "#FF0844",
        "accent_quaternary": "#F59E0B",
        "accent_violet": "#E11D48",
        "gradient": "linear-gradient(135deg, #FF0844 0%, #FF5E3A 50%, #FFAE00 100%)",
        "border_sidebar": "linear-gradient(180deg, #FF0844 0%, #FF5E3A 50%, #FFAE00 100%)",
        "border_card": "rgba(255, 94, 58, 0.3)",
        "glow": "0 0 35px rgba(255, 94, 58, 0.45), 0 0 50px rgba(255, 174, 0, 0.35)",
        "user_bubble_bg": "linear-gradient(135deg, rgba(255, 8, 68, 0.18) 0%, rgba(255, 94, 58, 0.22) 100%)",
        "user_bubble_border": "rgba(255, 94, 58, 0.5)",
        "assistant_bubble_bg": "linear-gradient(135deg, rgba(31, 15, 23, 0.92) 0%, rgba(48, 20, 32, 0.90) 100%)",
        "assistant_bubble_border": "rgba(255, 174, 0, 0.35)",
        "badge_bg": "linear-gradient(135deg, rgba(255, 94, 58, 0.15), rgba(255, 174, 0, 0.15))",
        "badge_border": "rgba(255, 94, 58, 0.5)",
        "badge_color": "#FFAE00",
        "text_pure": "#FFF1F2",
        "text_muted": "#FDA4AF",
        "preview_colors": ["#FF0844", "#FF5E3A", "#FFAE00", "#F59E0B"]
    },
    "🌑 Midnight Stealth": {
        "id": "midnight_stealth",
        "name": "Midnight Stealth",
        "description": "Pure OLED Obsidian, Titanium Platinum, and Frost Ice accents",
        "is_dark": True,
        "bg_void": "#000000",
        "bg_surface": "#0b0b0f",
        "bg_card": "linear-gradient(135deg, rgba(16, 16, 22, 0.92), rgba(24, 24, 32, 0.90))",
        "bg_card_subtle": "rgba(20, 20, 28, 0.75)",
        "accent_primary": "#38BDF8",
        "accent_secondary": "#E2E8F0",
        "accent_tertiary": "#94A3B8",
        "accent_quaternary": "#64748B",
        "accent_violet": "#475569",
        "gradient": "linear-gradient(135deg, #38BDF8 0%, #94A3B8 50%, #E2E8F0 100%)",
        "border_sidebar": "linear-gradient(180deg, #38BDF8 0%, #94A3B8 50%, #E2E8F0 100%)",
        "border_card": "rgba(255, 255, 255, 0.18)",
        "glow": "0 0 30px rgba(56, 189, 248, 0.35), 0 0 45px rgba(226, 232, 240, 0.20)",
        "user_bubble_bg": "linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.6) 100%)",
        "user_bubble_border": "rgba(148, 163, 184, 0.5)",
        "assistant_bubble_bg": "linear-gradient(135deg, rgba(16, 16, 22, 0.92) 0%, rgba(24, 24, 32, 0.90) 100%)",
        "assistant_bubble_border": "rgba(56, 189, 248, 0.35)",
        "badge_bg": "linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(226, 232, 240, 0.15))",
        "badge_border": "rgba(56, 189, 248, 0.45)",
        "badge_color": "#38BDF8",
        "text_pure": "#FFFFFF",
        "text_muted": "#94A3B8",
        "preview_colors": ["#000000", "#38BDF8", "#94A3B8", "#E2E8F0"]
    },
    "☀️ Daylight Pristine": {
        "id": "daylight_pristine",
        "name": "Daylight Pristine",
        "description": "Clean Enterprise Bright Mode with Sapphire and Lavender highlights",
        "is_dark": False,
        "bg_void": "#F8FAFC",
        "bg_surface": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_card_subtle": "#F1F5F9",
        "accent_primary": "#2563EB",
        "accent_secondary": "#7C3AED",
        "accent_tertiary": "#06B6D4",
        "accent_quaternary": "#10B981",
        "accent_violet": "#8B5CF6",
        "gradient": "linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)",
        "border_sidebar": "linear-gradient(180deg, #2563EB 0%, #7C3AED 100%)",
        "border_card": "rgba(203, 213, 225, 0.8)",
        "glow": "0 0 25px rgba(37, 99, 235, 0.20)",
        "user_bubble_bg": "linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%)",
        "user_bubble_border": "#93C5FD",
        "assistant_bubble_bg": "#FFFFFF",
        "assistant_bubble_border": "#E2E8F0",
        "badge_bg": "rgba(37, 99, 235, 0.10)",
        "badge_border": "rgba(37, 99, 235, 0.35)",
        "badge_color": "#2563EB",
        "text_pure": "#0F172A",
        "text_muted": "#64748B",
        "preview_colors": ["#F8FAFC", "#2563EB", "#7C3AED", "#06B6D4"]
    }
}


def get_current_theme_key() -> str:
    """Returns the active color theme key from session state."""
    if "color_theme" not in st.session_state:
        st.session_state["color_theme"] = "🌈 Rainbow Aurora"
    return st.session_state["color_theme"]


def get_current_theme() -> Dict[str, Any]:
    """Returns the dictionary for the active color theme."""
    key = get_current_theme_key()
    return COLOR_THEMES.get(key, COLOR_THEMES["🌈 Rainbow Aurora"])


def inject_theme_css() -> None:
    """Injects dynamic CSS variables and layout rules for the current theme."""
    theme = get_current_theme()

    css = f"""
    <style>
    :root {{
        --theme-name: "{theme['name']}";
        --bg-void: {theme['bg_void']};
        --bg-surface: {theme['bg_surface']};
        --bg-card: {theme['bg_card']};
        --bg-card2: {theme['bg_card_subtle']};
        --bg-card3: {theme['bg_card_subtle']};
        --bg-input: {theme['bg_surface']};
        --theme-accent-primary: {theme['accent_primary']};
        --theme-accent-secondary: {theme['accent_secondary']};
        --theme-accent-tertiary: {theme['accent_tertiary']};
        --theme-accent-quaternary: {theme['accent_quaternary']};
        --theme-gradient: {theme['gradient']};
        --theme-glow: {theme['glow']};
        --theme-border-card: {theme['border_card']};
        --theme-user-bubble-bg: {theme['user_bubble_bg']};
        --theme-user-bubble-border: {theme['user_bubble_border']};
        --theme-assistant-bubble-bg: {theme['assistant_bubble_bg']};
        --theme-assistant-bubble-border: {theme['assistant_bubble_border']};
        --text-pure: {theme['text_pure']};
        --text-muted: {theme['text_muted']};
        --sidebar-width: 270px;
    }}

    /* Global Body & Main Background */
    html, body, .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main, .main {{
        background: {theme['bg_void']} !important;
        background-color: {theme['bg_void']} !important;
        color: {theme['text_pure']} !important;
    }}

    /* Sidebar Dynamic Theme Glow & Border */
    div[data-testid="stSidebarNav"],
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child,
    div[data-testid="stSidebarContent"],
    div[data-testid="stSidebarUserContent"],
    div[data-testid="stSidebarHeader"],
    [data-testid="stSidebar"] {{
        background: {theme['bg_surface']} !important;
        background-color: {theme['bg_surface']} !important;
        border-right: 2px solid rgba(255, 255, 255, 0.15) !important;
        border-image: {theme['border_sidebar']} 1 !important;
        box-shadow: {theme['glow']} !important;
    }}

    /* Active Sidebar Navigation Item */
    section[data-testid="stSidebar"] [data-testid="baseButton-primary"],
    section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
    section[data-testid="stSidebar"] button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    div[data-testid="stSidebar"] [data-testid="baseButton-primary"],
    div[data-testid="stSidebar"] button[kind="primary"] {{
        background: {theme['gradient']} !important;
        background-size: 250% 250% !important;
        color: #FFFFFF !important;
        border: 1.5px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 13px !important;
        box-shadow: {theme['glow']} !important;
    }}

    /* Chat Messages Theming */
    .stChatMessage, [data-testid="stChatMessage"] {{
        background: {theme['bg_card']} !important;
        border: 1px solid {theme['border_card']} !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
        margin-bottom: 12px !important;
    }}

    /* Text Inputs & Areas */
    .stTextArea textarea, .stTextInput input, .stSelectbox [data-baseweb="select"] {{
        background: {theme['bg_surface']} !important;
        color: {theme['text_pure']} !important;
        border: 1.5px solid {theme['border_card']} !important;
        border-radius: 10px !important;
    }}

    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {theme['accent_primary']} !important;
        box-shadow: 0 0 15px {theme['accent_primary']}55 !important;
    }}

    /* Primary Buttons Glow */
    button[data-testid="baseButton-primary"],
    button[data-testid="stBaseButton-primary"],
    .stButton > button[kind="primary"] {{
        background: {theme['gradient']} !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 18px {theme['accent_primary']}44 !important;
    }}

    button[data-testid="baseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover {{
        box-shadow: {theme['glow']} !important;
        transform: translateY(-2px) !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
