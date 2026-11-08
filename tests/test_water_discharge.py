from __future__ import annotations

from dataclasses import replace

import pytest

from app import calculate_simple
from data.catalogs import WASHER_CATALOG
from data.sample_params import build_sample_simple_params
from data.washer_access import get_washer_model
from finance.variable_costs import (
    EXTRA_DRYER_RUNTIME_SEC_PER_WASH,
    calculate_elec_cost_per_wash,
    extra_dryer_kwh_per_wash,
)
from finance.water_discharge import (
    WATER_DISCHARGE_DEFAULT_PROFILE,
    WATER_PROFILE_BASIC,
    WATER_PROFILE_LEGACY_HALF_SEWAGE,
    WATER_PROFILE_TYPICAL_CAR_WASH_LT30,
    WATER_PROFILE_WITH_NV_CSV,
    normalize_water_discharge_profile,
    water_cost_per_m3_for_profile,
)
from finance.water_usage import (
    WATER_DISCHARGE_LT30_THRESHOLD_M3,
    estimated_water_m3_per_day,
    is_typical_lt30_profile_exceeded,
)
from ui.scenario_io import (
    ScenarioValidationError,
    deserialize_simple_params,
    serialize_simple_params,
)


def test_water_profile_formulas_msk_tariffs() -> None:
    supply, sewage = 53.50, 39.20
    assert water_cost_per_m3_for_profile(supply, sewage, WATER_PROFILE_BASIC) == pytest.approx(
        supply + sewage
    )
    assert water_cost_per_m3_for_profile(supply, sewage, WATER_PROFILE_WITH_NV_CSV) == pytest.approx(
        supply + sewage + 0.5 * sewage
    )
    assert water_cost_per_m3_for_profile(
        supply, sewage, WATER_PROFILE_TYPICAL_CAR_WASH_LT30
    ) == pytest.approx(supply + 3.5 * sewage)
    assert water_cost_per_m3_for_profile(
        supply, sewage, WATER_PROFILE_LEGACY_HALF_SEWAGE
    ) == pytest.approx(supply + 0.5 * sewage)


def test_default_profile_for_new_sessions() -> None:
    from dataclasses import fields

    from domain.params import SimpleParams

    assert WATER_DISCHARGE_DEFAULT_PROFILE == WATER_PROFILE_TYPICAL_CAR_WASH_LT30
    profile_field = next(f for f in fields(SimpleParams) if f.name == "water_discharge_profile")
    assert profile_field.default == WATER_DISCHARGE_DEFAULT_PROFILE


def test_legacy_profile_when_scenario_field_missing() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    del raw["water_discharge_profile"]
    params = deserialize_simple_params(raw)
    assert params.water_discharge_profile == WATER_PROFILE_LEGACY_HALF_SEWAGE


def test_extra_dryer_kwh_uses_30_seconds_per_wash() -> None:
    params = build_sample_simple_params()
    kwh = extra_dryer_kwh_per_wash(
        extra_dryers_enabled=True,
        model_code=params.model_code,
    )
    assert kwh == pytest.approx(11.0 * EXTRA_DRYER_RUNTIME_SEC_PER_WASH / 3600.0)


def test_extra_dryers_increase_electricity_opex() -> None:
    base = build_sample_simple_params()
    with_dryers = replace(base, extra_dryers_enabled=True)
    base_res = calculate_simple(base)
    dry_res = calculate_simple(with_dryers)
    assert dry_res.npv < base_res.npv


def test_nv_flags_increase_opex_vs_baseline() -> None:
    """Плата за НВ на ЦСВ и сверхнорматив — отдельные строки, снижают NPV."""
    base = build_sample_simple_params()
    with_norm = replace(base, nv_norm_enabled=True)
    with_both = replace(base, nv_norm_enabled=True, nv_over_enabled=True)
    assert calculate_simple(with_norm).npv < calculate_simple(base).npv
    assert calculate_simple(with_both).npv < calculate_simple(with_norm).npv


def test_nv_coefficient_values() -> None:
    from finance.tariffs import nv_coefficient

    assert nv_coefficient(norm_enabled=False, over_enabled=False) == 0.0
    assert nv_coefficient(norm_enabled=True, over_enabled=False) == 0.5
    assert nv_coefficient(norm_enabled=False, over_enabled=True) == 2.0
    assert nv_coefficient(norm_enabled=True, over_enabled=True) == 2.5


def test_invalid_water_profile_rejected() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    raw["water_discharge_profile"] = "unknown_profile"
    with pytest.raises(ScenarioValidationError):
        deserialize_simple_params(raw)


def test_normalize_water_discharge_profile_new_vs_scenario() -> None:
    assert normalize_water_discharge_profile(None, from_scenario=False) == WATER_DISCHARGE_DEFAULT_PROFILE
    assert normalize_water_discharge_profile(None, from_scenario=True) == WATER_PROFILE_LEGACY_HALF_SEWAGE


def test_calculate_elec_cost_per_wash_includes_extra_component() -> None:
    params = build_sample_simple_params()
    base_cost = calculate_elec_cost_per_wash(
        model_elec_per_wash_kwh=2.5,
        avg_elec_factor=0.94,
        elec_price=8.4,
        extra_dryers_enabled=False,
        model_code=params.model_code,
    )
    with_extra = calculate_elec_cost_per_wash(
        model_elec_per_wash_kwh=2.5,
        avg_elec_factor=0.94,
        elec_price=8.4,
        extra_dryers_enabled=True,
        model_code=params.model_code,
    )
    assert with_extra > base_cost


def test_estimated_water_m3_per_day_examples() -> None:
    l380 = get_washer_model("L380_PLUS", WASHER_CATALOG)
    l370 = get_washer_model("L370_PLUS", WASHER_CATALOG)
    assert estimated_water_m3_per_day(288, l380.water_per_wash_l) == pytest.approx(34.56)
    assert estimated_water_m3_per_day(288, l370.water_per_wash_l) == pytest.approx(31.68)


def test_typical_lt30_profile_guardrail_threshold() -> None:
    l370 = get_washer_model("L370_PLUS", WASHER_CATALOG)
    assert is_typical_lt30_profile_exceeded(
        profile=WATER_PROFILE_TYPICAL_CAR_WASH_LT30,
        cars_per_day=288,
        water_per_wash_l=l370.water_per_wash_l,
    )
    l380 = get_washer_model("L380_PLUS", WASHER_CATALOG)
    # при 120 л/авто 240 авто/сутки дают 28,8 м³ — ещё в пределах 30 м³
    assert not is_typical_lt30_profile_exceeded(
        profile=WATER_PROFILE_TYPICAL_CAR_WASH_LT30,
        cars_per_day=240,
        water_per_wash_l=l380.water_per_wash_l,
    )
    assert is_typical_lt30_profile_exceeded(
        profile=WATER_PROFILE_TYPICAL_CAR_WASH_LT30,
        cars_per_day=288,
        water_per_wash_l=l380.water_per_wash_l,
    )
    assert WATER_DISCHARGE_LT30_THRESHOLD_M3 == 30.0
