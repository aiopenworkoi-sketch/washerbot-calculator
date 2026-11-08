from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple

from data.catalogs import REGIONS, WASHER_CATALOG
from data.washer_access import get_washer_model
from domain.results import ProResult, SimpleResult
from ui.model_display import format_model_config_power_line
from finance.water_discharge import water_discharge_profile_label
from finance.water_usage import (
    is_typical_lt30_profile_exceeded,
    water_usage_assumption_value,
)
from finance.taxes import TAX_MODEL_BASELINE_YEAR, TAX_MODEL_SIMPLIFIED_NOTE
from ui.assumption_specs import build_pro_assumption_snapshot
from ui.card_specs import (
    build_pro_kpi_card_specs,
    build_simple_kpi_card_specs,
    metric_card_to_dict,
)
from ui.chart_specs import build_sensitivity_takeaway, rank_sensitivity_items
from ui.compare_specs import (
    CompareVariantSnapshot,
    ProComparisonSpec,
    build_pro_comparison_specs,
)
from ui.decision_specs import (
    build_executive_verdict_spec,
    build_pro_capacity_summary_specs,
    build_pro_scenario_card_specs,
)
from ui.hero_specs import (
    build_pro_executive_hero_spec,
    build_simple_executive_hero_spec,
)
from ui.display_fallbacks import (
    has_finite_irr,
    has_finite_payback_months,
    is_missing_numeric,
    is_missing_payback_months,
)
from ui.format_policies import (
    format_kpi_irr,
    format_kpi_npv_compact,
    format_kpi_payback,
)
from ui.memo_specs import build_pro_investment_memo
from ui.model_constants import format_npv_discount_rate_label
from ui.presentation_metrics import compute_pro_break_even_estimate
from ui.recommendation_specs import build_simple_hint_specs
from ui.renderers import fmt_money, fmt_money_compact
from ui.report_text import (
    format_presentation_multiplier,
    format_presentation_ratio_pct,
    format_report_int,
    format_report_money_per_unit,
    humanize_tax_regime,
    sanitize_report_texts,
    sanitize_report_visible_text,
)
from ui.scenario_specs import build_pro_scenario_summary_specs
from ui.text_fallbacks import coerce_visible_text


@dataclass(frozen=True)
class ReportKpiRow:
    label: str
    value: str
    hint: str = ""


@dataclass(frozen=True)
class ReportTableRow:
    cells: Tuple[str, ...]


@dataclass(frozen=True)
class SingleInvestmentReportSpec:
    title: str
    subtitle: str
    report_type: str
    generated_at: str
    config_lines: Tuple[str, ...]
    executive_headline: str
    executive_bullets: Tuple[str, ...]
    kpi_rows: Tuple[ReportKpiRow, ...]
    assumption_rows: Tuple[Tuple[str, str, str], ...]
    risk_notes: Tuple[str, ...]
    memo_headline: str
    memo_groups: Tuple[Tuple[str, Tuple[str, ...]], ...]
    memo_actions: Tuple[str, ...]
    scenario_rows: Tuple[Tuple[str, str, str, str], ...]
    sensitivity_bullets: Tuple[str, ...]
    break_even_rows: Tuple[ReportKpiRow, ...]
    break_even_note: str
    capacity_rows: Tuple[ReportKpiRow, ...]
    detail_rows: Tuple[ReportKpiRow, ...]
    disclaimers: Tuple[str, ...]
    status_label: str = ""
    status_severity: str = "info"
    mode_label: str = "Pro"


@dataclass(frozen=True)
class ComparisonVariantLine:
    variant_id: str
    label: str
    is_baseline: bool


@dataclass(frozen=True)
class ComparisonReportSpec:
    title: str
    subtitle: str
    report_type: str
    generated_at: str
    baseline_id: str
    variants: Tuple[ComparisonVariantLine, ...]
    baseline_label: str
    factual_bullets: Tuple[str, ...]
    narrative_bullets: Tuple[str, ...]
    comparison: ProComparisonSpec
    chart_summary_lines: Tuple[str, ...]
    disclaimers: Tuple[str, ...]


