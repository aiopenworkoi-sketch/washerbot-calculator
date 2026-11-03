from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from domain.params import ProParams
from domain.results import ProResult
from ui.compare_state import CompareVariantRecord
from ui.display_fallbacks import (
    has_finite_irr,
    has_finite_payback_months,
    is_missing_numeric,
    missing_placeholder,
)
from ui.format_policies import format_kpi_irr, format_kpi_npv_compact, format_kpi_payback
from ui.renderers import BRAND, fmt_percent_value, fmt_ratio_pct, style_plotly
from ui.text_fallbacks import coerce_visible_text

CompareDirection = Literal["higher_better", "lower_better"]


@dataclass(frozen=True)
class CompareVariantSnapshot:
    variant_id: str
    label: str
    params: ProParams
    result: ProResult


@dataclass(frozen=True)
class CompareMetricRowSpec:
    metric_key: str
    label: str
    direction: CompareDirection
    values: Tuple[str, ...]
    raw_values: Tuple[float, ...]
    deltas: Tuple[str, ...]


@dataclass(frozen=True)
class ProComparisonSpec:
    variants: Tuple[CompareVariantSnapshot, ...]
    baseline_id: str
    rows: Tuple[CompareMetricRowSpec, ...]
    narrative: Tuple[str, ...]
    chart: go.Figure


def build_variant_snapshot(
    variant_id: str,
    label: str,
    params: ProParams,
    result: ProResult,
) -> CompareVariantSnapshot:
    return CompareVariantSnapshot(
        variant_id=variant_id,
        label=label,
        params=params,
        result=result,
    )


def _metric_raw_values(
    snapshots: Tuple[CompareVariantSnapshot, ...],
    extractor,
) -> Tuple[float, ...]:
    return tuple(float(extractor(s.result)) for s in snapshots)


def _values_are_delta_comparable(
    baseline: float,
    value: float,
    *,
    payback_metric: bool = False,
    irr_metric: bool = False,
) -> bool:
    if payback_metric:
        return has_finite_payback_months(baseline) and has_finite_payback_months(value)
    if irr_metric:
        return has_finite_irr(baseline) and has_finite_irr(value)
    return not is_missing_numeric(baseline) and not is_missing_numeric(value)


def _format_delta(
    baseline: float,
    value: float,
    *,
    direction: CompareDirection,
    is_percent_metric: bool = False,
    payback_metric: bool = False,
    irr_metric: bool = False,
) -> str:
    if not _values_are_delta_comparable(
        baseline,
        value,
        payback_metric=payback_metric,
        irr_metric=irr_metric,
    ):
        return missing_placeholder()
    if baseline == value:
        return "0"
    diff = value - baseline
    if is_percent_metric:
        diff *= 100.0
    better = diff > 0 if direction == "higher_better" else diff < 0
    sign = "+" if diff > 0 else ""
    if is_percent_metric:
        text = f"{sign}{fmt_percent_value(abs(diff), decimals=1).removesuffix(' %')} п.п."
    elif abs(diff) >= 1e6:
        text = f"{sign}{diff/1e6:.2f} млн".replace(".", ",")
    elif abs(diff) >= 1e3:
        text = f"{sign}{diff/1e3:.0f} тыс."
    else:
        text = f"{sign}{abs(diff):.1f}".replace(".", ",")
        if payback_metric:
            text += " мес"
    suffix = " лучше" if better else " хуже"
    return text + suffix


def _build_metric_row(
    metric_key: str,
    label: str,
    direction: CompareDirection,
    snapshots: Tuple[CompareVariantSnapshot, ...],
    baseline_idx: int,
    formatters: Tuple[str, ...],
    raw_values: Tuple[float, ...],
    *,
    is_percent_metric: bool = False,
    payback_metric: bool = False,
    irr_metric: bool = False,
) -> CompareMetricRowSpec:
    baseline = raw_values[baseline_idx]
    deltas: list[str] = []
    for idx, value in enumerate(raw_values):
        if idx == baseline_idx:
            deltas.append("база")
        else:
            deltas.append(
                _format_delta(
                    baseline,
                    value,
                    direction=direction,
                    is_percent_metric=is_percent_metric,
                    payback_metric=payback_metric,
                    irr_metric=irr_metric,
                )
            )
    return CompareMetricRowSpec(
        metric_key=metric_key,
        label=label,
        direction=direction,
        values=formatters,
        raw_values=raw_values,
        deltas=tuple(deltas),
    )


