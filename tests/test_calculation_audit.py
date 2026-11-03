from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from app import calculate_pro, calculate_simple
from data.catalogs import PROGRAMS_DEFAULT, REGIONS, WASHER_CATALOG
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from data.washer_access import effective_power_kw, get_washer_model
from finance.program_mix import compute_program_mix
from finance.var_cost_per_wash import compute_var_cost_per_wash
from finance.variable_costs import EXTRA_DRYER_RUNTIME_SEC_PER_WASH, extra_dryer_kwh_per_wash
from finance.water_discharge import WATER_PROFILE_TYPICAL_CAR_WASH_LT30
from finance.water_usage import (
    estimated_water_m3_per_day,
    is_typical_lt30_profile_exceeded,
    water_usage_assumption_value,
)
from finance.opex import calculate_water_cost_per_m3
from ui.assumption_specs import assumption_row_value, build_pro_assumption_snapshot
from ui.report_specs import build_simple_investment_report_spec, build_single_investment_report_spec
from ui.scenario_io import (
    assert_params_roundtrip_equal,
    build_scenario_payload,
    deserialize_simple_params,
    params_from_scenario_payload,
    serialize_simple_params,
)

DEFAULT_EXPECTED_AVG_CHECK = 520.0
DEFAULT_EXPECTED_WATER_FACTOR = 0.92
DEFAULT_EXPECTED_ELEC_FACTOR = 0.905
DEFAULT_EXPECTED_CHEM_FACTOR = 0.955
DEFAULT_EXPECTED_WEIGHTED_DURATION_MIN = 5.15

OLD_3_PROGRAM_SCENARIO = {
    "EXPRESS": (300.0, 0.30),
    "STANDARD": (500.0, 0.50),
    "PREMIUM": (800.0, 0.20),
}


def _params_with_default_catalog() -> tuple:
    simple = replace(build_sample_simple_params(), programs=[deepcopy(p) for p in PROGRAMS_DEFAULT])
    pro = replace(build_sample_pro_params(), programs=[deepcopy(p) for p in PROGRAMS_DEFAULT])
    return simple, pro


def test_default_program_shares_sum_to_one() -> None:
    total = sum(program.share_default for program in PROGRAMS_DEFAULT)
    assert total == pytest.approx(1.0)
    assert len(PROGRAMS_DEFAULT) == 5


def test_default_mix_average_ticket_is_520() -> None:
    mix = compute_program_mix(PROGRAMS_DEFAULT)
    assert mix.avg_check == pytest.approx(DEFAULT_EXPECTED_AVG_CHECK)
    assert mix.program_count == 5


def test_default_weighted_factors_and_duration() -> None:
    mix = compute_program_mix(PROGRAMS_DEFAULT)
    assert mix.avg_water_factor == pytest.approx(DEFAULT_EXPECTED_WATER_FACTOR)
    assert mix.avg_elec_factor == pytest.approx(DEFAULT_EXPECTED_ELEC_FACTOR)
    assert mix.avg_chem_factor == pytest.approx(DEFAULT_EXPECTED_CHEM_FACTOR)
    assert mix.weighted_duration_min == pytest.approx(DEFAULT_EXPECTED_WEIGHTED_DURATION_MIN)


def test_average_ticket_matches_simple_and_pro_runtime() -> None:
    simple_params, pro_params = _params_with_default_catalog()
    assert calculate_simple(simple_params).avg_check == pytest.approx(DEFAULT_EXPECTED_AVG_CHECK)
    assert calculate_pro(pro_params).avg_check == pytest.approx(DEFAULT_EXPECTED_AVG_CHECK)


