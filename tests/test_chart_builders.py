from __future__ import annotations

from ui.chart_builders import build_sorted_horizontal_bar_figure


def test_horizontal_bar_sorted_ascending_by_value() -> None:
    fig = build_sorted_horizontal_bar_figure(
        ["Налог", "Аренда", "ЗП"],
        [100.0, 300.0, 200.0],
        palette="cost",
    )
    trace = fig.data[0]
    assert list(trace.y) == ["Налог", "ЗП", "Аренда"]
    assert list(trace.x) == [100.0, 200.0, 300.0]
    assert trace.orientation == "h"


def test_horizontal_bar_skips_non_positive() -> None:
    fig = build_sorted_horizontal_bar_figure(
        ["A", "B"],
        [0.0, 50.0],
        palette="capex",
    )
    assert len(fig.data[0].y) == 1
    assert fig.data[0].y[0] == "B"
