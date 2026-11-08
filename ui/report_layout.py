from __future__ import annotations

import html
from typing import Sequence

from ui.branding import document_logo_html
from ui.report_specs import ReportKpiRow

REPORT_CSS = """
:root {
  color-scheme: light;
}
body {
  font-family: "Segoe UI", system-ui, -apple-system, Arial, sans-serif;
  color: #0f172a;
  margin: 0;
  padding: 20px;
  background: #f1f5f9;
  line-height: 1.45;
  font-size: 10.5pt;
}
.wb-report {
  max-width: 210mm;
  margin: 0 auto;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 28px 32px 32px;
  box-sizing: border-box;
}
.wb-report-cover {
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 18px;
  margin-bottom: 22px;
  page-break-after: avoid;
}
.wb-report-brand {
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
  margin-bottom: 8px;
}
.wb-report h1 {
  font-size: 1.45rem;
  margin: 0 0 6px;
  color: #0b2545;
  line-height: 1.25;
  font-weight: 700;
}
.wb-report .subtitle {
  color: #475569;
  margin: 0 0 10px;
  font-size: 0.95rem;
}
.wb-report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
  color: #64748b;
  font-size: 0.82rem;
  margin-bottom: 10px;
}
.wb-report-badge {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border-radius: 999px;
  padding: 4px 10px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #475569;
}
.wb-report-badge--good { border-color: #86efac; background: #f0fdf4; color: #166534; }
.wb-report-badge--info { border-color: #93c5fd; background: #eff6ff; color: #1d4ed8; }
.wb-report-badge--warn { border-color: #fcd34d; background: #fffbeb; color: #92400e; }
.wb-report-badge--bad { border-color: #fca5a5; background: #fef2f2; color: #991b1b; }
.wb-config-line {
  color: #64748b;
  font-size: 0.84rem;
  margin: 0;
}
.wb-report h2 {
  font-size: 1rem;
  margin: 0 0 10px;
  color: #13315c;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.wb-report h3 {
  font-size: 0.9rem;
  margin: 14px 0 8px;
  color: #334155;
  font-weight: 600;
}
.wb-section {
  margin-top: 22px;
  page-break-inside: avoid;
}
.wb-section--exec {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px 18px;
  margin-top: 0;
  margin-bottom: 22px;
}
.wb-section--appendix {
  margin-top: 28px;
  padding-top: 14px;
  border-top: 1px dashed #cbd5e1;
}
.wb-appendix-label {
  font-size: 0.72rem;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #94a3b8;
  margin-bottom: 8px;
}
.wb-exec-headline {
  font-size: 1.05rem;
  font-weight: 600;
  color: #0b2545;
  margin: 0 0 12px;
  line-height: 1.35;
}
.wb-report ul {
  margin: 8px 0 0 18px;
  padding: 0;
}
.wb-report li {
  margin-bottom: 5px;
  line-height: 1.42;
}
.wb-report p {
  line-height: 1.48;
  margin: 8px 0;
}
.wb-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}
.wb-kpi {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fff;
  page-break-inside: avoid;
}
.wb-kpi-label {
  font-size: 0.74rem;
  color: #64748b;
}
.wb-kpi-value {
  font-size: 1rem;
  font-weight: 600;
  margin-top: 3px;
  color: #0f172a;
}
.wb-kpi-hint {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-top: 3px;
}
.wb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
  margin-top: 6px;
  table-layout: fixed;
  word-wrap: break-word;
  page-break-inside: avoid;
}
.wb-table th,
.wb-table td {
  border: 1px solid #e2e8f0;
  padding: 7px 9px;
  text-align: left;
  vertical-align: top;
}
.wb-table th {
  background: #f1f5f9;
  font-weight: 600;
  color: #334155;
}
.wb-table .metric {
  font-weight: 600;
  background: #f8fafc;
  width: 30%;
}
.wb-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.wb-table .delta {
  display: block;
  font-size: 0.74rem;
  color: #64748b;
  margin-top: 3px;
}
.wb-memo-group { margin-bottom: 10px; }
.wb-memo-group-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: #334155;
  font-size: 0.88rem;
}
.wb-disclaimer {
  margin-top: 24px;
  padding-top: 14px;
  border-top: 1px solid #e2e8f0;
  font-size: 0.78rem;
  color: #64748b;
  page-break-inside: avoid;
}
.wb-print-footer {
  margin-top: 18px;
  font-size: 0.74rem;
  color: #94a3b8;
  text-align: center;
}
@media print {
  body { background: #fff; padding: 0; }
  .wb-report {
    border: none;
    border-radius: 0;
    max-width: 100%;
    padding: 0;
    box-shadow: none;
  }
  .wb-section, .wb-kpi, .wb-table, .wb-section--exec { page-break-inside: avoid; }
  a { color: inherit; text-decoration: none; }
}
@page { margin: 14mm 12mm; size: A4; }
"""



