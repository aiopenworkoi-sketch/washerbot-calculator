from __future__ import annotations

import streamlit as st

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from domain.results import ProResult, SimpleResult
from ui.export_manifest import (
    build_pro_export_manifest,
    build_simple_export_manifest,
    render_export_manifest,
)
from ui.monthly_tables import (
    build_pro_monthly_table_df,
    build_simple_monthly_table_df,
)
from ui.presentation_mode import is_presentation_mode, presentation_secondary_panel
from ui.section_blocks import (
    render_section_subtitle,
    render_section_title,
)
from ui.ui_labels import ExportLabels, SectionTitles


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def _to_plain_number(value: Any) -> Any:
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, float):
        return float(value)
    if isinstance(value, int):
        return int(value)
    return value


def serialize_sensitivity_mapping(sensitivity: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Read-only serialization of res.sensitivity preserving runtime insertion order.
    Does not rebuild labels or recompute values.
    """
    serialized: List[Dict[str, Any]] = []
    for label, value in sensitivity.items():
        if not label:
            raise ValueError("sensitivity export labels must be non-empty")
        if "\ufffd" in label:
            raise ValueError("sensitivity export labels must not contain replacement characters")
        serialized.append({
            "label": label,
            "value": _to_plain_number(value),
        })
    return serialized


def build_simple_monthly_export_df(res: SimpleResult) -> pd.DataFrame:
    df = build_simple_monthly_table_df(res)
    return _round_export_frame(df, res.cars_per_month)


def build_pro_monthly_export_df(res: ProResult) -> pd.DataFrame:
    df = build_pro_monthly_table_df(res)
    return _round_export_frame(df, res.cars_per_month)


def _round_export_frame(df: pd.DataFrame, cars_per_month) -> pd.DataFrame:
    """
    В интерфейсе «Авто» показываем целыми, но в выгрузке нужна точность:
    иначе сумма по месяцам не сходится с моделью. Деньги округляем до копеек —
    иначе в CSV уезжают 15 знаков после запятой.
    """
    df = df.copy()
    df["Авто"] = cars_per_month.round(1)
    for column in df.columns:
        if column not in ("Месяц", "Авто"):
            df[column] = df[column].round(2)
    return df


def build_simple_export_payload(res: SimpleResult) -> Dict[str, Any]:
    return {
        "mode": "simple",
        "npv": _to_plain_number(res.npv),
        "irr": _to_plain_number(res.irr),
        "payback_months": _to_plain_number(res.payback_months),
        "monthly": build_simple_monthly_table_df(res).to_dict(orient="list"),
    }


def build_pro_export_payload(res: ProResult) -> Dict[str, Any]:
    return {
        "mode": "pro",
        "npv": _to_plain_number(res.npv),
        "irr": _to_plain_number(res.irr),
        "payback_months": _to_plain_number(res.payback_months),
        "sensitivity": serialize_sensitivity_mapping(res.sensitivity),
        "monthly": build_pro_monthly_table_df(res).to_dict(orient="list"),
    }


def serialize_simple_result(res: SimpleResult) -> Dict[str, Any]:
    return build_simple_export_payload(res)


def serialize_pro_result(res: ProResult) -> Dict[str, Any]:
    return build_pro_export_payload(res)


def render_simple_export_section(res: SimpleResult) -> None:
    with presentation_secondary_panel(
        SectionTitles.DETAIL_TABLES,
        subtitle=SectionTitles.DETAIL_TABLES_SUB,
        tier="utility",
    ):
        if not is_presentation_mode():
            render_section_title(SectionTitles.DETAIL_TABLES)
            render_section_subtitle(SectionTitles.DETAIL_TABLES_SUB)
        manifest = build_simple_export_manifest(res)
        monthly_df = build_simple_monthly_table_df(res)
        render_export_manifest(
            manifest,
            monthly_preview=(ExportLabels.SIMPLE_TABLE, monthly_df),
        )


def render_simple_monthly_table_block(res: SimpleResult) -> None:
    render_simple_export_section(res)


def render_pro_export_section(res: ProResult) -> None:
    with presentation_secondary_panel(
        SectionTitles.DETAIL_TABLES,
        subtitle=SectionTitles.DETAIL_TABLES_SUB,
        tier="utility",
    ):
        if not is_presentation_mode():
            render_section_title(SectionTitles.DETAIL_TABLES)
            render_section_subtitle(SectionTitles.DETAIL_TABLES_SUB)
        manifest = build_pro_export_manifest(res)
        monthly_df = build_pro_monthly_table_df(res)
        render_export_manifest(
            manifest,
            monthly_preview=(ExportLabels.PRO_TABLE, monthly_df),
        )
        try:
            from ui.excel_export import build_pro_excel_bytes

            st.download_button(
                "Скачать Excel (сводка + помесячно + допущения)",
                data=build_pro_excel_bytes(res),
                file_name=f"washerbot_model_{res.params.region_key}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_pro_xlsx",
            )
        except Exception:
            pass


def render_pro_monthly_table_block(res: ProResult) -> None:
    """Legacy entry — delegates to report-ready export section."""
    render_pro_export_section(res)
