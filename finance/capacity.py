from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Union

import numpy as np


Numeric = Union[float, np.ndarray]

# Профиль внутрисуточной нагрузки: мойка работает круглосуточно, но с 01:00 до
# 06:00 трафик почти нулевой, а пик приходится на 17:00–18:00.
_RAW_HOURLY_WEIGHTS: tuple[float, ...] = (
    0.020,  # 00
    0.010,  # 01
    0.005,  # 02
    0.004,  # 03
    0.004,  # 04
    0.008,  # 05
    0.020,  # 06
    0.035,  # 07
    0.045,  # 08
    0.050,  # 09
    0.050,  # 10
    0.050,  # 11
    0.055,  # 12
    0.055,  # 13
    0.055,  # 14
    0.060,  # 15
    0.068,  # 16
    0.072,  # 17
    0.070,  # 18
    0.065,  # 19
    0.060,  # 20
    0.050,  # 21
    0.035,  # 22
    0.024,  # 23
)
_HOURLY_TOTAL = sum(_RAW_HOURLY_WEIGHTS)
HOURLY_TRAFFIC_SHARES: tuple[float, ...] = tuple(w / _HOURLY_TOTAL for w in _RAW_HOURLY_WEIGHTS)
PEAK_HOUR_INDEX: int = max(range(len(HOURLY_TRAFFIC_SHARES)), key=lambda i: HOURLY_TRAFFIC_SHARES[i])
PEAK_HOUR_SHARE: float = HOURLY_TRAFFIC_SHARES[PEAK_HOUR_INDEX]


def estimate_peak_hour_utilization(
    monthly_utilization: float,
    peak_share: float = PEAK_HOUR_SHARE,
) -> float:
    """
    Загрузка в самый нагруженный час относительно часовой пропускной способности.

    monthly_utilization — отношение спроса к пропускной способности за месяц
    (средний час). Пиковый час загружен в `peak_share * 24` раз сильнее среднего.
    """
    util = max(0.0, float(monthly_utilization))
    return util * 24.0 * max(0.0, min(1.0, float(peak_share)))


@dataclass(frozen=True)
class CapacityDiagnostics:
    capacity_binding_months: int
    annual_unserved_demand: float
    annual_unserved_share: float
    peak_requested_utilization: float
    overloaded_month_indices: tuple[int, ...]
    peak_unserved_month: int
    zero_capacity_positive_demand_months: int


def _to_nonnegative_finite_array(values: Sequence[float], *, label: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError(f"{label} must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{label} must be finite")
    if np.any(arr < 0):
        raise ValueError(f"{label} must be non-negative")
    return arr


def normalize_program_shares(shares: Sequence[float]) -> List[float]:
    arr = _to_nonnegative_finite_array(shares, label="shares")
    total = float(arr.sum())
    if total <= 0:
        return (np.ones_like(arr) / arr.size).tolist()
    return (arr / total).tolist()


def weighted_program_duration_minutes(
    durations_minutes: Sequence[float],
    shares: Sequence[float],
) -> float:
    durations = _to_nonnegative_finite_array(durations_minutes, label="durations_minutes")
    if np.any(durations <= 0):
        raise ValueError("durations_minutes must be positive")

    shares_arr = _to_nonnegative_finite_array(shares, label="shares")
    if durations.size != shares_arr.size:
        raise ValueError("durations_minutes and shares must have the same length")

    normalized_shares = np.asarray(normalize_program_shares(shares_arr), dtype=float)
    value = float(np.dot(durations, normalized_shares))
    if not np.isfinite(value) or value <= 0:
        raise ValueError("weighted duration must be a positive finite number")
    return value


def estimate_daily_capacity(
    cars_per_hour_reference: float,
    cycle_time_reference_min: float,
    weighted_duration_min: float,
) -> float:
    reference_cph = max(0.0, float(cars_per_hour_reference))
    reference_cycle = float(cycle_time_reference_min)
    weighted_duration = float(weighted_duration_min)

    if not np.isfinite(reference_cycle) or reference_cycle <= 0:
        raise ValueError("cycle_time_reference_min must be a positive finite number")
    if not np.isfinite(weighted_duration) or weighted_duration <= 0:
        raise ValueError("weighted_duration_min must be a positive finite number")

    # В кодовой базе есть существующее допущение про 24 часа доступности в сутки.
    base_daily_capacity = reference_cph * 24.0
    duration_factor = reference_cycle / weighted_duration
    capacity = base_daily_capacity * duration_factor
    return max(0.0, float(capacity))


def estimate_monthly_capacity(
    daily_capacity_per_robot: float,
    work_days_month: int,
    n_robots: int,
) -> float:
    daily = max(0.0, float(daily_capacity_per_robot))
    days = max(0.0, float(work_days_month))
    robots = max(0.0, float(n_robots))
    return daily * days * robots


def cap_demand_by_capacity(demand: Numeric, capacity: Numeric) -> Numeric:
    demand_arr = np.maximum(np.asarray(demand, dtype=float), 0.0)
    capacity_arr = np.maximum(np.asarray(capacity, dtype=float), 0.0)
    served_arr = np.minimum(demand_arr, capacity_arr)

    if np.ndim(served_arr) == 0:
        return float(served_arr)
    return served_arr


def build_capacity_diagnostics(
    demand: Numeric,
    capacity: Numeric,
    *,
    eps: float = 1e-9,
) -> CapacityDiagnostics:
    demand_arr = np.maximum(np.asarray(demand, dtype=float), 0.0)
    capacity_arr = np.maximum(np.asarray(capacity, dtype=float), 0.0)
    if capacity_arr.ndim == 0:
        capacity_arr = np.full(demand_arr.shape, float(capacity_arr))

    n = demand_arr.size
    if n == 0:
        return CapacityDiagnostics(0, 0.0, 0.0, 0.0, (), 0, 0)

    unserved = np.maximum(demand_arr - capacity_arr, 0.0)
    binding_mask = demand_arr > (capacity_arr + eps)
    zero_cap_positive_demand_mask = (capacity_arr <= eps) & (demand_arr > eps)

    annual_n = min(12, n)
    annual_demand = float(np.sum(demand_arr[:annual_n]))
    annual_unserved = float(np.sum(unserved[:annual_n]))
    annual_unserved_share = (
        annual_unserved / annual_demand if annual_demand > eps else 0.0
    )

    peak_requested_utilization = 0.0
    for d, c in zip(demand_arr, capacity_arr):
        if c > eps:
            peak_requested_utilization = max(peak_requested_utilization, float(d / c))
        elif d > eps:
            peak_requested_utilization = max(peak_requested_utilization, 1.0e6)

    overloaded_indices = tuple(int(i) for i in np.flatnonzero(binding_mask))
    peak_unserved_month = 0
    if unserved.size > 0 and float(np.max(unserved)) > eps:
        peak_unserved_month = int(np.argmax(unserved)) + 1

    return CapacityDiagnostics(
        capacity_binding_months=int(np.count_nonzero(binding_mask)),
        annual_unserved_demand=annual_unserved,
        annual_unserved_share=annual_unserved_share,
        peak_requested_utilization=peak_requested_utilization,
        overloaded_month_indices=overloaded_indices,
        peak_unserved_month=peak_unserved_month,
        zero_capacity_positive_demand_months=int(
            np.count_nonzero(zero_cap_positive_demand_mask)
        ),
    )
