"""
WasherBot — Калькулятор окупаемости робот-мойки Leisuwash
Часть 1/5: Конфиг, каталог оборудования, упрощённая налоговая модель (ориентир 2026)
"""

from __future__ import annotations
from typing import Tuple
import math

import numpy as np
import streamlit as st

from data.catalogs import (
    REGIONS,
    SEASONALITY,
    WASHER_CATALOG,
)
from data.washer_access import get_washer_model
from domain.params import ProParams, SimpleParams
from domain.results import ProResult, SimpleResult
from finance.credit import calculate_credit_schedule
from finance.capacity import (
    build_capacity_diagnostics,
    cap_demand_by_capacity,
    estimate_daily_capacity,
    estimate_monthly_capacity,
    estimate_peak_hour_utilization,
)
from finance.ecology import build_eco_metrics
from finance.metrics import (
    calculate_irr,
    calculate_npv,
    calculate_payback,
)
from finance.model_constants import NPV_DISCOUNT_RATE_ANNUAL
from finance.model_core import _calculate_pro_core
from finance.tariffs import effective_tariffs, nv_coefficient
from finance.program_mix import compute_program_mix
from finance.seasonality import build_seasonality_factors
from finance.var_cost_per_wash import compute_var_cost_per_wash
from finance.sensitivity import build_pro_sensitivity_cases
from finance.taxation import calculate_monthly_tax_schedule
from finance.taxes import (
    TAX_MODEL_BASELINE_YEAR,
    insurance_contributions_sme,
    patent_cost_month_for_region,
)
from ui.exports import render_pro_export_section, render_simple_monthly_table_block
from ui.inputs import render_sidebar_pro, render_sidebar_simple
from ui.layout_styles import build_layout_css
from ui.streamlit_shell_css import (
    build_normal_streamlit_shell_css,
    build_presentation_streamlit_shell_css,
)
from ui.renderers import (
    BRAND,
    render_footer,
    render_header,
    render_mode_switcher,
)
from ui.theme_switch import init_theme, render_theme_toggle
from ui.light_shell_css import build_light_shell_css
try:
    from ui.theme_palette import is_light, rgba
except Exception:  # pragma: no cover - аварийный режим
    def is_light() -> bool:
        return False

    def rgba(color: str, alpha: float) -> str:
        return color
from ui.presentation_mode import (
    init_presentation_mode,
    render_presentation_flag,
    render_presentation_mode_controls,
)
from ui.results import (
    render_pro_assumptions_snapshot,
    render_pro_break_even_block,
    render_pro_capacity_block,
    render_pro_compare_block,
    render_pro_config_card,
    render_pro_detail_layer,
    render_pro_ecology_block,
    render_pro_executive_verdict,
    render_pro_investment_memo,
    render_pro_kpi_cards,
    render_pro_scenarios_block,
    render_pro_sensitivity_block,
    render_simple_breakdown_block,
    render_simple_cashflow_chart,
    render_simple_config_card,
    render_simple_executive_hero,
    render_simple_hints,
    render_simple_kpi_cards,
    render_simple_revenue_expenses_chart,
)


# ══════════════════════════════════════════════════════════════
# КОНФИГ СТРАНИЦЫ (вызывается ОДИН раз — здесь)
# ══════════════════════════════════════════════════════════════
def setup_page():
    """Конфигурация страницы Streamlit. Вызывается первой в main()."""
    st.set_page_config(
        page_title="WasherBot — Калькулятор робот-мойки Leisuwash",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": "WasherBot — финансовое моделирование автомоек Leisuwash"
        },
    )


