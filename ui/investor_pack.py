from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO
from typing import Sequence
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from domain.results import ProResult, SimpleResult
from ui.compare_state import CompareExportState, resolve_compare_export_state
from ui.monthly_tables import build_pro_monthly_table_df, build_simple_monthly_table_df
from ui.pdf_exports import (
    build_comparison_pdf_artifact,
    build_executive_summary_pdf_artifact,
    build_pro_pdf_artifact,
    build_simple_executive_summary_pdf_artifact,
    build_simple_pdf_artifact,
)
from ui.report_exports import (
    ReportArtifact,
    build_comparison_csv_artifact,
    build_comparison_report_artifact,
    build_executive_summary_artifact,
    build_simple_executive_summary_artifact,
    build_simple_report_artifact,
    build_single_report_artifact,
)


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def _pack_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _readme_text(*, mode: str, has_compare: bool) -> str:
    lines = [
        "WasherBot — investor pack",
        "",
        "Содержимое пакета подготовлено для передачи внешнему адресату.",
        "Показатели рассчитаны автоматически и не являются инвестиционной рекомендацией.",
        "",
        f"Режим: {mode}",
        "",
        "Структура:",
        "- executive_summary.html / .pdf — одностраничное резюме для совета директоров",
        "- full_report.html / .pdf — полный инвестиционный отчёт",
        "- raw_data/monthly.csv — помесячные данные модели",
    ]
    if has_compare:
        lines.extend(
            [
                "- compare/comparison_report.html / .pdf — отчёт сравнения вариантов",
                "- compare/comparison_matrix.csv — машиночитаемая матрица сравнения",
            ]
        )
    lines.extend(["", "manifest.json — машиночитаемое описание артефактов."])
    return "\n".join(lines)


def _zip_artifact(
    *,
    filename: str,
    files: dict[str, bytes],
    report_type: str,
    generated_at: str,
) -> ReportArtifact:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return ReportArtifact(
        filename=filename,
        mime="application/zip",
        content=buffer.getvalue(),
        report_type=report_type,
        generated_at=generated_at,
    )


def build_pro_investor_pack_artifact(
    res: ProResult,
    *,
    compare_snapshots: Sequence | None = None,
    baseline_id: str | None = None,
    compare_export_state: CompareExportState | None = None,
) -> ReportArtifact:
    if compare_export_state is not None:
        compare_snapshots = compare_export_state.snapshots
        baseline_id = compare_export_state.baseline_id
    elif compare_snapshots is None or baseline_id is None:
        session_state = resolve_compare_export_state()
        if session_state is not None:
            compare_snapshots = session_state.snapshots
            baseline_id = session_state.baseline_id

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ts = _pack_timestamp()

    exec_html = build_executive_summary_artifact(res)
    exec_pdf = build_executive_summary_pdf_artifact(res)
    full_pdf = build_pro_pdf_artifact(res)
    full_html = build_single_report_artifact(res)
    monthly_csv = _df_to_csv_bytes(build_pro_monthly_table_df(res))

    files: dict[str, bytes] = {
        "executive_summary.html": exec_html.content,
        "executive_summary.pdf": exec_pdf.content,
        "full_report.html": full_html.content,
        "full_report.pdf": full_pdf.content,
        "raw_data/monthly.csv": monthly_csv,
    }

    has_compare = (
        compare_snapshots is not None
        and baseline_id is not None
        and len(compare_snapshots) >= 2
    )
    baseline_label = None
    if has_compare:
        baseline_label = next(
            (
                s.label
                for s in compare_snapshots
                if s.variant_id == baseline_id
            ),
            None,
        )
    if has_compare:
        comp_pdf = build_comparison_pdf_artifact(
            compare_snapshots, baseline_id=baseline_id
        )
        comp_html = build_comparison_report_artifact(
            compare_snapshots, baseline_id=baseline_id
        )
        comp_csv = build_comparison_csv_artifact(
            compare_snapshots, baseline_id=baseline_id
        )
        files["compare/comparison_report.pdf"] = comp_pdf.content
        files["compare/comparison_report.html"] = comp_html.content
        files["compare/comparison_matrix.csv"] = comp_csv.content

    manifest = {
        "generated_at": generated_at,
        "report_type": "investor_pack_pro",
        "mode": "pro",
        "baseline_id": baseline_id if has_compare else None,
        "baseline_label": baseline_label,
        "disclaimer": (
            "Пакет сформирован автоматически. Показатели не являются "
            "инвестиционной рекомендацией или офертой."
        ),
        "artifacts": [
            {
                "name": name,
                "size_bytes": len(content),
                "mime": _mime_for_pack_file(name),
            }
            for name, content in sorted(files.items())
        ],
    }
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode(
        "utf-8"
    )
    files["README.txt"] = _readme_text(mode="pro", has_compare=has_compare).encode(
        "utf-8"
    )

    return _zip_artifact(
        filename=f"investor_pack_pro_{ts}.zip",
        files=files,
        report_type="investor_pack_pro",
        generated_at=generated_at,
    )


def build_simple_investor_pack_artifact(res: SimpleResult) -> ReportArtifact:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ts = _pack_timestamp()

    exec_html = build_simple_executive_summary_artifact(res)
    exec_pdf = build_simple_executive_summary_pdf_artifact(res)
    full_pdf = build_simple_pdf_artifact(res)
    full_html = build_simple_report_artifact(res)
    monthly_csv = _df_to_csv_bytes(build_simple_monthly_table_df(res))

    files: dict[str, bytes] = {
        "executive_summary.html": exec_html.content,
        "executive_summary.pdf": exec_pdf.content,
        "full_report.html": full_html.content,
        "full_report.pdf": full_pdf.content,
        "raw_data/monthly.csv": monthly_csv,
    }

    manifest = {
        "generated_at": generated_at,
        "report_type": "investor_pack_simple",
        "mode": "simple",
        "baseline_id": None,
        "disclaimer": (
            "Пакет сформирован автоматически на основе упрощённой модели WasherBot Simple."
        ),
        "artifacts": [
            {
                "name": name,
                "size_bytes": len(content),
                "mime": _mime_for_pack_file(name),
            }
            for name, content in sorted(files.items())
        ],
    }
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode(
        "utf-8"
    )
    files["README.txt"] = _readme_text(mode="simple", has_compare=False).encode("utf-8")

    return _zip_artifact(
        filename=f"investor_pack_simple_{ts}.zip",
        files=files,
        report_type="investor_pack_simple",
        generated_at=generated_at,
    )


def _mime_for_pack_file(name: str) -> str:
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".html"):
        return "text/html"
    if name.endswith(".csv"):
        return "text/csv"
    if name.endswith(".json"):
        return "application/json"
    if name.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"
