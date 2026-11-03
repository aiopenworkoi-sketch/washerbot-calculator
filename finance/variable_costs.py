from __future__ import annotations

from typing import Final

from data.washer_access import EXTRA_DRYERS_POWER_DELTA_KW, supports_extra_dryers

EXTRA_DRYER_RUNTIME_SEC_PER_WASH: Final = 30.0


def extra_dryer_kwh_per_wash(
    *,
    extra_dryers_enabled: bool,
    model_code: str,
) -> float:
    if not extra_dryers_enabled or not supports_extra_dryers(model_code):
        return 0.0
    return EXTRA_DRYERS_POWER_DELTA_KW * EXTRA_DRYER_RUNTIME_SEC_PER_WASH / 3600.0


def calculate_elec_cost_per_wash(
    *,
    model_elec_per_wash_kwh: float,
    avg_elec_factor: float,
    elec_price: float,
    extra_dryers_enabled: bool,
    model_code: str,
) -> float:
    base_kwh = float(model_elec_per_wash_kwh) * float(avg_elec_factor)
    extra_kwh = extra_dryer_kwh_per_wash(
        extra_dryers_enabled=extra_dryers_enabled,
        model_code=model_code,
    )
    return (base_kwh + extra_kwh) * float(elec_price)
