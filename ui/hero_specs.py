from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Tuple

from domain.results import ProResult, SimpleResult
from ui.decision_specs import build_executive_verdict_spec
from ui.display_fallbacks import has_finite_payback_months, is_missing_payback_months
from ui.format_policies import (
    format_kpi_irr,
    format_kpi_margin_ratio,
    format_kpi_npv_compact,
    format_kpi_payback,
)
from ui.view_guards import should_render_pessimistic_payback_success
from ui.model_constants import format_npv_discount_rate_label, format_npv_kpi_label

_STATUS_LABELS = {
    "good": "Привлекательно",
    "info": "Умеренно",
    "warn": "Требует проверки",
    "bad": "Не проходит порог",
}


@dataclass(frozen=True)
class HeroMetricSpec:
    label: str
    value: str
    hint: str = ""


@dataclass(frozen=True)
class ExecutiveHeroSpec:
    headline: str
    severity: str
    status_label: str
    metrics: Tuple[HeroMetricSpec, ...]
    context_line: str = ""


def _status_label(severity: str) -> str:
    return _STATUS_LABELS.get(severity, "Требует проверки")


def _simple_headline(res: SimpleResult) -> tuple[str, str]:
    p = res.params
    horizon = p.horizon_months

    if res.npv > 0 and has_finite_payback_months(res.payback_months):
        if res.payback_months <= horizon and res.payback_months <= 36:
            return (
                f"Окупаемость за {format_kpi_payback(res.payback_months)} при положительном NPV",
                "good",
            )
        if res.payback_months <= horizon:
            return (
                f"Проект окупается за {format_kpi_payback(res.payback_months)} "
                f"с NPV {format_kpi_npv_compact(res.npv)}",
                "info",
            )
        return (
            "Положительный NPV, окупаемость выходит за горизонт модели",
            "warn",
        )
    if is_missing_payback_months(res.payback_months) and res.npv <= 0:
        return ("На выбранном горизонте проект не окупается", "bad")
    if res.npv <= 0:
        return (f"NPV отрицательный при ставке {format_npv_discount_rate_label()} — порог доходности не достигнут", "bad")
    return ("Положительный NPV, срок окупаемости требует внимания", "warn")


def build_simple_executive_hero_spec(res: SimpleResult) -> ExecutiveHeroSpec:
    headline, severity = _simple_headline(res)
    p = res.params
    return ExecutiveHeroSpec(
        headline=headline,
        severity=severity,
        status_label=_status_label(severity),
        metrics=(
            HeroMetricSpec(
                "Окупаемость",
                format_kpi_payback(res.payback_months),
            ),
            HeroMetricSpec(
                format_npv_kpi_label(),
                format_kpi_npv_compact(res.npv),
                f"за {p.horizon_months // 12} лет",
            ),
            HeroMetricSpec(
                "IRR",
                format_kpi_irr(res.irr),
            ),
            HeroMetricSpec(
                "Прибыль/мес",
                format_kpi_npv_compact(res.avg_profit_month),
                f"маржа {format_kpi_margin_ratio(res.margin)}",
            ),
        ),
        context_line=(
            f"Инвестиции {format_kpi_npv_compact(p.total_investment)} · "
            f"средняя выручка {format_kpi_npv_compact(res.avg_revenue_month)}/мес"
        ),
    )


def build_pro_executive_hero_spec(res: ProResult) -> ExecutiveHeroSpec:
    verdict = build_executive_verdict_spec(res)
    p = res.params

    optim_label = format_kpi_payback(res.payback_optim)
    if should_render_pessimistic_payback_success(res):
        fourth = HeroMetricSpec(
            "Диапазон окупаемости",
            f"{optim_label} — {format_kpi_payback(res.payback_pessim)}",
            "опт. — песс.",
        )
    else:
        fourth = HeroMetricSpec(
            "Диапазон окупаемости",
            f"{optim_label} — не окупается",
            f"пессимистично за {p.horizon_months // 12} лет",
        )

    context = verdict.bullets[0] if verdict.bullets else ""

    return ExecutiveHeroSpec(
        headline=verdict.headline,
        severity=verdict.severity,
        status_label=_status_label(verdict.severity),
        metrics=(
            HeroMetricSpec(
                "Окупаемость",
                format_kpi_payback(res.payback_months),
            ),
            HeroMetricSpec(
                format_npv_kpi_label(),
                format_kpi_npv_compact(res.npv),
                f"за {p.horizon_months // 12} лет",
            ),
            HeroMetricSpec(
                "IRR",
                format_kpi_irr(res.irr),
            ),
            fourth,
        ),
        context_line=context,
    )


def render_executive_hero_html(spec: ExecutiveHeroSpec) -> str:
    metrics_html = "".join(
        (
            f'<div class="wb-hero-metric wb-hero-metric--{i}">'
            f'<div class="wb-hero-metric-label">{html.escape(metric.label)}</div>'
            f'<div class="wb-hero-metric-value">{html.escape(metric.value)}</div>'
            + (
                f'<div class="wb-hero-metric-hint">{html.escape(metric.hint)}</div>'
                if metric.hint
                else ""
            )
            + "</div>"
        )
        for i, metric in enumerate(spec.metrics)
    )
    context_html = (
        f'<p class="wb-hero-context">{html.escape(spec.context_line)}</p>'
        if spec.context_line
        else ""
    )
    return (
        f'<div class="wb-hero wb-hero--{html.escape(spec.severity)}">'
        f'<div class="wb-hero-top">'
        f'<span class="wb-hero-status">{html.escape(spec.status_label)}</span>'
        f'<h2 class="wb-hero-headline">{html.escape(spec.headline)}</h2>'
        f"</div>"
        f'<div class="wb-hero-metrics">{metrics_html}</div>'
        f"{context_html}"
        f"</div>"
    )
