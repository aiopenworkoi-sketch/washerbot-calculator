from __future__ import annotations

import math
from typing import Final

FORMAT_DEFAULTS: Final = {"missing": "—"}


def missing_placeholder() -> str:
    return FORMAT_DEFAULTS["missing"]


def is_missing_numeric(value: float | None) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    return False


def is_missing_payback_months(months: float) -> bool:
    return is_missing_numeric(months) or months <= 0


def has_finite_payback_months(months: float) -> bool:
    return not is_missing_payback_months(months)


def has_finite_irr(irr: float) -> bool:
    return not is_missing_numeric(irr)