# ══════════════════════════════════════════════════════════════
# CSS — тёмная контрастная тема
# ══════════════════════════════════════════════════════════════
def inject_css():
    """Внедряет фирменный CSS."""
    css = f"""
    <style>
    /* === STREAMLIT SHELL === */
    {build_normal_streamlit_shell_css()}
    {build_presentation_streamlit_shell_css()}
    .block-container {{
        padding-top: 1rem !important;
    }}

    /* === ОСНОВА === */
    .stApp {{
        background: linear-gradient(180deg, {BRAND['bg']} 0%, {BRAND['bg2']} 100%);
        color: {BRAND['text']};
    }}
    
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1240px;
    }}

    [data-testid="stAppViewContainer"] > .main .block-container {{
        padding-left: 2rem;
        padding-right: 2rem;
    }}
    
    /* === ТИПОГРАФИКА === */
    h1, h2, h3, h4, h5, h6 {{
        color: {BRAND['text']} !important;
        font-family: 'Inter', system-ui, sans-serif;
        font-weight: 700;
        letter-spacing: -0.01em;
    }}
    
    p, label, span, div {{
        color: {BRAND['text2']};
    }}
    
    /* === САЙДБАР === */
    section[data-testid="stSidebar"] {{
        background: {BRAND['bg2']} !important;
        border-right: 1px solid {BRAND['border']};
    }}
    
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: {BRAND['text2']} !important;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0;
        text-transform: none;
        margin-top: 1.4rem;
        margin-bottom: 0.6rem;
        padding-bottom: 0;
        border-bottom: none;
    }}

    .wb-sidebar-heading {{
        color: {BRAND['text']};
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin: 1.35rem 0 0.55rem 0;
        padding-bottom: 0.45rem;
        border-bottom: 1px solid {BRAND['border']};
    }}
    
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: {BRAND['muted']} !important;
        font-size: 0.78rem !important;
    }}
    
    section[data-testid="stSidebar"] label {{
        color: {BRAND['text']} !important;
        font-weight: 500;
        font-size: 0.9rem;
    }}
    
    /* === INPUT / NUMBER / SELECT === */
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background-color: {BRAND['card']} !important;
        color: {BRAND['text']} !important;
        border: 1px solid {BRAND['border']} !important;
        border-radius: 8px !important;
    }}
    
    .stNumberInput button {{
        background-color: {BRAND['card']} !important;
        color: {BRAND['text']} !important;
        border-color: {BRAND['border']} !important;
    }}
    
    /* === SLIDER === */
    .stSlider [data-baseweb="slider"] > div > div {{
        background: {BRAND['primary']} !important;
    }}
    
    .stSlider [role="slider"] {{
        background-color: {BRAND['primary']} !important;
        border: 2px solid {BRAND['text']} !important;
        box-shadow: none !important;
    }}
    
    /* === КНОПКИ === */
    .stButton > button {{
        background: {BRAND['card']};
        color: {BRAND['text']};
        border: 1px solid {BRAND['border']};
        border-radius: 10px;
        font-weight: 600;
        padding: 0.55rem 1.2rem;
        transition: all 0.18s ease;
    }}
    
    .stButton > button:hover {{
        border-color: {BRAND['primary']};
        background: {rgba(BRAND['primary'], 0.1)};
        transform: translateY(-1px);
    }}

    .stDownloadButton > button {{
        background: {BRAND['card']};
        color: {BRAND['text']};
        border: 1px solid {BRAND['border']};
        border-radius: 8px;
        font-weight: 600;
        padding: 0.45rem 0.85rem;
        min-height: 38px;
        font-size: 0.88rem;
        transition: all 0.18s ease;
    }}

    .stDownloadButton > button:hover {{
        border-color: {BRAND['primary']};
        background: {rgba(BRAND['primary'], 0.1)};
        transform: translateY(-1px);
    }}
    
    .stButton > button[kind="primary"] {{
        background: {BRAND['primary']};
        border: 1px solid {BRAND['primary']};
        color: {BRAND['on_primary']} !important;
        box-shadow: none;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background: {BRAND['accent']};
        box-shadow: none;
        transform: none;
    }}

    .stButton > button[kind="secondary"] {{
        background: transparent;
        border: 1px solid {BRAND['border']};
        color: {BRAND['text2']} !important;
        font-weight: 500;
        padding: 0.45rem 0.9rem;
        box-shadow: none;
    }}

    .stButton > button[kind="secondary"]:hover {{
        border-color: {rgba(BRAND['primary'], 0.45)};
        background: {rgba(BRAND['primary'], 0.06)};
        transform: none;
    }}

    .wb-compare-secondary .stButton > button {{
        padding: 0.42rem 0.75rem;
        font-size: 0.86rem;
        white-space: nowrap;
    }}
    
    /* === ШАПКА === */
    .wb-header {{
        background: {BRAND['bg2']};
        border: 1px solid {BRAND['border']};
        border-radius: 12px;
        padding: 22px 26px;
        margin-bottom: 22px;
        box-shadow: none;
    }}
    
    .wb-header-row {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 24px;
        flex-wrap: wrap;
    }}
    
    .wb-header-left {{ flex: 1; min-width: 280px; }}
    
    .wb-badge {{
        display: inline-block;
        padding: 4px 10px;
        background: {rgba(BRAND['primary'], 0.12)};
        color: {BRAND['primary']};
        border: 1px solid {rgba(BRAND['primary'], 0.28)};
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}
    
    .wb-title {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {BRAND['text']};
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }}
    
    .wb-subtitle {{
        color: {BRAND['text2']};
        font-size: 0.96rem;
        margin: 0;
    }}
    
    .wb-header-right {{
        text-align: right;
        font-size: 0.88rem;
        line-height: 1.7;
        color: {BRAND['text2']};
    }}
    
    .wb-header-right a {{
        color: {BRAND['text2']};
        text-decoration: none;
        font-weight: 500;
    }}
    
    .wb-header-right a:hover {{ text-decoration: underline; }}
    
    /* === КАРТОЧКИ === */
    .wb-card {{
        background: {BRAND['surface']};
        border: 1px solid {BRAND.get('border_default', BRAND['border'])};
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: none;
    }}
    
    .wb-card-title {{
        font-size: 1rem;
        font-weight: 700;
        color: {BRAND['text']};
        margin: 0 0 12px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    .wb-card-title::before {{
        display: none;
    }}
    
    /* === МЕТРИКИ === */
    .wb-metric {{
        background: {BRAND['surface']};
        border: 1px solid {BRAND.get('border_subtle', 'rgba(138, 152, 168, 0.16)')};
        border-left: 2px solid {BRAND.get('border_subtle', 'rgba(138, 152, 168, 0.16)')};
        border-radius: 10px;
        padding: 14px 16px;
        height: 100%;
        transition: border-color 0.15s ease;
    }}
    
    .wb-metric:hover {{
        border-color: {BRAND['border']};
        transform: none;
        box-shadow: none;
    }}

    .wb-metric--primary {{
        border-left-color: {rgba(BRAND['primary'], 0.55)};
        background: linear-gradient(180deg, {rgba(BRAND['primary'], 0.05)} 0%, {BRAND['surface']} 100%);
    }}

    .wb-metric--primary .wb-metric-value {{
        font-size: 1.85rem;
        font-weight: 700;
    }}

    .wb-metric--secondary .wb-metric-value {{
        font-size: 1.35rem;
        font-weight: 600;
        color: {BRAND['text']};
    }}

    .wb-metric--secondary .wb-metric-label {{
        font-size: 0.74rem;
    }}
    
    .wb-metric-label {{
        font-size: 0.76rem;
        color: {BRAND['muted']};
        text-transform: none;
        letter-spacing: 0.02em;
        font-weight: 500;
        margin-bottom: 6px;
    }}
    
    .wb-metric-value {{
        font-size: 1.45rem;
        font-weight: 700;
        color: {BRAND['text']};
        line-height: 1.1;
        letter-spacing: -0.02em;
    }}
    
    .wb-metric-hint {{
        font-size: 0.78rem;
        color: {BRAND['text2']};
        margin-top: 6px;
    }}
    
    .wb-metric.good {{ border-left-color: {BRAND['green']}; }}
    .wb-metric.good .wb-metric-value {{ color: {BRAND['green']}; }}
    
    .wb-metric.warn {{ border-left-color: {BRAND['yellow']}; }}
    .wb-metric.warn .wb-metric-value {{ color: {BRAND['text']}; }}
    
    .wb-metric.bad {{ border-left-color: {BRAND['red']}; }}
    .wb-metric.bad .wb-metric-value {{ color: {BRAND['text']}; }}

    .wb-metric.off {{
        border-left-color: {BRAND['muted']};
        opacity: 0.85;
    }}
    .wb-metric.off .wb-metric-value {{ color: {BRAND['text2']}; }}
    
    /* === ИНФО / ПРЕДУПРЕЖДЕНИЕ / УСПЕХ === */
    .wb-info {{
        background: {rgba(BRAND['primary'], 0.08)};
        border: 1px solid {rgba(BRAND['primary'], 0.3)};
        border-radius: 10px;
        padding: 12px 16px;
        color: {BRAND['text']};
        font-size: 0.9rem;
        margin: 10px 0;
    }}
    
    .wb-warn {{
        background: {rgba(BRAND['yellow'], 0.08)};
        border: 1px solid {rgba(BRAND['yellow'], 0.3)};
        border-radius: 10px;
        padding: 12px 16px;
        color: {BRAND['text']};
        font-size: 0.9rem;
        margin: 10px 0;
    }}
    
    .wb-success {{
        background: rgba(16,185,129,0.08);
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        color: {BRAND['text']};
        font-size: 0.9rem;
        margin: 10px 0;
    }}

    .wb-danger {{
        background: rgba(239,68,68,0.10);
        border: 1px solid rgba(239,68,68,0.35);
        border-radius: 10px;
        padding: 12px 16px;
        color: {BRAND['text']};
        font-size: 0.9rem;
        margin: 10px 0;
    }}
    
    /* === ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМОВ (premium segmented) === */
    .wb-mode-tabs {{
        margin: 0 0 8px 0;
        padding: 4px;
        border-radius: 12px;
        border: 1px solid {BRAND['border']};
        background: {rgba(BRAND['bg2'], 0.72)};
        box-shadow: inset 0 1px 0 {rgba(BRAND['text'], 0.03)};
    }}
    .wb-mode-tabs [data-testid="column"] {{
        padding: 0 2px !important;
    }}
    .wb-mode-tabs .stButton > button {{
        border-radius: 8px;
        border: 1px solid transparent;
        padding: 0.55rem 0.75rem;
        font-weight: 600;
        font-size: 0.9rem;
        background: transparent;
        box-shadow: none;
        width: 100%;
    }}
    .wb-mode-tabs .stButton > button[kind="primary"] {{
        background: linear-gradient(
            180deg,
            {rgba(BRAND['primary'], 0.22)} 0%,
            {rgba(BRAND['primary'], 0.1)} 100%
        );
        border-color: {rgba(BRAND['primary'], 0.45)};
        color: {BRAND['text']} !important;
        box-shadow: 0 0 0 1px {rgba(BRAND['primary'], 0.1)};
    }}
    .wb-mode-tabs .stButton > button[kind="secondary"] {{
        background: transparent;
        color: {BRAND['muted']} !important;
        border-color: transparent;
    }}
    .wb-mode-tabs .stButton > button[kind="secondary"]:hover {{
        color: {BRAND['text2']} !important;
        background: {rgba(BRAND['primary'], 0.08)};
        border-color: {rgba(BRAND['primary'], 0.18)};
    }}
    .wb-mode-tabs .stButton > button:hover {{
        transform: none;
    }}

    .wb-mode-info {{
        font-size: 0.76rem;
        color: {BRAND['muted']};
        text-align: center;
        margin: 0 0 14px 0;
        padding: 5px 10px;
        border: 1px solid {BRAND['border']};
        border-radius: 8px;
        background: {rgba(BRAND['bg2'], 0.35)};
    }}

    .wb-compare-secondary {{
        opacity: 0.96;
    }}
    .wb-compare-secondary .wb-section-subtitle {{
        margin-top: 0 !important;
    }}
    [data-testid="stExpander"] details {{
        border: 1px solid {BRAND['border']};
        border-radius: 10px;
        background: {rgba(BRAND['bg2'], 0.25)};
    }}
    [data-testid="stExpander"] summary {{
        font-weight: 600;
        color: {BRAND['text2']};
        font-size: 0.92rem;
    }}

    .wb-config-body {{
        display: flex;
        flex-direction: column;
        gap: 10px;
        color: {BRAND['text2']};
        font-size: 0.92rem;
        line-height: 1.55;
    }}

    .wb-config-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px 18px;
    }}

    .wb-config-segment {{
        display: inline-flex;
        align-items: baseline;
        gap: 6px;
        flex-wrap: wrap;
    }}

    .wb-config-kicker {{
        color: {BRAND['muted']};
        font-size: 0.74rem;
        font-weight: 500;
        letter-spacing: 0.02em;
    }}

    /* === DECISION LAYER === */
    .wb-verdict {{
        margin-bottom: 20px;
        border-left: 3px solid {BRAND['border']};
    }}
    .wb-verdict--good {{ border-left-color: {BRAND['green']}; }}
    .wb-verdict--warn {{ border-left-color: {BRAND['yellow']}; }}
    .wb-verdict--bad {{ border-left-color: {BRAND['red']}; }}
    .wb-verdict--info {{ border-left-color: {BRAND['primary']}; }}

    .wb-verdict-headline {{
        font-size: 1.12rem;
        font-weight: 600;
        color: {BRAND['text']};
        line-height: 1.45;
        margin-bottom: 12px;
    }}

    .wb-verdict-bullets {{
        margin: 0;
        padding-left: 1.1rem;
        color: {BRAND['text2']};
        font-size: 0.88rem;
        line-height: 1.65;
    }}
    .wb-verdict-bullet {{ margin-bottom: 4px; }}

    .wb-scenario-cards-row {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 12px 0 18px 0;
    }}
    @media (max-width: 900px) {{
        .wb-scenario-cards-row {{ grid-template-columns: 1fr; }}
    }}

    .wb-scenario-card {{
        background: {BRAND['card']};
        border: 1px solid {BRAND['border']};
        border-radius: 10px;
        padding: 14px 16px;
    }}
    .wb-scenario-card--base {{
        border-color: {rgba(BRAND['primary'], 0.45)};
        background: linear-gradient(180deg, {rgba(BRAND['primary'], 0.06)} 0%, {BRAND['card']} 100%);
    }}
    .wb-scenario-card-label {{
        font-size: 0.82rem;
        font-weight: 600;
        color: {BRAND['text']};
        margin-bottom: 10px;
        letter-spacing: 0.02em;
    }}
    .wb-scenario-card-metric {{
        display: flex;
        flex-direction: column;
        gap: 2px;
        margin-bottom: 8px;
    }}
    .wb-scenario-card-kicker {{
        font-size: 0.72rem;
        color: {BRAND['muted']};
    }}
    .wb-scenario-card-value {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {BRAND['text']};
    }}
    .wb-scenario-card-factor {{
        font-size: 0.76rem;
        color: {BRAND['text2']};
        margin-top: 4px;
    }}

    .wb-section-subtitle {{
        color: {BRAND['muted']};
        font-size: 0.86rem;
        margin: -6px 0 14px 0;
        line-height: 1.5;
    }}
    .wb-section-takeaway {{
        color: {BRAND['text2']};
        font-size: 0.88rem;
        margin: 0 0 12px 0;
        line-height: 1.55;
        padding-left: 10px;
        border-left: 2px solid {BRAND['border']};
    }}
    .wb-section-caption {{
        color: {BRAND['muted']};
        font-size: 0.78rem;
        margin: 8px 0 0 0;
        line-height: 1.5;
    }}
    .wb-detail-subheading {{
        color: {BRAND['text']};
        font-size: 0.95rem;
        font-weight: 600;
        margin: 18px 0 10px 0;
    }}

    /* === ASSUMPTIONS / MEMO LAYER === */
    .wb-assumption-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px 20px;
        margin-bottom: 14px;
    }}
    @media (max-width: 800px) {{
        .wb-assumption-grid {{ grid-template-columns: 1fr; }}
    }}
    .wb-assumption-row {{
        display: flex;
        flex-direction: column;
        gap: 2px;
        padding: 10px 12px;
        background: {BRAND['card']};
        border: 1px solid {BRAND['border']};
        border-radius: 8px;
    }}
    .wb-assumption-row--risk {{
        border-left: 2px solid {BRAND['yellow']};
    }}
    .wb-assumption-label {{
        font-size: 0.72rem;
        color: {BRAND['muted']};
        font-weight: 500;
    }}
    .wb-assumption-value {{
        font-size: 0.92rem;
        color: {BRAND['text']};
        font-weight: 600;
    }}
    .wb-assumption-note {{
        font-size: 0.74rem;
        color: {BRAND['text2']};
        line-height: 1.4;
    }}
    .wb-assumption-risks {{
        margin: 0;
        padding-left: 1.1rem;
        color: {BRAND['text2']};
        font-size: 0.82rem;
        line-height: 1.55;
    }}
    .wb-assumption-risk-item {{ margin-bottom: 4px; }}

    .wb-memo {{
        border-left: 3px solid {BRAND['border']};
    }}
    .wb-memo--good {{ border-left-color: {BRAND['green']}; }}
    .wb-memo--warn {{ border-left-color: {BRAND['yellow']}; }}
    .wb-memo--bad {{ border-left-color: {BRAND['red']}; }}
    .wb-memo--info {{ border-left-color: {BRAND['primary']}; }}
    .wb-memo-headline {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {BRAND['text']};
        margin-bottom: 16px;
        line-height: 1.45;
    }}
    .wb-memo-groups {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 16px;
    }}
    @media (max-width: 900px) {{
        .wb-memo-groups {{ grid-template-columns: 1fr; }}
    }}
    .wb-memo-group-title {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {BRAND['muted']};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }}
    .wb-memo-group {{
        background: {BRAND['card']};
        border: 1px solid {BRAND['border']};
        border-radius: 10px;
        padding: 12px 14px;
    }}
    .wb-memo-item {{
        font-size: 0.86rem;
        line-height: 1.5;
        margin-bottom: 6px;
        padding: 8px 10px;
        border-radius: 6px;
    }}
    .wb-memo-item:last-child {{ margin-bottom: 0; }}
    .wb-memo-actions-block {{
        border-top: 1px solid {BRAND['border']};
        padding-top: 14px;
    }}
    .wb-memo-actions {{
        margin: 6px 0 0 0;
        padding-left: 1.1rem;
        color: {BRAND['text2']};
        font-size: 0.86rem;
        line-height: 1.6;
    }}
    .wb-memo-action {{ margin-bottom: 4px; }}

    .wb-export-shell {{
        background: {BRAND['card']};
        border: 1px solid {BRAND['border']};
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }}
    .wb-export-note {{
        color: {BRAND['text2']};
        font-size: 0.86rem;
        margin: 0 0 6px 0;
        line-height: 1.5;
    }}

    .wb-compare-empty {{
        background: {BRAND['card']};
        border: 1px dashed {BRAND['border']};
        border-radius: 10px;
        padding: 16px 18px;
        color: {BRAND['text2']};
        font-size: 0.9rem;
        margin: 12px 0;
    }}
    .wb-compare-variant-name {{
        color: {BRAND['text']};
        font-size: 0.9rem;
        font-weight: 500;
    }}
    .wb-compare-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0 16px 0;
        font-size: 0.84rem;
    }}
    .wb-compare-table th,
    .wb-compare-table td {{
        border: 1px solid {BRAND['border']};
        padding: 8px 10px;
        text-align: left;
        vertical-align: top;
    }}
    .wb-compare-table th {{
        color: {BRAND['muted']};
        font-weight: 600;
        background: {BRAND['card']};
    }}
    .wb-compare-metric {{
        color: {BRAND['text2']};
        font-weight: 500;
    }}
    .wb-compare-delta {{
        color: {BRAND['muted']};
        font-size: 0.76rem;
    }}
    .wb-memo-neutral {{
        background: transparent;
        border: none;
        color: {BRAND['text2']};
        padding: 4px 0;
    }}

    /* === DETAIL TABS — base overrides (premium rail in layout_styles) === */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    
    /* === ТАБЛИЦЫ === */
    .stDataFrame, .stTable {{
        background: {BRAND['bg2']} !important;
        border-radius: 10px;
    }}
    
    /* === EXPANDER === */
    .stExpander {{
        background: {BRAND['bg2']};
        border: 1px solid {BRAND['border']};
        border-radius: 10px;
    }}
    
    .stExpander summary {{
        color: {BRAND['text']} !important;
        font-weight: 600;
    }}
    
    /* === ФУТЕР — base shell (premium layout in layout_styles) === */
    
    /* === МОБИЛЬНАЯ АДАПТАЦИЯ === */
    {build_layout_css(BRAND)}
    @media (max-width: 768px) {{
        .wb-title {{ font-size: 1.5rem; }}
        .wb-metric-value {{ font-size: 1.35rem; }}
        .wb-kpi-grid .wb-metric-value,
        .wb-kpi-grid .wb-metric--primary .wb-metric-value {{
            font-size: 1.28rem;
        }}
        .wb-header {{ padding: 18px; }}
        .wb-header-right {{ text-align: left; margin-top: 12px; }}
        .block-container {{ padding-left: 0.8rem !important; padding-right: 0.8rem !important; }}
    }}
    

    /* === МОБИЛЬНЫЕ ПРАВКИ (кнопка сайдбара не перекрывает контент) === */
    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 3.6rem !important;
        }}
        .wb-hero-headline {{
            font-size: 1.45rem !important;
            line-height: 1.28 !important;
        }}
        .wb-hero-title,
        .wb-title {{
            font-size: 1.6rem !important;
        }}
    }}
    /* чекбоксы/тумблеры: подпись не переносится на две строки */
    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] label p,
    [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] {{
        white-space: nowrap !important;
    }}
    /* === ТАБЛИЦЫ (HTML) === */
    .wb-table-wrap {{
        border: 1px solid {BRAND['border_subtle']};
        border-radius: 10px;
        overflow: auto;
        max-height: 460px;
        background: {BRAND['surface']};
    }}
    table.wb-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
        font-variant-numeric: tabular-nums;
    }}
    table.wb-table th {{
        position: sticky;
        top: 0;
        z-index: 2;
        background: {BRAND['surface2']};
        color: {BRAND['text']};
        text-align: right;
        padding: 8px 10px;
        border-bottom: 1px solid {BRAND['border']};
        white-space: nowrap;
    }}
    table.wb-table th:first-child,
    table.wb-table td:first-child {{ text-align: left; }}
    table.wb-table td {{
        padding: 7px 10px;
        text-align: right;
        color: {BRAND['text2']};
        border-bottom: 1px solid {BRAND['border_subtle']};
        white-space: nowrap;
    }}
    table.wb-table tbody tr:nth-child(even) td {{
        background: {rgba(BRAND['surface2'], 0.45)};
    }}
    table.wb-table tbody tr:hover td {{
        background: {rgba(BRAND['primary'], 0.08)};
    }}

    /* Streamlit разрывает HTML-обёртки вокруг виджетов: пустые div дают артефакты */
    .wb-chart-shell {{
        display: none !important;
    }}
    .wb-mode-tabs {{
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        min-height: 0 !important;
    }}
    /* === ТУЛТИПЫ (базовая тёмная тема) === */
    [data-testid="stTooltipContent"],
    [data-baseweb="tooltip"] {{
        background: {BRAND['surface2']} !important;
        border: 1px solid {BRAND['border']} !important;
        border-radius: 10px !important;
        max-width: 340px !important;
        padding: 8px 12px !important;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4) !important;
    }}
    [data-testid="stTooltipContent"] * {{
        color: {BRAND['text']} !important;
        background: transparent !important;
    }}
    /* === КОНТРАСТ КНОПОК (WCAG AA) === */
    .stButton > button[kind="primary"],
    [data-testid="stBaseButton-primary"] {{
        background: #1E6FE0 !important;
        border-color: #1E6FE0 !important;
        color: #FFFFFF !important;
    }}
    .stButton > button[kind="primary"] *,
    [data-testid="stBaseButton-primary"] * {{
        color: #FFFFFF !important;
    }}
    /* второй переключатель — только на мобильных, сверху сайдбара */
    .st-key-wb_theme_switch_sidebar {{
        display: none;
    }}
    @media (max-width: 900px) {{
        .st-key-wb_theme_switch_sidebar {{
            display: block;
            margin: 0 0 10px 0;
        }}
    }}
    /* === ПЕРЕКЛЮЧАТЕЛЬ ТЕМЫ (в потоке, справа под шапкой) === */
    .st-key-wb_theme_switch {{
        width: 100%;
        margin: 0 0 10px 0;
    }}
    .st-key-wb_theme_switch button {{
        border-radius: 999px !important;
        border: 1px solid {BRAND['border']} !important;
        background: {BRAND['card']} !important;
        color: {BRAND['text']} !important;
        font-size: 0.82rem !important;
        padding: 6px 12px !important;
    }}
    .wb-header {{
        padding-right: 24px;
    }}
    @media (max-width: 900px) {{
        .wb-header {{
            padding-right: 16px !important;
        }}
    }}
</style>
    """
    if is_light():
        css += build_light_shell_css(BRAND)
    st.markdown(css, unsafe_allow_html=True)


