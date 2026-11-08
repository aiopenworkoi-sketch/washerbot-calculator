from __future__ import annotations

from dataclasses import replace

import csv
import html
import io
from dataclasses import dataclass
from typing import Sequence

from domain.results import ProResult, SimpleResult
from ui.compare_specs import CompareVariantSnapshot
from ui.report_layout import (
    REPORT_CSS,
    report_theme_css,
    config_summary_line,
    render_appendix,
    render_bullets,
    render_executive_summary_block,
    render_kpi_grid,
    render_report_cover,
    render_section,
)
from ui.report_specs import (
    COMPARISON_CSV_COLUMNS,
    ComparisonReportSpec,
    ReportKpiRow,
    SimpleInvestmentReportSpec,
    SingleInvestmentReportSpec,
    build_comparison_matrix_rows,
    build_comparison_report_spec,
    build_simple_investment_report_spec,
    build_single_investment_report_spec,
    report_file_timestamp,
)
from ui.report_text import humanize_report_type


@dataclass(frozen=True)
class ReportArtifact:
    filename: str
    mime: str
    content: bytes
    report_type: str = ""
    generated_at: str = ""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _render_html_document(
    title: str,
    body: str,
    *,
    report_type: str,
    generated_at: str,
    extra_meta: Sequence[tuple[str, str]] = (),
) -> str:
    meta_tags = [
        '<meta charset="utf-8">',
        f'<meta name="washerbot-report-type" content="{_esc(report_type)}">',
        f'<meta name="washerbot-generated-at" content="{_esc(generated_at)}">',
    ]
    for key, value in extra_meta:
        meta_tags.append(f'<meta name="{_esc(key)}" content="{_esc(value)}">')
    footer = (
        f'<div class="wb-print-footer">WasherBot · {_esc(humanize_report_type(report_type))} · '
        f"сформирован {_esc(generated_at)}</div>"
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="ru">\n<head>\n'
        f"<title>{_esc(title)}</title>\n"
        f"{''.join(meta_tags)}\n"
        f"<style>{REPORT_CSS}{report_theme_css()}</style>\n"
        "</head>\n<body>\n"
        f'<div class="wb-report">{body}{footer}</div>\n'
        "</body>\n</html>"
    )


def _report_cover_from_spec(
    spec: SingleInvestmentReportSpec | SimpleInvestmentReportSpec,
) -> str:
    return render_report_cover(
        title=spec.title,
        subtitle=spec.subtitle,
        mode_label=spec.mode_label,
        report_type_label=humanize_report_type(spec.report_type),
        generated_at=spec.generated_at,
        status_label=spec.status_label,
        status_severity=spec.status_severity,
        config_summary=config_summary_line(spec.config_lines),
    )


def _pro_executive_metrics(spec: SingleInvestmentReportSpec) -> tuple[ReportKpiRow, ...]:
    return spec.kpi_rows[:5]


def _pro_scenario_lines(spec: SingleInvestmentReportSpec) -> tuple[str, ...]:
    if not spec.scenario_rows:
        return ()
    lines = []
    for name, factor, payback, cum in spec.scenario_rows:
        lines.append(f"{name} ({factor}): окупаемость {payback}, накопл. CF {cum}")
    return tuple(lines)


def _pro_risk_flags(spec: SingleInvestmentReportSpec) -> tuple[str, ...]:
    flags = list(spec.risk_notes[:3])
    for row in spec.assumption_rows[:2]:
        if row[2]:
            flags.append(f"{row[0]}: {row[2]}")
    return tuple(flags[:4])


def _pro_recommendation(spec: SingleInvestmentReportSpec) -> str:
    if spec.memo_actions:
        return spec.memo_actions[0]
    return spec.memo_headline


def _simple_executive_metrics(spec: SimpleInvestmentReportSpec) -> tuple[ReportKpiRow, ...]:
    return spec.kpi_rows[:5]


def _simple_scenario_lines(spec: SimpleInvestmentReportSpec) -> tuple[str, ...]:
    return spec.verdict_bullets[:3]


def _simple_risk_flags(spec: SimpleInvestmentReportSpec) -> tuple[str, ...]:
    return spec.insight_bullets[:4]


def _simple_recommendation(spec: SimpleInvestmentReportSpec) -> str:
    if spec.insight_bullets:
        return spec.insight_bullets[0]
    return spec.verdict_headline


def _render_pro_executive_summary(spec: SingleInvestmentReportSpec) -> str:
    return render_executive_summary_block(
        headline=spec.executive_headline,
        metric_rows=_pro_executive_metrics(spec),
        scenario_lines=_pro_scenario_lines(spec),
        risk_flags=_pro_risk_flags(spec),
        recommendation=_pro_recommendation(spec),
        context_bullets=spec.executive_bullets,
    )


def _render_simple_executive_summary(spec: SimpleInvestmentReportSpec) -> str:
    return render_executive_summary_block(
        headline=spec.verdict_headline,
        metric_rows=_simple_executive_metrics(spec),
        scenario_lines=_simple_scenario_lines(spec),
        risk_flags=_simple_risk_flags(spec),
        recommendation=_simple_recommendation(spec),
        context_bullets=spec.verdict_bullets,
    )


