from __future__ import annotations

from app import calculate_pro, calculate_simple
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from ui.hero_specs import (
    build_pro_executive_hero_spec,
    build_simple_executive_hero_spec,
    render_executive_hero_html,
)


def test_simple_hero_has_four_metrics_and_status() -> None:
    res = calculate_simple(build_sample_simple_params())
    spec = build_simple_executive_hero_spec(res)
    assert spec.status_label in {"Привлекательно", "Умеренно", "Требует проверки", "Не проходит порог"}
    assert len(spec.metrics) == 4
    assert spec.metrics[0].label == "Окупаемость"


def test_render_executive_hero_html_contains_headline() -> None:
    res = calculate_simple(build_sample_simple_params())
    spec = build_simple_executive_hero_spec(res)
    html_out = render_executive_hero_html(spec)
    assert "wb-hero" in html_out
    assert spec.headline in html_out
    assert "wb-hero-metric" in html_out
    assert "payback" not in html_out.lower()


def test_pro_hero_reuses_verdict_headline() -> None:
    res = calculate_pro(build_sample_pro_params())
    spec = build_pro_executive_hero_spec(res)
    assert spec.headline
    assert len(spec.metrics) == 4
    from ui.model_constants import format_npv_kpi_label
    assert spec.metrics[1].label == format_npv_kpi_label()
