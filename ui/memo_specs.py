from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from domain.results import ProResult
from ui.display_fallbacks import is_missing_payback_months
from ui.format_policies import format_kpi_npv_compact, format_kpi_payback
from ui.model_constants import format_npv_discount_rate_label
from ui.recommendation_specs import AdvisoryItemSpec, build_pro_recommendation_specs
from ui.ui_labels import ADVISORY_CSS_MAP, MemoGroupTitles, UIClassNames
from ui.view_guards import (
    has_visible_sensitivity,
    should_render_capacity_overload_advisory,
    should_render_high_debt_credit_advisory,
    should_render_pessimistic_payback_warning,
)

_MEMO_GROUP_ORDER: Tuple[Tuple[str, str], ...] = (
    (MemoGroupTitles.INVESTMENT, "investment"),
    (MemoGroupTitles.DRIVERS, "drivers"),
    (MemoGroupTitles.RISKS, "risks"),
    (MemoGroupTitles.OPERATIONS, "operations"),
)

_NEUTRAL_GROUP_TEXT: dict[str, str] = {
    "investment": "Базовые инвестиционные показатели соответствуют введённым допущениям модели.",
    "drivers": "Доминирующий драйвер NPV не выделен — чувствительность равномерно умеренная.",
    "risks": "Существенных рисков по сценарию трафика и долговой нагрузке не выявлено.",
    "operations": "Ограничений мощности на горизонте модели не выявлено.",
}


@dataclass(frozen=True)
class MemoGroupSpec:
    key: str
    title: str
    items: Tuple[AdvisoryItemSpec, ...]


@dataclass(frozen=True)
class InvestmentMemoSpec:
    headline: str
    severity: str
    groups: Tuple[MemoGroupSpec, ...]
    next_actions: Tuple[str, ...]


def _memo_headline(res: ProResult) -> Tuple[str, str]:
    rate = format_npv_discount_rate_label()
    if res.npv > 0 and not is_missing_payback_months(res.payback_months):
        return (
            f"Базовый сценарий: окупаемость {format_kpi_payback(res.payback_months)}, "
            f"NPV {format_kpi_npv_compact(res.npv)}",
            "good" if res.payback_months <= 36 else "info",
        )
    if res.npv > 0:
        return (
            f"NPV положительный ({format_kpi_npv_compact(res.npv)}), "
            "окупаемость требует проверки на горизонте",
            "warn",
        )
    if is_missing_payback_months(res.payback_months):
        return ("Проект не окупается на выбранном горизонте модели", "bad")
    return (
        f"NPV отрицательный ({format_kpi_npv_compact(res.npv)}) при ставке {rate}",
        "bad",
    )


def _classify_advisory_group(spec: AdvisoryItemSpec) -> str:
    if spec.key == "scenario_pessim":
        return "investment" if spec.severity == "good" else "risks"
    if spec.key == "npv_irr":
        return "risks" if spec.severity == "bad" else "investment"
    if spec.key in ("payback", "margin"):
        return "investment"
    if spec.key == "sensitivity_top":
        return "drivers"
    if spec.key == "credit_debt":
        return "risks"
    if spec.key == "capacity_overload":
        return "operations"
    return "investment"


def _neutral_advisory(group_key: str) -> AdvisoryItemSpec:
    return AdvisoryItemSpec(
        key=f"{group_key}_neutral",
        severity="info",
        text=_NEUTRAL_GROUP_TEXT[group_key],
    )


def build_pro_memo_groups(
    advisories: Tuple[AdvisoryItemSpec, ...],
) -> Tuple[MemoGroupSpec, ...]:
    buckets: dict[str, list[AdvisoryItemSpec]] = {
        key: [] for _, key in _MEMO_GROUP_ORDER
    }
    for spec in advisories:
        buckets[_classify_advisory_group(spec)].append(spec)

    groups: list[MemoGroupSpec] = []
    for title, key in _MEMO_GROUP_ORDER:
        items = buckets[key]
        if not items:
            items = [_neutral_advisory(key)]
        groups.append(MemoGroupSpec(key=key, title=title, items=tuple(items)))
    return tuple(groups)


def build_pro_next_actions(res: ProResult, advisories: Tuple[AdvisoryItemSpec, ...]) -> Tuple[str, ...]:
    """Presentation-only action list derived from existing advisory outputs."""
    keys = {spec.key for spec in advisories}
    severities = {spec.key: spec.severity for spec in advisories}
    actions: list[str] = []

    if "payback" in keys and severities.get("payback") in ("bad", "warn"):
        actions.append("Пересчитать сценарий с корректировкой трафика, цен или CAPEX")
    if "npv_irr" in keys and severities.get("npv_irr") == "bad":
        actions.append("Проверить допущения модели и структуру инвестиций")
    if "margin" in keys and severities.get("margin") == "warn":
        actions.append("Скорректировать OPEX или ценовую политику для улучшения маржи")
    if should_render_pessimistic_payback_warning(res):
        actions.append("Проработать пессимистичный сценарий и план снижения трафика")
    if has_visible_sensitivity(res.sensitivity):
        top_factor = max(res.sensitivity.items(), key=lambda x: x[1])[0]
        actions.append(f"Валидировать допущение по параметру «{top_factor}» с заказчиком")
    if should_render_capacity_overload_advisory(res):
        actions.append("Оценить риск capacity: расширение мощности или снижение планового трафика")
    if should_render_high_debt_credit_advisory(res):
        actions.append("Пересмотреть структуру финансирования и долговую нагрузку")
    if res.npv > 0 and not is_missing_payback_months(res.payback_months):
        actions.append("Подготовить выгрузку таблиц и KPI для инвестора или партнёра")

    if not actions:
        actions.append("Сверить ключевые допущения с фактическими рыночными данными")

    return tuple(actions[:5])


def build_pro_investment_memo(res: ProResult) -> InvestmentMemoSpec:
    advisories = build_pro_recommendation_specs(res)
    headline, severity = _memo_headline(res)
    return InvestmentMemoSpec(
        headline=headline,
        severity=severity,
        groups=build_pro_memo_groups(advisories),
        next_actions=build_pro_next_actions(res, advisories),
    )


def _render_memo_group_html(group: MemoGroupSpec) -> str:
    items_html = []
    for item in group.items:
        if item.key.endswith("_neutral"):
            items_html.append(f'<div class="wb-memo-item wb-memo-neutral">{item.text}</div>')
        else:
            css = ADVISORY_CSS_MAP[item.severity]
            items_html.append(f'<div class="wb-memo-item {css}">{item.text}</div>')
    return (
        f'<div class="wb-memo-group">'
        f'<div class="wb-memo-group-title">{group.title}</div>'
        f'{"".join(items_html)}'
        f"</div>"
    )


def render_investment_memo_html(spec: InvestmentMemoSpec) -> str:
    groups_html = "".join(_render_memo_group_html(g) for g in spec.groups)
    actions_html = "".join(
        f'<li class="wb-memo-action">{action}</li>' for action in spec.next_actions
    )
    return (
        f'<div class="{UIClassNames.CARD} wb-memo wb-memo--{spec.severity}">'
        f'<div class="wb-memo-headline">{spec.headline}</div>'
        f'<div class="wb-memo-groups">{groups_html}</div>'
        f'<div class="wb-memo-actions-block">'
        f'<div class="wb-memo-group-title">{MemoGroupTitles.NEXT_ACTIONS}</div>'
        f'<ul class="wb-memo-actions">{actions_html}</ul>'
        f"</div>"
        f"</div>"
    )
