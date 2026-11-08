from __future__ import annotations

from typing import List, Tuple

import numpy as np
import plotly.graph_objects as go

from domain.results import ProResult
from ui.format_policies import format_sensitivity_bar_percent
from ui.presentation_metrics import estimate_pro_monthly_capacity_series
from ui.renderers import BRAND, style_plotly
from ui.view_guards import should_render_capacity_overload_advisory


def rank_sensitivity_items(sensitivity: dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(sensitivity.items(), key=lambda x: x[1], reverse=True)


def build_sensitivity_takeaway(sorted_items: List[Tuple[str, float]]) -> str:
    if not sorted_items:
        return ""
    top_name, top_value = sorted_items[0]
    if len(sorted_items) > 1:
        second_name, second_value = sorted_items[1]
        return (
            f"Сильнее всего NPV меняют {top_name} и {second_name} "
            f"({format_sensitivity_bar_percent(top_value * 100)} и "
            f"{format_sensitivity_bar_percent(second_value * 100)} ΔNPV при +10%)."
        )
    return (
        f"Главный драйвер — {top_name} "
        f"({format_sensitivity_bar_percent(top_value * 100)} ΔNPV при +10%)."
    )


def _sensitivity_bar_colors(values_pct: List[float]) -> List[str]:
    """Один цвет для всех баров: длина уже кодирует величину (не дублируем цветом)."""
    return [BRAND["primary"]] * len(values_pct)


def build_sensitivity_driver_figure(
    sorted_items: List[Tuple[str, float]],
) -> go.Figure:
    """
    Ranked horizontal driver chart (not a symmetric tornado).

    res.sensitivity stores |NPV(+10%) − NPV_base| / |NPV_base| per parameter.
    """
    names = [item[0] for item in sorted_items]
    values_pct = [item[1] * 100 for item in sorted_items]
    hover_labels = [format_sensitivity_bar_percent(v) for v in values_pct]

    fig = go.Figure(
        go.Bar(
            x=values_pct,
            y=names,
            orientation="h",
            customdata=hover_labels,
            marker=dict(
                color=_sensitivity_bar_colors(values_pct),
                line=dict(color=BRAND["bg2"], width=1),
            ),
            text=hover_labels,
            textposition="outside",
            textfont=dict(color=BRAND["text2"], size=11),
            hovertemplate="<b>%{y}</b><br>Δ NPV: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Δ NPV, % от базового (параметр +10%)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=8, r=48, t=8, b=8),
    )
    return style_plotly(fig, height=max(260, 44 * len(names) + 80))


def build_capacity_throughput_figure(res: ProResult) -> go.Figure:
    capacity_line = estimate_pro_monthly_capacity_series(res)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=res.months,
            y=res.cars_per_month,
            mode="lines",
            name="Фактический поток",
            line=dict(color=BRAND["primary"], width=2),
            hovertemplate="<b>Месяц %{x}</b><br>Авто: %{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=res.months,
            y=capacity_line,
            mode="lines",
            name="Расчётная мощность",
            line=dict(color=BRAND["yellow"], width=1.5, dash="dot"),
            hovertemplate="<b>Месяц %{x}</b><br>Мощность: %{y:,.0f}<extra></extra>",
        )
    )
    if should_render_capacity_overload_advisory(res):
        overload_mask = res.cars_per_month >= capacity_line - 1e-6
        if np.any(overload_mask):
            fig.add_trace(
                go.Scatter(
                    x=res.months[overload_mask],
                    y=res.cars_per_month[overload_mask],
                    mode="markers",
                    name="У потолка мощности",
                    marker=dict(color=BRAND["red"], size=6, symbol="circle-open"),
                    hovertemplate="<b>Месяц %{x}</b><br>У потолка: %{y:,.0f}<extra></extra>",
                )
            )
    fig.update_layout(
        xaxis_title="Месяц",
        yaxis_title="Авто / мес",
        legend=dict(orientation="h", y=-0.22),
        margin=dict(t=8, b=8),
    )
    return style_plotly(fig, height=340)
