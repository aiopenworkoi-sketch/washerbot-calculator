from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence, Tuple

import pandas as pd
import streamlit as st

from domain.results import ProResult, SimpleResult
from ui.compare_state import CompareExportState, resolve_compare_export_state
from ui.investor_pack import build_pro_investor_pack_artifact, build_simple_investor_pack_artifact
from ui.monthly_tables import build_pro_monthly_table_df, build_simple_monthly_table_df
from ui.pdf_exports import (
    build_comparison_pdf_artifact,
    build_pro_pdf_artifact,
    build_simple_pdf_artifact,
)
from ui.report_exports import (
    ReportArtifact,
    build_comparison_csv_artifact,
    build_comparison_report_artifact,
    build_simple_report_artifact,
    build_single_report_artifact,
)
from ui.ui_labels import ExportLabels

PRIMARY_BOARD_GROUP_ID = "primary_board"


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


@dataclass(frozen=True)
class ExportActionSpec:
    action_id: str
    label: str
    description: str
    filename: str
    mime: str
    content: bytes
    widget_key: str
    available: bool = True
    unavailable_reason: str = ""
    layout_hint: str = "half"
    sort_order: int = 100
    format_badge: str = ""


@dataclass(frozen=True)
class ExportManifestGroup:
    group_id: str
    title: str
    description: str
    actions: Tuple[ExportActionSpec, ...]
    empty_message: str = ""


@dataclass(frozen=True)
class ExportManifest:
    mode: str
    summary: str
    fields_note: str
    groups: Tuple[ExportManifestGroup, ...]


def _action_from_artifact(
    action_id: str,
    label: str,
    description: str,
    artifact: ReportArtifact,
    widget_key: str,
    *,
    layout_hint: str = "half",
    sort_order: int = 100,
    format_badge: str = "",
) -> ExportActionSpec:
    return ExportActionSpec(
        action_id=action_id,
        label=label,
        description=description,
        filename=artifact.filename,
        mime=artifact.mime,
        content=artifact.content,
        widget_key=widget_key,
        available=True,
        layout_hint=layout_hint,
        sort_order=sort_order,
        format_badge=format_badge,
    )


def _csv_action(
    action_id: str,
    label: str,
    description: str,
    df: pd.DataFrame,
    *,
    widget_key: str,
    filename_prefix: str,
    layout_hint: str = "full",
    sort_order: int = 100,
) -> ExportActionSpec:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    return ExportActionSpec(
        action_id=action_id,
        label=label,
        description=description,
        filename=f"{filename_prefix}_{ts}.csv",
        mime="text/csv",
        content=_df_to_csv_bytes(df),
        widget_key=widget_key,
        available=True,
        layout_hint=layout_hint,
        sort_order=sort_order,
        format_badge="CSV",
    )


def _build_primary_board_actions(
    *,
    html_action_id: str,
    pdf_action_id: str,
    pack_action_id: str,
    csv_action_id: str,
    html_artifact: ReportArtifact,
    pdf_artifact: ReportArtifact,
    pack_artifact: ReportArtifact,
    monthly_df: pd.DataFrame,
    html_widget_key: str,
    pdf_widget_key: str,
    pack_widget_key: str,
    csv_widget_key: str,
    csv_filename_prefix: str,
) -> Tuple[ExportActionSpec, ...]:
    return (
        _action_from_artifact(
            html_action_id,
            ExportLabels.BOARD_HTML_TITLE,
            ExportLabels.BOARD_HTML_SUB,
            html_artifact,
            html_widget_key,
            layout_hint="half",
            sort_order=10,
            format_badge="HTML",
        ),
        _action_from_artifact(
            pdf_action_id,
            ExportLabels.BOARD_PDF_TITLE,
            ExportLabels.BOARD_PDF_SUB,
            pdf_artifact,
            pdf_widget_key,
            layout_hint="half",
            sort_order=20,
            format_badge="PDF",
        ),
        _action_from_artifact(
            pack_action_id,
            ExportLabels.BOARD_ZIP_TITLE,
            ExportLabels.BOARD_ZIP_SUB,
            pack_artifact,
            pack_widget_key,
            layout_hint="half",
            sort_order=30,
            format_badge="ZIP",
        ),
        _csv_action(
            csv_action_id,
            ExportLabels.BOARD_CSV_TITLE,
            ExportLabels.BOARD_CSV_SUB,
            monthly_df,
            widget_key=csv_widget_key,
            filename_prefix=csv_filename_prefix,
            layout_hint="half",
            sort_order=40,
        ),
    )


def build_simple_export_manifest(res: SimpleResult) -> ExportManifest:
    html_artifact = build_simple_report_artifact(res)
    pdf_artifact = build_simple_pdf_artifact(res)
    pack_artifact = build_simple_investor_pack_artifact(res)
    monthly_df = build_simple_monthly_table_df(res)
    primary_actions = _build_primary_board_actions(
        html_action_id="simple_html",
        pdf_action_id="simple_pdf",
        pack_action_id="simple_investor_pack",
        csv_action_id="simple_csv",
        html_artifact=html_artifact,
        pdf_artifact=pdf_artifact,
        pack_artifact=pack_artifact,
        monthly_df=monthly_df,
        html_widget_key="dl_simple_html_report",
        pdf_widget_key="dl_simple_pdf_report",
        pack_widget_key="dl_simple_investor_pack",
        csv_widget_key="dl_simple_csv",
        csv_filename_prefix="washerbot_simple",
    )
    return ExportManifest(
        mode="simple",
        summary="",
        fields_note="",
        groups=(
            ExportManifestGroup(
                group_id=PRIMARY_BOARD_GROUP_ID,
                title="",
                description="",
                actions=primary_actions,
            ),
        ),
    )


