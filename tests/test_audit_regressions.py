"""Регрессионные тесты по итогам аудита (ноябрь 2026)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from app import calculate_pro, calculate_simple
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from finance.sensitivity import evaluate_pro_sensitivity_case
from finance.taxes import patent_cost_month_for_region
from ui.scenario_io import (
    deserialize_pro_params,
    serialize_pro_params,
)


def test_osno_vat_is_inside_price_not_on_top() -> None:
    """НДС на ОСНО считается «изнутри» цены минус входящий НДС."""
    from finance.taxation import calculate_tax_for_year

    res = calculate_tax_for_year(
        revenue_year=10_000_000,
        taxable_profit_year=2_000_000,
        tax_regime="OSNO",
        vat_input_base_year=4_000_000,
    )
    expected_vat = (10_000_000 - 4_000_000) * 0.22 / 1.22
    assert res["vat"] == pytest.approx(expected_vat, rel=1e-9)
    assert res["tax"] == pytest.approx(0.25 * (2_000_000 - expected_vat), rel=1e-9)


def test_patent_scales_with_headcount() -> None:
    one = patent_cost_month_for_region("MSK", 1)
    two = patent_cost_month_for_region("MSK", 2)
    assert two == pytest.approx(one * 2)


def test_patent_charged_even_with_zero_revenue() -> None:
    base = build_sample_pro_params()
    res = calculate_pro(replace(base, tax_regime="PATENT", cars_per_day_avg=0.0))
    assert float(np.mean(res.tax_month)) > 0


def test_sensitivity_baseline_equals_main_npv() -> None:
    params = replace(build_sample_pro_params(), nv_norm_enabled=True, nv_over_enabled=True)
    main = calculate_pro(params).npv
    sens = evaluate_pro_sensitivity_case(params)
    assert sens == pytest.approx(main, rel=1e-6)


def test_opex_breakdown_reconciles_with_profit_and_loss() -> None:
    res = calculate_pro(build_sample_pro_params())
    n = 12
    pnl_costs = float(np.sum(res.revenue_month[:n] - res.profit_month[:n]))
    breakdown = sum(res.opex_breakdown_year1.values())
    assert breakdown == pytest.approx(pnl_costs, rel=1e-6)


def test_scenario_roundtrip_keeps_nv_and_tariffs() -> None:
    params = replace(
        build_sample_pro_params(),
        nv_norm_enabled=True,
        water_supply_override=70.0,
        elec_price_override=9.5,
    )
    restored = deserialize_pro_params(serialize_pro_params(params))
    assert restored.nv_norm_enabled is True
    assert restored.water_supply_override == pytest.approx(70.0)
    assert restored.elec_price_override == pytest.approx(9.5)


def test_simple_amortization_reduces_tax_base_for_profit_regimes() -> None:
    base = replace(build_sample_simple_params(), tax_regime="USN_PROFIT")
    five = calculate_simple(replace(base, amort_years_equipment=5))
    ten = calculate_simple(replace(base, amort_years_equipment=10))
    # более длинная амортизация → меньше расходов → больше EBT и прибыль
    assert ten.avg_profit_month > five.avg_profit_month