COMPARISON_CSV_COLUMNS: Tuple[str, ...] = (
    "report_type",
    "generated_at",
    "variant_id",
    "label",
    "is_baseline",
    "payback_months",
    "npv",
    "irr",
    "margin_net",
    "margin_ebitda",
    "capex_total",
    "own_funds",
    "avg_revenue_month",
    "avg_profit_month",
    "avg_ebitda_month",
    "annual_unserved_share",
    "payback_pessim",
    "payback_optim",
)


def report_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def report_file_timestamp() -> str:
    # UTC, чтобы имя файла не расходилось с ZIP-пакетом и полем generated_at
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _sanitize_kpi_row(row: ReportKpiRow) -> ReportKpiRow:
    return ReportKpiRow(
        sanitize_report_visible_text(row.label),
        sanitize_report_visible_text(row.value),
        sanitize_report_visible_text(row.hint),
    )


def _sanitize_kpi_rows(rows: Tuple[ReportKpiRow, ...]) -> Tuple[ReportKpiRow, ...]:
    return tuple(_sanitize_kpi_row(row) for row in rows)


def _finalize_single_investment_spec(
    spec: SingleInvestmentReportSpec,
) -> SingleInvestmentReportSpec:
    return replace(
        spec,
        config_lines=sanitize_report_texts(spec.config_lines),
        executive_headline=sanitize_report_visible_text(spec.executive_headline),
        executive_bullets=sanitize_report_texts(spec.executive_bullets),
        kpi_rows=_sanitize_kpi_rows(spec.kpi_rows),
        assumption_rows=tuple(
            (
                sanitize_report_visible_text(label),
                sanitize_report_visible_text(value),
                sanitize_report_visible_text(note),
            )
            for label, value, note in spec.assumption_rows
        ),
        risk_notes=sanitize_report_texts(spec.risk_notes),
        memo_headline=sanitize_report_visible_text(spec.memo_headline),
        memo_groups=tuple(
            (sanitize_report_visible_text(title), sanitize_report_texts(items))
            for title, items in spec.memo_groups
        ),
        memo_actions=sanitize_report_texts(spec.memo_actions),
        scenario_rows=tuple(
            tuple(sanitize_report_visible_text(cell) for cell in row)
            for row in spec.scenario_rows
        ),
        sensitivity_bullets=sanitize_report_texts(spec.sensitivity_bullets),
        break_even_rows=_sanitize_kpi_rows(spec.break_even_rows),
        break_even_note=sanitize_report_visible_text(spec.break_even_note),
        capacity_rows=_sanitize_kpi_rows(spec.capacity_rows),
        detail_rows=_sanitize_kpi_rows(spec.detail_rows),
        disclaimers=sanitize_report_texts(spec.disclaimers),
        status_label=sanitize_report_visible_text(spec.status_label),
        status_severity=sanitize_report_visible_text(spec.status_severity),
        mode_label=sanitize_report_visible_text(spec.mode_label),
    )


def _finalize_simple_investment_spec(
    spec: SimpleInvestmentReportSpec,
) -> SimpleInvestmentReportSpec:
    return replace(
        spec,
        config_lines=sanitize_report_texts(spec.config_lines),
        verdict_headline=sanitize_report_visible_text(spec.verdict_headline),
        verdict_bullets=sanitize_report_texts(spec.verdict_bullets),
        assumption_rows=tuple(
            (
                sanitize_report_visible_text(label),
                sanitize_report_visible_text(value),
            )
            for label, value in spec.assumption_rows
        ),
        kpi_rows=_sanitize_kpi_rows(spec.kpi_rows),
        insight_bullets=sanitize_report_texts(spec.insight_bullets),
        breakdown_lines=sanitize_report_texts(spec.breakdown_lines),
        disclaimers=sanitize_report_texts(spec.disclaimers),
        status_label=sanitize_report_visible_text(spec.status_label),
        status_severity=sanitize_report_visible_text(spec.status_severity),
        mode_label=sanitize_report_visible_text(spec.mode_label),
    )


