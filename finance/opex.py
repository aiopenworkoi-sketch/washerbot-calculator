from __future__ import annotations

from finance.water_discharge import (
    WATER_PROFILE_LEGACY_HALF_SEWAGE,
    water_cost_per_m3_for_profile,
)

ECO_NORMATIVE_DISCOUNT = 0.5     # legacy constant (see WATER_PROFILE_LEGACY_HALF_SEWAGE)
ECO_OVERNORM_PENALTY   = 2.0     # reserved; not used in profile-based runtime


def calculate_water_cost_per_m3(
    supply: float,
    sewage: float,
    apply_negative: bool = True,
    apply_overnorm: bool = False,
    recirculation_saving: float = 0.0,
    *,
    profile: str | None = None,
) -> float:
    """
    Стоимость 1 м³ воды.

    Runtime uses `profile` (see finance.water_discharge).
    Legacy kwargs apply_negative/apply_overnorm apply only when profile is None.
    """
    if profile is not None:
        cost = water_cost_per_m3_for_profile(supply, sewage, profile)
    else:
        sewage_eff = sewage
        if apply_overnorm:
            sewage_eff *= ECO_OVERNORM_PENALTY
        elif apply_negative:
            sewage_eff *= ECO_NORMATIVE_DISCOUNT
        cost = supply + sewage_eff
    cost *= (1.0 - max(0.0, min(1.0, recirculation_saving)))
    return cost


def legacy_half_sewage_water_cost_per_m3(supply: float, sewage: float) -> float:
    return water_cost_per_m3_for_profile(
        supply, sewage, WATER_PROFILE_LEGACY_HALF_SEWAGE
    )