def test_average_ticket_matches_assumptions_and_reports() -> None:
    _, pro_params = _params_with_default_catalog()
    pro_result = calculate_pro(pro_params)
    assumptions = build_pro_assumption_snapshot(pro_result)
    assert assumption_row_value(assumptions, "Средний чек") is not None

    simple_result = calculate_simple(replace(build_sample_simple_params(), programs=[deepcopy(p) for p in PROGRAMS_DEFAULT]))
    simple_report = build_simple_investment_report_spec(simple_result)
    pro_report = build_single_investment_report_spec(pro_result)

    assert simple_result.avg_check == pytest.approx(DEFAULT_EXPECTED_AVG_CHECK)
    assert pro_result.avg_check == pytest.approx(DEFAULT_EXPECTED_AVG_CHECK)
    assert any("520" in line for line in simple_report.config_lines)
    assert any("520" in line for line in pro_report.config_lines)


def test_var_cost_breakdown_equals_total_simple() -> None:
    params = replace(build_sample_simple_params(), programs=[deepcopy(p) for p in PROGRAMS_DEFAULT])
    result = calculate_simple(params)
    breakdown_total = sum(result.breakdown_year1[k] for k in ("Вода", "Электричество", "Химия"))
    var_total_year = float(result.var_costs_month[:12].sum())
    assert breakdown_total == pytest.approx(var_total_year, rel=1e-6)


def test_var_cost_breakdown_equals_total_pro() -> None:
    params = replace(build_sample_pro_params(), programs=[deepcopy(p) for p in PROGRAMS_DEFAULT])
    result = calculate_pro(params)
    breakdown_total = sum(result.opex_breakdown_year1[k] for k in ("Вода", "Электричество", "Химия"))
    var_total_year = float(result.var_costs_month[:12].sum())
    assert breakdown_total == pytest.approx(var_total_year, rel=1e-6)


def test_var_cost_per_wash_helper_matches_runtime() -> None:
    params = replace(build_sample_simple_params(), programs=[deepcopy(p) for p in PROGRAMS_DEFAULT])
    model = get_washer_model(params.model_code, WASHER_CATALOG)
    region = REGIONS[params.region_key]
    mix = compute_program_mix(params.programs)
    water_tariff = calculate_water_cost_per_m3(
        supply=region.water_supply,
        sewage=region.water_sewage,
        profile=params.water_discharge_profile,
    )
    breakdown = compute_var_cost_per_wash(
        model=model,
        mix=mix,
        water_cost_per_m3=water_tariff,
        elec_price=region.elec_price,
        extra_dryers_enabled=params.extra_dryers_enabled,
    )
    result = calculate_simple(params)
    per_wash_total = breakdown.total
    implied_per_wash = float(result.var_costs_month[0] / max(result.cars_per_month[0], 1e-9))
    assert per_wash_total == pytest.approx(implied_per_wash, rel=1e-6)
    assert breakdown.total == pytest.approx(
        breakdown.water + breakdown.electricity + breakdown.chemistry
    )


def test_extra_dryers_power_kwh_and_capacity_behavior() -> None:
    base_params = replace(
        build_sample_simple_params(),
        programs=[deepcopy(p) for p in PROGRAMS_DEFAULT],
        extra_dryers_enabled=False,
    )
    dryer_params = replace(base_params, extra_dryers_enabled=True)
    model = get_washer_model(base_params.model_code, WASHER_CATALOG)

    assert effective_power_kw(model, extra_dryers_enabled=False) == pytest.approx(model.power_kw)
    assert effective_power_kw(model, extra_dryers_enabled=True) == pytest.approx(model.power_kw + 11.0)

    kwh = extra_dryer_kwh_per_wash(extra_dryers_enabled=True, model_code=base_params.model_code)
    assert kwh == pytest.approx(11.0 * EXTRA_DRYER_RUNTIME_SEC_PER_WASH / 3600.0)

    base = calculate_simple(base_params)
    with_dryers = calculate_simple(dryer_params)
    assert with_dryers.cars_per_month[0] == pytest.approx(base.cars_per_month[0])
    assert with_dryers.var_costs_month[0] > base.var_costs_month[0]


