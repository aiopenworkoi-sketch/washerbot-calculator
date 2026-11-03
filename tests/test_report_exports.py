from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from app import calculate_pro, calculate_simple
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from ui.compare_specs import build_variant_snapshot
from ui.export_manifest import (
    build_compare_export_actions,
    build_pro_export_manifest,
    build_simple_export_manifest,
)
from ui.exports import serialize_pro_result
from ui.report_exports import (
    build_comparison_csv_artifact,
    build_comparison_report_artifact,
    build_executive_summary_artifact,
    build_simple_executive_summary_artifact,
    build_simple_report_artifact,
    build_single_report_artifact,
)
from ui.report_specs import (
    build_comparison_matrix_rows,
    build_simple_investment_report_spec,
    build_single_investment_report_spec,
)


def test_simple_html_report_artifact_smoke() -> None:
    res = calculate_simple(build_sample_simple_params())
    artifact = build_simple_report_artifact(res)
    assert artifact.filename.startswith("full_report_simple_")
    assert artifact.mime == "text/html"
    assert b"<html" in artifact.content.lower()
    assert artifact.report_type == "simple_investment"
    assert b"undefined" not in artifact.content.lower()


def test_simple_report_spec_compact() -> None:
    res = calculate_simple(build_sample_simple_params())
    spec = build_simple_investment_report_spec(res)
    assert spec.report_type == "simple_investment"
    assert spec.kpi_rows
    assert spec.verdict_headline
    assert spec.status_label
    assert spec.mode_label == "Simple"
    assert not hasattr(spec, "memo_headline")


def test_board_report_html_structure() -> None:
    res = calculate_pro(build_sample_pro_params())
    artifact = build_single_report_artifact(res)
    html = artifact.content.decode("utf-8")
    assert "wb-report-cover" in html
    assert "wb-section--exec" in html
    assert "wb-section--appendix" in html
    assert "Исполнительное резюме" in html
    assert "210mm" in html
    assert html.index("Исполнительное резюме") < html.index("Приложение")


def test_executive_summary_artifact_compact() -> None:
    res = calculate_pro(build_sample_pro_params())
    artifact = build_executive_summary_artifact(res)
    html = artifact.content.decode("utf-8")
    assert artifact.filename.startswith("executive_summary_pro_")
    assert "wb-report-cover" in html
    assert "wb-section--exec" in html
    assert "Приложение" not in html
    assert "Детализирующие показатели" not in html


def test_simple_executive_summary_artifact() -> None:
    res = calculate_simple(build_sample_simple_params())
    artifact = build_simple_executive_summary_artifact(res)
    html = artifact.content.decode("utf-8")
    assert artifact.filename.startswith("executive_summary_simple_")
    assert "wb-report-badge" in html
    assert "Simple" in html


def test_single_report_artifact_smoke() -> None:
    res = calculate_pro(build_sample_pro_params())
    artifact = build_single_report_artifact(res)
    assert artifact.filename.endswith(".html")
    assert artifact.mime == "text/html"
    assert b"<html" in artifact.content.lower()
    assert artifact.report_type == "pro_investment"
    assert b"undefined" not in artifact.content.lower()


def test_single_report_spec_sections() -> None:
    res = calculate_pro(build_sample_pro_params())
    spec = build_single_investment_report_spec(res)
    assert spec.executive_headline
    assert spec.kpi_rows
    assert spec.memo_headline
    assert spec.scenario_rows


def test_comparison_report_artifact_smoke() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    artifact = build_comparison_report_artifact([v1, v2], baseline_id="base")
    assert artifact.filename.endswith(".html")
    assert b"<html" in artifact.content.lower()
    assert artifact.report_type == "pro_comparison"


def test_comparison_csv_artifact_smoke() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    artifact = build_comparison_csv_artifact([v1, v2], baseline_id="base")
    text = artifact.content.decode("utf-8-sig")
    lines = text.splitlines()
    assert lines[0].startswith("report_type")
    assert len(lines) >= 3


def test_comparison_csv_missing_payback_empty() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    missing = replace(r1, payback_months=float("nan"))
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Нет PB", p1, missing)
    rows = build_comparison_matrix_rows([v1, v2], baseline_id="base")
    assert rows[1]["payback_months"] == ""


def test_simple_export_manifest() -> None:
    res = calculate_simple(build_sample_simple_params())
    manifest = build_simple_export_manifest(res)
    assert manifest.mode == "simple"
    action_ids = [a.action_id for g in manifest.groups for a in g.actions]
    assert action_ids == [
        "simple_html",
        "simple_pdf",
        "simple_investor_pack",
        "simple_csv",
    ]
    assert all(a.available for g in manifest.groups for a in g.actions)


