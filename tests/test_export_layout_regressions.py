from __future__ import annotations

from dataclasses import replace

from reportlab.platypus import Paragraph, Table

from app import calculate_pro
from data.sample_params import build_sample_pro_params
from ui.exports import build_pro_monthly_export_df
from ui.pdf_backend import pdf_table


def test_pdf_table_cells_are_wrapping_paragraphs() -> None:
    """Длинные тексты должны переноситься внутри колонки, а не вылезать за страницу."""
    table = pdf_table(
        ["Параметр", "Значение", "Комментарий"],
        [["Сезонность", "ноябрь–май", "очень длинный комментарий, который обязан переноситься"]],
        col_widths=[45, 55, 70],
    )
    assert isinstance(table, Table)
    for row in table._cellvalues:
        for cell in row:
            assert isinstance(cell, Paragraph)


def test_monthly_export_rows_sum_to_model_totals() -> None:
    """CSV-выгрузка не должна терять точность на округлении авто/мес."""
    result = calculate_pro(build_sample_pro_params())
    df = build_pro_monthly_export_df(result)
    assert abs(df["Авто"].sum() - float(result.cars_per_month.sum())) < 0.5
    assert abs(df["Выручка"].sum() - result.total_revenue) < 1.0
    assert abs(df["Прибыль"].sum() - result.total_profit) < 1.0


def test_compare_payback_delta_has_unit() -> None:
    """В матрице сравнения разница по окупаемости должна быть в месяцах."""
    from ui.compare_specs import build_variant_snapshot
    from ui.report_specs import build_comparison_report_spec

    base_params = build_sample_pro_params()
    base = calculate_pro(base_params)
    faster = replace(base_params, cars_per_day_avg=base_params.cars_per_day_avg * 1.3)
    variants = (
        build_variant_snapshot("v1", "База", base_params, base),
        build_variant_snapshot("v2", "Трафик +30%", faster, calculate_pro(faster)),
    )
    spec = build_comparison_report_spec(variants, baseline_id="v1")
    payback_row = next(row for row in spec.comparison.rows if "Окупаемость" == row.label)
    assert any("мес" in delta for delta in payback_row.deltas if delta not in ("база", ""))
