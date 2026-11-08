from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from finance.taxes import (
    TAX_MODEL_BASELINE_YEAR,
    OSNO_PROFIT_RATE,
    OSNO_VAT_RATE,
    PATENT_COST_MONTH,
    USN_INCOME_INSURANCE_DEDUCTION_CAP,
    USN_INCOME_RATE,
    USN_MIN_TAX_RATE,
    USN_PROFIT_RATE,
    USN_VAT_5_MAX,
    USN_VAT_7_MAX,
    USN_VAT_RATE_5,
    USN_VAT_RATE_7,
    USN_VAT_THRESHOLD,
)


@dataclass(frozen=True)
class TaxPolicy:
    year: int
    osno_profit_rate: float
    osno_vat_rate: float
    usn_income_rate: float
    usn_profit_rate: float
    usn_min_tax_rate: float
    usn_vat_threshold: float
    usn_vat_rate_5: float
    usn_vat_rate_7: float
    usn_vat_5_max: float
    usn_vat_7_max: float
    usn_income_deduction_cap: float
    patent_cost_month: float


def get_tax_policy_for_year(year: int) -> TaxPolicy:
    y = int(year)
    # Упрощённая policy: ставки из finance.taxes, ориентир — TAX_MODEL_BASELINE_YEAR.
    return TaxPolicy(
        year=y,
        osno_profit_rate=float(OSNO_PROFIT_RATE),
        osno_vat_rate=float(OSNO_VAT_RATE),
        usn_income_rate=float(USN_INCOME_RATE),
        usn_profit_rate=float(USN_PROFIT_RATE),
        usn_min_tax_rate=float(USN_MIN_TAX_RATE),
        usn_vat_threshold=float(USN_VAT_THRESHOLD),
        usn_vat_rate_5=float(USN_VAT_RATE_5),
        usn_vat_rate_7=float(USN_VAT_RATE_7),
        usn_vat_5_max=float(USN_VAT_5_MAX),
        usn_vat_7_max=float(USN_VAT_7_MAX),
        usn_income_deduction_cap=float(USN_INCOME_INSURANCE_DEDUCTION_CAP),
        patent_cost_month=float(PATENT_COST_MONTH),
    )


def profit_tax_rate_for_year(year: int) -> float:
    return max(0.0, get_tax_policy_for_year(year).osno_profit_rate)


def calculate_profit_tax(taxable_base: float, year: int) -> float:
    base = float(taxable_base)
    if not np.isfinite(base) or base <= 0:
        return 0.0
    return max(0.0, base * profit_tax_rate_for_year(year))


def _usn_vat_amount(revenue_year: float, policy: TaxPolicy) -> float:
    rev = max(0.0, float(revenue_year))
    if rev <= policy.usn_vat_threshold:
        return 0.0
    if rev <= policy.usn_vat_5_max:
        return rev * policy.usn_vat_rate_5
    return rev * policy.usn_vat_rate_7


def _usn_income_tax(revenue_year: float, insurance_year: float, policy: TaxPolicy) -> float:
    """УСН «доходы»: налог уменьшается на страховые взносы, но не более чем на 50%."""
    gross = max(0.0, float(revenue_year)) * policy.usn_income_rate
    deductible = min(max(0.0, float(insurance_year)), gross * policy.usn_income_deduction_cap)
    return max(0.0, gross - deductible)