def _finalize_comparison_report_spec(
    spec: ComparisonReportSpec,
) -> ComparisonReportSpec:
    comparison = replace(
        spec.comparison,
        rows=tuple(
            replace(
                row,
                label=sanitize_report_visible_text(row.label),
                values=sanitize_report_texts(row.values),
                deltas=sanitize_report_texts(row.deltas),
            )
            for row in spec.comparison.rows
        ),
        narrative=sanitize_report_texts(spec.comparison.narrative),
    )
    return replace(
        spec,
        variants=tuple(
            replace(
                line,
                label=sanitize_report_visible_text(line.label),
            )
            for line in spec.variants
        ),
        baseline_label=sanitize_report_visible_text(spec.baseline_label),
        factual_bullets=sanitize_report_texts(spec.factual_bullets),
        narrative_bullets=sanitize_report_texts(spec.narrative_bullets),
        comparison=comparison,
        chart_summary_lines=sanitize_report_texts(spec.chart_summary_lines),
        disclaimers=sanitize_report_texts(spec.disclaimers),
    )


def _water_config_line(res: ProResult | SimpleResult) -> str:
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    estimate = water_usage_assumption_value(p.cars_per_day_avg, model.water_per_wash_l)
    if is_typical_lt30_profile_exceeded(
        profile=p.water_discharge_profile,
        cars_per_day=p.cars_per_day_avg,
        water_per_wash_l=model.water_per_wash_l,
    ):
        return f"Оценочный расход воды: {estimate} м³/сутки — превышен лимит 30 м³/сутки"
    return f"Оценочный расход воды: {estimate} м³/сутки"


def _config_lines(res: ProResult) -> Tuple[str, ...]:
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    region = REGIONS[p.region_key]
    lines = [
        f"Модель: {model.name} × {p.n_robots}",
        format_model_config_power_line(p.model_code, extra_dryers_enabled=p.extra_dryers_enabled),
        _tariffs_line(res),
        _nv_line(res),
        _water_config_line(res),
        f"Регион: {region.name}",
        f"CAPEX: {fmt_money_compact(res.capex_total)} · Собственные: {fmt_money_compact(res.own_funds)}",
        f"Трафик: {p.cars_per_day_avg:.0f} авто/день/робот · Средний чек: {fmt_money(res.avg_check)}",
        f"Горизонт: {p.horizon_months} мес. · Налоговый режим: {humanize_tax_regime(p.tax_regime)}",
    ]
    if p.use_credit:
        lines.append(
            f"Кредит: {fmt_money_compact(p.credit_amount)} @ {format_presentation_ratio_pct(p.credit_rate_annual)}"
        )
    return tuple(lines)


def _default_disclaimers() -> Tuple[str, ...]:
    return (
        "Отчёт сформирован автоматически на основе модельных допущений WasherBot Pro.",
        TAX_MODEL_SIMPLIFIED_NOTE,
        f"Налоговая модель: упрощённая, ориентир {TAX_MODEL_BASELINE_YEAR}.",
        "Показатели не являются инвестиционной рекомендацией или офертой.",
    )


