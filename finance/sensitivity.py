from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Dict, List, Tuple

import numpy as np

from domain.params import ProParams
from finance.credit import calculate_credit_schedule
from finance.metrics import calculate_npv
from finance.model_core import _calculate_pro_core
from finance.model_constants import NPV_DISCOUNT_RATE_ANNUAL
from finance.taxation import calculate_monthly_tax_schedule
from finance.taxes import TAX_MODEL_BASELINE_YEAR
from finance.taxes import insurance_contributions_sme, patent_cost_month_for_region

# Параметр меняется на +10% (раньше использовался симметричный ±10%, но
# показывать размах между +10% и −10% как «ΔNPV при ±10%» было неверно — это
# завышало эффект примерно вдвое).
SYMMETRIC_PCT_SUFFIX = "+10%"


@dataclass(frozen=True)
class SensitivityCaseSpec:
    key: str
    label: str
    apply_up: Callable[[ProParams], ProParams]
    apply_down: Callable[[ProParams], ProParams]


def format_sensitivity_label(parameter_name: str, pct_suffix: str = SYMMETRIC_PCT_SUFFIX) -> str:
    return f"{parameter_name} {pct_suffix}"


def _scale_program_prices(params: ProParams, factor: float) -> List:
    return [replace(p, price_rub=p.price_rub * factor) for p in params.programs]


def build_pro_sensitivity_case_specs() -> Tuple[SensitivityCaseSpec, ...]:
    return (
        SensitivityCaseSpec(
            key="traffic",
            label=format_sensitivity_label("Трафик"),
            apply_up=lambda p: replace(p, cars_per_day_avg=p.cars_per_day_avg * 1.1),
            apply_down=lambda p: replace(p, cars_per_day_avg=p.cars_per_day_avg * 0.9),
        ),
        SensitivityCaseSpec(
            key="prices",
            label=format_sensitivity_label("Цены"),
            apply_up=lambda p: replace(p, programs=_scale_program_prices(p, 1.1)),
            apply_down=lambda p: replace(p, programs=_scale_program_prices(p, 0.9)),
        ),
        SensitivityCaseSpec(
            key="capex_equipment",
            label=format_sensitivity_label("CAPEX оборуд."),
            apply_up=lambda p: replace(p, capex_equipment=p.capex_equipment * 1.1),
            apply_down=lambda p: replace(p, capex_equipment=p.capex_equipment * 0.9),
        ),
        SensitivityCaseSpec(
            key="rent",
            label=format_sensitivity_label("Аренда"),
            apply_up=lambda p: replace(p, rent_month=p.rent_month * 1.1),
            apply_down=lambda p: replace(p, rent_month=p.rent_month * 0.9),
        ),
        SensitivityCaseSpec(
            key="admin_salary",
            label=format_sensitivity_label("ЗП админ."),
            apply_up=lambda p: replace(p, admin_salary_gross=p.admin_salary_gross * 1.1),
            apply_down=lambda p: replace(p, admin_salary_gross=p.admin_salary_gross * 0.9),
        ),
    )


PRO_SENSITIVITY_CASE_SPECS: Tuple[SensitivityCaseSpec, ...] = build_pro_sensitivity_case_specs()


def _validate_sensitivity_labels(labels: List[str]) -> None:
    if any(not label for label in labels):
        raise ValueError("sensitivity labels must be non-empty")
    if len(labels) != len(set(labels)):
        raise ValueError("sensitivity labels must be unique")
    if any("\ufffd" in label for label in labels):
        raise ValueError("sensitivity labels must not contain replacement characters")


def build_ordered_sensitivity_result(
    specs: Tuple[SensitivityCaseSpec, ...],
    values_by_label: Dict[str, float],
) -> Dict[str, float]:
    ordered: Dict[str, float] = {}
    for spec in specs:
        if spec.label in values_by_label:
            ordered[spec.label] = values_by_label[spec.label]
    _validate_sensitivity_labels(list(ordered.keys()))
    return ordered


def clone_params_with_overrides(params: ProParams, **overrides) -> ProParams:
    return replace(params, **overrides)


def evaluate_pro_sensitivity_case(params: ProParams) -> float:
    """
    Returns NPV for a ProParams case using the same capped/tax-aware path
    as the active Pro calculation components.
    """
    h = params.horizon_months
    core = _calculate_pro_core(params, traffic_factor=1.0)
    rev = core["revenue_month"]
    var = core["var_costs_month"]

    capex_total = (
        params.capex_equipment + params.capex_construction + params.capex_engineering
        + params.capex_premises + params.capex_launch + params.capex_other
    )
    credit_active = bool(
        params.use_credit and params.credit_amount > 0 and params.credit_term_months > 0
    )
    credit_used = min(max(0.0, params.credit_amount), capex_total) if credit_active else 0.0
    own_funds = max(0.0, capex_total - credit_used)

    salary_admin = params.admin_salary_gross * params.n_admins
    salary_man = params.manager_salary_gross * params.n_managers
    ins_a = insurance_contributions_sme(params.admin_salary_gross) * params.n_admins
    ins_m = insurance_contributions_sme(params.manager_salary_gross) * params.n_managers
    salary = salary_admin + salary_man + ins_a + ins_m

    opex = (
        params.rent_month + params.utilities_extra + params.security_month
        + params.marketing_month + params.maintenance_month
        + params.insurance_month + params.other_opex
    )

    if credit_active and credit_used > 0:
        sched = calculate_credit_schedule(
            credit_used,
            params.credit_rate_annual,
            params.credit_term_months,
            params.credit_grace_months,
        )
        ci = np.zeros(h)
        cp = np.zeros(h)
        n = min(h, params.credit_term_months)
        ci[:n] = sched["interest"][:n]
        cp[:n] = sched["principal"][:n]
    else:
        ci = np.zeros(h)
        cp = np.zeros(h)

    amort_pm = (
        params.capex_equipment / (params.amort_years_equipment * 12)
        if params.amort_years_equipment > 0 else 0
    )
    amort = np.zeros(h)
    amort[:min(h, params.amort_years_equipment * 12)] = amort_pm

    ebitda = rev - var - opex - salary
    ebt = ebitda - ci - amort
    tax = calculate_monthly_tax_schedule(
        revenue_month=rev,
        taxable_profit_month=ebt,
        tax_regime=params.tax_regime,
        start_year=TAX_MODEL_BASELINE_YEAR,
        insurance_month=ins_a + ins_m,
        patent_cost_month=patent_cost_month_for_region(params.region_key),
    )
    profit = ebt - tax
    cf_op = profit + amort - cp

    cf = np.zeros(h + 1)
    cf[0] = -own_funds
    cf[1:] = cf_op
    return calculate_npv(cf, discount_rate_annual=NPV_DISCOUNT_RATE_ANNUAL)


def _upward_case_delta(
    params: ProParams,
    spec: SensitivityCaseSpec,
    base: float,
) -> float:
    """|NPV(+10%) − NPV(база)| / |NPV(база)| — эффект одного шага +10%."""
    up_value = evaluate_pro_sensitivity_case(spec.apply_up(params))
    return abs(up_value - base) / abs(base)


def build_pro_sensitivity_cases(params: ProParams) -> Dict[str, float]:
    base = evaluate_pro_sensitivity_case(params)
    if abs(base) < 1:
        return {}

    values_by_label = {
        spec.label: _upward_case_delta(params, spec, base)
        for spec in PRO_SENSITIVITY_CASE_SPECS
    }
    return build_ordered_sensitivity_result(PRO_SENSITIVITY_CASE_SPECS, values_by_label)