def test_extra_dryers_assumption_note_mentions_throughput() -> None:
    params = replace(
        build_sample_pro_params(),
        programs=[deepcopy(p) for p in PROGRAMS_DEFAULT],
        extra_dryers_enabled=True,
    )
    result = calculate_pro(params)
    assumptions = build_pro_assumption_snapshot(result)
    dryer_row = next(row for row in assumptions.rows if row.label == "Доп. сушки")
    assert "пропускная способность не корректировалась" in dryer_row.note.lower()


def test_water_guardrail_threshold_cases() -> None:
    l380 = get_washer_model("L380_PLUS", WASHER_CATALOG)
    l370 = get_washer_model("L370_PLUS", WASHER_CATALOG)
    assert estimated_water_m3_per_day(288, l380.water_per_wash_l) == pytest.approx(34.56)
    assert estimated_water_m3_per_day(288, l370.water_per_wash_l) == pytest.approx(31.68)
    assert not is_typical_lt30_profile_exceeded(
        profile=WATER_PROFILE_TYPICAL_CAR_WASH_LT30,
        cars_per_day=240,
        water_per_wash_l=l380.water_per_wash_l,
    )
    assert is_typical_lt30_profile_exceeded(
        profile=WATER_PROFILE_TYPICAL_CAR_WASH_LT30,
        cars_per_day=288,
        water_per_wash_l=l370.water_per_wash_l,
    )


def test_water_guardrail_in_assumptions_and_report() -> None:
    params = replace(
        build_sample_pro_params(),
        model_code="L370_PLUS",
        cars_per_day_avg=288.0,
        water_discharge_profile=WATER_PROFILE_TYPICAL_CAR_WASH_LT30,
        programs=[deepcopy(p) for p in PROGRAMS_DEFAULT],
    )
    result = calculate_pro(params)
    model = get_washer_model(params.model_code, WASHER_CATALOG)
    assumptions = build_pro_assumption_snapshot(result)
    assert assumption_row_value(assumptions, "Оценочный расход воды, м³/сутки") == water_usage_assumption_value(
        params.cars_per_day_avg,
        model.water_per_wash_l,
    )
    water_row = next(row for row in assumptions.rows if row.label == "Оценочный расход воды, м³/сутки")
    assert "превышает лимит" in water_row.note

    report = build_single_investment_report_spec(result)
    assert any("31,68" in line and "превышен лимит" in line for line in report.config_lines)


def test_old_three_program_scenario_load_merge_and_roundtrip() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    raw["programs"] = [
        {"code": code, "price_rub": price, "share": share}
        for code, (price, share) in OLD_3_PROGRAM_SCENARIO.items()
    ]
    params = deserialize_simple_params(raw)
    assert len(params.programs) == 5
    loaded_codes = {program.code for program in params.programs if program.share_default > 0}
    assert loaded_codes == set(OLD_3_PROGRAM_SCENARIO.keys())
    zero_share_codes = {
        program.code for program in params.programs if program.share_default == 0.0
    }
    assert zero_share_codes == {"exterior_only", "vip"}

    mix = compute_program_mix(params.programs)
    assert mix.avg_check == pytest.approx(500.0)
    assert mix.total_share == pytest.approx(1.0)

    payload = build_scenario_payload("simple", params, title="legacy-3")
    mode, restored = params_from_scenario_payload(payload)
    assert mode == "simple"
    assert_params_roundtrip_equal(params, restored)


def test_body_only_alias_maps_to_technical_name() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    raw["programs"] = [
        {"code": "body_only", "price_rub": 100, "share": 0.10},
        {"code": "EXPRESS", "price_rub": 300, "share": 0.35},
        {"code": "STANDARD", "price_rub": 500, "share": 0.30},
        {"code": "PREMIUM", "price_rub": 900, "share": 0.15},
        {"code": "vip", "price_rub": 1200, "share": 0.10},
    ]
    params = deserialize_simple_params(raw)
    technical = next(program for program in params.programs if program.code == "exterior_only")
    assert technical.name == "Техническая"
    assert "Только кузов" not in {program.name for program in params.programs}
