from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from domain.results import ProResult
from ui.display_fallbacks import has_finite_payback_months, is_missing_payback_months
from ui.format_policies import (
    format_kpi_irr,
    format_kpi_npv_compact,
    format_kpi_payback,
    format_scenario_cumulative_money,
)
from ui.renderers import fmt_int, fmt_ratio_pct
from ui.scenario_specs import ScenarioSummarySpec
from ui.ui_labels import UIClassNames
from ui.view_guards import (
    has_visible_sensitivity,
    should_render_capacity_overload_advisory,
    should_render_pessimistic_payback_success,
    should_render_pessimistic_payback_warning,
)
from ui.model_constants import format_npv_discount_rate_label


@dataclass(frozen=True)
class ExecutiveVerdictSpec:
    headline: str
    severity: str
    bullets: Tuple[str, ...]


@dataclass(frozen=True)
class ScenarioCardSpec:
    key: str
    label: str
    payback_text: str
    cumulative_text: str
    factor_label: str
    accent_class: str


@dataclass(frozen=True)
class CapacitySummarySpec:
    label: str
    value: str
    hint: str
    status: str


def build_executive_verdict_spec(res: ProResult) -> ExecutiveVerdictSpec:
    p = res.params
    horizon = p.horizon_months

    if res.npv > 0 and has_finite_payback_months(res.payback_months):
        if res.payback_months <= horizon and res.payback_months <= 36:
            headline = (
                f"Проект окупается за {format_kpi_payback(res.payback_months)} "
                f"с положительным NPV"
            )
            severity = "good"
        elif res.payback_months <= horizon:
            headline = (
                f"Проект окупается за {format_kpi_payback(res.payback_months)}; "
                f"NPV {format_kpi_npv_compact(res.npv)}"
            )
            severity = "info"
        else:
            headline = "NPV положительный, окупаемость за пределами горизонта модели"
            severity = "warn"
    elif is_missing_payback_months(res.payback_months) and res.npv <= 0:
        headline = "Проект не окупается на выбранном горизонте"
        severity = "bad"
    elif res.npv <= 0:
        headline = f"NPV отрицательный при ставке {format_npv_discount_rate_label()} — инвестиция не проходит порог"
        severity = "bad"
    else:
        headline = "Положительный NPV, срок окупаемости требует внимания"
        severity = "warn"

    bullets: list[str] = [
        f"NPV {format_kpi_npv_compact(res.npv)} · IRR {format_kpi_irr(res.irr)} · "
        f"окупаемость {format_kpi_payback(res.payback_months)}",
    ]

    if should_render_pessimistic_payback_success(res):
        bullets.append(
            f"Диапазон окупаемости: от {format_kpi_payback(res.payback_optim)} (оптимистично) "
            f"до {format_kpi_payback(res.payback_pessim)} (пессимистично)"
        )
    elif should_render_pessimistic_payback_warning(res):
        bullets.append(
            "Пессимистичный сценарий не окупается на горизонте — устойчивость ограничена"
        )

    if should_render_capacity_overload_advisory(res):
        bullets.append(
            f"Мощность: {res.capacity_binding_months} мес. с ограничением, "
            f"потеряно {fmt_int(res.annual_unserved_demand)} авто/год "
            f"({fmt_ratio_pct(res.annual_unserved_share)})"
        )
    else:
        bullets.append("Мощность не ограничивает обслуживание спроса на горизонте")

    if has_visible_sensitivity(res.sensitivity):
        top_factor, top_delta = max(res.sensitivity.items(), key=lambda x: x[1])
        bullets.append(
            f"Главный драйвер NPV: {top_factor} (+10% → ΔNPV {fmt_ratio_pct(top_delta)})"
        )

    return ExecutiveVerdictSpec(
        headline=headline,
        severity=severity,
        bullets=tuple(bullets[:4]),
    )


