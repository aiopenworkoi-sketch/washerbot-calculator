from __future__ import annotations

from finance.model_constants import NPV_DISCOUNT_RATE_ANNUAL
from ui.renderers import fmt_ratio_pct

__all__ = (
    "NPV_DISCOUNT_RATE_ANNUAL",
    "format_npv_discount_rate_label",
    "format_npv_kpi_label",
)


def format_npv_discount_rate_label() -> str:
    return fmt_ratio_pct(NPV_DISCOUNT_RATE_ANNUAL)


def format_npv_kpi_label() -> str:
    return f"NPV (ставка {format_npv_discount_rate_label()})"