def calculate_simple(params: SimpleParams) -> SimpleResult:
    """Основной расчёт для простого режима."""
    
    model = get_washer_model(params.model_code, WASHER_CATALOG)
    region = REGIONS[params.region_key]
    H = params.horizon_months
    
    mix = compute_program_mix(params.programs)
    daily_capacity_per_robot = estimate_daily_capacity(
        cars_per_hour_reference=model.cars_per_hour,
        cycle_time_reference_min=model.cycle_time_min,
        weighted_duration_min=mix.weighted_duration_min,
    )
    monthly_capacity_total = estimate_monthly_capacity(
        daily_capacity_per_robot=daily_capacity_per_robot,
        work_days_month=params.work_days_month,
        n_robots=params.n_robots,
    )

    tariffs = effective_tariffs(
        region,
        water_supply_override=getattr(params, "water_supply_override", None),
        water_sewage_override=getattr(params, "water_sewage_override", None),
        elec_price_override=getattr(params, "elec_price_override", None),
    )
    water_cost_per_m3 = tariffs.water_supply + tariffs.water_sewage

    var_cost = compute_var_cost_per_wash(
        model=model,
        mix=mix,
        water_cost_per_m3=water_cost_per_m3,
        elec_price=tariffs.elec_price,
        extra_dryers_enabled=params.extra_dryers_enabled,
    )
    cost_water_per_wash = var_cost.water
    cost_elec_per_wash = var_cost.electricity
    cost_chem_per_wash = var_cost.chemistry
    var_cost_per_wash = var_cost.total
    avg_check = mix.avg_check
    
    # ── Авто/мес с сезонностью (на ОДИН робот) ──
    months = np.arange(1, H + 1)
    monthly_seasonality = build_seasonality_factors(SEASONALITY, 1.0)
    demand_per_month_one = np.zeros(H)
    for i in range(H):
        month_idx = i % 12  # 0..11
        seas = monthly_seasonality[month_idx]
        demand_per_month_one[i] = params.cars_per_day_avg * params.work_days_month * seas
    
    # На все роботы + ограничение техпропускной способностью
    demand_per_month = demand_per_month_one * params.n_robots
    cars_per_month = cap_demand_by_capacity(demand_per_month, monthly_capacity_total)
    capacity_diagnostics = build_capacity_diagnostics(
        demand_per_month,
        monthly_capacity_total,
    )
    
    # ── Выручка ──
    revenue_month = cars_per_month * avg_check
    
    # ── Переменные расходы ──
    var_costs_month = cars_per_month * var_cost_per_wash
    
    # ── ЗП администратора (1 человек на ВСЮ площадку, не множится на роботов) ──
    salary_gross = params.admin_salary_gross
    insurance = insurance_contributions_sme(salary_gross)
    salary_total = salary_gross + insurance  # компания платит gross + страховые
    salary_total_month = np.full(H, salary_total)
    
    # ── Постоянные (аренда, прочее — на ПЛОЩАДКУ, не множится) ──
    nv_per_m3_simple = tariffs.water_sewage * nv_coefficient(
        norm_enabled=bool(getattr(params, "nv_norm_enabled", False)),
        over_enabled=bool(getattr(params, "nv_over_enabled", False)),
    )
    water_m3_per_wash_simple = model.water_per_wash_l / 1000.0 * mix.avg_water_factor
    nv_month_simple = nv_per_m3_simple * cars_per_month * water_m3_per_wash_simple
    fix_costs_month = (
        np.full(H, params.rent_month + params.other_fixed)
        + float(getattr(params, 'property_tax_month', 0.0))
        + float(getattr(params, 'land_tax_month', 0.0))
        + float(getattr(params, 'ip_contributions_month', 0.0))
        + nv_month_simple
    )
    
    # ── Амортизация (линейная, на всю сумму инвестиций) ──
    amort_years = max(1, int(getattr(params, "amort_years_equipment", 5)))
    amort_pm = params.total_investment / (amort_years * 12) if params.total_investment > 0 else 0.0
    amortization_month = np.zeros(H)
    amortization_month[: min(H, amort_years * 12)] = amort_pm

    # ── EBT (до налога) ──
    ebt_month = (
        revenue_month - var_costs_month - fix_costs_month - salary_total_month - amortization_month
    )
    
    # База входящего НДС (для ОСНО): вода, электричество, химия, коммуналка, аренда
    vat_base_simple = (
        cars_per_month
        * (cost_water_per_wash + cost_elec_per_wash + cost_chem_per_wash)
        + np.full(H, params.rent_month + params.other_fixed)
    )

    # ── Налоги (упрощённая policy, ориентир TAX_MODEL_BASELINE_YEAR) ──
    tax_month = calculate_monthly_tax_schedule(
        revenue_month=revenue_month,
        taxable_profit_month=ebt_month,
        tax_regime=params.tax_regime,
        start_year=TAX_MODEL_BASELINE_YEAR,
        insurance_month=insurance,
        patent_cost_month=patent_cost_month_for_region(
            params.region_key,
            headcount=1 + (1 if params.admin_salary_gross > 0 else 0),
        ),
        vat_input_base_month=vat_base_simple,
    )
    
    # ── Чистая прибыль ──
    profit_month = ebt_month - tax_month
    
    # ── Cashflow ──
    cashflow = np.zeros(H + 1)
    cashflow[0] = -params.total_investment
    cashflow[1:] = profit_month + amortization_month
    cumulative = np.cumsum(cashflow)
    
    # ── KPI ──
    avg_revenue_month = float(np.mean(revenue_month))
    avg_profit_month = float(np.mean(profit_month))
    total_revenue = float(np.sum(revenue_month))
    total_profit = float(np.sum(profit_month))
    payback_months = calculate_payback(cumulative)
    # Остаточная стоимость бизнеса на горизонте (опция): × EBITDA последнего года
    terminal_value = 0.0
    if bool(getattr(params, "include_terminal_value", False)) and H >= 12:
        last_year_ebitda = float(np.sum(ebitda_month[-12:]))
        terminal_value = max(0.0, float(getattr(params, "terminal_multiple", 3.0)) * last_year_ebitda)
        if terminal_value > 0:
            monthly_rate = (1.0 + NPV_DISCOUNT_RATE_ANNUAL) ** (1.0 / 12.0) - 1.0
            cashflow_with_terminal = cashflow.copy()
            cashflow_with_terminal[-1] += terminal_value
        else:
            cashflow_with_terminal = cashflow.copy()
    else:
        cashflow_with_terminal = cashflow.copy()

    npv = calculate_npv(cashflow_with_terminal, discount_rate_annual=NPV_DISCOUNT_RATE_ANNUAL)
    irr = calculate_irr(cashflow_with_terminal)
    margin = (avg_profit_month / avg_revenue_month) if avg_revenue_month > 0 else 0
    
    # ── Структура расходов 1-го года ──
    n1 = min(12, H)
    breakdown_year1 = {
        "Вода": float(np.sum(cars_per_month[:n1] * cost_water_per_wash)),
        "Электричество": float(np.sum(cars_per_month[:n1] * cost_elec_per_wash)),
        "Химия": float(np.sum(cars_per_month[:n1] * cost_chem_per_wash)),
        "ЗП и взносы": float(np.sum(salary_total_month[:n1])),
        "Аренда": float(params.rent_month * n1),
        "Прочее (охрана, реклама)": float(params.other_fixed * n1),
        "Амортизация": float(np.sum(amortization_month[:n1])),
        "НВ на ЦСВ": float(np.sum(nv_month_simple[:n1])),
        "Налоги": float(np.sum(tax_month[:n1])),
    }
    
    return SimpleResult(
        months=months,
        cars_per_month=cars_per_month,
        revenue_month=revenue_month,
        var_costs_month=var_costs_month,
        fix_costs_month=fix_costs_month,
        salary_total_month=salary_total_month,
        tax_month=tax_month,
        profit_month=profit_month,
        cashflow=cashflow,
        cumulative=cumulative,
        avg_check=avg_check,
        avg_revenue_month=avg_revenue_month,
        avg_profit_month=avg_profit_month,
        total_revenue=total_revenue,
        total_profit=total_profit,
        payback_months=payback_months,
        npv=npv,
        irr=irr,
        margin=margin,
        breakdown_year1=breakdown_year1,
        params=params,
        capacity_binding_months=capacity_diagnostics.capacity_binding_months,
        annual_unserved_demand=capacity_diagnostics.annual_unserved_demand,
        annual_unserved_share=capacity_diagnostics.annual_unserved_share,
        peak_requested_utilization=capacity_diagnostics.peak_requested_utilization,
        peak_hour_utilization=estimate_peak_hour_utilization(
            capacity_diagnostics.peak_requested_utilization
        ),
        peak_unserved_month=capacity_diagnostics.peak_unserved_month,
        zero_capacity_positive_demand_months=capacity_diagnostics.zero_capacity_positive_demand_months,
    )