def render_executive_verdict_html(spec: ExecutiveVerdictSpec) -> str:
    bullet_html = "".join(
        f'<li class="wb-verdict-bullet">{item}</li>' for item in spec.bullets
    )
    return (
        f'<div class="{UIClassNames.CARD} wb-verdict wb-verdict--{spec.severity}">'
        f'<div class="wb-verdict-headline">{spec.headline}</div>'
        f'<ul class="wb-verdict-bullets">{bullet_html}</ul>'
        f"</div>"
    )


def build_pro_scenario_card_specs(
    scenario_specs: Tuple[ScenarioSummarySpec, ...],
) -> Tuple[ScenarioCardSpec, ...]:
    accent_by_key = {
        "pessim": "wb-scenario-card--pessim",
        "base": "wb-scenario-card--base",
        "optim": "wb-scenario-card--optim",
    }

    return tuple(
        ScenarioCardSpec(
            key=spec.key,
            label=spec.summary_label,
            payback_text=format_kpi_payback(spec.payback_months),
            cumulative_text=format_scenario_cumulative_money(spec.cumulative[-1]),
            factor_label=spec.factor_label,
            accent_class=accent_by_key.get(spec.key, ""),
        )
        for spec in scenario_specs
    )


def render_scenario_cards_html(cards: Tuple[ScenarioCardSpec, ...]) -> str:
    items = []
    for card in cards:
        items.append(
            f'<div class="wb-scenario-card {card.accent_class}">'
            f'<div class="wb-scenario-card-label">{card.label}</div>'
            f'<div class="wb-scenario-card-metric">'
            f'<span class="wb-scenario-card-kicker">Окупаемость</span>'
            f'<span class="wb-scenario-card-value">{card.payback_text}</span>'
            f"</div>"
            f'<div class="wb-scenario-card-metric">'
            f'<span class="wb-scenario-card-kicker">Накопленный поток</span>'
            f'<span class="wb-scenario-card-value">{card.cumulative_text}</span>'
            f"</div>"
            f'<div class="wb-scenario-card-factor">Трафик {card.factor_label}</div>'
            f"</div>"
        )
    return f'<div class="wb-scenario-cards-row">{"".join(items)}</div>'


def build_pro_capacity_summary_specs(res: ProResult) -> Tuple[CapacitySummarySpec, ...]:
    from ui.format_policies import format_peak_load_percent

    p = res.params
    overload = should_render_capacity_overload_advisory(res)
    binding_status = "warn" if overload else "good"
    unserved_status = "warn" if res.annual_unserved_demand > 0 else "off"
    peak_text = format_peak_load_percent(res.peak_requested_utilization, style="pro")

    specs = [
        CapacitySummarySpec(
            "Месяцев с ограничением",
            f"{res.capacity_binding_months} / {p.horizon_months}",
            "спрос выше пропускной способности",
            binding_status,
        ),
        CapacitySummarySpec(
            "Необслуженный спрос (1-й год)",
            f"{fmt_int(res.annual_unserved_demand)} авто",
            f"{fmt_ratio_pct(res.annual_unserved_share)} от запроса",
            unserved_status,
        ),
        CapacitySummarySpec(
            "Пиковая запрошенная загрузка",
            peak_text,
            "относительно месячной пропускной способности",
            "warn" if overload else "off",
        ),
        CapacitySummarySpec(
            "Пиковая часовая загрузка",
            format_peak_load_percent(res.peak_hour_utilization, style="pro"),
            "в самый нагруженный час (17:00–18:00), мойка работает 24/7",
            "warn" if res.peak_hour_utilization >= 0.85 else "off",
        ),
    ]
    if res.peak_unserved_month > 0:
        specs.append(
            CapacitySummarySpec(
                "Пик потерь",
                f"месяц {res.peak_unserved_month}",
                "максимум неудовлетворённого спроса",
                "warn",
            )
        )
    if res.zero_capacity_positive_demand_months > 0:
        specs.append(
            CapacitySummarySpec(
                "Нулевая мощность при спросе",
                str(res.zero_capacity_positive_demand_months),
                "мес. с capacity = 0 и спросом > 0",
                "bad",
            )
        )
    return tuple(specs)
