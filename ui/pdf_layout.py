from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import PageBreak, Paragraph, Spacer
from reportlab.lib.units import mm

from ui.pdf_backend import (
    build_pdf_bytes,
    pdf_bullets,
    pdf_cover_block,
    pdf_paragraph,
    pdf_styles,
    pdf_table,
    _escape_pdf_text,
)
from ui.report_specs import (
    ComparisonReportSpec,
    ReportKpiRow,
    SimpleInvestmentReportSpec,
    SingleInvestmentReportSpec,
)


def _section_title(title: str, styles: dict) -> list:
    # keepWithNext: заголовок не должен оставаться внизу страницы без содержимого
    style = ParagraphStyle(
        "WBSectionKeep",
        parent=styles["section"],
        keepWithNext=1,
    )
    return [Paragraph(_escape_pdf_text(title), style)]


def _kpi_grid(rows: Sequence[ReportKpiRow], styles: dict) -> list:
    if not rows:
        return []
    table_rows = []
    for row in rows:
        hint = f" ({row.hint})" if row.hint else ""
        table_rows.append([row.label, f"{row.value}{hint}"])
    return [
        pdf_table(["Показатель", "Значение"], table_rows, col_widths=[70 * mm, 100 * mm]),
        Spacer(1, 3 * mm),
    ]


def _disclaimers(disclaimers: Sequence[str], styles: dict) -> list:
    flowables = [Spacer(1, 4 * mm), pdf_paragraph("Методология и оговорки", styles["section"])]
    for line in disclaimers:
        flowables.append(pdf_paragraph(line, styles["disclaimer"]))
    return flowables


def _cover_from_spec(
    spec: SingleInvestmentReportSpec | SimpleInvestmentReportSpec,
    styles: dict,
) -> list:
    return pdf_cover_block(
        spec.title,
        spec.subtitle,
        spec.report_type,
        spec.generated_at,
        styles,
        mode_label=spec.mode_label,
        status_label=spec.status_label,
    )


def _pro_executive_page(
    spec: SingleInvestmentReportSpec,
    styles: dict,
    section_title: str = "Исполнительное резюме",
) -> list:
    flowables: list = []
    flowables.extend(_section_title(section_title, styles))
    flowables.append(pdf_paragraph(spec.executive_headline, styles["body"]))
    flowables.extend(_kpi_grid(spec.kpi_rows[:5], styles))
    if spec.scenario_rows:
        flowables.append(pdf_paragraph("Диапазон сценариев", styles["body"]))
        scenario_lines = [
            f"{name} ({factor}): окупаемость {payback}, накопл. CF {cum}"
            for name, factor, payback, cum in spec.scenario_rows
        ]
        flowables.extend(pdf_bullets(scenario_lines, styles))
    if spec.risk_notes:
        flowables.append(pdf_paragraph("Ключевые риски", styles["body"]))
        flowables.extend(pdf_bullets(spec.risk_notes[:4], styles))
    if spec.memo_actions:
        flowables.append(pdf_paragraph("Рекомендация", styles["body"]))
        flowables.append(pdf_paragraph(spec.memo_actions[0], styles["body"]))
    elif spec.memo_headline:
        flowables.append(pdf_paragraph(spec.memo_headline, styles["body"]))
    return flowables


def _simple_executive_page(
    spec: SimpleInvestmentReportSpec,
    styles: dict,
    section_title: str = "Исполнительное резюме",
) -> list:
    flowables: list = []
    flowables.extend(_section_title(section_title, styles))
    flowables.append(pdf_paragraph(spec.verdict_headline, styles["body"]))
    flowables.extend(_kpi_grid(spec.kpi_rows[:5], styles))
    if spec.verdict_bullets:
        flowables.append(pdf_paragraph("Контекст", styles["body"]))
        flowables.extend(pdf_bullets(spec.verdict_bullets[:3], styles))
    if spec.insight_bullets:
        flowables.append(pdf_paragraph("Риски и наблюдения", styles["body"]))
        flowables.extend(pdf_bullets(spec.insight_bullets[:4], styles))
    return flowables


def render_executive_summary_pdf(
    spec: SingleInvestmentReportSpec | SimpleInvestmentReportSpec,
) -> bytes:
    # На обложке краткой версии не должно стоять название полного отчёта
    spec = replace(
        spec,
        title=f"Исполнительное резюме — {spec.mode_label}",
        report_type=f"{spec.report_type}_executive",
    )
    styles = pdf_styles()
    flowables: list = []
    flowables.extend(_cover_from_spec(spec, styles))
    if isinstance(spec, SingleInvestmentReportSpec):
        flowables.extend(_pro_executive_page(spec, styles, section_title="Ключевые выводы"))
    else:
        flowables.extend(_simple_executive_page(spec, styles, section_title="Ключевые выводы"))
    flowables.extend(_disclaimers(spec.disclaimers[:2], styles))
    return build_pdf_bytes(flowables)


def render_simple_spec_pdf(spec: SimpleInvestmentReportSpec) -> bytes:
    styles = pdf_styles()
    flowables: list = []
    flowables.extend(_cover_from_spec(spec, styles))
    flowables.extend(_simple_executive_page(spec, styles))
    flowables.extend(_section_title("Ключевые показатели", styles))
    flowables.extend(_kpi_grid(spec.kpi_rows, styles))
    flowables.extend(_section_title("Допущения", styles))
    assumption_rows = [[left, right] for left, right in spec.assumption_rows]
    flowables.append(
        pdf_table(["Параметр", "Значение"], assumption_rows, col_widths=[70 * mm, 100 * mm])
    )
    if spec.breakdown_lines or spec.insight_bullets:
        flowables.append(PageBreak())
        flowables.extend(_section_title("Приложение: детали", styles))
        if spec.breakdown_lines:
            flowables.append(pdf_paragraph("Структура выручки (год 1)", styles["body"]))
            flowables.extend(pdf_bullets(spec.breakdown_lines, styles))
        if spec.insight_bullets:
            flowables.append(pdf_paragraph("Наблюдения", styles["body"]))
            flowables.extend(pdf_bullets(spec.insight_bullets, styles))
    flowables.extend(_disclaimers(spec.disclaimers, styles))
    return build_pdf_bytes(flowables)


