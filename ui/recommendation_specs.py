from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

from ui.display_fallbacks import has_finite_irr, is_missing_payback_months
from ui.view_guards import (
    has_visible_sensitivity,
    should_render_capacity_overload_advisory,
    should_render_high_debt_credit_advisory,
    should_render_pessimistic_payback_success,
    should_render_pessimistic_payback_warning,
    should_show_peak_unserved_month,
    should_show_zero_capacity_positive_demand_months,
)

import streamlit as st

from data.catalogs import WASHER_CATALOG
from data.washer_access import get_washer_model
from domain.results import ProResult, SimpleResult
from ui.format_policies import (
    format_kpi_margin_ratio,
    format_kpi_npv_compact,
    format_kpi_payback,
    format_peak_load_percent,
)
from ui.renderers import (
    fmt_int,
    fmt_pct,
    fmt_ratio_pct,
)
from ui.ui_labels import ADVISORY_CSS_MAP, ADVISORY_ICON_MAP


@dataclass(frozen=True)
class AdvisoryItemSpec:
    key: str
    severity: Literal["good", "bad", "warn", "info"]
    text: str
    icon: str | None = None


def build_simple_payback_hint_spec(res: SimpleResult) -> AdvisoryItemSpec:
    if is_missing_payback_months(res.payback_months):
        return AdvisoryItemSpec(
            key="payback",
            severity="warn",
            text=(
                "<b>Проект не окупается</b> на выбранном горизонте. "
                "Попробуйте увеличить трафик, поднять цены или сократить инвестиции."
            ),
        )
    if res.payback_months > 60:
        return AdvisoryItemSpec(
            key="payback",
            severity="warn",
            text=(
                f"Срок окупаемости <b>{format_kpi_payback(res.payback_months)}</b> "
                "превышает 5 лет. Рассмотрите снижение CAPEX или увеличение трафика."
            ),
        )
    if res.payback_months < 24:
        return AdvisoryItemSpec(
            key="payback",
            severity="good",
            text=(
                f"Отличный срок окупаемости — <b>{format_kpi_payback(res.payback_months)}</b>. "
                "Проект финансово привлекателен."
            ),
        )
    return AdvisoryItemSpec(
        key="payback",
        severity="info",
        text=(
            f"Срок окупаемости — <b>{format_kpi_payback(res.payback_months)}</b>. "
            "Это нормальный показатель для автомоек."
        ),
    )


def build_simple_load_hint_spec(res: SimpleResult) -> AdvisoryItemSpec | None:
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    max_cars_day = model.cars_per_hour * 24
    load_pct = p.cars_per_day_avg / max_cars_day
    if load_pct < 0.15:
        return AdvisoryItemSpec(
            key="load",
            severity="info",
            text=(
                f"Текущая загрузка робота — <b>{fmt_ratio_pct(load_pct, decimals=0)}</b> "
                f"от теоретического максимума. Есть запас по росту трафика до "
                f"{int(max_cars_day * 0.5)} авто/день/робот."
            ),
        )
    if load_pct > 0.7:
        return AdvisoryItemSpec(
            key="load",
            severity="warn",
            text=(
                f"Загрузка <b>{fmt_ratio_pct(load_pct, decimals=0)}</b> близка к пределу. "
                "Рассмотрите установку дополнительного робота."
            ),
        )
    return None


def build_simple_capacity_hint_spec(res: SimpleResult) -> AdvisoryItemSpec | None:
    if not should_render_capacity_overload_advisory(res):
        return None

    p = res.params
    peak_load_text = format_peak_load_percent(res.peak_requested_utilization, style="simple")
    peak_month_text = (
        f" Пик неудовлетворённого спроса — месяц <b>{res.peak_unserved_month}</b>."
        if should_show_peak_unserved_month(res.peak_unserved_month) else ""
    )
    zero_cap_text = (
        f" Месяцев с нулевой capacity и положительным спросом: "
        f"<b>{res.zero_capacity_positive_demand_months}</b>."
        if should_show_zero_capacity_positive_demand_months(res.zero_capacity_positive_demand_months) else ""
    )
    return AdvisoryItemSpec(
        key="capacity_overload",
        severity="warn",
        text=(
            f"<b>Перегруз capacity:</b> в <b>{res.capacity_binding_months}</b> из "
            f"<b>{p.horizon_months}</b> месяцев спрос выше технической пропускной способности. "
            f"Необслуженный спрос за 1-й год — <b>{fmt_int(res.annual_unserved_demand)}</b> авто "
            f"(<b>{fmt_ratio_pct(res.annual_unserved_share)}</b> от запрошенного). "
            f"Пиковая запрошенная загрузка — {peak_load_text}, "
            f"в самый нагруженный час — {format_peak_load_percent(res.peak_hour_utilization, style='simple')}."
            f"{peak_month_text}{zero_cap_text} "
            "Расчёт ограничивает фактический поток по правилу served = min(demand, capacity)."
        ),
    )


def build_simple_hint_specs(res: SimpleResult) -> Tuple[AdvisoryItemSpec, ...]:
    specs: list[AdvisoryItemSpec] = [build_simple_payback_hint_spec(res)]
    load_spec = build_simple_load_hint_spec(res)
    if load_spec is not None:
        specs.append(load_spec)
    capacity_spec = build_simple_capacity_hint_spec(res)
    if capacity_spec is not None:
        specs.append(capacity_spec)
    return tuple(specs)


