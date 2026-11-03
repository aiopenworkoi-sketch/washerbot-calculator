from __future__ import annotations

import math
from dataclasses import replace

import pytest

from app import calculate_pro, calculate_simple
from data.sample_params import (
    build_sample_pro_overload_params,
    build_sample_pro_params,
    build_sample_simple_params,
)
from finance.capacity import build_capacity_diagnostics
from finance.model_constants import NPV_DISCOUNT_RATE_ANNUAL
from ui.compare_specs import (
    build_pro_comparison_specs,
    build_variant_snapshot,
)
from ui.display_fallbacks import has_finite_payback_months, missing_placeholder
from ui.exports import serialize_pro_result
from ui.model_constants import NPV_DISCOUNT_RATE_ANNUAL as UI_NPV_RATE


def test_calculate_simple_smoke() -> None:
    res = calculate_simple(build_sample_simple_params())
    assert math.isfinite(res.npv)
    assert math.isfinite(res.payback_months) or res.payback_months <= 0
    assert len(res.months) == res.params.horizon_months


def test_calculate_pro_smoke() -> None:
    res = calculate_pro(build_sample_pro_params())
    assert math.isfinite(res.npv)
    assert res.capex_total > 0
    assert len(res.sensitivity) >= 0


def test_serialize_pro_result_smoke() -> None:
    res = calculate_pro(build_sample_pro_params())
    payload = serialize_pro_result(res)
    assert isinstance(payload, dict)
    assert "npv" in payload
    assert "payback_months" in payload
    assert payload["npv"] == res.npv


def test_compare_specs_two_variants() -> None:
    base = calculate_pro(build_sample_pro_params())
    alt = calculate_pro(build_sample_pro_overload_params())
    snapshots = (
        build_variant_snapshot("a", "База", base.params, base),
        build_variant_snapshot("b", "Перегруз", alt.params, alt),
    )
    spec = build_pro_comparison_specs(snapshots, baseline_id="a")
    assert len(spec.rows) >= 5
    assert len(spec.variants) == 2
    payback_row = next(r for r in spec.rows if r.metric_key == "payback")
    assert len(payback_row.values) == 2


def test_compare_missing_payback_handling() -> None:
    base = calculate_pro(build_sample_pro_params())
    missing = replace(
        base,
        payback_months=float("nan"),
        payback_pessim=float("inf"),
        payback_optim=-1.0,
    )
    snapshots = (
        build_variant_snapshot("a", "База", base.params, base),
        build_variant_snapshot("b", "Нет окупаемости", missing.params, missing),
    )
    spec = build_pro_comparison_specs(snapshots, baseline_id="a")
    payback_row = next(r for r in spec.rows if r.metric_key == "payback")
    assert payback_row.values[1] == missing_placeholder()
    assert payback_row.deltas[1] == missing_placeholder()
    chart = spec.chart
    payback_trace = chart.data[1]
    assert payback_trace.y[1] is None
    assert payback_trace.text[1] == "не окупается"
    assert not has_finite_payback_months(missing.payback_months)


def test_capacity_diagnostics_smoke() -> None:
    params = build_sample_pro_overload_params()
    res = calculate_pro(params)
    capacity = [100.0] * len(res.cars_per_month)
    diag = build_capacity_diagnostics(
        demand=res.cars_per_month,
        capacity=capacity,
    )
    assert diag.annual_unserved_demand >= 0
    assert math.isfinite(diag.annual_unserved_share)


def test_discount_rate_single_source() -> None:
    assert NPV_DISCOUNT_RATE_ANNUAL == UI_NPV_RATE == 0.18


def test_ui_does_not_import_app() -> None:
    import ast
    from pathlib import Path

    ui_dir = Path("ui")
    for path in ui_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "app":
                pytest.fail(f"{path} imports app")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "app":
                        pytest.fail(f"{path} imports app")
