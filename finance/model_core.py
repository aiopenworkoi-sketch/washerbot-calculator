from __future__ import annotations

from typing import Dict

import numpy as np

from data.catalogs import REGIONS, SEASONALITY, WASHER_CATALOG
from data.washer_access import get_washer_model
from domain.params import ProParams
from finance.capacity import (
    build_capacity_diagnostics,
    cap_demand_by_capacity,
    estimate_daily_capacity,
    estimate_monthly_capacity,
)
from finance.program_mix import compute_program_mix
from finance.seasonality import build_seasonality_factors
from finance.tariffs import effective_tariffs, nv_coefficient
from finance.var_cost_per_wash import compute_var_cost_per_wash


def _calculate_pro_core(params: ProParams, traffic_factor: float = 1.0) -> Dict[str, np.ndarray]:
    """
    Ядро расчёта (используется для базового, пессим. и оптим. сценариев).
    traffic_factor — множитель к трафику.
    """
    model = get_washer_model(params.model_code, WASHER_CATALOG)
    region = REGIONS[params.region_key]
    H = params.horizon_months

    mix = compute_program_mix(params.programs)
    daily_capacity_per_robot = estimate_daily_capacity(
        cars_per_hour_reference=model.cars_per_hour,
        cycle_time_reference_min=model.cycle_time_min,
        weighted_duration_min=mix.weighted_duration_min,
    )
    monthly_capacity_total = estimate_monthly_capacity(
        daily_capacity_per_robot=daily_capacity_per_robot,
        work_days_month=params.work_days_month,
        n_robots=params.n_robots,
    )

    tariffs = effective_tariffs(
        region,
        water_supply_override=getattr(params, 'water_supply_override', None),
        water_sewage_override=getattr(params, 'water_sewage_override', None),
        elec_price_override=getattr(params, 'elec_price_override', None),
    )
    # Плата за НВ на ЦСВ считается отдельной строкой OPEX, поэтому в стоимости
    # воды остаются только водоснабжение и водоотведение.
    water_cost_per_m3 = tariffs.water_supply + tariffs.water_sewage

    # Оборотная вода: доля не может быть меньше 0 и больше 0.95, иначе стоимость
    # воды уходит в минус и проект «зарабатывает» на расходе.
    eco_recycle_pct = min(0.95, max(0.0, float(params.eco_water_recycle_pct)))

    var_cost = compute_var_cost_per_wash(
        model=model,
        mix=mix,
        water_cost_per_m3=water_cost_per_m3,
        elec_price=tariffs.elec_price,
        extra_dryers_enabled=params.extra_dryers_enabled,
        water_recycle_factor=(1.0 - eco_recycle_pct),
        chem_premium_factor=1.15 if params.eco_chem_premium else 1.0,
    )

    monthly_seasonality = build_seasonality_factors(SEASONALITY, params.seasonality_strength)
    demand_per_month_one = np.zeros(H)
    for i in range(H):
        m_idx = i % 12
        seas = monthly_seasonality[m_idx]
        demand_per_month_one[i] = (
            params.cars_per_day_avg * params.work_days_month * seas * traffic_factor
        )

    demand_per_month = demand_per_month_one * params.n_robots
    cars_per_month = cap_demand_by_capacity(demand_per_month, monthly_capacity_total)
    capacity_diagnostics = build_capacity_diagnostics(
        demand_per_month,
        monthly_capacity_total,
    )

    revenue_month = cars_per_month * mix.avg_check
    var_costs_month = cars_per_month * var_cost.total

    return {
        "cars_per_month": cars_per_month,
        "revenue_month": revenue_month,
        "var_costs_month": var_costs_month,
        "avg_check": mix.avg_check,
        "cost_water_per_wash": var_cost.water,
        "cost_elec_per_wash": var_cost.electricity,
        "cost_chem_per_wash": var_cost.chemistry,
        "capacity_diagnostics": capacity_diagnostics,
        "weighted_duration_min": mix.weighted_duration_min,
        # Взвешенные по программам множители — нужны для эко-метрик, чтобы
        # экономия воды и переплата за химию считались по фактическому расходу.
        "avg_water_factor": mix.avg_water_factor,
        "avg_chem_factor": mix.avg_chem_factor,
        # Для строки «НВ на ЦСВ»: объём стоков на мойку и тариф водоотведения
        "water_m3_per_wash": (
            model.water_per_wash_l / 1000.0
            * mix.avg_water_factor
            * (1.0 - eco_recycle_pct)
        ),
        "sewage_tariff": tariffs.water_sewage,
        "water_supply_tariff": tariffs.water_supply,
        "elec_tariff": tariffs.elec_price,
        "nv_coefficient": nv_coefficient(
            norm_enabled=bool(getattr(params, "nv_norm_enabled", False)),
            over_enabled=bool(getattr(params, "nv_over_enabled", False)),
        ),
    }
