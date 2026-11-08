from __future__ import annotations

import numpy as np


def calculate_npv(cashflows: np.ndarray, discount_rate_annual: float) -> float:
    """
    NPV для месячных потоков.
    cashflows[0] — инвестиция (с минусом).
    """
    if len(cashflows) == 0:
        return 0.0
    monthly_rate = (1 + discount_rate_annual) ** (1/12) - 1
    periods = np.arange(len(cashflows))
    factors = (1 + monthly_rate) ** periods
    return float(np.sum(cashflows / factors))


def calculate_irr(cashflows: np.ndarray, periods_per_year: int = 12) -> float:
    """
    IRR методом Ньютона. Возвращает годовую ставку.
    NaN если не сходится.
    """
    if len(cashflows) < 2:
        return float("nan")
    if not (np.any(cashflows > 0) and np.any(cashflows < 0)):
        return float("nan")

    def npv_at(rate: float) -> float:
        if rate <= -0.9999:
            return 1e18
        periods = np.arange(len(cashflows))
        return float(np.sum(cashflows / (1 + rate) ** periods))

    # Ищем месячную IRR в диапазоне
    low, high = -0.99, 10.0
    f_low, f_high = npv_at(low), npv_at(high)

    if f_low * f_high > 0:
        # Расширим
        for h in [50, 200, 1000]:
            f_high = npv_at(h)
            if f_low * f_high < 0:
                high = h
                break
        else:
            return float("nan")

    # Бисекция
    for _ in range(200):
        mid = (low + high) / 2
        f_mid = npv_at(mid)
        if abs(f_mid) < 1e-6:
            break
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid

    monthly_irr = (low + high) / 2
    annual = (1 + monthly_irr) ** periods_per_year - 1
    if not np.isfinite(annual) or annual > 100:
        return float("nan")
    return float(annual)


def calculate_payback(cumulative_cf: np.ndarray) -> float:
    """
    Простой срок окупаемости в месяцах.
    cumulative_cf[0] — инвестиция отрицательная.
    NaN если не окупается.
    """
    if len(cumulative_cf) < 2:
        return float("nan")

    for i in range(1, len(cumulative_cf)):
        if cumulative_cf[i] >= 0:
            prev = cumulative_cf[i-1]
            curr = cumulative_cf[i]
            if curr == prev:
                return float(i)
            frac = -prev / (curr - prev)
            return float(i - 1 + frac)

    return float("nan")