def build_single_investment_report_spec(res: ProResult) -> SingleInvestmentReportSpec:
    hero = build_pro_executive_hero_spec(res)
    verdict = build_executive_verdict_spec(res)
    assumptions = build_pro_assumption_snapshot(res)
    memo = build_pro_investment_memo(res)
    scenarios = build_pro_scenario_summary_specs(res)
    scenario_cards = build_pro_scenario_card_specs(scenarios)
    be = compute_pro_break_even_estimate(res)

    kpi_rows = tuple(
        ReportKpiRow(card["label"], card["value"], card.get("hint", ""))
        for card in (metric_card_to_dict(c) for c in build_pro_kpi_card_specs(res))
    )

    assumption_rows = tuple(
        (row.label, row.value, row.note or "") for row in assumptions.rows
    )

    memo_groups = tuple(
        (group.title, tuple(item.text for item in group.items))
        for group in memo.groups
    )

    scenario_rows = tuple(
        (card.label, card.factor_label, card.payback_text, card.cumulative_text)
        for card in scenario_cards
    )

    sensitivity_items = rank_sensitivity_items(res.sensitivity)
    sensitivity_bullets: tuple[str, ...] = ()
    takeaway = build_sensitivity_takeaway(sensitivity_items)
    if takeaway:
        sensitivity_bullets = (takeaway,)
    if sensitivity_items:
        # Первые два параметра уже названы в сводной фразе — не дублируем их в списке.
        skip = 2 if takeaway else 0
        top_lines = tuple(
            f"{name}: ΔNPV {format_presentation_ratio_pct(delta)} при +10%"
            for name, delta in sensitivity_items[skip:skip + 3]
        )
        sensitivity_bullets = sensitivity_bullets + top_lines

    if be.operational_cars_per_month is None:
        be_value = "—"
        be_hint = "недостаточно данных для оценки"
    else:
        be_value = f"{format_report_int(be.operational_cars_per_month)} авто/мес"
        be_hint = (
            f"маржа {format_report_money_per_unit(be.unit_contribution_rub, suffix='₽/авто')} · "
            f"фикс. нагрузка {format_report_money_per_unit(be.monthly_fixed_ops_rub, suffix='₽/мес')}"
        )

    break_even_rows = (
        ReportKpiRow("Порог авто/мес", be_value, be_hint),
        ReportKpiRow(
            "Окупаемость капитала",
            format_kpi_payback(res.payback_months),
            f"NPV {format_kpi_npv_compact(res.npv)}",
        ),
        ReportKpiRow(
            "Фактический поток",
            f"{format_report_int(be.avg_actual_cars_per_month)} авто/мес",
            "среднее по горизонту",
        ),
    )

    capacity_rows = tuple(
        ReportKpiRow(spec.label, spec.value, spec.hint)
        for spec in build_pro_capacity_summary_specs(res)
    )

    detail_rows = (
        ReportKpiRow("Выручка за период", fmt_money_compact(res.total_revenue), ""),
        ReportKpiRow("Прибыль за период", fmt_money_compact(res.total_profit), ""),
        ReportKpiRow("Средний EBITDA/мес", fmt_money_compact(res.avg_ebitda_month), ""),
    )

    return _finalize_single_investment_spec(
        SingleInvestmentReportSpec(
        title="Инвестиционный отчёт — WasherBot Pro",
        subtitle="Один вариант конфигурации",
        report_type="pro_investment",
        generated_at=report_timestamp(),
        config_lines=_config_lines(res),
        executive_headline=verdict.headline,
        executive_bullets=verdict.bullets,
        kpi_rows=kpi_rows,
        assumption_rows=assumption_rows,
        risk_notes=assumptions.risk_notes,
        memo_headline=memo.headline,
        memo_groups=memo_groups,
        memo_actions=memo.next_actions,
        scenario_rows=scenario_rows,
        sensitivity_bullets=sensitivity_bullets,
        break_even_rows=break_even_rows,
        break_even_note=be.formula_note,
        capacity_rows=capacity_rows,
        detail_rows=detail_rows,
        disclaimers=_default_disclaimers(),
        status_label=hero.status_label,
        status_severity=hero.severity,
        mode_label="Pro",
        )
    )


