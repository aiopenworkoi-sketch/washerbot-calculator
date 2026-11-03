from __future__ import annotations

from typing import Literal, Sequence

import plotly.graph_objects as go

from ui.renderers import BRAND, fmt_money_compact, style_plotly

BarPalette = Literal["cost", "capex"]


def _bar_colors(values: Sequence[float], palette: BarPalette) -> list[str]:
    if not values:
        return []
    max_v = max(values)
    colors: list[str] = []
    for value in values:
        ratio = value / max_v if max_v > 0 else 0.0
        if palette == "capex":
            if ratio > 0.66:
                colors.append(BRAND["primary"])
            elif ratio > 0.33:
                colors.append(BRAND["accent"])
            else:
                colors.append(BRAND["muted"])
        else:
            if ratio > 0.66:
                colors.append(BRAND["red"])
            elif ratio > 0.33:
                colors.append("#A67A7A")
            else:
                colors.append(BRAND["muted"])
    return colors


def build_sorted_horizontal_bar_figure(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    palette: BarPalette = "cost",
    height: int = 380,
    xaxis_title: str = "₽ за год",
) -> go.Figure:
    pairs = sorted(
        ((label, value) for label, value in zip(labels, values) if value > 0),
        key=lambda item: item[1],
        reverse=False,
    )
    if not pairs:
        return go.Figure()

    names = [item[0] for item in pairs]
    amounts = [item[1] for item in pairs]
    total = sum(amounts)
    text_labels = [
        f"{fmt_money_compact(value)} · {value / total * 100:.0f} %".replace(".", ",")
        if total > 0
        else fmt_money_compact(value)
        for value in amounts
    ]

    fig = go.Figure(
        go.Bar(
            y=names,
            x=amounts,
            orientation="h",
            marker=dict(
                color=_bar_colors(amounts, palette),
                line=dict(color=BRAND["bg2"], width=1),
            ),
            text=text_labels,
            textposition="outside",
            textfont=dict(color=BRAND["text2"], size=11),
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} ₽<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title=xaxis_title,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=8, r=72, t=12, b=36),
        showlegend=False,
    )
    return style_plotly(fig, height=height)