def test_pro_export_manifest_without_compare_cache() -> None:
    res = calculate_pro(build_sample_pro_params())
    manifest = build_pro_export_manifest(res)
    compare_group = next(g for g in manifest.groups if g.group_id == "pro_compare")
    assert compare_group.actions == ()
    assert compare_group.empty_message


def test_compare_export_actions_from_snapshots() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    actions = build_compare_export_actions([v1, v2], baseline_id="base")
    assert len(actions) == 3
    assert all(a.available for a in actions)
    assert actions[0].widget_key == "dl_pro_compare_html_report"
    assert actions[1].widget_key == "dl_pro_compare_pdf_report"
    assert actions[2].widget_key == "dl_pro_compare_matrix_csv"


def test_pro_export_manifest_with_compare_state_without_render(monkeypatch) -> None:
    import streamlit as st

    from ui.compare_state import (
        CompareVariantRecord,
        SESSION_BASELINE_KEY,
        SESSION_VARIANTS_KEY,
        sync_compare_snapshots_cache,
    )

    p1 = build_sample_pro_params()
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    fake_state: dict = {
        SESSION_VARIANTS_KEY: [
            CompareVariantRecord("base", "База", p1),
            CompareVariantRecord("alt", "Альт", p2),
        ],
        SESSION_BASELINE_KEY: "base",
    }
    monkeypatch.setattr(st, "session_state", fake_state)
    sync_compare_snapshots_cache(calculate_pro)

    res = calculate_pro(p1)
    manifest = build_pro_export_manifest(res)
    compare_group = next(g for g in manifest.groups if g.group_id == "pro_compare")
    assert len(compare_group.actions) == 3
    assert [a.action_id for a in compare_group.actions] == [
        "pro_compare_html",
        "pro_compare_pdf",
        "pro_compare_csv",
    ]


def test_sync_compare_snapshots_cache_enables_export(monkeypatch) -> None:
    import streamlit as st

    from ui.compare_state import (
        CompareVariantRecord,
        SESSION_BASELINE_KEY,
        SESSION_VARIANTS_KEY,
        get_compare_export_state,
        sync_compare_snapshots_cache,
    )

    p1 = build_sample_pro_params()
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    fake_state: dict = {
        SESSION_VARIANTS_KEY: [
            CompareVariantRecord("base", "База", p1),
            CompareVariantRecord("alt", "Альт", p2),
        ],
        SESSION_BASELINE_KEY: "base",
    }
    monkeypatch.setattr(st, "session_state", fake_state)
    sync_compare_snapshots_cache(calculate_pro)
    export_state = get_compare_export_state()
    assert export_state is not None
    assert len(export_state.snapshots) == 2
    assert export_state.baseline_id == "base"
    actions = build_compare_export_actions(
        export_state.snapshots,
        baseline_id=export_state.baseline_id,
    )
    assert len(actions) == 3


def test_export_actions_have_layout_hints() -> None:
    res = calculate_pro(build_sample_pro_params())
    manifest = build_pro_export_manifest(res)
    primary = next(g for g in manifest.groups if g.group_id == "primary_board")
    html_action, pdf_action, pack_action, csv_action = primary.actions
    assert html_action.layout_hint == "half"
    assert pdf_action.layout_hint == "half"
    assert pack_action.layout_hint == "half"
    assert csv_action.layout_hint == "half"
    assert html_action.sort_order < pdf_action.sort_order < pack_action.sort_order < csv_action.sort_order
    assert html_action.label == "HTML отчёт"
    assert csv_action.label == "CSV данные"


def test_raw_export_payload_unchanged() -> None:
    res = calculate_pro(build_sample_pro_params())
    payload = serialize_pro_result(res)
    assert sorted(payload.keys()) == ["irr", "mode", "monthly", "npv", "payback_months", "sensitivity"]
    assert payload["mode"] == "pro"


def _visible_text_from_html(html_bytes: bytes) -> str:
    import re

    text = html_bytes.decode("utf-8")
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split()).lower()


def test_reports_no_visible_bad_tokens() -> None:
    from ui.report_text import humanize_report_type

    simple = build_simple_report_artifact(calculate_simple(build_sample_simple_params()))
    pro = build_single_report_artifact(calculate_pro(build_sample_pro_params()))
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    comp = build_comparison_report_artifact(
        [
            build_variant_snapshot("base", "База", p1, r1),
            build_variant_snapshot("alt", "Alt", p2, calculate_pro(p2)),
        ],
        baseline_id="base",
    )
    for artifact in (simple, pro, comp):
        text = _visible_text_from_html(artifact.content)
        assert "undefined" not in text
        assert " nan " not in f" {text} "
        assert " none " not in f" {text} "
        assert "<b>" not in text
        assert "usn_income" not in text
        assert "pro_investment" not in text
        assert "simple_investment" not in text
        assert "%%" not in text
        assert humanize_report_type(artifact.report_type).lower() in _visible_text_from_html(
            artifact.content
        ).lower()