def build_pro_recommendation_specs(res: ProResult) -> Tuple[AdvisoryItemSpec, ...]:
    p = res.params
    specs: list[AdvisoryItemSpec] = []

    if is_missing_payback_months(res.payback_months):
        specs.append(AdvisoryItemSpec(
            key="payback",
            severity="bad",
            text="Проект не окупается на горизонте — пересмотрите модель.",
        ))
    elif res.payback_months < 30:
        specs.append(AdvisoryItemSpec(
            key="payback",
            severity="good",
            text=f"Отличная окупаемость — {format_kpi_payback(res.payback_months)}.",
        ))
    elif res.payback_months > 60:
        specs.append(AdvisoryItemSpec(
            key="payback",
            severity="warn",
            text=(
                f"Длинная окупаемость ({format_kpi_payback(res.payback_months)}). "
                "Рассмотрите снижение CAPEX или увеличение трафика."
            ),
        ))
    else:
        specs.append(AdvisoryItemSpec(
            key="payback",
            severity="info",
            text=f"Окупаемость в норме — {format_kpi_payback(res.payback_months)}.",
        ))

    if res.npv > 0 and has_finite_irr(res.irr) and res.irr > 0.20:
        specs.append(AdvisoryItemSpec(
            key="npv_irr",
            severity="good",
            text=(
                f"NPV положительный ({format_kpi_npv_compact(res.npv)}), "
                f"IRR {fmt_pct(res.irr)} — проект финансово привлекателен."
            ),
        ))
    elif res.npv < 0:
        specs.append(AdvisoryItemSpec(
            key="npv_irr",
            severity="bad",
            text=(
                f"NPV отрицательный ({format_kpi_npv_compact(res.npv)}) — "
                "проект уничтожает стоимость при ставке 18%."
            ),
        ))

    if res.margin_net < 0.10:
        specs.append(AdvisoryItemSpec(
            key="margin",
            severity="warn",
            text=(
                f"Низкая чистая маржа ({format_kpi_margin_ratio(res.margin_net)}). "
                "Проверьте структуру OPEX и цены."
            ),
        ))
    elif res.margin_net > 0.25:
        specs.append(AdvisoryItemSpec(
            key="margin",
            severity="good",
            text=f"Высокая маржа ({format_kpi_margin_ratio(res.margin_net)}) — есть запас прочности.",
        ))

    if should_render_pessimistic_payback_success(res):
        specs.append(AdvisoryItemSpec(
            key="scenario_pessim",
            severity="good",
            text=(
                f"Даже в пессимистичном сценарии (×{p.scenario_pessim_factor:.2f}) "
                f"проект окупается за {format_kpi_payback(res.payback_pessim)}."
            ),
        ))
    elif should_render_pessimistic_payback_warning(res):
        specs.append(AdvisoryItemSpec(
            key="scenario_pessim",
            severity="warn",
            text=(
                "В пессимистичном сценарии проект не окупается — "
                "высокий риск при снижении трафика."
            ),
        ))

    if should_render_high_debt_credit_advisory(res):
        debt_ratio = res.params.credit_amount / res.capex_total if res.capex_total > 0 else 0
        specs.append(AdvisoryItemSpec(
            key="credit_debt",
            severity="warn",
            text=f"Доля заёмных средств — {format_kpi_margin_ratio(debt_ratio)}. Высокая долговая нагрузка.",
        ))

    if has_visible_sensitivity(res.sensitivity):
        top_factor = max(res.sensitivity.items(), key=lambda x: x[1])
        specs.append(AdvisoryItemSpec(
            key="sensitivity_top",
            severity="info",
            text=(
                f"Самый влиятельный параметр — <b>{top_factor[0]}</b> "
                f"(меняет NPV на {fmt_ratio_pct(top_factor[1])} при +10%)."
            ),
        ))

    if should_render_capacity_overload_advisory(res):
        peak_text = format_peak_load_percent(res.peak_requested_utilization, style="pro")
        specs.append(AdvisoryItemSpec(
            key="capacity_overload",
            severity="warn",
            text=(
                f"Перегруз capacity: <b>{res.capacity_binding_months}</b> из "
                f"<b>{p.horizon_months}</b> месяцев спрос выше пропускной способности. "
                f"Необслуженный спрос за 1-й год — <b>{fmt_int(res.annual_unserved_demand)}</b> авто "
                f"(<b>{fmt_ratio_pct(res.annual_unserved_share)}</b>). "
                f"Пиковая запрошенная загрузка — <b>{peak_text}</b>."
                + (
                    f" Пик неудовлетворённого спроса — месяц <b>{res.peak_unserved_month}</b>."
                    if should_show_peak_unserved_month(res.peak_unserved_month) else ""
                )
            ),
        ))

    return tuple(specs)


def render_advisory_items(specs: Tuple[AdvisoryItemSpec, ...]) -> None:
    for spec in specs:
        css = ADVISORY_CSS_MAP[spec.severity]
        icon = spec.icon if spec.icon is not None else ADVISORY_ICON_MAP[spec.severity]
        prefix = f"{icon} " if icon else ""
        st.markdown(
            f'<div class="{css}">{prefix}{spec.text}</div>',
            unsafe_allow_html=True,
        )


def advisory_item_to_dict(spec: AdvisoryItemSpec) -> dict:
    return {
        "key": spec.key,
        "severity": spec.severity,
        "text": spec.text,
        "icon": spec.icon if spec.icon is not None else ADVISORY_ICON_MAP[spec.severity],
    }
