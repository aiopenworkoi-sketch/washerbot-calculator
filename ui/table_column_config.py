from __future__ import annotations

import inspect
from functools import lru_cache
from typing import Any, Callable

import pandas as pd
import streamlit as st


@lru_cache(maxsize=32)
def supports_column_kwarg(column_factory: Callable[..., Any], kwarg_name: str) -> bool:
    """Return True when Streamlit column config class accepts kwarg_name."""
    try:
        return kwarg_name in inspect.signature(column_factory).parameters
    except (TypeError, ValueError):
        return False


def _build_column(
    column_factory: Callable[..., Any],
    label: str,
    *,
    alignment: str | None = "right",
    **extra: Any,
) -> Any:
    kwargs: dict[str, Any] = dict(extra)
    if alignment and supports_column_kwarg(column_factory, "alignment"):
        kwargs["alignment"] = alignment
    try:
        return column_factory(label, **kwargs)
    except TypeError:
        return column_factory(label)


def safe_text_column(label: str, *, alignment: str | None = "right", **extra: Any) -> Any:
    return _build_column(st.column_config.TextColumn, label, alignment=alignment, **extra)


def safe_number_column(label: str, *, alignment: str | None = "right", **extra: Any) -> Any:
    return _build_column(st.column_config.NumberColumn, label, alignment=alignment, **extra)


def _is_numeric_column(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


def infer_table_column_config(df: pd.DataFrame) -> dict[str, Any]:
    """Build column_config for non-first columns; never raises."""
    if df.empty or len(df.columns) < 2:
        return {}

    config: dict[str, Any] = {}
    for col in df.columns[1:]:
        label = str(col)
        try:
            if _is_numeric_column(df[col]):
                config[col] = safe_number_column(label)
            else:
                config[col] = safe_text_column(label)
        except TypeError:
            continue
    return config