def render_pro_spec_pdf(spec: SingleInvestmentReportSpec) -> bytes:
    styles = pdf_styles()
    flowables: list = []
    flowables.extend(_cover_from_spec(spec, styles))
    flowables.extend(_pro_executive_page(spec, styles))
    flowables.extend(_section_title("Ключевые KPI", styles))
    flowables.extend(_kpi_grid(spec.kpi_rows, styles))
    flowables.extend(_section_title("Сценарии трафика", styles))
    scenario_rows = [[a, b, c, d] for a, b, c, d in spec.scenario_rows]
    flowables.append(
        pdf_table(
            ["Сценарий", "Множитель", "Окупаемость", "Накопл. CF"],
            scenario_rows,
            col_widths=[35 * mm, 30 * mm, 45 * mm, 60 * mm],
        )
    )
    if spec.sensitivity_bullets:
        flowables.extend(_section_title("Драйверы NPV", styles))
        flowables.extend(pdf_bullets(spec.sensitivity_bullets, styles))
    flowables.extend(_section_title("Операции и мощность", styles))
    flowables.extend(_kpi_grid(spec.capacity_rows, styles))
    flowables.extend(_section_title("Порог покрытия постоянных затрат", styles))
    flowables.extend(_kpi_grid(spec.break_even_rows, styles))
    if spec.break_even_note:
        flowables.append(pdf_paragraph(spec.break_even_note, styles["body"]))
    flowables.append(Spacer(1, 6 * mm))
    flowables.extend(_section_title("Допущения и риски", styles))
    assumption_rows = [[a, b, c] for a, b, c in spec.assumption_rows]
    flowables.append(
        pdf_table(
            ["Параметр", "Значение", "Комментарий"],
            assumption_rows,
            col_widths=[45 * mm, 55 * mm, 70 * mm],
        )
    )
    if spec.risk_notes:
        flowables.append(pdf_paragraph("Ключевые риски", styles["body"]))
        flowables.extend(pdf_bullets(spec.risk_notes, styles))
    flowables.extend(_section_title("Инвестиционный меморандум", styles))
    flowables.append(pdf_paragraph(spec.memo_headline, styles["body"]))
    for group_title, bullets in spec.memo_groups:
        flowables.append(pdf_paragraph(group_title, styles["body"]))
        flowables.extend(pdf_bullets(bullets, styles))
    if spec.memo_actions:
        flowables.append(pdf_paragraph("Рекомендуемые действия", styles["body"]))
        flowables.extend(pdf_bullets(spec.memo_actions, styles))
    flowables.extend(_section_title("Приложение: детализирующие показатели", styles))
    flowables.extend(_kpi_grid(spec.detail_rows, styles))
    flowables.extend(_disclaimers(spec.disclaimers, styles))
    return build_pdf_bytes(flowables)


def _comparison_matrix_table(spec: ComparisonReportSpec, styles: dict) -> list:
    comp = spec.comparison
    headers = ["Показатель"] + [v.label for v in comp.variants]
    rows = []
    baseline_idx = next(
        (i for i, v in enumerate(comp.variants) if v.variant_id == comp.baseline_id),
        0,
    )
    for row in comp.rows:
        cells = [row.label]
        for idx, value in enumerate(row.values):
            delta = row.deltas[idx] if idx < len(row.deltas) else ""
            if idx == baseline_idx or delta in ("база", "0", "—"):
                cells.append(value)
            else:
                cells.append(f"{value} ({delta})")
        rows.append(cells)
    col_count = len(headers)
    label_width = 48 * mm
    variant_width = max(35 * mm, (122 * mm) / max(col_count - 1, 1))
    col_widths = [label_width] + [variant_width] * (col_count - 1)
    return [pdf_table(headers, rows, col_widths=col_widths), Spacer(1, 3 * mm)]


def render_comparison_spec_pdf(spec: ComparisonReportSpec) -> bytes:
    styles = pdf_styles()
    flowables: list = []
    flowables.extend(
        pdf_cover_block(
            spec.title,
            spec.subtitle,
            spec.report_type,
            spec.generated_at,
            styles,
            mode_label="Pro",
            status_label=f"База: {spec.baseline_label}",
        )
    )
    flowables.extend(_section_title("Ключевые trade-offs", styles))
    flowables.extend(pdf_bullets(spec.factual_bullets, styles))
    if spec.narrative_bullets:
        flowables.extend(_section_title("Краткие выводы", styles))
        flowables.extend(pdf_bullets(spec.narrative_bullets, styles))
    flowables.extend(_section_title("Матрица сравнения", styles))
    flowables.extend(_comparison_matrix_table(spec, styles))
    flowables.extend(_section_title("Приложение: варианты", styles))
    variant_lines = [
        f"{line.label}{' (база)' if line.is_baseline else ''}"
        for line in spec.variants
    ]
    flowables.extend(pdf_bullets(variant_lines, styles))
    if spec.chart_summary_lines:
        flowables.extend(pdf_bullets(spec.chart_summary_lines, styles))
    flowables.extend(_disclaimers(spec.disclaimers, styles))
    return build_pdf_bytes(flowables)
