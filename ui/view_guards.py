from __future__ import annotations

from typing import Mapping

from domain.params import ProParams
from domain.results import ProResult, SimpleResult
from ui.display_fallbacks import has_finite_payback_months, is_missing_payback_months

HIGH_DEBT_RATIO_THRESHOLD = 0.7


def should_show_payback_marker(payback_months: float) -> bool:
    return has_finite_payback_months(payback_months)


def has_capacity_overload(capacity_binding_months: int) -> bool:
    return capacity_binding_months > 0


def should_render_capacity_overload_advisory(res: SimpleResult | ProResult) -> bool:
    return has_capacity_overload(res.capacity_binding_months)


def has_visible_sensitivity(sensitivity: Mapping[str, float]) -> bool:
    return bool(sensitivity)


def has_active_credit(params: ProParams) -> bool:
    return params.use_credit and params.credit_amount > 0


def should_render_pessimistic_payback_success(res: ProResult) -> bool:
    p = res.params
    return (
        has_finite_payback_months(res.payback_pessim)
        and res.payback_pessim <= p.horizon_months
    )


def should_render_pessimistic_payback_warning(res: ProResult) -> bool:
    return is_missing_payback_months(res.payback_pessim)


def should_show_peak_unserved_month(peak_unserved_month: int) -> bool:
    return peak_unserved_month > 0


def should_show_zero_capacity_positive_demand_months(zero_capacity_months: int) -> bool:
    return zero_capacity_months > 0


def should_render_ecology_block(params: ProParams) -> bool:
    return params.eco_water_recycle_pct > 0 or params.eco_chem_premium


def should_render_high_debt_credit_advisory(res: ProResult) -> bool:
    if not has_active_credit(res.params):
        return False
    debt_ratio = (
        res.params.credit_amount / res.capex_total if res.capex_total > 0 else 0
    )
    return debt_ratio > HIGH_DEBT_RATIO_THRESHOLD
