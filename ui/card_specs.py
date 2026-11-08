from __future__ import annotations

from typing import Tuple

import numpy as np

from data.catalogs import REGIONS, WASHER_CATALOG
from data.washer_access import get_washer_model
from domain.results import ProResult, SimpleResult
from ui.format_policies import (
    format_kpi_cars_per_month,
    format_kpi_irr,
    format_kpi_margin_ratio,
    format_kpi_npv_compact,
    format_kpi_payback_compact,
    kpi_irr_status,
    kpi_npv_status,
    kpi_payback_status,
)
from ui.kpi_cards import MetricCardSpec, render_metric_cards
from ui.renderers import (
    BRAND,
    fmt_money,
    fmt_money_compact,
    fmt_percent_value,
    fmt_ratio_pct,
    fmt_volume_m3,
)
from ui.ui_labels import UIClassNames
from ui.model_constants import format_npv_kpi_label


def build_simple_kpi_card_specs(res: SimpleResult) -> Tuple[MetricCardSpec, ...]:
    p = res.params
    payback_status = kpi_payback_status(res.payback_months)
    margin_status = "good" if res.margin > 0.25 else "warn" if res.margin > 0.10 else "bad"
    npv_status = kpi_npv_status(res.npv)
    irr_status = kpi_irr_status(res.irr)

    return (
        MetricCardSpec(
            "Срок окупаемости",
            format_kpi_payback_compact(res.payback_months),
            f"при инвестициях {format_kpi_npv_compact(p.total_investment)}",
            payback_status,
            "primary",
        ),
        MetricCardSpec(
            "Прибыль/мес (среднее)",
            format_kpi_npv_compact(res.avg_profit_month),
            f"маржа {format_kpi_margin_ratio(res.margin)}",
            margin_status,
            "primary",
        ),
        MetricCardSpec(
            format_npv_kpi_label(),
            format_kpi_npv_compact(res.npv),
            f"за {p.horizon_months // 12} лет",
            npv_status,
            "secondary",
        ),
        MetricCardSpec(
            "IRR (годовая)",
            format_kpi_irr(res.irr),
            "внутренняя норма доходности",
            irr_status,
        ),
        MetricCardSpec("Выручка/мес", format_kpi_npv_compact(res.avg_revenue_month), "среднее"),
        MetricCardSpec("Авто/мес", format_kpi_cars_per_month(res.cars_per_month), f"× {p.n_robots} робот"),
        MetricCardSpec(
            "Выручка за период",
            format_kpi_npv_compact(res.total_revenue),
            f"{p.horizon_months} мес",
        ),
        MetricCardSpec(
            "Прибыль за период",
            format_kpi_npv_compact(res.total_profit),
            f"{p.horizon_months} мес",
        ),
    )


def build_pro_kpi_card_specs(res: ProResult) -> Tuple[MetricCardSpec, ...]:
    p = res.params
    payback_status = kpi_payback_status(res.payback_months)
    margin_status = "good" if res.margin_net > 0.20 else "warn" if res.margin_net > 0.08 else "bad"
    npv_status = kpi_npv_status(res.npv)
    irr_status = kpi_irr_status(res.irr)

    return (
        MetricCardSpec(
            "Окупаемость",
            format_kpi_payback_compact(res.payback_months),
            f"при {format_kpi_npv_compact(res.own_funds)} собств.",
            payback_status,
            "primary",
        ),
        MetricCardSpec(
            format_npv_kpi_label(),
            format_kpi_npv_compact(res.npv),
            f"за {p.horizon_months // 12} лет",
            npv_status,
            "primary",
        ),
        MetricCardSpec(
            "IRR годовая",
            format_kpi_irr(res.irr),
            "внутр. норма доходности",
            irr_status,
            "secondary",
        ),
        MetricCardSpec(
            "Маржа чистая",
            format_kpi_margin_ratio(res.margin_net),
            f"EBITDA {format_kpi_margin_ratio(res.margin_ebitda)}",
            margin_status,
        ),
        MetricCardSpec("Выручка/мес", format_kpi_npv_compact(res.avg_revenue_month), "среднее"),
        MetricCardSpec("EBITDA/мес", format_kpi_npv_compact(res.avg_ebitda_month), "до налогов и %"),
        MetricCardSpec("Прибыль/мес", format_kpi_npv_compact(res.avg_profit_month), "после налогов"),
        MetricCardSpec(
            "Авто/мес",
            format_kpi_cars_per_month(res.cars_per_month),
            f"× {p.n_robots} робот",
        ),
    )


