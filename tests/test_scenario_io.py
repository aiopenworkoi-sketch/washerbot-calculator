from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app import calculate_pro, calculate_simple
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from domain.params import ProParams, SimpleParams
from ui.exports import serialize_pro_result, serialize_simple_result
from ui.scenario_io import (
    SCENARIO_SCHEMA_VERSION,
    ScenarioValidationError,
    assert_params_roundtrip_equal,
    build_scenario_payload,
    deserialize_pro_params,
    deserialize_simple_params,
    params_from_scenario_payload,
    parse_scenario_json,
    scenario_payload_to_json,
    scenario_to_widget_state,
    serialize_pro_params,
    serialize_simple_params,
    validate_scenario_payload,
)
from ui.scenario_state import (
    apply_pending_scenario_hydration,
    delete_session_scenario,
    duplicate_session_scenario,
    list_session_scenarios,
    queue_scenario_apply,
    save_scenario_to_session,
)


def test_serialize_simple_scenario_payload() -> None:
    params = build_sample_simple_params()
    payload = build_scenario_payload("simple", params, title="База", note="тест")
    assert payload["schema_version"] == SCENARIO_SCHEMA_VERSION
    assert payload["mode"] == "simple"
    assert payload["title"] == "База"
    assert payload["params"]["model_code"] == params.model_code
    assert len(payload["params"]["programs"]) == 5


def test_serialize_pro_scenario_payload() -> None:
    params = build_sample_pro_params()
    payload = build_scenario_payload("pro", params, title="Pro base")
    assert payload["mode"] == "pro"
    assert payload["params"]["use_credit"] is True
    assert "scenario_pessim_factor" in payload["params"]


def test_roundtrip_simple_params() -> None:
    original = build_sample_simple_params()
    payload = build_scenario_payload("simple", original)
    mode, restored = params_from_scenario_payload(payload)
    assert mode == "simple"
    assert isinstance(restored, SimpleParams)
    assert_params_roundtrip_equal(original, restored)


def test_roundtrip_pro_params() -> None:
    original = build_sample_pro_params()
    payload = build_scenario_payload("pro", original)
    mode, restored = params_from_scenario_payload(payload)
    assert mode == "pro"
    assert isinstance(restored, ProParams)
    assert_params_roundtrip_equal(original, restored)


def test_roundtrip_via_json_file_text() -> None:
    original = build_sample_simple_params()
    text = scenario_payload_to_json(build_scenario_payload("simple", original, title="JSON"))
    parsed = parse_scenario_json(text)
    mode, restored = params_from_scenario_payload(parsed)
    assert mode == "simple"
    assert_params_roundtrip_equal(original, restored)


def test_invalid_json_raises() -> None:
    with pytest.raises(ScenarioValidationError, match="JSON"):
        parse_scenario_json("{not json")


def test_invalid_schema_version() -> None:
    payload = build_scenario_payload("simple", build_sample_simple_params())
    payload["schema_version"] = 99
    with pytest.raises(ScenarioValidationError, match="версия"):
        validate_scenario_payload(payload)


def test_invalid_mode() -> None:
    payload = build_scenario_payload("simple", build_sample_simple_params())
    payload["mode"] = "ultra"
    with pytest.raises(ScenarioValidationError, match="mode"):
        validate_scenario_payload(payload)


def test_missing_required_param_field() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    del raw["total_investment"]
    with pytest.raises(ScenarioValidationError, match="total_investment"):
        deserialize_simple_params(raw)


def test_unknown_program_code_rejected() -> None:
    raw = serialize_simple_params(build_sample_simple_params())
    raw["programs"] = [{"code": "UNKNOWN", "price_rub": 100, "share": 0.5}]
    with pytest.raises(ScenarioValidationError, match="программы"):
        deserialize_simple_params(raw)


def test_extra_root_fields_are_ignored_on_validate() -> None:
    payload = build_scenario_payload("simple", build_sample_simple_params())
    payload["future_field"] = {"nested": True}
    validated = validate_scenario_payload(payload)
    assert validated["mode"] == "simple"


def test_scenario_to_widget_state_simple_keys() -> None:
    params = build_sample_simple_params()
    state = scenario_to_widget_state("simple", params)
    assert state["s_horizon"] == params.horizon_months // 12
    assert "s_model" in state
    assert "s_prog_price_EXPRESS" in state


def test_scenario_to_widget_state_pro_credit_rate_percent() -> None:
    params = build_sample_pro_params()
    state = scenario_to_widget_state("pro", params)
    assert state["p_credit_rate"] == pytest.approx(params.credit_rate_annual * 100.0)
    assert state["p_eco_recycle"] == int(round(params.eco_water_recycle_pct * 100))


def test_session_scenario_crud() -> None:
    fake_state: dict = {}

    with patch("ui.scenario_state.st") as mock_st:
        mock_st.session_state = fake_state
        params = build_sample_simple_params()
        record = save_scenario_to_session("Тест 1", "simple", params, note="memo")
        assert record.name == "Тест 1"
        assert len(list_session_scenarios()) == 1

        dup = duplicate_session_scenario(record.scenario_id)
        assert dup is not None
        assert len(list_session_scenarios()) == 2

        assert delete_session_scenario(record.scenario_id) is True
        assert len(list_session_scenarios()) == 1


def test_loading_scenario_switches_mode() -> None:
    fake_state: dict = {"mode": "simple"}

    pro_payload = build_scenario_payload("pro", build_sample_pro_params(), title="Pro load")

    with patch("ui.scenario_state.st") as mock_st:
        mock_st.session_state = fake_state
        queue_scenario_apply(pro_payload)
        assert apply_pending_scenario_hydration() is True
        assert fake_state["mode"] == "pro"
        assert "p_horizon" in fake_state


def test_scenario_import_does_not_break_export_pipeline() -> None:
    simple_payload = build_scenario_payload("simple", build_sample_simple_params())
    _, simple_params = params_from_scenario_payload(simple_payload)
    simple_res = calculate_simple(simple_params)
    simple_export = serialize_simple_result(simple_res)
    assert "npv" in simple_export

    pro_payload = build_scenario_payload("pro", build_sample_pro_params())
    _, pro_params = params_from_scenario_payload(pro_payload)
    pro_res = calculate_pro(pro_params)
    pro_export = serialize_pro_result(pro_res)
    assert "npv" in pro_export


def test_compact_json_is_valid_and_smaller() -> None:
    payload = build_scenario_payload("simple", build_sample_simple_params(), title="x")
    pretty = scenario_payload_to_json(payload, compact=False)
    compact = scenario_payload_to_json(payload, compact=True)
    assert len(compact) < len(pretty)
    assert json.loads(compact)["mode"] == "simple"