def build_comparison_factual_bullets(
    snapshots: Sequence[CompareVariantSnapshot],
    *,
    baseline_id: str,
) -> Tuple[str, ...]:
    if len(snapshots) < 2:
        return ()

    bullets: list[str] = []
    baseline = next((s for s in snapshots if s.variant_id == baseline_id), snapshots[0])

    npv_leader = max(snapshots, key=lambda s: s.result.npv)
    bullets.append(
        f"Лучший NPV: «{npv_leader.label}» ({format_kpi_npv_compact(npv_leader.result.npv)})."
    )

    finite_irr = [s for s in snapshots if has_finite_irr(s.result.irr)]
    if finite_irr:
        irr_leader = max(finite_irr, key=lambda s: s.result.irr)
        bullets.append(
            f"Лучший IRR: «{irr_leader.label}» ({format_kpi_irr(irr_leader.result.irr)})."
        )

    finite_paybacks = [
        s for s in snapshots if has_finite_payback_months(s.result.payback_months)
    ]
    if finite_paybacks:
        fastest = min(finite_paybacks, key=lambda s: s.result.payback_months)
        bullets.append(
            f"Быстрее окупается: «{fastest.label}» "
            f"({format_kpi_payback(fastest.result.payback_months)})."
        )
    else:
        bullets.append("Ни один вариант не показывает окупаемость на горизонте модели.")

    equity_leader = min(snapshots, key=lambda s: s.result.own_funds)
    bullets.append(
        f"Меньше собственных средств: «{equity_leader.label}» "
        f"({format_kpi_npv_compact(equity_leader.result.own_funds)})."
    )

    capex_leader = min(snapshots, key=lambda s: s.result.capex_total)
    bullets.append(
        f"Меньший CAPEX: «{capex_leader.label}» "
        f"({format_kpi_npv_compact(capex_leader.result.capex_total)})."
    )

    capacity_cases = [s for s in snapshots if s.result.annual_unserved_share > 0]
    if capacity_cases:
        worst = max(capacity_cases, key=lambda s: s.result.annual_unserved_share)
        bullets.append(
            f"Наибольшее давление мощности: «{worst.label}» "
            f"({format_presentation_ratio_pct(worst.result.annual_unserved_share)} потерь спроса)."
        )
    else:
        bullets.append("По всем вариантам существенных ограничений мощности не выявлено.")

    leaders = {npv_leader.variant_id, equity_leader.variant_id, capex_leader.variant_id}
    if finite_irr:
        leaders.add(irr_leader.variant_id)
    if finite_paybacks:
        leaders.add(fastest.variant_id)
    if len(leaders) > 1:
        bullets.append(
            "Trade-offs смешанные: лидеры по NPV, IRR, окупаемости и equity могут различаться."
        )
    elif baseline.variant_id not in leaders and leaders:
        bullets.append(
            f"Сравнение относительно базового «{baseline.label}»; лидерство распределено между вариантами."
        )

    return tuple(bullets[:8])


def _chart_summary_lines(spec: ProComparisonSpec) -> Tuple[str, ...]:
    lines: list[str] = []
    for snapshot in spec.variants:
        payback = snapshot.result.payback_months
        if has_finite_payback_months(payback):
            payback_text = format_kpi_payback(payback)
        else:
            payback_text = "не окупается"
        lines.append(
            f"«{snapshot.label}»: NPV {format_kpi_npv_compact(snapshot.result.npv)}, "
            f"окупаемость {payback_text}"
        )
    return tuple(lines)


def build_comparison_report_spec(
    snapshots: Sequence[CompareVariantSnapshot],
    *,
    baseline_id: str,
) -> ComparisonReportSpec:
    snap_tuple = tuple(snapshots)
    comparison = build_pro_comparison_specs(snap_tuple, baseline_id=baseline_id)
    baseline = next(
        (s for s in snap_tuple if s.variant_id == comparison.baseline_id),
        snap_tuple[0],
    )
    variants = tuple(
        ComparisonVariantLine(
            s.variant_id,
            coerce_visible_text(s.label, default="Вариант") or "Вариант",
            s.variant_id == comparison.baseline_id,
        )
        for s in snap_tuple
    )
    disclaimers = _default_disclaimers() + (
        "Сравнение построено по зафиксированным конфигурациям; варианты могут отличаться "
        "не только одним параметром.",
        "Отсутствующие окупаемость/IRR в матрице отмечены как «—», в CSV — пустые значения.",
    )
    return _finalize_comparison_report_spec(
        ComparisonReportSpec(
        title="Отчёт сравнения конфигураций — WasherBot Pro",
        subtitle="Сопоставление инвестиционных вариантов",
        report_type="pro_comparison",
        generated_at=report_timestamp(),
        baseline_id=comparison.baseline_id,
        variants=variants,
        baseline_label=baseline.label,
        factual_bullets=build_comparison_factual_bullets(
            snap_tuple, baseline_id=comparison.baseline_id
        ),
        narrative_bullets=comparison.narrative,
        comparison=comparison,
        chart_summary_lines=_chart_summary_lines(comparison),
        disclaimers=disclaimers,
        )
    )