def _build_narrative(
    snapshots: Tuple[CompareVariantSnapshot, ...],
    baseline_idx: int,
) -> Tuple[str, ...]:
    baseline = snapshots[baseline_idx]
    bullets: list[str] = []

    npv_leader = max(snapshots, key=lambda s: s.result.npv)
    if npv_leader.variant_id != baseline.variant_id:
        bullets.append(
            f"Лучший NPV — «{npv_leader.label}» "
            f"({format_kpi_npv_compact(npv_leader.result.npv)})."
        )

    finite_paybacks = [
        s for s in snapshots if has_finite_payback_months(s.result.payback_months)
    ]
    if finite_paybacks:
        fastest = min(finite_paybacks, key=lambda s: s.result.payback_months)
        if fastest.variant_id != baseline.variant_id:
            bullets.append(
                f"Быстрее окупается «{fastest.label}» "
                f"({format_kpi_payback(fastest.result.payback_months)})."
            )

    equity_leader = min(snapshots, key=lambda s: s.result.own_funds)
    if equity_leader.variant_id != baseline.variant_id:
        bullets.append(
            f"Меньше собственных средств требует «{equity_leader.label}» "
            f"({format_kpi_npv_compact(equity_leader.result.own_funds)})."
        )

    capacity_cases = [s for s in snapshots if s.result.annual_unserved_share > 0]
    if capacity_cases:
        worst = max(capacity_cases, key=lambda s: s.result.annual_unserved_share)
        bullets.append(
            f"Наибольшее давление мощности у «{worst.label}» "
            f"({fmt_ratio_pct(worst.result.annual_unserved_share)} потерь)."
        )
    elif len(snapshots) >= 2:
        bullets.append("По всем вариантам ограничений мощности на горизонте не выявлено.")

    if not bullets:
        bullets.append(
            f"Сравнение относительно базового варианта «{baseline.label}»."
        )
    return tuple(bullets[:4])


def build_comparison_chart(
    snapshots: Tuple[CompareVariantSnapshot, ...],
) -> go.Figure:
    labels = [s.label for s in snapshots]
    npv_values = [s.result.npv for s in snapshots]
    payback_values: list[float | None] = []
    payback_hover: list[str] = []
    for snapshot in snapshots:
        months = snapshot.result.payback_months
        if has_finite_payback_months(months):
            payback_values.append(months)
            payback_hover.append(f"{months:.0f} мес.")
        else:
            payback_values.append(None)
            payback_hover.append("не окупается")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("NPV", "Окупаемость, мес."),
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=npv_values,
            name="NPV",
            marker_color=BRAND["primary"],
            hovertemplate="<b>%{x}</b><br>NPV: %{y:,.0f} ₽<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=payback_values,
            name="Окупаемость",
            marker_color=BRAND["accent"],
            text=payback_hover,
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Окупаемость: %{text}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.update_layout(
        showlegend=False,
        barmode="group",
        margin=dict(t=40, b=40),
    )
    fig.update_yaxes(title_text="₽", row=1, col=1)
    fig.update_yaxes(title_text="мес.", row=1, col=2)
    return style_plotly(fig, height=360)


