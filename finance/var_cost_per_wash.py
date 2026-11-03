from __future__ import annotations

from dataclasses import dataclass

from domain.models import WasherModel
from finance.opex import calculate_water_cost_per_m3
from finance.program_mix import ProgramMixMetrics
from finance.variable_costs import calculate_elec_cost_per_wash


@dataclass(frozen=True)
class VarCostPerWashBreakdown:
    water: float
    electricity: float
    chemistry: float

    @property
    def total(self) -> float:
        return self.water + self.electricity + self.chemistry


def compute_var_cost_per_wash(
    *,
    model: WasherModel,
    mix: ProgramMixMetrics,
    water_cost_per_m3: float,
    elec_price: float,
    extra_dryers_enabled: bool,
    water_recycle_factor: float = 1.0,
    chem_premium_factor: float = 1.0,
) -> VarCostPerWashBreakdown:
    water = (
        model.water_per_wash_l
        * mix.avg_water_factor
        / 1000.0
        * water_cost_per_m3
        * water_recycle_factor
    )
    electricity = calculate_elec_cost_per_wash(
        model_elec_per_wash_kwh=model.elec_per_wash_kwh,
        avg_elec_factor=mix.avg_elec_factor,
        elec_price=elec_price,
        extra_dryers_enabled=extra_dryers_enabled,
        model_code=model.code,
    )
    chemistry = model.chem_per_wash_rub * mix.avg_chem_factor * chem_premium_factor
    return VarCostPerWashBreakdown(
        water=float(water),
        electricity=float(electricity),
        chemistry=float(chemistry),
    )