def build_pro_credit_card_specs(res: ProResult) -> Tuple[MetricCardSpec, ...]:
    p = res.params
    total_interest = float(np.sum(res.credit_interest_month))
    overpay_pct = (total_interest / p.credit_amount * 100) if p.credit_amount > 0 else 0
    return (
        MetricCardSpec(
            "Сумма кредита",
            fmt_money_compact(p.credit_amount),
            f"@ {fmt_ratio_pct(p.credit_rate_annual)} годовых",
        ),
        MetricCardSpec(
            "Переплата по %",
            fmt_money_compact(total_interest),
            f"{fmt_percent_value(overpay_pct)} от тела",
        ),
        MetricCardSpec(
            "Платёж/мес (средн.)",
            fmt_money_compact(np.mean(res.credit_principal_month + res.credit_interest_month)),
            f"срок {p.credit_term_months} мес",
        ),
    )


def build_pro_ecology_card_specs(res: ProResult) -> Tuple[MetricCardSpec, ...]:
    p = res.params
    return (
        MetricCardSpec(
            "Экономия воды/год",
            fmt_volume_m3(res.water_saved_m3_year),
            f"{fmt_ratio_pct(p.eco_water_recycle_pct, decimals=0)} оборотной воды",
            "good" if p.eco_water_recycle_pct > 0 else "off",
        ),
        MetricCardSpec(
            "Экономия на воде/год",
            fmt_money_compact(res.water_cost_saving_rub_year),
            "снижение OPEX",
            "good" if res.water_cost_saving_rub_year > 0 else "off",
        ),
        MetricCardSpec(
            "Доплата за биохимию/год",
            fmt_money_compact(res.chem_extra_cost_year),
            "+15% к стоимости" if p.eco_chem_premium else "не используется",
            "warn" if p.eco_chem_premium else "off",
        ),
    )


def _config_segment_html(parts: list[str]) -> str:
    return (
        '<div class="wb-config-row">'
        + "".join(f'<span class="wb-config-segment">{part}</span>' for part in parts)
        + "</div>"
    )


def build_simple_config_card_html(res: SimpleResult) -> str:
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    region = REGIONS[p.region_key]
    row1 = _config_segment_html([
        f"<span class='wb-config-kicker'>Модель</span> <b>{model.name}</b> × {p.n_robots} шт.",
        f"<span class='wb-config-kicker'>Регион</span> <b>{region.name}</b>",
    ])
    row2 = _config_segment_html([
        f"<span class='wb-config-kicker'>Инвестиции</span> <b>{fmt_money_compact(p.total_investment)}</b>",
        f"<span class='wb-config-kicker'>Трафик</span> {p.cars_per_day_avg:.0f} авто/день/робот",
        f"<span class='wb-config-kicker'>Средний чек</span> <b>{fmt_money(res.avg_check)}</b>",
    ])
    return (
        f'<div class="{UIClassNames.CARD} {UIClassNames.CONFIG_SUMMARY} wb-surface-secondary">'
        f'<div class="wb-config-title">Конфигурация</div>'
        f'<div class="wb-config-body">{row1}{row2}</div></div>'
    )


def build_pro_config_card_html(res: ProResult) -> str:
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    region = REGIONS[p.region_key]
    credit_part = (
        f"<span class='wb-config-kicker'>Кредит</span> "
        f"<b>{fmt_money_compact(p.credit_amount)}</b> @ {fmt_ratio_pct(p.credit_rate_annual)}"
        if p.use_credit else ""
    )
    row1 = _config_segment_html([
        f"<span class='wb-config-kicker'>Модель</span> <b>{model.name}</b> × {p.n_robots}",
        f"<span class='wb-config-kicker'>Регион</span> <b>{region.name}</b>",
    ])
    capex_parts = [
        f"<span class='wb-config-kicker'>CAPEX</span> <b>{fmt_money_compact(res.capex_total)}</b>",
        f"<span class='wb-config-kicker'>Собств.</span> <b>{fmt_money_compact(res.own_funds)}</b>",
    ]
    if credit_part:
        capex_parts.append(credit_part)
    row2 = _config_segment_html(capex_parts)
    row3 = _config_segment_html([
        f"<span class='wb-config-kicker'>Трафик</span> {p.cars_per_day_avg:.0f} авто/день/робот",
        f"<span class='wb-config-kicker'>Средний чек</span> <b>{fmt_money(res.avg_check)}</b>",
    ])
    return (
        f'<div class="{UIClassNames.CARD} {UIClassNames.CONFIG_SUMMARY} wb-surface-secondary">'
        f'<div class="wb-config-title">Конфигурация проекта</div>'
        f'<div class="wb-config-body">{row1}{row2}{row3}</div></div>'
    )


def metric_card_to_dict(spec: MetricCardSpec) -> dict:
    return {
        "label": spec.label,
        "value": spec.value,
        "hint": spec.hint,
        "status": spec.status,
    }
