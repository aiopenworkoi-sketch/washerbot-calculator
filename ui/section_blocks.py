from __future__ import annotations

from typing import Any

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.renderers import PLOTLY_PRESENTATION_CONFIG
from ui.table_column_config import infer_table_column_config
from ui.text_fallbacks import coerce_visible_text
from ui.ui_labels import UIClassNames


def render_section_header(
    title: str | None,
    *,
    subtitle: str | None = None,
    eyebrow: str | None = None,
    style: str | None = None,
) -> None:
    """Unified section header: optional eyebrow, title, subtitle."""
    clean_title = html.escape(coerce_visible_text(title) or "")
    if not clean_title:
        return
    clean_sub = html.escape(coerce_visible_text(subtitle) or "") if subtitle else ""
    clean_eye = html.escape(coerce_visible_text(eyebrow) or "") if eyebrow else ""
    title_style = f' style="{style}"' if style else ""
    eyebrow_html = (
        f'<div class="wb-section-eyebrow">{clean_eye}</div>' if clean_eye else ""
    )
    subtitle_html = (
        f'<p class="wb-section-subtitle">{clean_sub}</p>' if clean_sub else ""
    )
    st.markdown(
        f'<div class="wb-section-head">'
        f"{eyebrow_html}"
        f'<div class="{UIClassNames.CARD_TITLE} wb-section-title"{title_style}>{clean_title}</div>'
        f"{subtitle_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_section_title(title_html: str | None, *, style: str | None = None) -> None:
    render_section_header(title_html, style=style)


def render_section_spacer(*, tight: bool = False) -> None:
    css_class = "wb-section-block--tight" if tight else "wb-section-block"
    st.markdown(f'<div class="{css_class}"></div>', unsafe_allow_html=True)


def render_plotly_section(fig: go.Figure, *, use_container_width: bool = True) -> None:
    st.markdown('<div class="wb-chart-shell">', unsafe_allow_html=True)
    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        config=PLOTLY_PRESENTATION_CONFIG,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _format_table_cell(value: Any) -> str:
    """Формат ячейки: деньги — с пробелами, проценты — с запятой."""
    import math

    if value is None:
        return ""
    if isinstance(value, bool):
        return "да" if value else "нет"
    if isinstance(value, (int,)):
        return f"{value:,}".replace(",", " ")
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "—"
        if abs(value) >= 1000:
            return f"{value:,.0f}".replace(",", " ")
        if abs(value) >= 100:
            return f"{value:,.0f}".replace(",", " ")
        return f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return html.escape(str(value))


def render_dataframe_section(
    df: pd.DataFrame,
    *,
    use_container_width: bool = True,
    hide_index: bool = True,
    height: int | None = None,
    column_config: dict[str, Any] | None = None,
) -> None:
    """Таблица на HTML: перекрашивается темой (st.dataframe — canvas)."""
    if df is None or df.empty:
        return
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in df.columns)
    body_rows = []
    for row in df.itertuples(index=False, name=None):
        cells = "".join(f"<td>{_format_table_cell(v)}</td>" for v in row)
        body_rows.append(f"<tr>{cells}</tr>")
    table_html = (
        '<div class="wb-table-wrap"><table class="wb-table">'
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_section_subtitle(text: str | None) -> None:
    """Standalone subtitle when section title is rendered separately."""
    clean = coerce_visible_text(text)
    if not clean:
        return
    st.markdown(
        f'<p class="wb-section-subtitle wb-section-subtitle--standalone">{clean}</p>',
        unsafe_allow_html=True,
    )


def render_section_takeaway(text: str | None) -> None:
    clean = coerce_visible_text(text)
    if not clean:
        return
    st.markdown(
        f'<p class="wb-section-takeaway">{clean}</p>',
        unsafe_allow_html=True,
    )


def render_narrative_chart_section(
    title_html: str,
    fig: go.Figure,
    *,
    subtitle: str | None = None,
    takeaway: str | None = None,
    caption: str | None = None,
    title_style: str | None = None,
    use_container_width: bool = True,
) -> None:
    st.markdown('<div class="wb-section-block">', unsafe_allow_html=True)
    render_section_title(title_html, style=title_style)
    if subtitle:
        render_section_subtitle(subtitle)
    if takeaway:
        render_section_takeaway(takeaway)
    render_plotly_section(fig, use_container_width=use_container_width)
    if caption:
        clean_caption = coerce_visible_text(caption)
        if clean_caption:
            st.markdown(
                f'<p class="wb-section-caption">{clean_caption}</p>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def render_titled_chart_section(
    title_html: str,
    fig: go.Figure,
    *,
    title_style: str | None = None,
    use_container_width: bool = True,
) -> None:
    st.markdown('<div class="wb-section-block">', unsafe_allow_html=True)
    render_section_title(title_html, style=title_style)
    render_plotly_section(fig, use_container_width=use_container_width)
    st.markdown("</div>", unsafe_allow_html=True)


def render_titled_table_section(
    title_html: str,
    df: pd.DataFrame,
    *,
    title_style: str | None = None,
    use_container_width: bool = True,
    hide_index: bool = True,
    height: int | None = None,
) -> None:
    render_section_title(title_html, style=title_style)
    render_dataframe_section(
        df,
        use_container_width=use_container_width,
        hide_index=hide_index,
        height=height,
    )
