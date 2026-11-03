from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from io import BytesIO
from zipfile import ZipFile

from app import calculate_pro
from data.sample_params import build_sample_pro_params
from ui.compare_specs import build_variant_snapshot
from ui.compare_state import compare_export_state_from_snapshots
from ui.export_manifest import build_pro_export_manifest
from ui.investor_pack import build_pro_investor_pack_artifact


def test_pro_export_manifest_explicit_compare_state_without_session() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 5)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    export_state = compare_export_state_from_snapshots(
        (v1, v2),
        baseline_id="base",
    )

    manifest = build_pro_export_manifest(r1, compare_export_state=export_state)
    compare_group = next(g for g in manifest.groups if g.group_id == "pro_compare")
    assert len(compare_group.actions) == 3
    assert [a.action_id for a in compare_group.actions] == [
        "pro_compare_html",
        "pro_compare_pdf",
        "pro_compare_csv",
    ]


def test_compare_zip_contains_compare_artifacts() -> None:
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 5)
    r2 = calculate_pro(p2)
    v1 = build_variant_snapshot("base", "База", p1, r1)
    v2 = build_variant_snapshot("alt", "Альтернатива", p2, r2)
    export_state = compare_export_state_from_snapshots(
        (v1, v2),
        baseline_id="base",
    )

    artifact = build_pro_investor_pack_artifact(
        r1,
        compare_export_state=export_state,
    )
    with ZipFile(BytesIO(artifact.content)) as archive:
        names = sorted(archive.namelist())

    assert "compare/comparison_report.pdf" in names
    assert "compare/comparison_report.html" in names
    assert "compare/comparison_matrix.csv" in names
