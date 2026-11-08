from __future__ import annotations

from typing import Final, Literal

import numpy as np
import pandas as pd

from ui.display_fallbacks import (
    has_finite_irr,
    has_finite_payback_months,
)
from ui.renderers import (
    fmt_int,
    fmt_irr,
    fmt_money,
    fmt_money_compact,
    fmt_months,
    fmt_pct,
    fmt_percent_value,
)

PEAK_UTILIZATION_INFINITY_THRESHOLD: Final = 1.0e5

MONTHLY_DISPLAY_SKIP_COLUMNS: Final = frozenset({"Месяц"})
MONTHLY_DISPLAY_INT_COLUMNS: Final = frozenset({"Авто"})


def format_kpi_payback(months: float) -> str:
    return fmt_months(months)


def format_kpi_payback_compact(months: float) -> str:
    """Payback label for KPI cards — тот же вид, что и в тексте отчёта."""
    return fmt_months(months)


def format_kpi_npv_compact(value: float) -> str:
    return fmt_money_compact(value)


def format_kpi_irr(value: float) -> str:
    return fmt_irr(value)


def format_kpi_margin_ratio(value: float) -> str:
    return fmt_pct(value)


def format_kpi_cars_per_month(cars_per_month: np.ndarray) -> str:
    return fmt_int(np.mean(cars_per_month))


def format_scenario_cumulative_money(value: float) -> str:
    return fmt_money(value)


def format_sensitivity_bar_percent(value: float) -> str:
    return fmt_percent_value(value)


# Единая шкала оценки окупаемости (мес.) — используется во всех блоках UI
PAYBACK_EXCELLENT_MONTHS = 30
PAYBACK_GOOD_MONTHS = 36
PAYBACK_LONG_MONTHS = 60


def kpi_payback_status(payback_months: float) -> str:
    if not has_finite_payback_months(payback_months):
        return "bad"
    if payback_months <= PAYBACK_EXCELLENT_MONTHS:
        return "good"
    if payback_months <= PAYBACK_GOOD_MONTHS:
        return "good"
    if payback_months <= PAYBACK_LONG_MONTHS:
        return "warn"
    return "bad"


def kpi_npv_status(npv: float) -> str:
    return "good" if npv > 0 else "bad"


def kpi_irr_status(irr: float) -> str:
    return "good" if has_finite_irr(irr) and irr > 0.20 else "warn"


def format_peak_load_percent(
    peak_requested_utilization: float,
    *,
    style: Literal["simple", "pro"],
) -> str:
    if peak_requested_utilization >= PEAK_UTILIZATION_INFINITY_THRESHOLD:
        if style == "simple":
            return "выше расчётной capacity (capacity = 0)"
        return "выше расчётной capacity"
    peak_pct = peak_requested_utilization * 100.0
    formatted = fmt_percent_value(peak_pct, decimals=0)
    if style == "simple":
        return f"<b>{formatted}</b> от расчётной пропускной способности"
    return formatted


def format_monthly_table_for_display(df: pd.DataFrame) -> pd.DataFrame:
    df_fmt = df.copy()
    for col in df_fmt.columns:
        if col in MONTHLY_DISPLAY_SKIP_COLUMNS:
            continue
        if col in MONTHLY_DISPLAY_INT_COLUMNS:
            df_fmt[col] = df_fmt[col].apply(fmt_int)
        else:
            df_fmt[col] = df_fmt[col].apply(fmt_money)
    return df_fmt


def format_breakdown_year1_table(df: pd.DataFrame) -> pd.DataFrame:
    df_show = df.copy()
    df_show["Сумма за год"] = df_show["Сумма за год"].apply(fmt_money)
    df_show["Доля"] = df_show["Доля"].apply(fmt_pct)
    return df_show