def build_compare_export_actions(
    snapshots: Sequence,
    *,
    baseline_id: str,
) -> Tuple[ExportActionSpec, ...]:
    compare_html = build_comparison_report_artifact(
        snapshots, baseline_id=baseline_id
    )
    compare_pdf = build_comparison_pdf_artifact(
        snapshots, baseline_id=baseline_id
    )
    compare_csv = build_comparison_csv_artifact(
        snapshots, baseline_id=baseline_id
    )
    return (
        _action_from_artifact(
            "pro_compare_html",
            ExportLabels.DOWNLOAD_HTML_COMPARE,
            ExportLabels.EXPORT_HTML_SHORT,
            compare_html,
            "dl_pro_compare_html_report",
            layout_hint="half",
            sort_order=10,
            format_badge="HTML",
        ),
        _action_from_artifact(
            "pro_compare_pdf",
            ExportLabels.DOWNLOAD_PDF_COMPARE,
            ExportLabels.EXPORT_PDF_SHORT,
            compare_pdf,
            "dl_pro_compare_pdf_report",
            layout_hint="half",
            sort_order=20,
            format_badge="PDF",
        ),
        _action_from_artifact(
            "pro_compare_csv",
            ExportLabels.DOWNLOAD_CSV_COMPARE,
            ExportLabels.EXPORT_CSV_COMPARE_DESC,
            compare_csv,
            "dl_pro_compare_matrix_csv",
            layout_hint="half",
            sort_order=30,
            format_badge="CSV",
        ),
    )


def build_pro_export_manifest(
    res: ProResult,
    *,
    compare_export_state: CompareExportState | None = None,
) -> ExportManifest:
    html_artifact = build_single_report_artifact(res)
    pdf_artifact = build_pro_pdf_artifact(res)
    compare_state = resolve_compare_export_state(
        compare_export_state=compare_export_state,
    )
    pack_artifact = build_pro_investor_pack_artifact(
        res,
        compare_export_state=compare_state,
    )
    monthly_df = build_pro_monthly_table_df(res)

    primary_actions = _build_primary_board_actions(
        html_action_id="pro_html_single",
        pdf_action_id="pro_pdf_single",
        pack_action_id="pro_investor_pack",
        csv_action_id="pro_csv",
        html_artifact=html_artifact,
        pdf_artifact=pdf_artifact,
        pack_artifact=pack_artifact,
        monthly_df=monthly_df,
        html_widget_key="dl_pro_html_report",
        pdf_widget_key="dl_pro_pdf_report",
        pack_widget_key="dl_pro_investor_pack",
        csv_widget_key="dl_pro_csv",
        csv_filename_prefix="washerbot_pro",
    )

    compare_actions: list[ExportActionSpec] = []
    compare_empty = ExportLabels.EXPORT_COMPARE_EMPTY
    if compare_state is not None:
        compare_actions.extend(
            build_compare_export_actions(
                compare_state.snapshots,
                baseline_id=compare_state.baseline_id,
            )
        )

    return ExportManifest(
        mode="pro",
        summary="",
        fields_note="",
        groups=(
            ExportManifestGroup(
                group_id=PRIMARY_BOARD_GROUP_ID,
                title="",
                description="",
                actions=primary_actions,
            ),
            ExportManifestGroup(
                group_id="pro_compare",
                title="Сравнение конфигураций",
                description="",
                actions=tuple(compare_actions),
                empty_message=compare_empty,
            ),
        ),
    )


def render_export_manifest(
    manifest: ExportManifest,
    *,
    monthly_preview: tuple[str, pd.DataFrame] | None = None,
) -> None:
    from ui.export_layout import render_export_board, render_export_secondary_group

    primary_group = next(
        (group for group in manifest.groups if group.group_id == PRIMARY_BOARD_GROUP_ID),
        None,
    )
    secondary_groups = [
        group for group in manifest.groups if group.group_id != PRIMARY_BOARD_GROUP_ID
    ]

    if primary_group is not None:
        render_export_board(primary_group.actions)

    if monthly_preview is not None:
        st.markdown('<div class="wb-export-secondary wb-export-monthly-block">', unsafe_allow_html=True)
        expander_label, preview_df = monthly_preview
        with st.expander(expander_label, expanded=False):
            from ui.format_policies import format_monthly_table_for_display
            from ui.section_blocks import render_dataframe_section

            df_fmt = format_monthly_table_for_display(preview_df)
            render_dataframe_section(df_fmt, height=420 if manifest.mode == "pro" else 400)
        st.markdown("</div>", unsafe_allow_html=True)

    for group in secondary_groups:
        render_export_secondary_group(group)

    st.markdown('<div class="wb-section-block--tight"></div>', unsafe_allow_html=True)
