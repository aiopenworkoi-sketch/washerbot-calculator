from __future__ import annotations

from typing import Mapping


def build_layout_css(brand: Mapping[str, str]) -> str:
    """Scoped layout polish: export grid, chart shells, section rhythm."""
    return f"""
    /* === LAYOUT POLISH (Step 39 / 39B) === */
    .wb-section-block {{
        margin-bottom: 20px;
    }}
    .wb-section-block--tight {{
        margin-bottom: 14px;
    }}
    .wb-card-title {{
        margin-bottom: 12px !important;
    }}
    .wb-section-subtitle {{
        margin: -4px 0 12px 0 !important;
    }}
    .wb-section-takeaway {{
        margin: 0 0 14px 0 !important;
    }}
    .wb-section-caption {{
        margin: 10px 0 0 0 !important;
    }}
    .wb-detail-subheading {{
        margin: 18px 0 10px 0 !important;
    }}
    .wb-export-groups-shell {{
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 0;
    }}
    .wb-export-board {{
        display: block;
        margin: 0 0 10px 0;
        padding: 10px 12px;
        background: rgba(17, 24, 39, 0.42);
        border: 1px solid {brand['border_subtle']};
        border-radius: 12px;
        box-sizing: border-box;
    }}
    .wb-export-board [data-testid="stHorizontalBlock"]:has(.wb-export-tile--board) {{
        align-items: stretch !important;
        gap: 10px !important;
        margin-bottom: 10px;
    }}
    .wb-export-board [data-testid="stHorizontalBlock"]:has(.wb-export-tile--board):last-child {{
        margin-bottom: 0;
    }}
    .wb-export-shell {{
        margin-bottom: 8px;
        padding: 8px 12px !important;
    }}
    .wb-export-shell .wb-export-note {{
        margin: 0 0 2px 0 !important;
        font-size: 0.82rem !important;
        line-height: 1.4 !important;
    }}
    .wb-export-shell .wb-section-caption {{
        margin: 0 !important;
        font-size: 0.75rem !important;
        line-height: 1.35 !important;
    }}
    .wb-export-group {{
        margin: 0;
        padding: 8px 10px;
        background: rgba(17, 24, 39, 0.35);
        border: 1px solid {brand['border_subtle']};
        border-radius: 10px;
    }}
    .wb-export-group--utility {{
        opacity: 0.95;
        background: rgba(17, 24, 39, 0.22);
    }}
    .wb-export-group--utility .wb-export-group-title {{
        font-size: 0.82rem;
        font-weight: 500;
        color: {brand['text2']};
    }}
    .wb-export-group-head {{
        margin-bottom: 6px;
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 6px 10px;
    }}
    .wb-export-group-title {{
        color: {brand['text']};
        font-size: 0.88rem;
        font-weight: 600;
        margin: 0;
        line-height: 1.3;
    }}
    .wb-export-group-desc {{
        color: {brand['muted']};
        font-size: 0.75rem;
        margin: 0;
        line-height: 1.35;
        flex: 1 1 12rem;
    }}
    .wb-export-tile {{
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-height: 0;
        margin-bottom: 2px;
    }}
    .wb-export-tile--board {{
        flex: 1 1 auto;
        min-height: 108px;
        padding: 10px 10px 6px 10px;
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid {brand['border_subtle']};
        border-radius: 10px;
        box-sizing: border-box;
    }}
    .wb-export-tile--board.wb-export-tile--disabled {{
        opacity: 0.55;
    }}
    .wb-export-tile-title {{
        color: {brand['text']};
        font-size: 0.86rem;
        font-weight: 600;
        line-height: 1.25;
        margin: 0;
    }}
    .wb-export-secondary {{
        margin-top: 12px;
        opacity: 0.92;
    }}
    .wb-export-monthly-block {{
        padding-top: 4px;
    }}
    .wb-export-group--secondary {{
        margin-top: 14px;
        padding: 10px 12px;
        background: rgba(17, 24, 39, 0.22);
        border: 1px dashed {brand['border_subtle']};
        border-radius: 10px;
    }}
    .wb-export-group--secondary .wb-export-group-title {{
        font-size: 0.82rem;
        font-weight: 500;
        color: {brand['text2']};
        margin: 0 0 8px 0;
    }}
    .wb-export-tile-head {{
        display: flex;
        align-items: center;
        gap: 6px;
        min-height: 0;
    }}
    .wb-export-tile-hint {{
        color: {brand['text2']};
        font-size: 0.75rem;
        line-height: 1.35;
        margin: 0;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 1;
        overflow: hidden;
    }}
    .wb-export-card {{
        display: none;
    }}
    .wb-export-action {{
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-height: 0;
        height: auto;
        box-sizing: border-box;
    }}
    [data-testid="stHorizontalBlock"]:has(.wb-export-tile) {{
        align-items: stretch !important;
        gap: 8px !important;
    }}
    [data-testid="column"]:has(.wb-export-tile--board) {{
        display: flex;
        flex-direction: column;
        min-width: 0;
        gap: 6px;
    }}
    [data-testid="column"]:has(.wb-export-tile) {{
        display: flex;
        flex-direction: column;
        min-width: 0;
        gap: 4px;
    }}
    [data-testid="column"]:has(.wb-export-tile) [data-testid="stDownloadButton"],
    [data-testid="column"]:has(.wb-export-tile) .stDownloadButton {{
        margin-top: auto;
        width: 100%;
    }}
    [data-testid="column"]:has(.wb-export-tile--board) .stDownloadButton > button {{
        min-height: 42px;
        font-weight: 600;
    }}
    [data-testid="column"]:has(.wb-export-tile) .stDownloadButton > button {{
        min-height: 40px;
        padding: 0.35rem 0.55rem;
        font-size: 0.8rem;
        width: 100%;
        box-sizing: border-box;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .wb-export-compare-empty {{
        min-height: 48px;
        display: flex;
        align-items: center;
        font-size: 0.82rem;
    }}
    .wb-export-monthly-separator {{
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed {brand['border_subtle']};
    }}
    .wb-export-badge {{
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {brand['cyan']};
        background: rgba(46, 134, 255, 0.08);
        border: 1px solid rgba(46, 134, 255, 0.22);
        border-radius: 999px;
        padding: 2px 7px;
        width: fit-content;
        flex-shrink: 0;
    }}
    .wb-compare-panel {{
        background: {brand['card']};
        border: 1px solid {brand['border']};
        border-radius: 10px;
        padding: 12px 14px;
        margin: 0 0 16px 0;
        overflow-x: auto;
        max-width: 100%;
        box-sizing: border-box;
    }}
    .wb-chart-shell {{
        background: {brand['card']};
        border: 1px solid {brand['border']};
        border-radius: 10px;
        padding: 8px 10px 2px 10px;
        margin: 0 0 12px 0;
        overflow: hidden;
        max-width: 100%;
        box-sizing: border-box;
    }}
    .wb-chart-shell [data-testid="stPlotlyChart"] {{
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 0;
        margin: 0;
    }}
    .wb-chart-shell [data-testid="stPlotlyChart"] > div {{
        width: 100% !important;
        max-width: 100% !important;
    }}
    .wb-table-shell {{
        background: {brand['card']};
        border: 1px solid {brand['border']};
        border-radius: 10px;
        padding: 4px 6px;
        margin: 0 0 16px 0;
        overflow-x: auto;
        max-width: 100%;
        box-sizing: border-box;
    }}
    .wb-table-shell [data-testid="stDataFrame"] {{
        font-variant-numeric: tabular-nums;
        width: 100%;
    }}
    [data-testid="stMarkdownContainer"] p:has(.wb-chart-shell),
    [data-testid="stMarkdownContainer"] p:has(.wb-table-shell),
    .stMarkdown p:has(.wb-chart-shell),
    .stMarkdown p:has(.wb-table-shell) {{
        margin: 0;
    }}
    [data-testid="stPlotlyChart"] {{
        background: {brand['card']};
        border: 1px solid {brand['border']};
        border-radius: 10px;
        padding: 8px 10px 2px 10px;
        margin: 0 0 16px 0;
        box-sizing: border-box;
        max-width: 100%;
        overflow: hidden;
    }}
    [data-testid="stPlotlyChart"] > div {{
        width: 100% !important;
    }}
    .wb-export-shell + .wb-export-group .wb-export-group-title,
    .wb-export-group:first-of-type .wb-export-group-title {{
        margin-top: 0;
    }}
    /* Компактный режим для 1366x768: первый экран должен показывать вердикт */
    @media (max-width: 1500px) {{
        .wb-header {{
            padding: 12px 18px !important;
            margin-bottom: 10px !important;
        }}
        .wb-hero {{
            padding: 14px 18px 12px 18px;
            margin-bottom: 12px;
        }}
        .wb-hero-headline {{
            font-size: 1.15rem;
        }}
        .wb-hero-metric {{
            padding: 8px 10px;
        }}
        .wb-hero-metric-value {{
            font-size: 1.2rem;
        }}
        .wb-kpi-grid {{
            gap: 8px;
        }}
    }}
    @media (max-width: 900px) {{
        [data-testid="stHorizontalBlock"]:has(.wb-export-tile) {{
            flex-wrap: wrap !important;
        }}
    }}
    @media (max-width: 640px) {{
        .wb-export-board {{
            padding: 8px 8px;
        }}
        .wb-export-board [data-testid="stHorizontalBlock"]:has(.wb-export-tile--board) {{
            flex-direction: column !important;
            margin-bottom: 0;
        }}
        [data-testid="stHorizontalBlock"]:has(.wb-export-tile) {{
            flex-direction: column !important;
        }}
        [data-testid="column"]:has(.wb-export-tile--board) {{
            width: 100% !important;
            flex: 1 1 100% !important;
        }}
        [data-testid="column"]:has(.wb-export-tile) {{
            width: 100% !important;
            flex: 1 1 100% !important;
        }}
        .wb-export-tile--board {{
            min-height: 96px;
        }}
        .wb-export-group {{
            padding: 8px 8px;
        }}
        .wb-export-group-desc {{
            flex-basis: 100%;
        }}
        [data-testid="column"]:has(.wb-export-tile) .stDownloadButton > button {{
            min-height: 46px;
            font-size: 0.88rem;
        }}
    }}
    @media (max-width: 768px) {{
        section[data-testid="stSidebar"] [data-testid="stNumberInput"] input,
        section[data-testid="stSidebar"] [data-testid="stTextInput"] input,
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] input,
        section[data-testid="stSidebar"] textarea {{
            font-size: 16px !important;
        }}
        section[data-testid="stSidebar"] .stButton > button,
        section[data-testid="stSidebar"] [data-testid="stDownloadButton"] button {{
            min-height: 46px !important;
        }}
        .wb-scenario-mobile-zone .stButton > button,
        .wb-scenario-mobile-zone [data-testid="stDownloadButton"] button {{
            min-height: 46px !important;
        }}
        .wb-scenario-mobile-zone [data-testid="stHorizontalBlock"] {{
            flex-direction: column !important;
        }}
        .wb-footer-pill,
        .wb-footer-cta {{
            min-height: 44px;
            font-size: 0.86rem;
            width: 100%;
            justify-content: center;
        }}
    }}

    /* === KPI GRID (Step 39A) === */
    .wb-kpi-shell {{
        width: 100%;
        max-width: 100%;
        margin: 0 0 14px 0;
        box-sizing: border-box;
    }}
    [data-testid="stMarkdownContainer"] p:has(.wb-kpi-shell),
    .stMarkdown p:has(.wb-kpi-shell) {{
        margin: 0;
    }}
    .wb-kpi-grid {{
        display: grid;
        gap: 12px;
        width: 100%;
        max-width: 100%;
        margin: 0;
        align-items: stretch;
        grid-auto-rows: 1fr;
        box-sizing: border-box;
    }}
    .wb-kpi-grid--cols-4 {{
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }}
    .wb-kpi-grid--cols-3 {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }}
    .wb-kpi-grid--cols-2 {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .wb-kpi-grid--cols-1 {{
        grid-template-columns: minmax(0, 1fr);
    }}
    .wb-kpi-grid .wb-metric {{
        display: flex;
        flex-direction: column;
        min-height: 122px;
        height: 100%;
        min-width: 0;
        max-width: 100%;
        overflow: hidden;
        box-sizing: border-box;
        padding: 14px 16px;
    }}
    .wb-kpi-grid .wb-metric-body {{
        flex: 1 1 auto;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        gap: 6px;
        min-height: 74px;
        min-width: 0;
    }}
    .wb-kpi-grid .wb-metric-label--clamp {{
        flex: 0 0 auto;
        min-height: 2.5em;
        max-height: 2.5em;
        line-height: 1.25;
        margin-bottom: 2px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow-wrap: anywhere;
        word-break: break-word;
    }}
    .wb-kpi-grid .wb-metric-value {{
        font-variant-numeric: tabular-nums;
        flex: 0 0 auto;
        min-width: 0;
        max-width: 100%;
        font-size: 1.35rem;
        line-height: 1.15;
        overflow-wrap: anywhere;
        word-break: break-word;
        hyphens: auto;
    }}
    .wb-kpi-grid .wb-metric--primary .wb-metric-value {{
        font-size: 1.35rem;
        font-weight: 700;
    }}
    .wb-kpi-grid .wb-metric--secondary .wb-metric-value {{
        font-size: 1.25rem;
        font-weight: 600;
    }}
    .wb-kpi-grid .wb-metric-value--compact {{
        font-size: 1.12rem;
    }}
    .wb-kpi-grid .wb-metric-value--long {{
        font-size: 1.02rem;
        line-height: 1.2;
    }}
    .wb-kpi-grid .wb-metric-hint--clamp {{
        flex: 0 0 auto;
        margin-top: auto;
        min-height: 2.7em;
        max-height: 2.7em;
        line-height: 1.35;
        overflow: hidden;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow-wrap: anywhere;
        word-break: break-word;
    }}
    .wb-kpi-grid .wb-metric-hint--empty {{
        visibility: hidden;
        pointer-events: none;
    }}
    @media (max-width: 1100px) {{
        .wb-kpi-grid--cols-4 {{
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }}
        .wb-kpi-grid--cols-3 {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}
    @media (max-width: 900px) {{
        .wb-kpi-grid--cols-4,
        .wb-kpi-grid--cols-3 {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}
    @media (max-width: 640px) {{
        .wb-kpi-grid--cols-4,
        .wb-kpi-grid--cols-3,
        .wb-kpi-grid--cols-2 {{
            grid-template-columns: minmax(0, 1fr);
        }}
        .wb-kpi-grid .wb-metric {{
            min-height: 112px;
        }}
        .wb-kpi-grid .wb-metric-value,
        .wb-kpi-grid .wb-metric--primary .wb-metric-value {{
            font-size: 1.28rem;
        }}
    }}

    /* === STEP 40: EXECUTIVE HERO + VISUAL SYSTEM === */
    .wb-main-canvas {{
        max-width: 1180px;
        margin: 0 auto;
    }}
    .wb-hero {{
        background: linear-gradient(
            135deg,
            rgba(91, 141, 239, 0.10) 0%,
            {brand['surface']} 38%,
            {brand['surface2']} 100%
        );
        border: 1px solid {brand['border_default']};
        border-radius: 16px;
        padding: 22px 24px 20px 24px;
        margin: 0 0 20px 0;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.22);
    }}
    .wb-hero--good {{
        border-color: rgba(79, 168, 130, 0.35);
    }}
    .wb-hero--info {{
        border-color: rgba(91, 141, 239, 0.35);
    }}
    .wb-hero--warn {{
        border-color: rgba(184, 154, 74, 0.35);
    }}
    .wb-hero--bad {{
        border-color: rgba(201, 107, 107, 0.35);
    }}
    .wb-hero-top {{
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 18px;
    }}
    .wb-hero-status {{
        display: inline-flex;
        align-self: flex-start;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {brand['text2']};
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid {brand['border_subtle']};
        border-radius: 999px;
        padding: 4px 10px;
    }}
    .wb-hero--good .wb-hero-status {{
        color: {brand['green']};
        border-color: rgba(79, 168, 130, 0.35);
        background: rgba(79, 168, 130, 0.08);
    }}
    .wb-hero--bad .wb-hero-status {{
        color: {brand['red']};
        border-color: rgba(201, 107, 107, 0.35);
        background: rgba(201, 107, 107, 0.08);
    }}
    .wb-hero-headline {{
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.35;
        color: {brand['text']};
        margin: 0;
        letter-spacing: -0.02em;
        max-width: 52rem;
    }}
    .wb-hero-metrics {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
    }}
    .wb-hero-metric {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid {brand['border_subtle']};
        border-radius: 12px;
        padding: 12px 14px;
        min-width: 0;
    }}
    .wb-hero-metric-label {{
        font-size: 0.75rem;
        font-weight: 500;
        color: {brand['muted']};
        margin-bottom: 6px;
        letter-spacing: 0.02em;
    }}
    .wb-hero-metric-value {{
        font-variant-numeric: tabular-nums;
        font-size: 1.45rem;
        font-weight: 700;
        color: {brand['text']};
        line-height: 1.15;
        letter-spacing: -0.02em;
        overflow-wrap: anywhere;
    }}
    .wb-hero-metric-hint {{
        font-size: 0.75rem;
        color: {brand['text2']};
        margin-top: 5px;
        line-height: 1.35;
    }}
    .wb-hero-context {{
        font-size: 0.82rem;
        color: {brand['muted']};
        margin: 14px 0 0 0;
        line-height: 1.5;
        max-width: 56rem;
    }}
    @media (max-width: 900px) {{
        .wb-hero-metrics {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
        .wb-hero-headline {{
            font-size: 1.2rem;
        }}
    }}
    @media (max-width: 520px) {{
        .wb-hero {{
            padding: 16px 14px;
        }}
        .wb-hero-metrics {{
            grid-template-columns: minmax(0, 1fr);
        }}
        .wb-hero-metric-value {{
            font-size: 1.28rem;
        }}
    }}

    .wb-surface-secondary {{
        background: {brand['surface']} !important;
        border-color: {brand['border_subtle']} !important;
        box-shadow: none !important;
        padding: 14px 16px !important;
        margin-bottom: 14px !important;
    }}
    .wb-config-title {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {brand['muted']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0 0 10px 0;
    }}

    .wb-section-head {{
        margin: 0 0 14px 0;
        padding-bottom: 2px;
    }}
    .wb-section-head .wb-section-title {{
        margin-bottom: 0 !important;
    }}
    .wb-section-head .wb-section-title::before {{
        display: none;
    }}
    .wb-section-title {{
        font-size: 1.02rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}
    .wb-section-eyebrow {{
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: {brand['muted']};
        margin-bottom: 4px;
    }}
    .wb-section-head .wb-section-subtitle {{
        margin: 6px 0 0 0 !important;
        font-size: 0.84rem;
        line-height: 1.45;
        color: {brand['muted']};
        max-width: 48rem;
    }}
    .wb-section-subtitle--standalone {{
        margin: -6px 0 12px 0 !important;
    }}
    .wb-section-takeaway {{
        font-size: 0.88rem !important;
        color: {brand['text2']} !important;
    }}
    .wb-section-caption {{
        font-size: 0.78rem !important;
        color: {brand['muted']} !important;
    }}
    .wb-detail-subheading {{
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: {brand['text2']} !important;
    }}

    /* === DETAIL SECTION SWITCHER (premium segmented tabs) === */
    .wb-detail-tabs-rail {{
        margin: 4px 0 10px 0;
    }}
    .wb-detail-tabs-rail ~ [data-testid="stTabs"],
    .wb-detail-tabs-rail + div [data-testid="stTabs"],
    div:has(> .wb-detail-tabs-rail) [data-testid="stTabs"] {{
        margin-top: 0;
    }}
    [data-testid="stTabs"]:has([data-baseweb="tab"][aria-selected="true"]) {{
        margin-bottom: 8px;
    }}
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 4px;
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid {brand['border_subtle']};
        border-radius: 12px;
        padding: 4px;
        min-height: 44px;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }}
    [data-testid="stTabs"] [data-baseweb="tab-border"] {{
        display: none;
    }}
    [data-testid="stTabs"] [data-baseweb="tab"] {{
        background: transparent;
        color: {brand['muted']};
        font-weight: 600;
        font-size: 0.84rem;
        border-radius: 8px;
        padding: 8px 14px;
        border: 1px solid transparent;
        transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
        white-space: nowrap;
    }}
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {{
        color: {brand['text2']};
        background: rgba(91, 141, 239, 0.08);
        border-color: rgba(91, 141, 239, 0.18);
    }}
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {{
        color: {brand['text']} !important;
        background: linear-gradient(
            180deg,
            rgba(91, 141, 239, 0.22) 0%,
            rgba(91, 141, 239, 0.1) 100%
        ) !important;
        border-color: rgba(91, 141, 239, 0.45) !important;
        box-shadow: 0 0 0 1px rgba(91, 141, 239, 0.12), 0 6px 18px rgba(15, 23, 42, 0.35);
    }}
    @media (max-width: 768px) {{
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            flex-wrap: wrap;
            justify-content: stretch;
        }}
        [data-testid="stTabs"] [data-baseweb="tab"] {{
            flex: 1 1 auto;
            text-align: center;
            font-size: 0.8rem;
            padding: 8px 10px;
        }}
    }}

    /* === PREMIUM FOOTER / CLOSING CTA === */
    .wb-footer {{
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.98) 55%, rgba(12, 18, 32, 1) 100%);
        border: 1px solid {brand['border_subtle']};
        border-radius: 14px;
        padding: 18px 20px 14px 20px;
        margin-top: 24px;
        text-align: left;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }}
    .wb-footer-grid {{
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
        gap: 16px 24px;
        align-items: center;
    }}
    .wb-footer-kicker {{
        color: {brand['muted']};
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 0 0 6px 0;
    }}
    .wb-footer h3 {{
        color: {brand['text']} !important;
        margin: 0 0 6px 0;
        font-size: 1.08rem;
        line-height: 1.35;
        font-weight: 600;
    }}
    .wb-footer-support {{
        color: {brand['text2']};
        font-size: 0.86rem;
        margin: 0;
        line-height: 1.45;
        max-width: 34rem;
    }}
    .wb-footer-contact {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
        align-items: center;
    }}
    .wb-footer-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: {brand['text']} !important;
        text-decoration: none !important;
        font-weight: 500;
        font-size: 0.8rem;
        padding: 7px 12px;
        border-radius: 999px;
        border: 1px solid {brand['border_subtle']};
        background: rgba(15, 23, 42, 0.55);
        transition: border-color 0.15s ease, background 0.15s ease;
    }}
    .wb-footer-pill:hover {{
        border-color: rgba(91, 141, 239, 0.45);
        background: rgba(91, 141, 239, 0.1);
        text-decoration: none !important;
    }}
    .wb-footer-cta {{
        display: inline-flex;
        align-items: center;
        color: {brand['text']} !important;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 8px 14px;
        border-radius: 8px;
        border: 1px solid rgba(91, 141, 239, 0.45);
        background: rgba(91, 141, 239, 0.14);
    }}
    .wb-footer-cta:hover {{
        background: rgba(91, 141, 239, 0.22);
        text-decoration: none !important;
    }}
    .wb-footer-legal {{
        margin: 12px 0 0 0 !important;
        padding-top: 10px;
        border-top: 1px solid {brand['border_subtle']};
        font-size: 0.75rem !important;
        color: {brand['muted']} !important;
        text-align: center;
        line-height: 1.4;
    }}
    @media (max-width: 860px) {{
        .wb-footer-grid {{
            grid-template-columns: 1fr;
        }}
        .wb-footer-contact {{
            justify-content: flex-start;
        }}
    }}

    .wb-kpi-shell .wb-metric {{
        background: {brand['surface']};
        border: 1px solid {brand['border_subtle']};
        border-left: 2px solid {brand['border_subtle']};
        box-shadow: none;
    }}
    .wb-kpi-shell .wb-metric--primary {{
        background: linear-gradient(180deg, rgba(91,141,239,0.05) 0%, {brand['surface']} 100%);
        border-left-color: rgba(91, 141, 239, 0.55);
    }}
    .wb-chart-shell,
    .wb-table-shell {{
        background: {brand['surface']};
        border: 1px solid {brand['border_subtle']};
        box-shadow: none;
    }}
    .wb-table-shell [data-testid="stDataFrame"] {{
        font-size: 0.84rem;
    }}
    .wb-table-shell [data-testid="stDataFrame"] th {{
        font-size: 0.76rem;
        color: {brand['muted']};
        font-weight: 600;
    }}

    section[data-testid="stSidebar"] {{
        border-right-color: {brand['border_subtle']} !important;
        background: {brand['surface_muted']} !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: {brand['muted']} !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em;
        margin-top: 1rem !important;
        margin-bottom: 0.45rem !important;
    }}
    section[data-testid="stSidebar"] .wb-sidebar-heading {{
        font-size: 0.75rem !important;
        margin: 1rem 0 0.4rem 0 !important;
        padding-bottom: 0.35rem !important;
        border-bottom-color: {brand['border_subtle']} !important;
    }}
    section[data-testid="stSidebar"] label {{
        font-size: 0.86rem !important;
    }}
    section[data-testid="stSidebar"] .stNumberInput,
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stTextInput {{
        margin-bottom: 0.35rem;
    }}

    /* === STEP 41: PRESENTATION MODE + INVESTOR POLISH === */
    .wb-presentation-recovery {{
        margin: -6px 0 14px 0;
        padding: 10px 12px;
        border: 1px solid {brand['border_subtle']};
        border-radius: 10px;
        background: rgba(91, 141, 239, 0.06);
    }}
    .wb-presentation-recovery .stCaption {{
        text-align: center;
    }}
    .wb-sidebar-affordance {{
        text-align: center;
        font-size: 0.76rem;
        color: {brand['muted']};
        margin: -4px 0 12px 0;
        line-height: 1.4;
    }}
    .wb-presentation-flag {{
        display: none;
    }}
    .wb-sidebar-pulse-marker {{
        display: none;
    }}
    @keyframes wb-sidebar-pulse {{
        0%, 100% {{ box-shadow: inset 3px 0 0 transparent; }}
        50% {{ box-shadow: inset 3px 0 0 rgba(91, 141, 239, 0.85); }}
    }}
    section[data-testid="stSidebar"]:has(.wb-sidebar-pulse-marker) {{
        animation: wb-sidebar-pulse 0.9s ease-in-out 3;
        border-right-color: rgba(91, 141, 239, 0.55) !important;
    }}
    .wb-tier-panel {{
        margin-top: 4px;
    }}
    .wb-tier-panel--utility {{
        opacity: 0.96;
    }}
    .wb-tier-panel--tertiary {{
        opacity: 0.92;
    }}
    [data-testid="stExpander"]:has(.wb-tier-panel--utility) {{
        border-style: dashed;
        opacity: 0.92;
    }}
    [data-testid="stExpander"]:has(.wb-tier-panel--tertiary) {{
        opacity: 0.88;
    }}
    [data-testid="stExpander"]:has(.wb-compare-secondary) {{
        border-color: {brand['border_subtle']};
        background: rgba(14, 19, 25, 0.35);
    }}
    .wb-hero-status {{
        transition: border-color 0.15s ease, background 0.15s ease;
    }}
    .wb-hero-metric {{
        transition: border-color 0.15s ease, background 0.15s ease;
    }}
    .wb-hero-metric:hover {{
        border-color: rgba(91, 141, 239, 0.28);
        background: rgba(255, 255, 255, 0.045);
    }}
    .wb-kpi-shell .wb-metric {{
        transition: border-color 0.15s ease;
    }}
    .wb-kpi-shell .wb-metric:hover {{
        border-color: rgba(91, 141, 239, 0.22);
    }}

    /* Scope presentation polish to main content only — never hide or remove sidebar. */
    [data-testid="stMain"]:has(.wb-presentation-flag) .block-container {{
        max-width: 1320px;
        padding-top: 0.75rem !important;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-config-summary {{
        padding: 8px 12px !important;
        margin-bottom: 10px !important;
        opacity: 0.92;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-config-body {{
        gap: 6px;
        font-size: 0.84rem;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-hero {{
        margin-bottom: 14px;
        padding: 18px 20px 16px 20px;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-kpi-shell {{
        margin-bottom: 10px;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-kpi-grid .wb-metric {{
        min-height: 108px;
        padding: 12px 14px;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-section-block,
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-section-block--tight {{
        margin-bottom: 12px;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-section-head {{
        margin-bottom: 10px;
    }}
    [data-testid="stMain"]:has(.wb-presentation-flag) .wb-header {{
        padding: 16px 20px;
        margin-bottom: 14px;
    }}
    .wb-presentation-sidebar-marker {{
        display: none;
    }}
    section[data-testid="stSidebar"]:has(.wb-presentation-sidebar-marker) {{
        border-right-color: {brand['border_subtle']} !important;
    }}
    section[data-testid="stSidebar"]:has(.wb-presentation-sidebar-marker) label {{
        opacity: 0.94;
    }}
    @media (max-width: 900px) {{
        [data-testid="stMain"]:has(.wb-presentation-flag) .wb-hero-metrics {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}
    @media (max-width: 640px) {{
        [data-testid="stMain"]:has(.wb-presentation-flag) .block-container {{
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }}
    }}
    """
