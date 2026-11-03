from __future__ import annotations

from typing import Sequence

from domain.results import ProResult, SimpleResult
from ui.compare_specs import CompareVariantSnapshot
from ui.pdf_layout import (
    render_comparison_spec_pdf,
    render_executive_summary_pdf,
    render_pro_spec_pdf,
    render_simple_spec_pdf,
)
from ui.report_exports import ReportArtifact
from ui.report_specs import (
    build_comparison_report_spec,
    build_simple_investment_report_spec,
    build_single_investment_report_spec,
    report_file_timestamp,
)


def _pdf_artifact(
    *,
    filename: str,
    pdf_bytes: bytes,
    report_type: str,
    generated_at: str,
) -> ReportArtifact:
    return ReportArtifact(
        filename=filename,
        mime="application/pdf",
        content=pdf_bytes,
        report_type=report_type,
        generated_at=generated_at,
    )


def build_simple_pdf_artifact(res: SimpleResult) -> ReportArtifact:
    spec = build_simple_investment_report_spec(res)
    pdf_bytes = render_simple_spec_pdf(spec)
    ts = report_file_timestamp()
    return _pdf_artifact(
        filename=f"full_report_simple_{ts}.pdf",
        pdf_bytes=pdf_bytes,
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def build_simple_executive_summary_pdf_artifact(res: SimpleResult) -> ReportArtifact:
    spec = build_simple_investment_report_spec(res)
    pdf_bytes = render_executive_summary_pdf(spec)
    ts = report_file_timestamp()
    return _pdf_artifact(
        filename=f"executive_summary_simple_{ts}.pdf",
        pdf_bytes=pdf_bytes,
        report_type=f"{spec.report_type}_executive",
        generated_at=spec.generated_at,
    )


def build_pro_pdf_artifact(res: ProResult) -> ReportArtifact:
    spec = build_single_investment_report_spec(res)
    pdf_bytes = render_pro_spec_pdf(spec)
    ts = report_file_timestamp()
    return _pdf_artifact(
        filename=f"full_report_pro_{ts}.pdf",
        pdf_bytes=pdf_bytes,
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )


def build_executive_summary_pdf_artifact(res: ProResult) -> ReportArtifact:
    spec = build_single_investment_report_spec(res)
    pdf_bytes = render_executive_summary_pdf(spec)
    ts = report_file_timestamp()
    return _pdf_artifact(
        filename=f"executive_summary_pro_{ts}.pdf",
        pdf_bytes=pdf_bytes,
        report_type=f"{spec.report_type}_executive",
        generated_at=spec.generated_at,
    )


def build_comparison_pdf_artifact(
    snapshots: Sequence[CompareVariantSnapshot],
    *,
    baseline_id: str,
) -> ReportArtifact:
    spec = build_comparison_report_spec(snapshots, baseline_id=baseline_id)
    pdf_bytes = render_comparison_spec_pdf(spec)
    ts = report_file_timestamp()
    return _pdf_artifact(
        filename=f"comparison_report_pro_{ts}.pdf",
        pdf_bytes=pdf_bytes,
        report_type=spec.report_type,
        generated_at=spec.generated_at,
    )