# ══════════════════════════════════════════════════════════════
# UI — SIMPLE
# ══════════════════════════════════════════════════════════════
def render_simple_ui(res: SimpleResult):
    """Рендер результатов простого режима."""
    render_simple_config_card(res)
    render_simple_executive_hero(res)
    render_simple_kpi_cards(res)
    render_simple_cashflow_chart(res)
    render_simple_revenue_expenses_chart(res)
    render_simple_breakdown_block(res)
    render_simple_monthly_table_block(res)
    render_simple_hints(res)


# ══════════════════════════════════════════════════════════════
# ENTRY-POINT для simple режима
# ══════════════════════════════════════════════════════════════
def run_simple_mode():
    """Запуск простого режима: сайдбар + расчёт + UI."""
    params = render_sidebar_simple()
    result = calculate_simple(params)
    render_simple_ui(result)



def calculate_pro(params: ProParams) -> ProResult:
    """Полный расчёт PRO-режима."""
    
    H = params.horizon_months
    months = np.arange(1, H + 1)
    
    # ── База ──
    core = _calculate_pro_core(params, traffic_factor=1.0)
    cars_per_month = core["cars_per_month"]
    revenue_month = core["revenue_month"]
    var_costs_month = core["var_costs_month"]
    avg_check = core["avg_check"]
    capacity_diagnostics = core["capacity_diagnostics"]
    
    # ── CAPEX ──
    capex_total = (
        params.capex_equipment + params.capex_construction + params.capex_engineering
        + params.capex_premises + params.capex_launch + params.capex_other
    )

    # ── Кредит ──
    credit_active = bool(params.use_credit and params.credit_amount > 0 and params.credit_term_months > 0)
    # Кредит не может превышать CAPEX: иначе собственные вложения = 0 и модель показывает
    # «окупаемость 0 месяцев» при заёмных деньгах больше проекта.
    credit_used = min(max(0.0, params.credit_amount), capex_total) if credit_active else 0.0
    own_funds = max(0.0, capex_total - credit_used)

    capex_breakdown = {
        "Оборудование": params.capex_equipment,
        "СМР, фундамент": params.capex_construction,
        "Инженерные сети": params.capex_engineering,
        "Помещение": params.capex_premises,
        "Запуск, ПНР": params.capex_launch,
        "Прочее, резерв": params.capex_other,
    }
    
    # ── Кредит ──
    if credit_active and credit_used > 0:
        sched = calculate_credit_schedule(
            amount=credit_used,
            annual_rate=params.credit_rate_annual,
            term_months=params.credit_term_months,
            grace_months=params.credit_grace_months,
        )
        # Развёртываем на горизонт H
        credit_interest_month = np.zeros(H)
        credit_principal_month = np.zeros(H)
        n_use = min(H, params.credit_term_months)
        credit_interest_month[:n_use] = sched["interest"][:n_use]
        credit_principal_month[:n_use] = sched["principal"][:n_use]
    else:
        credit_interest_month = np.zeros(H)
        credit_principal_month = np.zeros(H)
    
    # ── Амортизация (линейная, на оборудование) ──
    # Учитывается только в режимах, где она снижает базу
    amort_per_month = (
        params.capex_equipment / (params.amort_years_equipment * 12)
        if params.amort_years_equipment > 0 else 0
    )
    amort_period = params.amort_years_equipment * 12
    amortization_month = np.zeros(H)
    amortization_month[:min(H, amort_period)] = amort_per_month
    
    # ── ЗП ──
    salary_admin_gross = params.admin_salary_gross * params.n_admins
    salary_manager_gross = params.manager_salary_gross * params.n_managers
    salary_gross_total = salary_admin_gross + salary_manager_gross
    
    # Страховые: считаем по каждому сотруднику отдельно (МРОТ для каждого)
    insurance_admin = (
        insurance_contributions_sme(params.admin_salary_gross) * params.n_admins
    )
    insurance_manager = (
        insurance_contributions_sme(params.manager_salary_gross) * params.n_managers
    )
    salary_total = salary_gross_total + insurance_admin + insurance_manager
    salary_total_month = np.full(H, salary_total)
    
    # ── OPEX ──
    opex_per_month = (
        params.rent_month + params.utilities_extra + params.security_month
        + params.marketing_month + params.maintenance_month
        + params.insurance_month + params.other_opex
        + float(getattr(params, "property_tax_month", 0.0))
        + float(getattr(params, "land_tax_month", 0.0))
        + float(getattr(params, "ip_contributions_month", 0.0))
    )
    # ── Плата за НВ на ЦСВ и сверхнормативный сброс (п. 123(4) / п. 203 Правил № 644) ──
    # Считается от фактического объёма стоков: авто × м³ на мойку × коэффициент.
    nv_per_m3 = float(core.get("sewage_tariff", 0.0)) * float(core.get("nv_coefficient", 0.0))
    nv_month = nv_per_m3 * cars_per_month * float(core.get("water_m3_per_wash", 0.0))
    opex_month = np.full(H, opex_per_month) + nv_month
    
    # ── EBITDA ──
    ebitda_month = revenue_month - var_costs_month - opex_month - salary_total_month
    
    # ── EBT (до налога): − %кредита − амортизация ──
    ebt_month = ebitda_month - credit_interest_month - amortization_month
    
    # База входящего НДС (для ОСНО)
    vat_base_month = (
        cars_per_month
        * (core["cost_water_per_wash"] + core["cost_elec_per_wash"] + core["cost_chem_per_wash"])
        + np.full(H, params.utilities_extra + params.rent_month)
    )

    # ── Налоги (упрощённая policy, ориентир TAX_MODEL_BASELINE_YEAR) ──
    tax_month = calculate_monthly_tax_schedule(
        revenue_month=revenue_month,
        taxable_profit_month=ebt_month,
        tax_regime=params.tax_regime,
        start_year=TAX_MODEL_BASELINE_YEAR,
        insurance_month=insurance_admin + insurance_manager,
        patent_cost_month=patent_cost_month_for_region(
                params.region_key,
                headcount=1 + getattr(params, "n_admins", 0) + getattr(params, "n_managers", 0),
            ),
    )
    
    # ── Чистая прибыль (после налога) ──
    profit_month = ebt_month - tax_month
    
    # ── Cashflow: учитывает движение денег, а не P&L ──
    # Из прибыли возвращаем амортизацию (она не денежный отток),
    # вычитаем погашение тела кредита (денежный отток)
    cashflow_op = profit_month + amortization_month - credit_principal_month
    
    cashflow = np.zeros(H + 1)
    cashflow[0] = -own_funds   # из своего кармана
    cashflow[1:] = cashflow_op
    cumulative = np.cumsum(cashflow)
    
    # ── KPI ──
    avg_revenue_month = float(np.mean(revenue_month))
    avg_profit_month = float(np.mean(profit_month))
    avg_ebitda_month = float(np.mean(ebitda_month))
    total_revenue = float(np.sum(revenue_month))
    total_profit = float(np.sum(profit_month))
    payback_months = calculate_payback(cumulative)
    if own_funds <= 0:
        # Собственных вложений нет — окупаемость «нулевого чека» не имеет смысла.
        payback_months = float("nan")
    # Остаточная стоимость бизнеса на горизонте (опция): × EBITDA последнего года
    terminal_value = 0.0
    if bool(getattr(params, "include_terminal_value", False)) and H >= 12:
        last_year_ebitda = float(np.sum(ebitda_month[-12:]))
        terminal_value = max(0.0, float(getattr(params, "terminal_multiple", 3.0)) * last_year_ebitda)
    cf_for_npv = cashflow.copy()
    if terminal_value > 0:
        cf_for_npv[-1] += terminal_value
    npv = calculate_npv(cf_for_npv, discount_rate_annual=NPV_DISCOUNT_RATE_ANNUAL)
    irr = calculate_irr(cf_for_npv)
    margin_net = (avg_profit_month / avg_revenue_month) if avg_revenue_month > 0 else 0
    margin_ebitda = (avg_ebitda_month / avg_revenue_month) if avg_revenue_month > 0 else 0
    
    # ── Сценарии ──
    def _scenario_cumulative(factor: float) -> Tuple[np.ndarray, float]:
        c = _calculate_pro_core(params, traffic_factor=factor)
        rev = c["revenue_month"]
        var = c["var_costs_month"]
        ebitda = rev - var - opex_month - salary_total_month
        ebt = ebitda - credit_interest_month - amortization_month
        vat_base_c = (
            c["cars_per_month"]
            * (c["cost_water_per_wash"] + c["cost_elec_per_wash"] + c["cost_chem_per_wash"])
            + np.full(H, params.utilities_extra + params.rent_month)
        )
        tax = calculate_monthly_tax_schedule(
            revenue_month=rev,
            taxable_profit_month=ebt,
            tax_regime=params.tax_regime,
            start_year=TAX_MODEL_BASELINE_YEAR,
            insurance_month=insurance_admin + insurance_manager,
            patent_cost_month=patent_cost_month_for_region(
                params.region_key,
                headcount=1 + getattr(params, "n_admins", 0) + getattr(params, "n_managers", 0),
            ),
            vat_input_base_month=vat_base_c,
        )
        prof = ebt - tax
        cf_op = prof + amortization_month - credit_principal_month
        cf_op = prof + amortization_month - credit_principal_month
        cf = np.zeros(H + 1)
        cf[0] = -own_funds
        cf[1:] = cf_op
        cum = np.cumsum(cf)
        if own_funds <= 0:
            return cum, float("nan")
        return cum, calculate_payback(cum)
    
    cumulative_pessim, payback_pessim = _scenario_cumulative(params.scenario_pessim_factor)
    cumulative_optim, payback_optim = _scenario_cumulative(params.scenario_optim_factor)
    
    # ── Структура OPEX за 1-й год ──
    n1 = min(12, H)
    opex_breakdown_year1 = {
        "Вода": float(np.sum(cars_per_month[:n1] * core["cost_water_per_wash"])),
        "Электричество": float(np.sum(cars_per_month[:n1] * core["cost_elec_per_wash"])),
        "Химия": float(np.sum(cars_per_month[:n1] * core["cost_chem_per_wash"])),
        "НВ на ЦСВ": float(np.sum(nv_month[:n1])),
        "ЗП и взносы": float(np.sum(salary_total_month[:n1])),
        "Аренда": float(params.rent_month * n1),
        "Коммуналка": float(params.utilities_extra * n1),
        "Охрана": float(params.security_month * n1),
        "Маркетинг": float(params.marketing_month * n1),
        "ТО, расходники": float(params.maintenance_month * n1),
        "Страхование": float(params.insurance_month * n1),
        "Прочее": float(params.other_opex * n1),
        "Имущество / земля": float(
            (params.property_tax_month + params.land_tax_month) * n1
        ),
        "Взносы ИП": float(params.ip_contributions_month * n1),
        "Амортизация": float(np.sum(amortization_month[:n1])),
        "% по кредиту": float(np.sum(credit_interest_month[:n1])),
        "Налоги": float(np.sum(tax_month[:n1])),
    }
    
    # ── Чувствительность (Δ NPV при +10% к параметру) ──
    sensitivity = build_pro_sensitivity_cases(params)
    
    # ── Экология ──
    model = get_washer_model(params.model_code, WASHER_CATALOG)
    region = REGIONS[params.region_key]
    annual_cars = float(np.sum(cars_per_month[:n1])) if n1 > 0 else 0
    eco_metrics = build_eco_metrics(
        annual_served_washes=annual_cars,
        # фактический расход на мойку с учётом микса программ (а не базовый по модели)
        water_per_wash_l=model.water_per_wash_l * float(core.get("avg_water_factor", 1.0)),
        chem_per_wash_rub=model.chem_per_wash_rub * float(core.get("avg_chem_factor", 1.0)),
        eco_water_recycle_pct=params.eco_water_recycle_pct,
        eco_chem_premium=params.eco_chem_premium,
        water_total_tariff_rub_per_m3=(
            float(core.get("water_supply_tariff", region.water_supply))
            + float(core.get("sewage_tariff", region.water_sewage))
        ),
    )
    
    return ProResult(
        months=months,
        cars_per_month=cars_per_month,
        revenue_month=revenue_month,
        var_costs_month=var_costs_month,
        opex_month=opex_month,
        salary_total_month=salary_total_month,
        credit_interest_month=credit_interest_month,
        credit_principal_month=credit_principal_month,
        amortization_month=amortization_month,
        ebitda_month=ebitda_month,
        ebt_month=ebt_month,
        tax_month=tax_month,
        profit_month=profit_month,
        cashflow=cashflow,
        cumulative=cumulative,
        avg_check=avg_check,
        capex_total=capex_total,
        own_funds=own_funds,
        avg_revenue_month=avg_revenue_month,
        avg_profit_month=avg_profit_month,
        avg_ebitda_month=avg_ebitda_month,
        total_revenue=total_revenue,
        total_profit=total_profit,
        payback_months=payback_months,
        npv=npv,
        irr=irr,
        margin_net=margin_net,
        margin_ebitda=margin_ebitda,
        payback_pessim=payback_pessim,
        payback_optim=payback_optim,
        cumulative_pessim=cumulative_pessim,
        cumulative_optim=cumulative_optim,
        capex_breakdown=capex_breakdown,
        opex_breakdown_year1=opex_breakdown_year1,
        sensitivity=sensitivity,
        water_saved_m3_year=eco_metrics.water_saved_m3_year,
        chem_extra_cost_year=eco_metrics.chem_extra_cost_year,
        water_cost_saving_rub_year=eco_metrics.water_cost_saving_rub_year,
        params=params,
        capacity_binding_months=capacity_diagnostics.capacity_binding_months,
        annual_unserved_demand=capacity_diagnostics.annual_unserved_demand,
        annual_unserved_share=capacity_diagnostics.annual_unserved_share,
        peak_requested_utilization=capacity_diagnostics.peak_requested_utilization,
        peak_hour_utilization=estimate_peak_hour_utilization(
            capacity_diagnostics.peak_requested_utilization
        ),
        peak_unserved_month=capacity_diagnostics.peak_unserved_month,
        zero_capacity_positive_demand_months=capacity_diagnostics.zero_capacity_positive_demand_months,
    )


