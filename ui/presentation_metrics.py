from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from data.catalogs import WASHER_CATALOG
from data.washer_access import get_washer_model
from domain.results import ProResult
from finance.capacity import (
    estimate_daily_capacity,
    estimate_monthly_capacity,
    weighted_program_duration_minutes,
)


@dataclass(frozen=True)
class BreakEvenEstimate:
    """UI-only monthly cars threshold covering loaded fixed costs."""

    operational_cars_per_month: float | None
    unit_contribution_rub: float
    monthly_fixed_ops_rub: float
    avg_actual_cars_per_month: float
    headroom_ratio: float | None
    formula_note: str


def compute_pro_break_even_estimate(res: ProResult) -> BreakEvenEstimate:
    """
    Presentation-only threshold: cars/month needed to cover average monthly
    fixed load (OPEX + salary + tax + credit interest) via unit contribution.

    Not classic operating break-even (excludes amortization / principal);
    not capital payback.
    """
    cars = res.cars_per_month
    active = cars > 1e-6
    if not np.any(active):
        return BreakEvenEstimate(
            operational_cars_per_month=None,
            unit_contribution_rub=0.0,
            monthly_fixed_ops_rub=0.0,
            avg_actual_cars_per_month=0.0,
            headroom_ratio=None,
            formula_note=(
                "Недостаточно данных: нет месяцев с положительным потоком авто."
            ),
        )

    unit_contribution = float(
        np.mean((res.revenue_month[active] - res.var_costs_month[active]) / cars[active])
    )
    monthly_fixed_ops = float(
        np.mean(
            res.opex_month
            + res.salary_total_month
            + res.tax_month
            + res.credit_interest_month
        )
    )
    avg_actual = float(np.mean(cars))

    if unit_contribution <= 1e-6:
        be_cars = None
        headroom = None
    else:
        be_cars = monthly_fixed_ops / unit_contribution
        headroom = avg_actual / be_cars if be_cars > 0 else None

    return BreakEvenEstimate(
        operational_cars_per_month=be_cars,
        unit_contribution_rub=unit_contribution,
        monthly_fixed_ops_rub=monthly_fixed_ops,
        avg_actual_cars_per_month=avg_actual,
        headroom_ratio=headroom,
        formula_note=(
            "Порог авто/мес = средние (OPEX + ЗП + налог + проценты по кредиту) / "
            "средняя маржа на авто (выручка − переменные). "
            "Без амортизации и тела кредита; отдельно от окупаемости капитала."
        ),
    )


def estimate_pro_monthly_capacity_series(res: ProResult) -> np.ndarray:
    """
    Display-only monthly capacity ceiling using the same capacity helpers as the model.
    Returns a constant-per-month array aligned with res.months.
    """
    p = res.params
    model = get_washer_model(p.model_code, WASHER_CATALOG)
    weighted_duration = weighted_program_duration_minutes(
        [prog.duration_min for prog in p.programs],
        [prog.share_default for prog in p.programs],
    )
    daily_per_robot = estimate_daily_capacity(
        cars_per_hour_reference=model.cars_per_hour,
        cycle_time_reference_min=model.cycle_time_min,
        weighted_duration_min=weighted_duration,
    )
    monthly_cap = estimate_monthly_capacity(
        daily_capacity_per_robot=daily_per_robot,
        work_days_month=p.work_days_month,
        n_robots=p.n_robots,
    )
    return np.full(len(res.months), monthly_cap, dtype=float)