def build_pro_comparison_specs(
    snapshots: Tuple[CompareVariantSnapshot, ...],
    *,
    baseline_id: str,
) -> ProComparisonSpec:
    if len(snapshots) < 2:
        raise ValueError("comparison requires at least 2 variants")

    baseline_idx = next(
        (i for i, s in enumerate(snapshots) if s.variant_id == baseline_id),
        0,
    )

    rows: list[CompareMetricRowSpec] = []

    payback_raw = _metric_raw_values(snapshots, lambda r: r.payback_months)
    rows.append(
        _build_metric_row(
            "payback",
            "Окупаемость",
            "lower_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_payback(v) for v in payback_raw),
            payback_raw,
            payback_metric=True,
        )
    )

    npv_raw = _metric_raw_values(snapshots, lambda r: r.npv)
    rows.append(
        _build_metric_row(
            "npv",
            "NPV",
            "higher_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_npv_compact(v) for v in npv_raw),
            npv_raw,
        )
    )

    irr_raw = _metric_raw_values(snapshots, lambda r: r.irr)
    rows.append(
        _build_metric_row(
            "irr",
            "IRR",
            "higher_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_irr(v) for v in irr_raw),
            irr_raw,
            is_percent_metric=True,
            irr_metric=True,
        )
    )

    margin_raw = _metric_raw_values(snapshots, lambda r: r.margin_net)
    rows.append(
        _build_metric_row(
            "margin_net",
            "Маржа чистая",
            "higher_better",
            snapshots,
            baseline_idx,
            tuple(fmt_ratio_pct(v) for v in margin_raw),
            margin_raw,
            is_percent_metric=True,
        )
    )

    capex_raw = _metric_raw_values(snapshots, lambda r: r.capex_total)
    rows.append(
        _build_metric_row(
            "capex_total",
            "CAPEX",
            "lower_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_npv_compact(v) for v in capex_raw),
            capex_raw,
        )
    )

    own_raw = _metric_raw_values(snapshots, lambda r: r.own_funds)
    rows.append(
        _build_metric_row(
            "own_funds",
            "Собственные средства",
            "lower_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_npv_compact(v) for v in own_raw),
            own_raw,
        )
    )

    revenue_raw = _metric_raw_values(snapshots, lambda r: r.avg_revenue_month)
    rows.append(
        _build_metric_row(
            "avg_revenue_month",
            "Выручка/мес",
            "higher_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_npv_compact(v) for v in revenue_raw),
            revenue_raw,
        )
    )

    unserved_raw = _metric_raw_values(snapshots, lambda r: r.annual_unserved_share)
    rows.append(
        _build_metric_row(
            "annual_unserved_share",
            "Потери спроса (1-й год)",
            "lower_better",
            snapshots,
            baseline_idx,
            tuple(fmt_ratio_pct(v) for v in unserved_raw),
            unserved_raw,
            is_percent_metric=True,
        )
    )

    pessim_raw = _metric_raw_values(snapshots, lambda r: r.payback_pessim)
    rows.append(
        _build_metric_row(
            "payback_pessim",
            "Окупаемость (песс.)",
            "lower_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_payback(v) for v in pessim_raw),
            pessim_raw,
            payback_metric=True,
        )
    )

    optim_raw = _metric_raw_values(snapshots, lambda r: r.payback_optim)
    rows.append(
        _build_metric_row(
            "payback_optim",
            "Окупаемость (опт.)",
            "lower_better",
            snapshots,
            baseline_idx,
            tuple(format_kpi_payback(v) for v in optim_raw),
            optim_raw,
            payback_metric=True,
        )
    )

    narrative = _build_narrative(snapshots, baseline_idx)
    chart = build_comparison_chart(snapshots)

    return ProComparisonSpec(
        variants=snapshots,
        baseline_id=snapshots[baseline_idx].variant_id,
        rows=tuple(rows),
        narrative=narrative,
        chart=chart,
    )


def render_comparison_matrix_html(spec: ProComparisonSpec) -> str:
    variant_labels = [coerce_visible_text(v.label, default="Вариант") for v in spec.variants]
    header = "".join(f"<th>{label}</th>" for label in variant_labels)

    body_rows = []
    baseline_idx = next(
        (i for i, v in enumerate(spec.variants) if v.variant_id == spec.baseline_id),
        0,
    )
    for row in spec.rows:
        cells = []
        for idx, value in enumerate(row.values):
            delta = row.deltas[idx] if idx < len(row.deltas) else ""
            if idx == baseline_idx or delta in ("база", "0", missing_placeholder()):
                cells.append(f"<td>{value}</td>")
            else:
                cells.append(
                    f"<td>{value}<br><span class='wb-compare-delta'>{delta}</span></td>"
                )
        body_rows.append(
            f"<tr><td class='wb-compare-metric'>{row.label}</td>"
            f"{''.join(cells)}</tr>"
        )

    return (
        f'<table class="wb-compare-table"><thead><tr>'
        f"<th>Показатель</th>{header}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )
