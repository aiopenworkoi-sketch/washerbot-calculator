from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from domain.params import ProParams, SimpleParams


@dataclass
class SimpleResult:
    months: np.ndarray                  # 1..N
    cars_per_month: np.ndarray          # авто/мес (с сезонностью, на все роботы)
    revenue_month: np.ndarray           # выручка/мес
    var_costs_month: np.ndarray         # переменные расходы/мес
    fix_costs_month: np.ndarray         # постоянные расходы/мес
    salary_total_month: np.ndarray      # ЗП с налогами/мес
    tax_month: np.ndarray               # налоги/мес
    profit_month: np.ndarray            # чистая прибыль/мес
    cashflow: np.ndarray                # денежный поток (включая инвестицию в [0])
    cumulative: np.ndarray              # накопленный CF

    # KPI
    avg_check: float
    avg_revenue_month: float
    avg_profit_month: float
    total_revenue: float
    total_profit: float
    payback_months: float
    npv: float
    irr: float
    margin: float

    # Структура
    breakdown_year1: Dict[str, float]   # категории расходов за 1-й год

    # Параметры (для рендера)
    params: SimpleParams

    # Capacity overload diagnostics (read-only)
    capacity_binding_months: int = 0
    annual_unserved_demand: float = 0.0
    annual_unserved_share: float = 0.0
    peak_requested_utilization: float = 0.0
    peak_hour_utilization: float = 0.0
    peak_unserved_month: int = 0
    zero_capacity_positive_demand_months: int = 0


@dataclass
class ProResult:
    months: np.ndarray
    cars_per_month: np.ndarray
    revenue_month: np.ndarray
    var_costs_month: np.ndarray
    opex_month: np.ndarray              # все постоянные кроме ЗП и налогов
    salary_total_month: np.ndarray
    credit_interest_month: np.ndarray
    credit_principal_month: np.ndarray
    amortization_month: np.ndarray
    ebitda_month: np.ndarray            # выручка − перем. − OPEX − ЗП
    ebt_month: np.ndarray               # − % по кредиту − амортизация
    tax_month: np.ndarray
    profit_month: np.ndarray            # чистая прибыль
    cashflow: np.ndarray
    cumulative: np.ndarray

    # KPI
    avg_check: float
    capex_total: float
    own_funds: float                    # собственные средства = capex − кредит
    avg_revenue_month: float
    avg_profit_month: float
    avg_ebitda_month: float
    total_revenue: float
    total_profit: float
    payback_months: float
    npv: float
    irr: float
    margin_net: float
    margin_ebitda: float

    # Сценарии
    payback_pessim: float
    payback_optim: float
    cumulative_pessim: np.ndarray
    cumulative_optim: np.ndarray

    # Структура
    capex_breakdown: Dict[str, float]
    opex_breakdown_year1: Dict[str, float]

    # Чувствительность
    sensitivity: Dict[str, float]       # параметр -> Δ NPV (%)

    # Экология
    water_saved_m3_year: float
    chem_extra_cost_year: float
    water_cost_saving_rub_year: float

    params: ProParams

    # Capacity overload diagnostics (read-only)
    capacity_binding_months: int = 0
    annual_unserved_demand: float = 0.0
    annual_unserved_share: float = 0.0
    peak_requested_utilization: float = 0.0
    peak_hour_utilization: float = 0.0
    peak_unserved_month: int = 0
    zero_capacity_positive_demand_months: int = 0
