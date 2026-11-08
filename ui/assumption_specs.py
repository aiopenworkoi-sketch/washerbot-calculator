from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from finance.taxes import TAX_MODEL_BASELINE_YEAR, TAX_MODEL_SIMPLIFIED_NOTE
from finance.tariffs import effective_tariffs, nv_coefficient, nv_mode_label
from finance.water_usage import water_usage_assumption_value
from data.catalogs import REGIONS, WASHER_CATALOG
from data.washer_access import get_washer_model, supports_extra_dryers
from finance.variable_costs import EXTRA_DRYER_RUNTIME_SEC_PER_WASH, extra_dryer_kwh_per_wash
from domain.results import ProResult
from ui.format_policies import format_kpi_cars_per_month, format_kpi_npv_compact
from ui.model_constants import format_npv_discount_rate_label
from ui.renderers import fmt_int, fmt_money_compact, fmt_ratio_pct
from ui.view_guards import (
    has_active_credit,
    has_visible_sensitivity,
    should_render_capacity_overload_advisory,
)


@dataclass(frozen=True)
class AssumptionRowSpec:
    label: str
    value: str
    note: str = ""
    risk_sensitive: bool = False


@dataclass(frozen=True)
class AssumptionSnapshotSpec:
    rows: Tuple[AssumptionRowSpec, ...]
    risk_notes: Tuple[str, ...]


def build_pro_assumption_snapshot(res: ProResult) -> AssumptionSnapshotSpec:
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    region = REGIONS[p.region_key]

    tariffs_used = effective_tariffs(
        region,
        water_supply_override=getattr(p, "water_supply_override", None),
        water_sewage_override=getattr(p, "water_sewage_override", None),
        elec_price_override=getattr(p, "elec_price_override", None),
    )
    nv_norm = bool(getattr(p, "nv_norm_enabled", False))
    nv_over = bool(getattr(p, "nv_over_enabled", False))
    nv_coef = nv_coefficient(norm_enabled=nv_norm, over_enabled=nv_over)

    rows: list[AssumptionRowSpec] = [
        AssumptionRowSpec(
            "Горизонт модели",
            f"{p.horizon_months} мес. ({p.horizon_months // 12} лет)",
            "все KPI и окупаемость считаются в этом окне",
        ),
        AssumptionRowSpec(
            "Налоговая модель",
            f"упрощённая, ориентир {TAX_MODEL_BASELINE_YEAR}",
            TAX_MODEL_SIMPLIFIED_NOTE,
            risk_sensitive=True,
        ),
        AssumptionRowSpec(
            "Сезонность трафика",
            "высокий сезон: ноябрь–май",
            "июнь–октябрь ниже среднего; профиль нормирован на среднее 1,0",
        ),
        AssumptionRowSpec(
            "Внутрисуточный профиль",
            "мойка 24/7, спад 01:00–06:00",
            "пик 17:00–18:00 — около 7,4 % суточного трафика в этот час",
        ),
        AssumptionRowSpec(
            "Ставка дисконтирования",
            format_npv_discount_rate_label(),
            "модельная ставка NPV (фиксирована в расчёте)",
            risk_sensitive=True,
        ),
        AssumptionRowSpec(
            "Средний чек",
            fmt_money_compact(res.avg_check),
            "взвешенный по программам мойки",
            risk_sensitive=True,
        ),
        AssumptionRowSpec(
            "Трафик",
            f"{p.cars_per_day_avg:.0f} авто/день/робот",
            f"~{format_kpi_cars_per_month(res.cars_per_month)} авто/мес (факт)",
            risk_sensitive=True,
        ),
        AssumptionRowSpec(
            "CAPEX / собственные",
            f"{fmt_money_compact(res.capex_total)} / {fmt_money_compact(res.own_funds)}",
            "единовременные инвестиции и equity",
        ),
        AssumptionRowSpec(
            "Сценарии трафика",
            f"×{p.scenario_pessim_factor:.2f} — ×{p.scenario_optim_factor:.2f}",
            "пессимистичный и оптимистичный множители",
            risk_sensitive=True,
        ),
        AssumptionRowSpec(
            "Регион / модель",
            f"{region.name} · {model.name} × {p.n_robots}",
            "тарифы и производительность",
        ),
        AssumptionRowSpec(
            "Тарифы (с НДС)",
            (
                f"вода {tariffs_used.water_supply:.2f} · водоотведение {tariffs_used.water_sewage:.2f} ₽/м³ · "
                f"электро {tariffs_used.elec_price:.2f} ₽/кВт·ч"
            ).replace(".", ","),
            "цены как в счёте, правятся в сайдбаре",
        ),
        AssumptionRowSpec(
            "НВ на ЦСВ",
            (
                f"{nv_mode_label(norm_enabled=nv_norm, over_enabled=nv_over)} · "
                f"{nv_coef:.1f} × {tariffs_used.water_sewage:.2f} = "
                f"{nv_coef * tariffs_used.water_sewage:.2f} ₽/м³ стоков"
            ).replace(".", ","),
            "п. 123(4) и п. 203 Правил № 644",
            risk_sensitive=nv_coef > 0,
        ),
        AssumptionRowSpec(
            "Оценочный расход воды, м³/сутки",
            water_usage_assumption_value(p.cars_per_day_avg, model.water_per_wash_l),
            (
                "превышает лимит <30 м³/сутки — проверьте применимость; без recycle и mix-факторов"
                if p.cars_per_day_avg * model.water_per_wash_l / 1000.0 > 30.0
                else "без recycle и mix-факторов"
            ),
            risk_sensitive=p.cars_per_day_avg * model.water_per_wash_l / 1000.0 > 30.0,
        ),
    ]

    if p.extra_dryers_enabled and supports_extra_dryers(p.model_code):
        extra_kwh = extra_dryer_kwh_per_wash(
            extra_dryers_enabled=True,
            model_code=p.model_code,
        )
        rows.append(
            AssumptionRowSpec(
                "Доп. сушки",
                f"+11 кВт мощности; +{extra_kwh:.3f} кВт·ч/мойку",
                (
                    f"усреднённо {EXTRA_DRYER_RUNTIME_SEC_PER_WASH:.0f} с работы на мойку; "
                    "учтены в мощности и электроэнергии; пропускная способность не корректировалась"
                ),
            )
        )

    if has_active_credit(p):
        rows.append(
            AssumptionRowSpec(
                "Кредит",
                f"{fmt_money_compact(p.credit_amount)} @ {fmt_ratio_pct(p.credit_rate_annual)}",
                f"срок {p.credit_term_months} мес.",
                risk_sensitive=True,
            )
        )

    if has_visible_sensitivity(res.sensitivity):
        top_factor, top_delta = max(res.sensitivity.items(), key=lambda x: x[1])
        rows.append(
            AssumptionRowSpec(
                "Главный драйвер NPV",
                top_factor,
                f"ΔNPV {fmt_ratio_pct(top_delta)} при +10%",
                risk_sensitive=True,
            )
        )

    capacity_note = (
        f"{res.capacity_binding_months} мес. с ограничением, "
        f"{fmt_int(res.annual_unserved_demand)} авто/год потеряно"
        if should_render_capacity_overload_advisory(res)
        else "ограничений мощности на горизонте нет"
    )
    rows.append(
        AssumptionRowSpec(
            "Мощность",
            "есть давление" if should_render_capacity_overload_advisory(res) else "без давления",
            capacity_note,
            risk_sensitive=should_render_capacity_overload_advisory(res),
        )
    )

    risk_notes = _build_risk_notes(res)
    return AssumptionSnapshotSpec(rows=tuple(rows), risk_notes=risk_notes)