# ══════════════════════════════════════════════════════════════
# UI — PRO
# ══════════════════════════════════════════════════════════════
def render_pro_ui(res: ProResult):
    """Рендер результатов PRO-режима."""
    from ui.compare_state import sync_compare_snapshots_cache

    sync_compare_snapshots_cache(calculate_pro)
    render_pro_config_card(res)
    render_pro_executive_verdict(res)
    render_pro_kpi_cards(res)
    render_pro_scenarios_block(res)
    render_pro_sensitivity_block(res)
    render_pro_break_even_block(res)
    render_pro_capacity_block(res)
    render_pro_assumptions_snapshot(res)
    render_pro_investment_memo(res)
    render_pro_compare_block(res, calculate_pro_fn=calculate_pro)
    render_pro_detail_layer(res)
    render_pro_export_section(res)
    render_pro_ecology_block(res)


# ══════════════════════════════════════════════════════════════
# ENTRY-POINT для PRO режима
# ══════════════════════════════════════════════════════════════
def run_pro_mode():
    """Запуск углублённого режима."""
    params = render_sidebar_pro()
    result = calculate_pro(params)
    render_pro_ui(result)


# ══════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ══════════════════════════════════════════════════════════════
def main():
    """Точка входа в приложение."""
    setup_page()
    init_presentation_mode()
    init_theme()
    inject_css()
    with st.sidebar:
        render_theme_toggle(key_suffix="_sidebar")

    if "mode" not in st.session_state:
        st.session_state.mode = "simple"
    mode = st.session_state.mode

    render_header(mode)
    _theme_spacer, _theme_col = st.columns([4, 1])
    with _theme_col:
        render_theme_toggle()
    mode = render_mode_switcher()
    render_presentation_mode_controls()
    render_presentation_flag()

    from ui.scenario_state import apply_pending_scenario_hydration

    apply_pending_scenario_hydration()

    try:
        if mode == "pro":
            run_pro_mode()
        else:
            run_simple_mode()
    except Exception as e:
        st.markdown(
            f'<div class="wb-danger"><b>Ошибка расчёта:</b> {str(e)}<br>'
            f'<span style="font-size:0.85rem; color:{BRAND["muted"]};">'
            f'Проверьте корректность введённых параметров в сайдбаре.</span></div>',
            unsafe_allow_html=True,
        )
        with st.expander("Технические детали ошибки", expanded=False):
            import traceback
            st.code(traceback.format_exc(), language="python")
    render_footer()
# ══════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
