from __future__ import annotations

from typing import List, Sequence

import numpy as np


def _validate_monthly_factors(coeffs: Sequence[float]) -> np.ndarray:
    arr = np.asarray(coeffs, dtype=float)
    if arr.size != 12:
        raise ValueError(f"expected 12 monthly factors, got {arr.size}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("monthly factors must be finite")
    if np.any(arr < 0):
        raise ValueError("monthly factors must be non-negative")
    return arr


def normalize_monthly_factors(coeffs: Sequence[float]) -> List[float]:
    """
    Scale 12 monthly factors so sum(c) == 12 (mean == 1.0).
    Preserves relative month-to-month shape.
    """
    arr = _validate_monthly_factors(coeffs)
    total = float(arr.sum())
    if total <= 0:
        return [1.0] * 12
    return (arr * (12.0 / total)).tolist()


def build_seasonality_factors(
    base_factors: Sequence[float],
    strength: float,
) -> List[float]:
    """
    Apply seasonality strength, then normalize to sum == 12.

    strength 0 -> flat profile (all 1.0).
    strength 1 -> full base profile, normalized.
    """
    arr = _validate_monthly_factors(base_factors)
    s = float(strength)
    adjusted = 1.0 + (arr - 1.0) * s
    return normalize_monthly_factors(adjusted)
