from __future__ import annotations

from app import calculate_pro, calculate_simple
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from ui.card_specs import build_pro_kpi_card_specs, build_simple_kpi_card_specs
from ui.format_policies import format_kpi_payback, format_kpi_payback_compact
from ui.kpi_cards import MetricCardSpec, metric_card_html, resolve_kpi_grid_cols


def test_format_kpi_payback_compact_matches_full_style() -> None:
    """Единый формат: карточки и текст отчёта пишут окупаемость одинаково."""
    months = 37.0
    full = format_kpi_payback(months)
    compact = format_kpi_payback_compact(months)
    assert compact == full == "3 года 1 мес"


def test_simple_kpi_cards_use_same_payback_style() -> None:
    res = calculate_simple(build_sample_simple_params())
    specs = build_simple_kpi_card_specs(res)
    payback_card = specs[0]
    assert payback_card.label == "Срок окупаемости"
    assert payback_card.value == format_kpi_payback(res.payback_months)


def test_kpi_grid_html_has_equal_height_structure() -> None:
    res = calculate_pro(build_sample_pro_params())
    specs = build_pro_kpi_card_specs(res)
    html = "".join(metric_card_html(spec) for spec in specs)
    assert "wb-metric-body" in html
    assert "wb-metric-label--clamp" in html
    assert "wb-metric-hint--clamp" in html
    assert "wb-metric-hint--empty" in html or "wb-metric-hint--clamp" in html
    assert html.count("wb-metric-label--clamp") == len(specs)


def test_resolve_kpi_grid_cols() -> None:
    assert resolve_kpi_grid_cols(1) == 1
    assert resolve_kpi_grid_cols(2) == 2
    assert resolve_kpi_grid_cols(3) == 3
    assert resolve_kpi_grid_cols(8, desktop_cols=4) == 4
    assert resolve_kpi_grid_cols(3, desktop_cols=4) == 3
    assert resolve_kpi_grid_cols(5, desktop_cols=2) == 2


def test_long_kpi_content_has_clamp_classes() -> None:
    spec = MetricCardSpec(
        "Срок окупаемости",
        "3 г 1 мес",
        "при инвестициях 15,00 млн ₽ и очень длинном пояснении для проверки переноса",
    )
    html = metric_card_html(spec)
    assert "wb-metric-label--clamp" in html
    assert "wb-metric-hint--clamp" in html
    assert "Срок окупаемости" in html


def test_pro_kpi_payback_card_not_overlong() -> None:
    res = calculate_pro(build_sample_pro_params())
    payback = build_pro_kpi_card_specs(res)[0].value
    assert len(payback) <= 16
