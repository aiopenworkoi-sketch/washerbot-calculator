"""Светлая тема: перекрытия нативных компонентов Streamlit 1.53.

Селекторы сверены с бандлом Streamlit 1.53 (data-testid / data-baseweb),
поэтому перекрашиваются реальные узлы, а не угаданные классы.
Порталы (dropdown, tooltip) рендерятся в <body> — их красим без скоупа.
"""

from __future__ import annotations

from typing import Mapping

from ui.theme_palette import rgba


def build_light_shell_css(brand: Mapping[str, str]) -> str:
    t = brand
    panel = t["surface"]
    hover = rgba(t["primary"], 0.10)
    return f"""
<style>
    /* ============ КАРКАС ============ */
    :root {{ color-scheme: light; }}
    html, body,
    [data-testid="stApp"] {{
        background: {t['bg']} !important;
        color: {t['text']} !important;
        color-scheme: light !important;
    }}
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {{
        background: {t['bg']} !important;
    }}
    [data-testid="stHeader"] {{
        background: {rgba(t['bg'], 0.94)} !important;
        border-bottom: 1px solid {t['border_subtle']} !important;
    }}
    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"] {{ background: transparent !important; }}
    [data-testid="stToolbar"] button {{ color: {t['text2']} !important; }}
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"] {{
        background: {t['bg']} !important;
        border-top: 1px solid {t['border_subtle']} !important;
    }}

    /* ============ САЙДБАР ============ */
    [data-testid="stSidebar"] {{
        background: {t['surface_muted']} !important;
        border-right: 1px solid {t['border_subtle']} !important;
        color-scheme: light !important;
    }}
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{ color: {t['text']} !important; }}
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"] button {{
        color: {t['text2']} !important;
        background: {t['card']} !important;
        border: 1px solid {t['border']} !important;
    }}


    [data-testid="stSidebarCollapseButton"] button *,
    [data-testid="stExpandSidebarButton"] *, [data-testid="stExpandSidebarButton"] button * {{
        color: {t['text2']} !important;
        fill: {t['text2']} !important;
        opacity: 1 !important;
    }}
    /* ============ ТЕКСТ ============ */
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] :is(p, li, span, h1, h2, h3, h4, h5, h6, strong, em) {{
        color: {t['text']} !important;
    }}
    [data-testid="stMarkdownContainer"] a {{ color: {t['accent']} !important; }}
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {{ color: {t['muted']} !important; }}
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {{ color: {t['text']} !important; }}
    [data-testid="stWidgetLabel"] svg {{ fill: {t['muted']} !important; }}
    [data-testid="stMarkdownContainer"] :not(pre) > code {{
        background: {panel} !important;
        color: {t['accent']} !important;
    }}

    /* ============ ВВОД ТЕКСТА / ЧИСЛА ============ */
    [data-testid="stTextInputRootElement"],
    [data-testid="stTextAreaRootElement"],
    div[data-baseweb="input"],
    div[data-baseweb="textarea"] {{
        background: {t['surface2']} !important;
        border-color: {t['border']} !important;
        color: {t['text']} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stTextInputRootElement"] input,
    [data-testid="stTextAreaRootElement"] textarea,
    [data-testid="stNumberInputField"] {{
        color: {t['text']} !important;
        -webkit-text-fill-color: {t['text']} !important;
        background: transparent !important;
    }}
    input::placeholder, textarea::placeholder {{
        color: {t['muted']} !important;
        -webkit-text-fill-color: {t['muted']} !important;
        opacity: 1 !important;
    }}
    [data-testid="stTextInputRootElement"]:focus-within,
    [data-testid="stTextAreaRootElement"]:focus-within,
    [data-testid="stNumberInputContainer"].focused {{
        border-color: {t['primary']} !important;
    }}
    [data-testid="stNumberInputContainer"] {{
        background: {t['surface2']} !important;
        border-color: {t['border']} !important;
    }}
    [data-testid="stNumberInputStepUp"],
    [data-testid="stNumberInputStepDown"] {{
        background: {panel} !important;
        color: {t['text']} !important;
    }}
    [data-testid="stNumberInputStepUp"] svg,
    [data-testid="stNumberInputStepDown"] svg {{ fill: {t['text2']} !important; }}

    /* ============ SELECTBOX (портал вне stApp) ============ */
    div[data-baseweb="select"] > div {{
        background: {t['surface2']} !important;
        border-color: {t['border']} !important;
        color: {t['text']} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="select"] :is(input, svg) {{
        color: {t['text']} !important;
        fill: {t['muted']} !important;
    }}
    div[role="listbox"][data-baseweb="menu"],
    ul[data-testid="stSelectboxVirtualDropdown"] {{
        background: {t['surface2']} !important;
        border: 1px solid {t['border']} !important;
        box-shadow: 0 10px 28px rgba(31, 27, 22, 0.18) !important;
    }}
    [data-testid="stSelectboxVirtualDropdown"] li,
    li[role="option"] {{ color: {t['text']} !important; background: transparent !important; }}
    [data-testid="stSelectboxVirtualDropdown"] li:hover,
    [data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"],
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {{ background: {hover} !important; }}
    [data-baseweb="tag"] {{ background: {panel} !important; color: {t['text']} !important; }}

    /* ============ СЛАЙДЕР ============ */
    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {{
        background: {t['primary']} !important;
        border-color: {t['on_primary']} !important;
    }}
    [data-testid="stSliderThumbValue"] {{ color: {t['accent']} !important; }}
    [data-testid="stSliderTickBar"] {{ color: {t['muted']} !important; opacity: 1 !important; }}
    [data-testid="stSlider"] div[data-testid="stTickBarMin"],
    [data-testid="stSlider"] div[data-testid="stTickBarMax"] {{ color: {t['muted']} !important; }}

    /* ============ ЧЕКБОКС / РАДИО / ПЕРЕКЛЮЧАТЕЛЬ ============ */
    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label {{ color: {t['text']} !important; }}
    [data-baseweb="checkbox"] > div:first-child,
    [data-baseweb="radio"] > div:first-child {{
        background: {t['surface2']} !important;
        border-color: {t['border']} !important;
    }}
    [data-baseweb="checkbox"] [data-checked="true"],
    [data-baseweb="radio"] [data-checked="true"] {{
        background: {t['primary']} !important;
        border-color: {t['primary']} !important;
    }}

    /* ============ КНОПКИ ============ */
    [data-testid="stButton"] [data-testid^="stBaseButton-"],
    [data-testid="stDownloadButton"] [data-testid^="stBaseButton-"],
    [data-testid="stFormSubmitButton"] [data-testid^="stBaseButton-"] {{
        background: {t['surface2']} !important;
        border: 1px solid {t['border']} !important;
        color: {t['text']} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stButton"] [data-testid^="stBaseButton-"] *,
    [data-testid="stDownloadButton"] [data-testid^="stBaseButton-"] * {{ color: inherit !important; }}
    [data-testid="stButton"] [data-testid^="stBaseButton-"]:hover,
    [data-testid="stDownloadButton"] [data-testid^="stBaseButton-"]:hover {{
        background: {panel} !important;
        border-color: {t['primary']} !important;
        color: {t['accent']} !important;
    }}
    [data-testid="stBaseButton-primary"],
    [data-testid="stButton"] [data-testid="stBaseButton-primary"],
    [data-testid="stDownloadButton"] [data-testid="stBaseButton-primary"],
    [data-testid="stFormSubmitButton"] [data-testid="stBaseButton-primary"] {{
        background: {t['primary']} !important;
        border-color: {t['primary']} !important;
        color: {t['on_primary']} !important;
    }}
    [data-testid="stBaseButton-primary"] * {{ color: {t['on_primary']} !important; }}
    [data-testid="stBaseButton-primary"]:hover {{
        background: {t['accent']} !important;
        border-color: {t['accent']} !important;
        color: {t['bg']} !important;
    }}
    [data-testid="stBaseButton-primary"]:hover * {{ color: {t['bg']} !important; }}


    /* disabled/loading состояние primary-кнопки */
    .stButton > button[kind="primary"]:disabled,
    .stButton > button[kind="primary"][disabled],
    [data-testid="stBaseButton-primary"]:disabled,
    [data-testid="stBaseButton-primary"][disabled] {{
        background: {t['primary']} !important;
        border-color: {t['primary']} !important;
        color: {t['on_primary']} !important;
        opacity: 1 !important;
    }}
    .stButton > button[kind="primary"]:disabled *,
    [data-testid="stBaseButton-primary"]:disabled * {{
        color: {t['on_primary']} !important;
    }}


    /* primary: базовое состояние (атрибут kind, а не testid) */
    .stButton > button[kind="primary"],
    button[kind="primary"],
    [data-testid="stButton"] button[kind="primary"] {{
        background: {t['primary']} !important;
        border-color: {t['primary']} !important;
        color: {t['on_primary']} !important;
    }}
    .stButton > button[kind="primary"] *,
    button[kind="primary"] * {{
        color: {t['on_primary']} !important;
    }}
    /* primary: hover / active / focus — тёмное золото с белым текстом */
    .stButton > button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:active,
    .stButton > button[kind="primary"]:focus-visible,
    button[kind="primary"]:hover,
    button[kind="primary"]:active,
    button[kind="primary"]:focus-visible {{
        background: {t['accent']} !important;
        border-color: {t['accent']} !important;
        color: #FFFFFF !important;
    }}
    .stButton > button[kind="primary"]:hover *,
    .stButton > button[kind="primary"]:active *,
    button[kind="primary"]:hover *,
    button[kind="primary"]:active * {{
        color: #FFFFFF !important;
    }}

    /* primary: убираем прозрачность disabled/loading, чтобы текст не «серел» */
    .stButton > button[kind="primary"],
    button[kind="primary"],
    [data-testid="stBaseButton-primary"] {{ opacity: 1 !important; }}
    .stButton > button[kind="primary"] *,
    button[kind="primary"] *,
    [data-testid="stBaseButton-primary"] * {{ opacity: 1 !important; }}
    .stButton > button[kind="primary"]:disabled,
    button[kind="primary"]:disabled,
    [data-testid="stBaseButton-primary"]:disabled {{
        opacity: 1 !important;
        color: {t['on_primary']} !important;
    }}
    /* ============ ТАБЫ ============ */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        border-bottom: 1px solid {t['border_subtle']} !important;
        gap: 4px;
    }}
    [data-baseweb="tab"] {{ color: {t['text2']} !important; background: transparent !important; }}
    [data-baseweb="tab"][aria-selected="true"] {{ color: {t['accent']} !important; }}
    [data-baseweb="tab-highlight"] {{ background: {t['primary']} !important; }}
    [data-baseweb="tab-border"] {{ background: {t['border_subtle']} !important; }}

    /* ============ ЭКСПАНДЕР ============ */
    [data-testid="stExpander"] details {{
        background: {t['card']} !important;
        border: 1px solid {t['border_subtle']} !important;
        border-radius: 10px;
    }}
    [data-testid="stExpander"] summary,
    [data-testid="stExpanderDetails"] {{
        background: transparent !important;
        color: {t['text']} !important;
    }}
    [data-testid="stExpander"] summary:hover {{ color: {t['accent']} !important; }}
    [data-testid="stExpander"] summary svg {{ fill: {t['text2']} !important; }}

    /* ============ АЛЕРТЫ ============ */
    [data-baseweb="notification"] {{
        border: 1px solid {t['border_subtle']} !important;
        border-radius: 10px !important;
    }}
    [data-baseweb="notification"]:has([data-testid="stAlertContentInfo"]) {{
        background: {rgba(t['primary'], 0.07)} !important;
    }}
    [data-baseweb="notification"]:has([data-testid="stAlertContentSuccess"]) {{
        background: {rgba(t['green'], 0.10)} !important;
    }}
    [data-baseweb="notification"]:has([data-testid="stAlertContentWarning"]) {{
        background: {rgba(t['yellow'], 0.12)} !important;
    }}
    [data-baseweb="notification"]:has([data-testid="stAlertContentError"]) {{
        background: {rgba(t['red'], 0.10)} !important;
    }}
    [data-testid="stAlertContainer"] :is(p, li, span) {{ color: {t['text']} !important; }}

    /* ============ КОД / ТУЛТИП / ЗАГРУЗКА / ПРОГРЕСС ============ */
    [data-testid="stCode"], [data-testid="stMarkdownPre"] {{
        background: {panel} !important;
        border: 1px solid {t['border_subtle']} !important;
        border-radius: 10px !important;
    }}
    [data-testid="stCode"] * {{ color: {t['text']} !important; }}
    [data-testid="stCodeCopyButton"] {{ background: {t['surface2']} !important; color: {t['muted']} !important; }}
    [data-testid="stTooltipContent"] {{
        background: {t['text']} !important;
        color: {t['bg']} !important;
    }}
    [data-testid="stTooltipContent"] * {{ color: {t['bg']} !important; }}
    [data-testid="stFileUploaderDropzone"] {{
        background: {panel} !important;
        border: 1px dashed {t['border']} !important;
    }}
    [data-testid="stFileUploaderDropzone"] * {{ color: {t['text']} !important; }}
    [data-testid="stSpinnerIcon"] {{ color: {t['primary']} !important; }}
    [data-testid="stProgress"] p {{ color: {t['muted']} !important; }}

    /* ============ ТАБЛИЦА (HTML) ============ */
    .wb-table-wrap {{
        border: 1px solid {t['border_subtle']};
        border-radius: 10px;
        overflow: auto;
        max-height: 460px;
        background: {t['surface2']};
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
        background: {panel} !important;
        color: {t['text']} !important;
        text-align: right;
        padding: 8px 10px;
        border-bottom: 1px solid {t['border']} !important;
        white-space: nowrap;
    }}
    table.wb-table th:first-child,
    table.wb-table td:first-child {{ text-align: left; }}
    table.wb-table td {{
        padding: 7px 10px;
        text-align: right;
        color: {t['text2']} !important;
        border-bottom: 1px solid {t['border_subtle']} !important;
        white-space: nowrap;
    }}
    table.wb-table tbody tr:nth-child(even) td {{ background: {rgba(t['surface'], 0.55)}; }}
    table.wb-table tbody tr:hover td {{ background: {rgba(t['primary'], 0.06)}; }}


    /* === ЧЕКБОКСЫ / ТУМБЛЕРЫ: checked-состояние по теме === */
    label[data-baseweb=checkbox] > span,
    label[data-baseweb=radio] > span {{
        background: {t['surface2']} !important;
        border-color: {t['border']} !important;
    }}
    label[data-baseweb=checkbox]:has(input:checked) > span,
    label[data-baseweb=radio]:has(input:checked) > span {{
        background: {t['primary']} !important;
        border-color: {t['primary']} !important;
    }}
    label[data-baseweb=checkbox]:has(input:checked) > span svg,
    label[data-baseweb=radio]:has(input:checked) > span svg {{
        fill: {t['on_primary']} !important;
        color: {t['on_primary']} !important;
    }}

    /* === РАЗДЕЛИТЕЛИ === */
    hr, [data-testid=stDivider] {{
        border-color: {t['border_subtle']} !important;
        background: {t['border_subtle']} !important;
    }}
    /* ============ СКРОЛЛБАРЫ ============ */
    * {{ scrollbar-width: thin; scrollbar-color: {t['border']} transparent; }}
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: {t['surface_muted']}; }}
    ::-webkit-scrollbar-thumb {{
        background: {rgba(t['border'], 0.75)};
        border-radius: 8px;
        border: 2px solid {t['surface_muted']};
    }}
</style>
"""
