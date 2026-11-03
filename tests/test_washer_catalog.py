from __future__ import annotations

import pytest

from app import calculate_pro, calculate_simple
from data.catalogs import WASHER_CATALOG
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from data.washer_access import (
    EXTRA_DRYERS_POWER_DELTA_KW,
    effective_power_kw,
    get_washer_model,
    resolve_model_code,
    supports_extra_dryers,
)
from dataclasses import replace
from domain.params import SimpleParams
from ui.scenario_io import (
    ScenarioValidationError,
    deserialize_simple_params,
    serialize_simple_params,
)


def test_active_catalog_has_six_models_without_s90() -> None:
    assert set(WASHER_CATALOG.keys()) == {
        "L360",
        "L360_MINI",
        "L370_PLUS",
        "L380_PLUS",
        "L_SG",
        "L_DG",
    }
    assert "L_S90" not in WASHER_CATALOG


def test_l360_water_per_wash_updated() -> None:
    assert WASHER_CATALOG["L360"].water_per_wash_l == 120  # спец. производителя: 120 л/цикл


def test_l370_plus_core_specs() -> None:
    model = WASHER_CATALOG["L370_PLUS"]
    assert model.name == "Leisuwash 370 Plus"
    assert model.power_kw == 28
    assert model.water_per_wash_l == 110
    assert model.cycle_time_min == 5.0
    assert model.cars_per_hour == 12


def test_l_sg_replaces_s90_baseline_with_updates() -> None:
    model = WASHER_CATALOG["L_SG"]
    assert model.name == "Leisuwash SG"
    assert model.power_kw == 22
    assert model.water_per_wash_l == 100
    assert model.cars_per_hour == 14
    assert model.cycle_time_min == 4.0


def test_legacy_s90_alias_resolves_to_sg() -> None:
    assert resolve_model_code("L_S90") == "L_SG"
    assert get_washer_model("L_S90", WASHER_CATALOG).code == "L_SG"


def test_legacy_s90_scenario_deserializes_to_sg() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    raw["model_code"] = "L_S90"
    params = deserialize_simple_params(raw)
    assert params.model_code == "L_SG"
    res = calculate_simple(params)
    assert res.params.model_code == "L_SG"


def test_extra_dryers_supported_only_for_four_models() -> None:
    assert supports_extra_dryers("L360")
    assert supports_extra_dryers("L360_MINI")
    assert supports_extra_dryers("L370_PLUS")
    assert supports_extra_dryers("L380_PLUS")
    assert not supports_extra_dryers("L_SG")
    assert not supports_extra_dryers("L_DG")
    assert not supports_extra_dryers("L_S90")


def test_effective_power_kw_adds_delta_when_enabled() -> None:
    model = WASHER_CATALOG["L380_PLUS"]
    assert effective_power_kw(model, extra_dryers_enabled=False) == 24
    assert effective_power_kw(model, extra_dryers_enabled=True) == 24 + EXTRA_DRYERS_POWER_DELTA_KW


def test_extra_dryers_ignored_for_sg_on_deserialize() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    raw["model_code"] = "L_SG"
    raw["extra_dryers_enabled"] = True
    params = deserialize_simple_params(raw)
    assert params.model_code == "L_SG"
    assert params.extra_dryers_enabled is False


def test_old_scenario_without_extra_dryers_field_loads() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    del raw["extra_dryers_enabled"]
    params = deserialize_simple_params(raw)
    assert params.extra_dryers_enabled is False


def test_extra_dryers_increase_electricity_opex_and_npv() -> None:
    base = build_sample_simple_params()
    with_dryers = replace(base, extra_dryers_enabled=True)
    base_res = calculate_simple(base)
    dry_res = calculate_simple(with_dryers)
    assert dry_res.npv < base_res.npv


def test_calculate_pro_with_extra_dryers_enabled() -> None:
    params = replace(build_sample_pro_params(), extra_dryers_enabled=True)
    res = calculate_pro(params)
    base = calculate_pro(build_sample_pro_params())
    assert res.npv < base.npv


def test_unknown_model_still_rejected() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    raw["model_code"] = "UNKNOWN"
    with pytest.raises(ScenarioValidationError, match="модель"):
        deserialize_simple_params(raw)
