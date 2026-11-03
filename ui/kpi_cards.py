from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Tuple

import streamlit as st

from ui.text_fallbacks import coerce_visible_text
from ui.renderers import missing_placeholder


@dataclass(frozen=True)
class MetricCardSpec:
    label: str
    value: str
    hint: str = ""
    status: str = ""
    emphasis: str = ""


def _value_size_class(value: str) -> str:
    length = len(value)
    if length >= 16:
        return "wb-metric-value--long"
    if length >= 11:
        return "wb-metric-value--compact"
    return ""


def resolve_kpi_grid_cols(card_count: int, *, desktop_cols: int = 4) -> int:
    """Pick a stable desktop column count for KPI cards (1..4)."""
    capped = max(1, min(desktop_cols, 4))
    if card_count <= 1:
        return 1
    if card_count == 2:
        return min(2, capped)
    if card_count == 3:
        return min(3, capped)
    return capped


def metric_card_html(spec: MetricCardSpec) -> str:
    label_clean = html.escape(coerce_visible_text(spec.label) or "")
    value_clean = html.escape(coerce_visible_text(spec.value) or missing_placeholder())
    hint_clean = coerce_visible_text(spec.hint)
    hint_html = (
        f'<div class="wb-metric-hint wb-metric-hint--clamp">{html.escape(hint_clean)}</div>'
        if hint_clean
        else (
            '<div class="wb-metric-hint wb-metric-hint--clamp wb-metric-hint--empty">'
            "&nbsp;</div>"
        )
    )

    cls = "wb-metric"
    if spec.emphasis == "primary":
        cls += " wb-metric--primary"
    elif spec.emphasis == "secondary":
        cls += " wb-metric--secondary"
    if spec.status:
        cls += f" {html.escape(spec.status)}"

    value_cls = "wb-metric-value"
    size_class = _value_size_class(value_clean)
    if size_class:
        value_cls += f" {size_class}"

    return (
        f'<div class="{cls}">'
        f'<div class="wb-metric-label wb-metric-label--clamp">{label_clean}</div>'
        f'<div class="wb-metric-body">'
        f'<div class="{value_cls}">{value_clean}</div>'
        f"{hint_html}"
        f"</div></div>"
    )


def render_kpi_grid(
    cards: Tuple[MetricCardSpec, ...],
    *,
    desktop_cols: int = 4,
) -> None:
    if not cards:
        return

    cols = resolve_kpi_grid_cols(len(cards), desktop_cols=desktop_cols)
    cards_html = "".join(metric_card_html(card) for card in cards)
    st.markdown(
        f'<div class="wb-kpi-shell">'
        f'<div class="wb-kpi-grid wb-kpi-grid--cols-{cols} wb-kpi-grid--items-{len(cards)}">'
        f"{cards_html}"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def render_metric_cards(
    cards: Tuple[MetricCardSpec, ...],
    *,
    cols_per_row: int = 4,
    column_factory=None,
) -> None:
    _ = column_factory
    render_kpi_grid(cards, desktop_cols=cols_per_row)
