from __future__ import annotations

from typing import Any, Callable

import pandas as pd
import pytest
import streamlit as st

from ui.table_column_config import (
    infer_table_column_config,
    safe_number_column,
    safe_text_column,
    supports_column_kwarg,
)


def test_supports_column_kwarg_returns_bool_for_text_column() -> None:
    assert isinstance(supports_column_kwarg(st.column_config.TextColumn, "alignment"), bool)
    assert supports_column_kwarg(st.column_config.TextColumn, "label") is True


def test_safe_text_column_does_not_raise() -> None:
    col = safe_text_column("Доля")
    assert col is not None


def test_safe_number_column_does_not_raise() -> None:
    col = safe_number_column("Сумма")
    assert col is not None


def test_infer_table_column_config_numeric_columns() -> None:
    df = pd.DataFrame(
        {
            "Статья": ["Аренда", "ЗП"],
            "Сумма за год": [1_800_000.0, 1_200_000.0],
            "Доля": [0.45, 0.30],
        }
    )
    config = infer_table_column_config(df)
    assert "Статья" not in config
    assert "Сумма за год" in config
    assert "Доля" in config
    assert len(config) == 2


def test_infer_table_column_config_text_columns() -> None:
    df = pd.DataFrame(
        {
            "Статья": ["Аренда"],
            "Сумма за год": ["1 800 000 ₽"],
            "Доля": ["45,0 %"],
        }
    )
    config = infer_table_column_config(df)
    assert set(config) == {"Сумма за год", "Доля"}


def test_infer_table_column_config_empty_dataframe() -> None:
    assert infer_table_column_config(pd.DataFrame()) == {}


def test_safe_text_column_fallback_without_alignment(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_factory(label: str, **kwargs: Any) -> dict[str, Any]:
        if "alignment" in kwargs:
            raise TypeError("unexpected keyword argument 'alignment'")
        return {"label": label, **kwargs}

    monkeypatch.setattr(
        "ui.table_column_config.supports_column_kwarg",
        lambda _factory, _name: False,
    )
    monkeypatch.setattr(st.column_config, "TextColumn", fake_factory)

    result = safe_text_column("Доля", alignment="right")
    assert result == {"label": "Доля"}


def test_build_column_skips_alignment_when_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def recording_factory(label: str, **kwargs: Any) -> dict[str, Any]:
        calls.append({"label": label, **kwargs})
        return calls[-1]

    monkeypatch.setattr(
        "ui.table_column_config.supports_column_kwarg",
        lambda _factory, name: name == "label",
    )

    from ui.table_column_config import _build_column

    _build_column(recording_factory, "NPV", alignment="right")
    assert calls == [{"label": "NPV"}]


def test_infer_table_column_config_skips_failing_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_label: str, **_kwargs: Any) -> None:
        raise TypeError("boom")

    monkeypatch.setattr("ui.table_column_config.safe_number_column", boom)
    monkeypatch.setattr(
        "ui.table_column_config.safe_text_column",
        lambda label, **kwargs: {"label": label},
    )

    df = pd.DataFrame({"A": ["x"], "B": [1.0], "C": ["y"]})
    config = infer_table_column_config(df)
    assert "B" not in config
    assert "C" in config