def render_executive_summary_html(
    spec: SingleInvestmentReportSpec | SimpleInvestmentReportSpec,
) -> str:
    spec = replace(
        spec,
        title=f"Исполнительное резюме — {spec.mode_label}",
        report_type=f"{spec.report_type}_executive",
    )
    if isinstance(spec, SingleInvestmentReportSpec):
        cover = _report_cover_from_spec(spec)
        exec_block = _render_pro_executive_summary(spec)
        title = f"Исполнительное резюме — {spec.mode_label}"
    else:
        cover = _report_cover_from_spec(spec)
        exec_block = _render_simple_executive_summary(spec)
        title = f"Исполнительное резюме — {spec.mode_label}"
    disclaimer = f'<div class="wb-disclaimer">{render_bullets(spec.disclaimers[:2])}</div>'
    body = cover + exec_block + disclaimer
    return _render_html_document(
        title,
        body,
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def render_simple_report_html(spec: SimpleInvestmentReportSpec) -> str:
    assumption_rows = "".join(
        f"<tr><td>{_esc(label)}</td><td>{_esc(value)}</td></tr>"
        for label, value in spec.assumption_rows
    )
    body = (
        _report_cover_from_spec(spec)
        + _render_simple_executive_summary(spec)
        + render_section("Ключевые показатели", render_kpi_grid(spec.kpi_rows))
        + render_section("Допущения", f'<table class="wb-table"><tbody>{assumption_rows}</tbody></table>')
        + render_appendix(
            "Детали и структура расходов",
            render_bullets(spec.breakdown_lines)
            + "<h3>Наблюдения</h3>"
            + render_bullets(spec.insight_bullets),
        )
        + f'<div class="wb-disclaimer">{render_bullets(spec.disclaimers)}</div>'
    )
    return _render_html_document(
        spec.title,
        body,
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def render_single_report_html(spec: SingleInvestmentReportSpec) -> str:
    assumption_rows = "".join(
        f"<tr><td>{_esc(label)}</td><td>{_esc(value)}</td><td>{_esc(note)}</td></tr>"
        for label, value, note in spec.assumption_rows
    )
    scenario_rows = "".join(
        f"<tr><td>{_esc(name)}</td><td>{_esc(factor)}</td>"
        f"<td>{_esc(payback)}</td><td>{_esc(cum)}</td></tr>"
        for name, factor, payback, cum in spec.scenario_rows
    )
    memo_groups = []
    for title, items in spec.memo_groups:
        memo_groups.append(
            f'<div class="wb-memo-group"><div class="wb-memo-group-title">{_esc(title)}</div>'
            f"{render_bullets(items)}</div>"
        )
    body = (
        _report_cover_from_spec(spec)
        + _render_pro_executive_summary(spec)
        + render_section("Ключевые KPI", render_kpi_grid(spec.kpi_rows))
        + render_section(
            "Сценарии трафика",
            f'<table class="wb-table"><thead><tr><th>Сценарий</th><th>Множитель</th>'
            f"<th>Окупаемость</th><th>Накопл. CF</th></tr></thead>"
            f"<tbody>{scenario_rows}</tbody></table>",
        )
        + render_section("Драйверы NPV", render_bullets(spec.sensitivity_bullets))
        + render_section(
            "Операции и мощность",
            render_kpi_grid(spec.capacity_rows)
            + "<h3>Порог покрытия постоянных затрат</h3>"
            + render_kpi_grid(spec.break_even_rows)
            + f"<p>{_esc(spec.break_even_note)}</p>",
        )
        + render_section(
            "Допущения",
            f'<table class="wb-table"><thead><tr><th>Параметр</th><th>Значение</th>'
            f"<th>Комментарий</th></tr></thead><tbody>{assumption_rows}</tbody></table>"
            + "<h3>Риски</h3>"
            + render_bullets(spec.risk_notes),
        )
        + render_section(
            "Инвестиционный меморандум",
            f'<p><strong>{_esc(spec.memo_headline)}</strong></p>'
            f"{''.join(memo_groups)}"
            f"<h3>Рекомендуемые действия</h3>"
            f"{render_bullets(spec.memo_actions)}",
        )
        + render_appendix(
            "Детализирующие показатели",
            render_kpi_grid(spec.detail_rows),
        )
        + f'<div class="wb-disclaimer">{render_bullets(spec.disclaimers)}</div>'
    )
    return _render_html_document(
        spec.title,
        body,
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def render_comparison_matrix_table_html(spec: ComparisonReportSpec) -> str:
    comp = spec.comparison
    variant_labels = [_esc(v.label) for v in comp.variants]
    header = "".join(f"<th>{label}</th>" for label in variant_labels)
    baseline_idx = next(
        (i for i, v in enumerate(comp.variants) if v.variant_id == comp.baseline_id),
        0,
    )
    body_rows = []
    for row in comp.rows:
        cells = []
        for idx, value in enumerate(row.values):
            delta = row.deltas[idx] if idx < len(row.deltas) else ""
            if idx == baseline_idx or delta in ("база", "0", "—"):
                cells.append(f"<td>{_esc(value)}</td>")
            else:
                cells.append(
                    f"<td>{_esc(value)}<span class='delta'>{_esc(delta)}</span></td>"
                )
        body_rows.append(
            f"<tr><td class='metric'>{_esc(row.label)}</td>{''.join(cells)}</tr>"
        )
    return (
        f'<table class="wb-table"><thead><tr><th>Показатель</th>{header}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )


def render_comparison_report_html(spec: ComparisonReportSpec) -> str:
    cover = render_report_cover(
        title=spec.title,
        subtitle=spec.subtitle,
        mode_label="Pro",
        report_type_label=humanize_report_type(spec.report_type),
        generated_at=spec.generated_at,
        status_label=f"База: {spec.baseline_label}",
        status_severity="info",
        config_summary=f"Сравнение {len(spec.variants)} вариантов",
    )
    variants_html = render_bullets(
        [
            f"{line.label}{' (база)' if line.is_baseline else ''}"
            for line in spec.variants
        ]
    )
    body = (
        cover
        + render_section("Ключевые trade-offs", render_bullets(spec.factual_bullets))
        + render_section("Краткие выводы", render_bullets(spec.narrative_bullets))
        + render_section("Матрица сравнения", render_comparison_matrix_table_html(spec))
        + render_appendix(
            "Варианты и сводка графиков",
            variants_html + render_bullets(spec.chart_summary_lines),
        )
        + f'<div class="wb-disclaimer">{render_bullets(spec.disclaimers)}</div>'
    )
    return _render_html_document(
        spec.title,
        body,
        report_type=spec.report_type,
        generated_at=spec.generated_at,
        extra_meta=(("washerbot-baseline-id", spec.baseline_id),),
    )


def _artifact_from_bytes(
    *,
    filename: str,
    mime: str,
    content: bytes,
    report_type: str,
    generated_at: str,
) -> ReportArtifact:
    return ReportArtifact(
        filename=filename,
        mime=mime,
        content=content,
        report_type=report_type,
        generated_at=generated_at,
    )


def build_simple_report_artifact(res: SimpleResult) -> ReportArtifact:
    spec = build_simple_investment_report_spec(res)
    html_text = render_simple_report_html(spec)
    ts = report_file_timestamp()
    return _artifact_from_bytes(
        filename=f"full_report_simple_{ts}.html",
        mime="text/html",
        content=html_text.encode("utf-8"),
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def build_simple_executive_summary_artifact(res: SimpleResult) -> ReportArtifact:
    spec = build_simple_investment_report_spec(res)
    html_text = render_executive_summary_html(spec)
    ts = report_file_timestamp()
    return _artifact_from_bytes(
        filename=f"executive_summary_simple_{ts}.html",
        mime="text/html",
        content=html_text.encode("utf-8"),
        report_type=f"{spec.report_type}_executive",
        generated_at=spec.generated_at,
    )


def build_single_report_artifact(res: ProResult) -> ReportArtifact:
    spec = build_single_investment_report_spec(res)
    html_text = render_single_report_html(spec)
    ts = report_file_timestamp()
    return _artifact_from_bytes(
        filename=f"full_report_pro_{ts}.html",
        mime="text/html",
        content=html_text.encode("utf-8"),
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def build_executive_summary_artifact(res: ProResult) -> ReportArtifact:
    spec = build_single_investment_report_spec(res)
    html_text = render_executive_summary_html(spec)
    ts = report_file_timestamp()
    return _artifact_from_bytes(
        filename=f"executive_summary_pro_{ts}.html",
        mime="text/html",
        content=html_text.encode("utf-8"),
        report_type=f"{spec.report_type}_executive",
        generated_at=spec.generated_at,
    )


def build_comparison_report_artifact(
    snapshots: Sequence[CompareVariantSnapshot],
    *,
    baseline_id: str,
) -> ReportArtifact:
    spec = build_comparison_report_spec(snapshots, baseline_id=baseline_id)
    html_text = render_comparison_report_html(spec)
    ts = report_file_timestamp()
    return _artifact_from_bytes(
        filename=f"comparison_report_pro_{ts}.html",
        mime="text/html",
        content=html_text.encode("utf-8"),
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def build_comparison_csv_artifact(
    snapshots: Sequence[CompareVariantSnapshot],
    *,
    baseline_id: str,
) -> ReportArtifact:
    rows = build_comparison_matrix_rows(snapshots, baseline_id=baseline_id)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(COMPARISON_CSV_COLUMNS),
        delimiter=";",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    ts = report_file_timestamp()
    generated_at = rows[0]["generated_at"] if rows else ""
    return _artifact_from_bytes(
        filename=f"comparison_matrix_{ts}.csv",
        mime="text/csv",
        content=buffer.getvalue().encode("utf-8-sig"),
        report_type="comparison_matrix",
        generated_at=generated_at,
    )
