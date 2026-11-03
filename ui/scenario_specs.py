from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

from domain.results import ProResult
from ui.format_policies import (
    format_kpi_payback,
    format_scenario_cumulative_money,
)
from ui.renderers import BRAND


@dataclass(frozen=True)
class ScenarioSummarySpec:
    key: str
    summary_label: str
    chart_name: str
    factor_label: str
    cumulative: np.ndarray
    payback_months: float
    hover_label: str
    line_color: str
    line_width: float
    line_dash: str | None = None
    fill_to_zero: bool = False
    fill_color: str | None = None


def build_pro_scenario_summary_specs(res: ProResult) -> Tuple[ScenarioSummarySpec, ...]:
    p = res.params
    return (
        ScenarioSummarySpec(
            key="pessim",
            summary_label="Пессимистичный",
            chart_name=f"Пессимистичный (×{p.scenario_pessim_factor:.2f})",
            factor_label=f"×{p.scenario_pessim_factor:.2f}",
            cumulative=res.cumulative_pessim,
            payback_months=res.payback_pessim,
            hover_label="Пессим.",
            line_color=BRAND["red"],
            line_width=2.5,
            line_dash="dot",
        ),
        ScenarioSummarySpec(
            key="base",
            summary_label="Базовый",
            chart_name="Базовый",
            factor_label="×1.00",
            cumulative=res.cumulative,
            payback_months=res.payback_months,
            hover_label="База",
            line_color=BRAND["primary"],
            line_width=3.5,
            fill_to_zero=True,
            fill_color="rgba(46,134,255,0.12)",
        ),
        ScenarioSummarySpec(
            key="optim",
            summary_label="Оптимистичный",
            chart_name=f"Оптимистичный (×{p.scenario_optim_factor:.2f})",
            factor_label=f"×{p.scenario_optim_factor:.2f}",
            cumulative=res.cumulative_optim,
            payback_months=res.payback_optim,
            hover_label="Оптим.",
            line_color=BRAND["green"],
            line_width=2.5,
            line_dash="dot",
        ),
    )


def build_pro_scenario_chart_specs(res: ProResult) -> Tuple[ScenarioSummarySpec, ...]:
    specs = build_pro_scenario_summary_specs(res)
    by_key: Dict[str, ScenarioSummarySpec] = {spec.key: spec for spec in specs}
    return (
        by_key["optim"],
        by_key["base"],
        by_key["pessim"],
    )


def build_pro_scenario_summary_rows(
    specs: Tuple[ScenarioSummarySpec, ...],
) -> List[dict]:
    return [
        {
            "Сценарий": spec.summary_label,
            "Множитель трафика": spec.factor_label,
            "Окупаемость": format_kpi_payback(spec.payback_months),
            "Накопл. CF на конец": format_scenario_cumulative_money(spec.cumulative[-1]),
        }
        for spec in specs
    ]


def scenario_summary_spec_to_dict(spec: ScenarioSummarySpec) -> dict:
    return {
        "key": spec.key,
        "summary_label": spec.summary_label,
        "chart_name": spec.chart_name,
        "factor_label": spec.factor_label,
        "payback_months": spec.payback_months,
        "cumulative_last": float(spec.cumulative[-1]),
        "hover_label": spec.hover_label,
        "line_color": spec.line_color,
        "line_width": spec.line_width,
        "line_dash": spec.line_dash,
        "fill_to_zero": spec.fill_to_zero,
    }
