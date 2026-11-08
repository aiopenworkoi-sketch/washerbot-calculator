from __future__ import annotations

from ui.theme_tokens import BRAND, rgba

# Streamlit 1.53 sidebar recovery controls (verified via browser CDP).
SIDEBAR_EXPAND_CONTROL_SELECTOR = '[data-testid="stExpandSidebarButton"]'
SIDEBAR_COLLAPSE_CONTROL_SELECTOR = '[data-testid="stSidebarCollapseButton"]'
SIDEBAR_RECOVERY_CONTROLS_SELECTOR = (
    f"{SIDEBAR_EXPAND_CONTROL_SELECTOR}, {SIDEBAR_COLLAPSE_CONTROL_SELECTOR}"
)


def _sidebar_recovery_control_css() -> str:
    """Keep native expand/collapse controls visible and clickable on dark shell."""
    return f"""
    {SIDEBAR_RECOVERY_CONTROLS_SELECTOR} {{
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 1000001 !important;
    }}
    {SIDEBAR_EXPAND_CONTROL_SELECTOR} button,
    {SIDEBAR_COLLAPSE_CONTROL_SELECTOR} button {{
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        min-width: 44px !important;
        min-height: 44px !important;
        color: {BRAND['text']} !important;
        background: {rgba(BRAND['text'], 0.08)} !important;
        border: 1px solid {rgba(BRAND['text'], 0.2)} !important;
        border-radius: 6px !important;
    }}
    @media (max-width: 768px) {{
        {SIDEBAR_EXPAND_CONTROL_SELECTOR} {{
            position: fixed !important;
            left: max(8px, env(safe-area-inset-left)) !important;
            top: max(8px, env(safe-area-inset-top)) !important;
            z-index: 1000003 !important;
        }}
        {SIDEBAR_EXPAND_CONTROL_SELECTOR} button,
        {SIDEBAR_COLLAPSE_CONTROL_SELECTOR} button {{
            min-width: 46px !important;
            min-height: 46px !important;
            border-radius: 8px !important;
        }}
    }}
    """


def build_normal_streamlit_shell_css() -> str:
    """Minimal Streamlit chrome — never hide toolbar subtree that hosts sidebar expand."""
    return (
        _sidebar_recovery_control_css()
        + """
    header[data-testid="stHeader"] {
        visibility: visible !important;
        height: auto !important;
        min-height: 2.75rem !important;
        overflow: visible !important;
        background: transparent !important;
        border-bottom: none !important;
        pointer-events: auto !important;
    }
    header[data-testid="stHeader"] [data-testid="stToolbar"] {
        visibility: visible !important;
        height: auto !important;
        min-height: 2.75rem !important;
        overflow: visible !important;
        pointer-events: auto !important;
    }
    header[data-testid="stHeader"] [data-testid="stLogo"],
    header[data-testid="stHeader"] [data-testid="stDecoration"],
    header[data-testid="stHeader"] [data-testid="stToolbarActions"],
    header[data-testid="stHeader"] [data-testid="stMainMenu"],
    header[data-testid="stHeader"] [data-testid="stStatusWidget"] {
        display: none !important;
    }
    [data-testid="stDecoration"] {
        display: none;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }
    .stDeployButton {
        display: none !important;
    }
    """
    )


def build_presentation_streamlit_shell_css() -> str:
    """Presentation shell — same header rail; do not zero-height header (kills expand)."""
    return (
        _sidebar_recovery_control_css()
        + """
    [data-testid="stAppViewContainer"]:has(.wb-presentation-flag) header[data-testid="stHeader"] {
        visibility: visible !important;
        height: auto !important;
        min-height: 2.25rem !important;
        overflow: visible !important;
        background: transparent !important;
        pointer-events: auto !important;
    }
    [data-testid="stAppViewContainer"]:has(.wb-presentation-flag) header[data-testid="stHeader"] [data-testid="stToolbar"] {
        visibility: visible !important;
        height: auto !important;
        min-height: 2.25rem !important;
        overflow: visible !important;
        pointer-events: auto !important;
    }
    [data-testid="stAppViewContainer"]:has(.wb-presentation-flag) [data-testid="stDecoration"] {
        display: none;
    }
    """
    )
