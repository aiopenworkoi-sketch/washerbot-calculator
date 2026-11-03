from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Final, Tuple

from data.catalogs import (
    DEFAULT_MODEL,
    DEFAULT_REGION,
    PROGRAMS_DEFAULT,
    REGIONS,
    WASHER_CATALOG,
)
from domain.models import WashProgram
from domain.params import ProParams, SimpleParams
from finance.water_discharge import WATER_PROFILE_LEGACY_HALF_SEWAGE

SAMPLE_CASE_NAMES: Final[Tuple[str, ...]] = (
    "simple_baseline",
    "pro_baseline",
    "pro_overload",
)

SAMPLE_PRO_OVERLOAD_CARS_PER_DAY: Final[float] = 500.0


def _copy_programs(programs: Tuple[WashProgram, ...] | list[WashProgram]) -> list[WashProgram]:
    return [deepcopy(program) for program in programs]


def build_sample_simple_params() -> SimpleParams:
    model = WASHER_CATALOG[DEFAULT_MODEL]
    region = REGIONS[DEFAULT_REGION]
    suggested_rent = int(region.rent_per_m2 * model.space_required_m2)
    return SimpleParams(
        model_code=DEFAULT_MODEL,
        n_robots=1,
        region_key=DEFAULT_REGION,
        total_investment=15_000_000.0,
        cars_per_day_avg=50.0,
        work_days_month=30,
        programs=_copy_programs(PROGRAMS_DEFAULT),
        admin_salary_gross=60_000.0,
        rent_month=float(suggested_rent),
        other_fixed=40_000.0,
        tax_regime="USN_INCOME",
        horizon_months=60,
        water_discharge_profile=WATER_PROFILE_LEGACY_HALF_SEWAGE,
    )


def build_sample_pro_params() -> ProParams:
    return ProParams(
        model_code="L380_PLUS",
        n_robots=1,
        region_key="MSK",
        capex_equipment=13_200_000.0,
        capex_construction=2_000_000.0,
        capex_engineering=1_500_000.0,
        capex_premises=0.0,
        capex_launch=500_000.0,
        capex_other=0.0,
        use_credit=True,
        credit_amount=8_000_000.0,
        credit_rate_annual=0.18,
        credit_term_months=60,
        credit_grace_months=6,
        cars_per_day_avg=80.0,
        work_days_month=26,
        seasonality_strength=1.0,
        programs=_copy_programs(PROGRAMS_DEFAULT),
        n_admins=1,
        admin_salary_gross=80_000.0,
        n_managers=0,
        manager_salary_gross=120_000.0,
        rent_month=150_000.0,
        utilities_extra=25_000.0,
        security_month=30_000.0,
        marketing_month=40_000.0,
        maintenance_month=35_000.0,
        insurance_month=15_000.0,
        other_opex=10_000.0,
        tax_regime="USN_INCOME",
        amort_years_equipment=7,
        horizon_months=84,
        scenario_pessim_factor=0.7,
        scenario_optim_factor=1.3,
        eco_water_recycle_pct=0.0,
        eco_chem_premium=False,
        water_discharge_profile=WATER_PROFILE_LEGACY_HALF_SEWAGE,
    )


def build_sample_pro_overload_params() -> ProParams:
    return replace(
        build_sample_pro_params(),
        cars_per_day_avg=SAMPLE_PRO_OVERLOAD_CARS_PER_DAY,
    )
