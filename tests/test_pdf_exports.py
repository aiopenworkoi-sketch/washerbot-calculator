from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
from zipfile import ZipFile

from app import calculate_pro, calculate_simple
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from ui.compare_specs import build_variant_snapshot
from ui.export_manifest import (
    build_compare_export_actions,
    build_pro_export_manifest,
    build_simple_export_manifest,
)
from ui.investor_pack import build_pro_investor_pack_artifact
from ui.pdf_exports import (
    build_comparison_pdf_artifact,
    build_pro_pdf_artifact,
    build_simple_pdf_artifact,
)
from ui.report_exports import (
    build_comparison_report_artifact,
    build_simple_report_artifact,
    build_single_report_artifact,
)


def _assert_pdf_artifact(artifact, *, prefix: str, report_type: str) -> None:
    assert artifact.filename.startswith(prefix)
    assert artifact.filename.endswith(".pdf")
    assert artifact.mime == "application/pdf"
    assert len(artifact.content) > 500
    assert artifact.content[:5] == b"%PDF-"
    assert artifact.report_type == report_type


def test_simple_pdf_artifact_smoke() -> None:
    res = calculate_simple(build_sample_simple_params())
    artifact = build_simple_pdf_artifact(res)
    _assert_pdf_artifact(artifact, prefix="full_report_simple_", report_type="simple_investment")


def test_pro_pdf_artifact_smoke() -> None:
    res = calculate_pro(build_sample_pro_params())
    artifact = build_pro_pdf_artifact(res)
    _assert_pdf_artifact(
        artifact, prefix="full_report_pro_", report_type="pro_investment"
    )


def test_comparison_pdf_artifact_smoke() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 5)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    artifact = build_comparison_pdf_artifact([v1, v2], baseline_id="base")
    _assert_pdf_artifact(
        artifact, prefix="comparison_report_pro_", report_type="pro_comparison"
    )


def test_pro_investor_pack_zip_smoke() -> None:
    res = calculate_pro(build_sample_pro_params())
    artifact = build_pro_investor_pack_artifact(res)
    assert artifact.filename.startswith("investor_pack_pro_")
    assert artifact.mime == "application/zip"
    assert len(artifact.content) > 1000
    with ZipFile(BytesIO(artifact.content)) as archive:
        names = sorted(archive.namelist())
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    assert names == [
        "README.txt",
        "executive_summary.html",
        "executive_summary.pdf",
        "full_report.html",
        "full_report.pdf",
        "manifest.json",
        "raw_data/monthly.csv",
    ]
    assert manifest["mode"] == "pro"
    assert manifest["report_type"] == "investor_pack_pro"


def test_pro_investor_pack_includes_compare_when_provided() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 5)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    res = r1
    artifact = build_pro_investor_pack_artifact(
        res, compare_snapshots=[v1, v2], baseline_id="base"
    )
    with ZipFile(BytesIO(artifact.content)) as archive:
        names = sorted(archive.namelist())
    assert names == [
        "README.txt",
        "compare/comparison_matrix.csv",
        "compare/comparison_report.html",
        "compare/comparison_report.pdf",
        "executive_summary.html",
        "executive_summary.pdf",
        "full_report.html",
        "full_report.pdf",
        "manifest.json",
        "raw_data/monthly.csv",
    ]


def test_simple_export_manifest_includes_pdf_and_pack() -> None:
    res = calculate_simple(build_sample_simple_params())
    manifest = build_simple_export_manifest(res)
    action_ids = [a.action_id for g in manifest.groups for a in g.actions]
    assert action_ids == [
        "simple_html",
        "simple_pdf",
        "simple_investor_pack",
        "simple_csv",
    ]


def test_pro_export_manifest_includes_pdf_and_pack() -> None:
    res = calculate_pro(build_sample_pro_params())
    manifest = build_pro_export_manifest(res)
    action_ids = [a.action_id for g in manifest.groups for a in g.actions]
    assert "pro_pdf_single" in action_ids
    assert "pro_investor_pack" in action_ids


def test_compare_export_actions_include_pdf() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 5)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    actions = build_compare_export_actions([v1, v2], baseline_id="base")
    assert len(actions) == 3
    assert [a.action_id for a in actions] == [
        "pro_compare_html",
        "pro_compare_pdf",
        "pro_compare_csv",
    ]
    pdf_action = next(a for a in actions if a.action_id == "pro_compare_pdf")
    assert pdf_action.mime == "application/pdf"
    assert pdf_action.content[:5] == b"%PDF-"


def test_existing_html_exports_still_work() -> None:
    simple = build_simple_report_artifact(calculate_simple(build_sample_simple_params()))
    pro = build_single_report_artifact(calculate_pro(build_sample_pro_params()))
    assert simple.mime == "text/html"
    assert pro.mime == "text/html"
    assert b"<html" in simple.content.lower()
    assert b"<html" in pro.content.lower()