def _csv_cell(value: Any, *, payback: bool = False) -> str:
    if payback:
        if not has_finite_payback_months(float(value)):
            return ""
        return f"{float(value):.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (int, float)):
        if is_missing_numeric(float(value)):
            return ""
        return f"{float(value):.6f}".rstrip("0").rstrip(".")
    text = coerce_visible_text(value, default="")
    return text or ""


def build_comparison_matrix_rows(
    snapshots: Sequence[CompareVariantSnapshot],
    *,
    baseline_id: str,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for snapshot in snapshots:
        r = snapshot.result
        rows.append({
            "report_type": "comparison_matrix",
            "generated_at": report_timestamp(),
            "variant_id": snapshot.variant_id,
            "label": coerce_visible_text(snapshot.label, default="Вариант") or "Вариант",
            "is_baseline": "1" if snapshot.variant_id == baseline_id else "0",
            "payback_months": _csv_cell(r.payback_months, payback=True),
            "npv": _csv_cell(r.npv),
            "irr": _csv_cell(r.irr),
            "margin_net": _csv_cell(r.margin_net),
            "margin_ebitda": _csv_cell(r.margin_ebitda),
            "capex_total": _csv_cell(r.capex_total),
            "own_funds": _csv_cell(r.own_funds),
            "avg_revenue_month": _csv_cell(r.avg_revenue_month),
            "avg_profit_month": _csv_cell(r.avg_profit_month),
            "avg_ebitda_month": _csv_cell(r.avg_ebitda_month),
            "annual_unserved_share": _csv_cell(r.annual_unserved_share),
            "payback_pessim": _csv_cell(r.payback_pessim, payback=True),
            "payback_optim": _csv_cell(r.payback_optim, payback=True),
        })
    return rows


@dataclass(frozen=True)
class SimpleInvestmentReportSpec:
    title: str
    subtitle: str
    report_type: str
    generated_at: str
    config_lines: Tuple[str, ...]
    verdict_headline: str
    verdict_bullets: Tuple[str, ...]
    assumption_rows: Tuple[Tuple[str, str], ...]
    kpi_rows: Tuple[ReportKpiRow, ...]
    insight_bullets: Tuple[str, ...]
    breakdown_lines: Tuple[str, ...]
    disclaimers: Tuple[str, ...]
    status_label: str = ""
    status_severity: str = "info"
    mode_label: str = "Simple"


def _simple_config_lines(res: SimpleResult) -> Tuple[str, ...]:
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    region = REGIONS[p.region_key]
    return (
        f"Модель: {model.name} × {p.n_robots}",
        format_model_config_power_line(p.model_code, extra_dryers_enabled=p.extra_dryers_enabled),
        _tariffs_line(res),
        _nv_line(res),
        _water_config_line(res),
        f"Регион: {region.name}",
        f"Инвестиции: {fmt_money_compact(p.total_investment)}",
        f"Трафик: {p.cars_per_day_avg:.0f} авто/день/робот · Средний чек: {fmt_money(res.avg_check)}",
        f"Горизонт: {p.horizon_months} мес. · Налоговый режим: {humanize_tax_regime(p.tax_regime)}",
    )


def _simple_disclaimers() -> Tuple[str, ...]:
    return (
        "Отчёт сформирован автоматически на основе упрощённой модели WasherBot Simple.",
        TAX_MODEL_SIMPLIFIED_NOTE,
        f"NPV рассчитан при ставке дисконтирования {format_npv_discount_rate_label()}.",
        "Тарифы и нормативы — на 2026 год; уточняются по счёту водоканала и энергосбыта.",
        "Не учтено: налог на имущество и землю, взносы ИП «за себя», терминальная стоимость, инфляция тарифов.",
        "Показатели не являются инвестиционной рекомендацией или офертой.",
    )


def _simple_verdict_headline(res: SimpleResult) -> str:
    if is_missing_payback_months(res.payback_months):
        return "Проект не окупается на выбранном горизонте модели"
    if res.npv > 0:
        return (
            f"Окупаемость {format_kpi_payback(res.payback_months)}, "
            f"NPV {format_kpi_npv_compact(res.npv)}"
        )
    return f"NPV отрицательный ({format_kpi_npv_compact(res.npv)})"


def build_simple_investment_report_spec(res: SimpleResult) -> SimpleInvestmentReportSpec:
    hero = build_simple_executive_hero_spec(res)
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    hints = build_simple_hint_specs(res)
    insight_bullets = tuple(
        text
        for text in (
            sanitize_report_visible_text(coerce_visible_text(h.text, default="") or "")
            for h in hints
        )
        if text
    )

    breakdown_lines = tuple(
        f"{name}: {fmt_money_compact(value)}"
        for name, value in sorted(
            res.breakdown_year1.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]
    )

    assumption_rows = (
        ("Горизонт модели", f"{p.horizon_months} мес."),
        ("Ставка дисконтирования NPV", format_npv_discount_rate_label()),
        ("Налоговый режим", humanize_tax_regime(p.tax_regime)),
        ("Инвестиции", fmt_money_compact(p.total_investment)),
        (
            "Оценочный расход воды, м³/сутки",
            water_usage_assumption_value(p.cars_per_day_avg, model.water_per_wash_l),
        ),
    )

    kpi_rows = tuple(
        ReportKpiRow(card["label"], card["value"], card.get("hint", ""))
        for card in (metric_card_to_dict(c) for c in build_simple_kpi_card_specs(res))
    )

    verdict_bullets = (
        f"IRR {format_kpi_irr(res.irr)} · маржа {format_presentation_ratio_pct(res.margin)}",
        f"Средняя прибыль/мес: {fmt_money_compact(res.avg_profit_month)}",
        f"Выручка за период: {fmt_money_compact(res.total_revenue)}",
    )

    return _finalize_simple_investment_spec(
        SimpleInvestmentReportSpec(
        title="Инвестиционный отчёт — WasherBot Simple",
        subtitle="Упрощённая модель окупаемости",
        report_type="simple_investment",
        generated_at=report_timestamp(),
        config_lines=_simple_config_lines(res),
        verdict_headline=_simple_verdict_headline(res),
        verdict_bullets=verdict_bullets,
        assumption_rows=assumption_rows,
        kpi_rows=kpi_rows,
        insight_bullets=insight_bullets,
        breakdown_lines=breakdown_lines,
        disclaimers=_simple_disclaimers(),
        status_label=hero.status_label,
        status_severity=hero.severity,
        mode_label="Simple",
        )
    )


def _effective_tariffs_for(params) -> tuple[float, float, float]:
    from finance.tariffs import effective_tariffs

    region = REGIONS[params.region_key]
    tariffs = effective_tariffs(
        region,
        water_supply_override=getattr(params, "water_supply_override", None),
        water_sewage_override=getattr(params, "water_sewage_override", None),
        elec_price_override=getattr(params, "elec_price_override", None),
    )
    return tariffs.water_supply, tariffs.water_sewage, tariffs.elec_price


def _tariffs_line(res) -> str:
    """Строка с тарифами, которые реально пошли в расчёт (с НДС)."""
    supply, sewage, elec = _effective_tariffs_for(res.params)
    return (
        f"Тарифы (с НДС): вода {supply:.2f} · водоотведение {sewage:.2f} ₽/м³ · "
        f"электро {elec:.2f} ₽/кВт·ч"
    ).replace(".", ",")


def _nv_line(res) -> str:
    """Строка о плате за НВ на ЦСВ и сверхнормативный сброс."""
    from finance.tariffs import nv_coefficient, nv_mode_label

    p = res.params
    _, sewage, _ = _effective_tariffs_for(p)
    norm = bool(getattr(p, "nv_norm_enabled", False))
    over = bool(getattr(p, "nv_over_enabled", False))
    coef = nv_coefficient(norm_enabled=norm, over_enabled=over)
    label = nv_mode_label(norm_enabled=norm, over_enabled=over)
    return f"НВ на ЦСВ: {label} · {coef:.1f} × {sewage:.2f} = {coef * sewage:.2f} ₽/м³ стоков".replace(".", ",")
