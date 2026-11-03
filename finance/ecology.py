from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EcoMetrics:
    water_saved_m3_year: float
    water_cost_saving_rub_year: float
    chem_extra_cost_year: float


def build_eco_metrics(
    *,
    annual_served_washes: float,
    water_per_wash_l: float,
    chem_per_wash_rub: float,
    eco_water_recycle_pct: float,
    eco_chem_premium: bool,
    water_total_tariff_rub_per_m3: float,
) -> EcoMetrics:
    served = max(0.0, float(annual_served_washes))
    water_per_wash_l_safe = max(0.0, float(water_per_wash_l))
    chem_per_wash_rub_safe = max(0.0, float(chem_per_wash_rub))
    recycle_pct = min(max(float(eco_water_recycle_pct), 0.0), 1.0)
    water_tariff = max(0.0, float(water_total_tariff_rub_per_m3))

    water_saved_m3_year = served * water_per_wash_l_safe / 1000.0 * recycle_pct
    water_cost_saving_rub_year = water_saved_m3_year * water_tariff
    chem_extra_cost_year = served * chem_per_wash_rub_safe * (0.15 if eco_chem_premium else 0.0)

    return EcoMetrics(
        water_saved_m3_year=water_saved_m3_year,
        water_cost_saving_rub_year=water_cost_saving_rub_year,
        chem_extra_cost_year=chem_extra_cost_year,
    )