def calculate_tax_for_year(
    revenue_year: float,
    taxable_profit_year: float,
    tax_regime: str,
    year: int = TAX_MODEL_BASELINE_YEAR,
    *,
    insurance_year: float = 0.0,
    patent_cost_month: float | None = None,
    vat_input_base_year: float = 0.0,
) -> Dict[str, float]:
    policy = get_tax_policy_for_year(year)
    rev = max(0.0, float(revenue_year))
    prof = float(taxable_profit_year)
    regime = str(tax_regime)
    result = {
        "tax": 0.0,
        "vat": 0.0,
        "total": 0.0,
        "fixed": 0.0,
        "regime": regime,
        "year": policy.year,
    }

    if regime == "USN_INCOME":
        tax = _usn_income_tax(rev, insurance_year, policy)
        vat = _usn_vat_amount(rev, policy)
        result["tax"] = tax
        result["vat"] = vat
        result["total"] = max(0.0, tax + vat)
        return result

    if regime == "USN_PROFIT":
        tax_normal = max(0.0, prof) * policy.usn_profit_rate
        tax_min = rev * policy.usn_min_tax_rate
        tax = max(tax_normal, tax_min)
        vat = _usn_vat_amount(rev, policy)
        result["tax"] = tax
        result["vat"] = vat
        result["total"] = max(0.0, tax + vat)
        return result

    if regime == "PATENT":
        monthly = policy.patent_cost_month if patent_cost_month is None else max(0.0, float(patent_cost_month))
        tax = monthly * 12.0
        result["tax"] = max(0.0, tax)
        result["vat"] = 0.0
        result["total"] = result["tax"]
        # Патент — фиксированный платёж: начисляется и при нулевой выручке
        result["fixed"] = result["tax"]
        return result

    if regime == "OSNO":
        # Цены в модели — с НДС, поэтому НДС считается «изнутри» (r/(1+r)),
        # а к уплате идёт разница между исходящим и входящим НДС.
        rate = max(0.0, policy.osno_vat_rate)
        output_vat = rev * rate / (1.0 + rate)
        input_vat = max(0.0, float(vat_input_base_year)) * rate / (1.0 + rate)
        vat = max(0.0, output_vat - input_vat)
        # Прибыль в модели посчитана на «грязной» выручке — очищаем базу от НДС
        taxable = max(0.0, prof - vat)
        tax = calculate_profit_tax(taxable, policy.year)
        result["tax"] = tax
        result["vat"] = vat
        result["total"] = max(0.0, tax + vat)
        return result

    return result


def build_calendar_year_schedule(start_year: int, horizon_months: int) -> List[int]:
    y0 = int(start_year)
    h = max(0, int(horizon_months))
    return [y0 + (i // 12) for i in range(h)]


def _allocate_annual_tax(revenue_month: np.ndarray, annual_tax_total: float) -> np.ndarray:
    rev = np.maximum(np.asarray(revenue_month, dtype=float), 0.0)
    total = float(np.sum(rev))
    if total <= 0:
        return np.zeros_like(rev, dtype=float)
    return rev / total * max(0.0, float(annual_tax_total))


def calculate_monthly_tax_schedule(
    revenue_month: np.ndarray,
    taxable_profit_month: np.ndarray,
    tax_regime: str,
    *,
    start_year: int = TAX_MODEL_BASELINE_YEAR,
    insurance_month: float = 0.0,
    patent_cost_month: float | None = None,
    vat_input_base_month: np.ndarray | None = None,
) -> np.ndarray:
    rev = np.asarray(revenue_month, dtype=float)
    prof = np.asarray(taxable_profit_month, dtype=float)
    if rev.shape != prof.shape:
        raise ValueError("revenue_month and taxable_profit_month must have the same shape")

    h = rev.size
    if vat_input_base_month is not None:
        vat_input_base = np.asarray(vat_input_base_month, dtype=float)
        if vat_input_base.shape != rev.shape:
            raise ValueError("vat_input_base_month must have the same shape as revenue_month")
    else:
        vat_input_base = None
    years = build_calendar_year_schedule(start_year, h)
    tax_month = np.zeros(h, dtype=float)
    n_years = (h + 11) // 12
    for y in range(n_years):
        i0 = y * 12
        i1 = min((y + 1) * 12, h)
        year = years[i0] if i0 < len(years) else start_year
        insurance_year = max(0.0, float(insurance_month)) * (i1 - i0)
        annual = calculate_tax_for_year(
            revenue_year=float(np.sum(rev[i0:i1])),
            taxable_profit_year=float(np.sum(prof[i0:i1])),
            tax_regime=tax_regime,
            year=year,
            insurance_year=insurance_year,
            patent_cost_month=patent_cost_month,
            vat_input_base_year=(
                float(np.sum(vat_input_base[:i1])) - float(np.sum(vat_input_base[:i0]))
                if vat_input_base is not None else 0.0
            ),
        )
        fixed = max(0.0, float(annual.get("fixed", 0.0)))
        variable = max(0.0, float(annual["total"]) - fixed)
        months = max(1, i1 - i0)
        tax_month[i0:i1] = _allocate_annual_tax(rev[i0:i1], variable) + fixed / months
    return np.maximum(tax_month, 0.0)