DARK_REPORT_CSS = """
body { background: #071225 !important; color: #E5E7EB !important; }
.wb-report { background: #0B1B33 !important; border-color: #24344F !important; color: #E5E7EB !important; }
.wb-report-cover { border-bottom-color: #24344F !important; }
.wb-report h1, .wb-report h2, .wb-report h3,
.wb-report p, .wb-report li, .wb-report span, .wb-report strong,
.wb-report .subtitle, .wb-report .wb-exec-headline { color: #E5E7EB !important; }
.wb-report .subtitle, .wb-report .wb-kpi-label, .wb-report .wb-kpi-hint,
.wb-report .wb-config-line, .wb-report .wb-appendix-label,
.wb-report .wb-disclaimer, .wb-report .wb-print-footer { color: #93A4BF !important; }
.wb-report .wb-section { border-color: #24344F !important; }
.wb-report .wb-kpi { background: #101C33 !important; border-color: #24344F !important; }
.wb-report .wb-kpi-value { color: #FFFFFF !important; }
.wb-report .wb-table th { background: #101C33 !important; color: #E5E7EB !important; border-color: #24344F !important; }
.wb-report .wb-table td { color: #D7DEE8 !important; border-color: #1E2C44 !important; }
.wb-report .wb-table tr:nth-child(even) td { background: #0E1B30 !important; }
.wb-report a { color: #8FC2FF !important; }
.wb-report .wb-report-badge { background: #101C33 !important; border-color: #24344F !important; color: #E5E7EB !important; }
.wb-report .wb-memo-group { background: #101C33 !important; border-color: #24344F !important; }
.wb-report hr { border-color: #24344F !important; }
"""


def report_theme_css() -> str:
    """Дополнительный CSS отчёта: тёмная тема — тёмный документ."""
    from ui.theme_tokens import is_light

    return "" if is_light() else DARK_REPORT_CSS

def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_kpi_grid(rows: Sequence[ReportKpiRow]) -> str:
    items = []
    for row in rows:
        hint = f'<div class="wb-kpi-hint">{_esc(row.hint)}</div>' if row.hint else ""
        items.append(
            f'<div class="wb-kpi"><div class="wb-kpi-label">{_esc(row.label)}</div>'
            f'<div class="wb-kpi-value">{_esc(row.value)}</div>{hint}</div>'
        )
    return f'<div class="wb-kpi-grid">{"".join(items)}</div>'


def render_bullets(items: Sequence[str]) -> str:
    if not items:
        return "<p>—</p>"
    return "<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in items) + "</ul>"


def render_section(title: str, inner_html: str, *, css_class: str = "wb-section") -> str:
    return f'<section class="{css_class}"><h2>{_esc(title)}</h2>{inner_html}</section>'


def render_report_cover(
    *,
    title: str,
    subtitle: str,
    mode_label: str,
    report_type_label: str,
    generated_at: str,
    status_label: str,
    status_severity: str,
    config_summary: str,
) -> str:
    badge_class = f"wb-report-badge wb-report-badge--{status_severity}"
    brand_html = document_logo_html(height=28) or _esc("WasherBot · Investment Analytics")
    return (
        f'<header class="wb-report-cover">'
        f'<div class="wb-report-brand">{brand_html}</div>'
        f"<h1>{_esc(title)}</h1>"
        f'<p class="subtitle">{_esc(subtitle)}</p>'
        f'<div class="wb-report-meta">'
        f'<span class="{badge_class}">{_esc(status_label)}</span>'
        f"<span>Режим: {_esc(mode_label)}</span>"
        f"<span>{_esc(report_type_label)}</span>"
        f"<span>Сформирован: {_esc(generated_at)}</span>"
        f"</div>"
        f'<p class="wb-config-line">{_esc(config_summary)}</p>'
        f"</header>"
    )


def render_executive_summary_block(
    *,
    headline: str,
    metric_rows: Sequence[ReportKpiRow],
    scenario_lines: Sequence[str],
    risk_flags: Sequence[str],
    recommendation: str,
    context_bullets: Sequence[str],
) -> str:
    scenario_html = render_bullets(scenario_lines) if scenario_lines else ""
    risks_html = render_bullets(risk_flags) if risk_flags else "<p>—</p>"
    context_html = render_bullets(context_bullets[:3]) if context_bullets else ""
    recommendation_html = (
        f'<p class="wb-exec-headline">{_esc(recommendation)}</p>'
        if recommendation
        else ""
    )
    inner = (
        f'<p class="wb-exec-headline">{_esc(headline)}</p>'
        f"{render_kpi_grid(metric_rows)}"
        f"<h3>Диапазон сценариев</h3>{scenario_html}"
        f"<h3>Ключевые риски и допущения</h3>{risks_html}"
        f"{recommendation_html}"
        f"<h3>Контекст</h3>{context_html}"
    )
    return render_section("Исполнительное резюме", inner, css_class="wb-section wb-section--exec")


def render_appendix(title: str, inner_html: str) -> str:
    return (
        f'<section class="wb-section wb-section--appendix">'
        f'<div class="wb-appendix-label">Приложение</div>'
        f"<h2>{_esc(title)}</h2>{inner_html}</section>"
    )


def config_summary_line(config_lines: Sequence[str], *, max_len: int = 220) -> str:
    summary = " · ".join(config_lines[:4])
    if len(summary) > max_len:
        return summary[: max_len - 1] + "…"
    return summary