def _build_risk_notes(res: ProResult) -> Tuple[str, ...]:
    p = res.params
    notes: list[str] = [
        "Результат — модельная оценка; фактические показатели зависят от рынка и исполнения.",
        f"NPV и IRR чувствительны к трафику, ценам и CAPEX; горизонт — {p.horizon_months} мес.",
    ]
    if should_render_capacity_overload_advisory(res):
        notes.append(
            "Часть спроса не обслуживается из‑за лимита мощности — выручка может быть завышена "
            "относительно реального потенциала без расширения."
        )
    if has_active_credit(p):
        notes.append(
            "График кредита и проценты заложены по введённым условиям; изменение ставки или срока "
            "пересчитывается только при смене параметров."
        )
    if np.mean(res.cars_per_month) > 0:
        notes.append(
            "Порог покрытия затрат — упрощённая оценка по средним месячным потокам."
        )
    return tuple(notes[:4])


def assumption_row_value(spec: AssumptionSnapshotSpec, label: str) -> str | None:
    for row in spec.rows:
        if row.label == label:
            return row.value
    return None


def render_assumption_snapshot_html(spec: AssumptionSnapshotSpec) -> str:
    rows_html = []
    for row in spec.rows:
        risk_cls = " wb-assumption-row--risk" if row.risk_sensitive else ""
        note_html = (
            f'<span class="wb-assumption-note">{row.note}</span>' if row.note else ""
        )
        rows_html.append(
            f'<div class="wb-assumption-row{risk_cls}">'
            f'<span class="wb-assumption-label">{row.label}</span>'
            f'<span class="wb-assumption-value">{row.value}</span>'
            f"{note_html}"
            f"</div>"
        )
    risks_html = "".join(
        f'<li class="wb-assumption-risk-item">{note}</li>' for note in spec.risk_notes
    )
    not_covered = (
        '<p class="wb-assumption-note" style="margin-top:10px">'
        '<b>Что не учтено:</b> налог на имущество и землю, взносы ИП «за себя», '
        'терминальная стоимость, инфляция тарифов. Тарифы и нормативы — на 2026 год; '
        'уточняются по счёту водоканала и энергосбыта.'
        '</p>'
    )
    return (
        f'<div class="wb-assumption-grid">{"".join(rows_html)}</div>'
        f'<ul class="wb-assumption-risks">{risks_html}</ul>'
        f'{not_covered}'
    )
