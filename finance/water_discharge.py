from __future__ import annotations

from typing import Dict, Final, Tuple

WATER_PROFILE_BASIC: Final = "basic"
WATER_PROFILE_WITH_NV_CSV: Final = "with_nv_csv"
WATER_PROFILE_TYPICAL_CAR_WASH_LT30: Final = "typical_car_wash_lt30"
WATER_PROFILE_LEGACY_HALF_SEWAGE: Final = "legacy_half_sewage"

WATER_DISCHARGE_DEFAULT_PROFILE: Final = WATER_PROFILE_TYPICAL_CAR_WASH_LT30

PUBLIC_WATER_DISCHARGE_PROFILES: Tuple[Tuple[str, str], ...] = (
    (WATER_PROFILE_BASIC, "Базовый"),
    (WATER_PROFILE_WITH_NV_CSV, "С НВ на ЦСВ"),
    (WATER_PROFILE_TYPICAL_CAR_WASH_LT30, "Типовая автомойка (<30 м³/сутки)"),
)

_WATER_PROFILE_LABELS: Dict[str, str] = {
    WATER_PROFILE_BASIC: "Базовый",
    WATER_PROFILE_WITH_NV_CSV: "С НВ на ЦСВ",
    WATER_PROFILE_TYPICAL_CAR_WASH_LT30: "Типовая автомойка (<30 м³/сутки)",
    WATER_PROFILE_LEGACY_HALF_SEWAGE: "Legacy: 0,5× канализация",
}

_KNOWN_PROFILES = frozenset(_WATER_PROFILE_LABELS.keys())


def is_legacy_water_discharge_profile(profile: str) -> bool:
    return profile == WATER_PROFILE_LEGACY_HALF_SEWAGE


def water_discharge_profile_label(profile: str) -> str:
    return _WATER_PROFILE_LABELS.get(profile, profile)


def normalize_water_discharge_profile(
    value: str | None,
    *,
    from_scenario: bool,
) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return WATER_PROFILE_LEGACY_HALF_SEWAGE if from_scenario else WATER_DISCHARGE_DEFAULT_PROFILE
    key = str(value).strip()
    if key in _KNOWN_PROFILES:
        return key
    raise ValueError(f"Unknown water discharge profile: {value!r}")


def water_cost_per_m3_for_profile(
    supply: float,
    sewage: float,
    profile: str,
) -> float:
    supply_f = max(0.0, float(supply))
    sewage_f = max(0.0, float(sewage))

    if profile == WATER_PROFILE_BASIC:
        return supply_f + sewage_f
    if profile == WATER_PROFILE_WITH_NV_CSV:
        return supply_f + sewage_f + 0.5 * sewage_f
    if profile == WATER_PROFILE_TYPICAL_CAR_WASH_LT30:
        return supply_f + sewage_f + 0.5 * sewage_f + 2.0 * sewage_f
    if profile == WATER_PROFILE_LEGACY_HALF_SEWAGE:
        return supply_f + 0.5 * sewage_f
    raise ValueError(f"Unknown water discharge profile: {profile!r}")


def effective_water_tariff_rub_per_m3(
    supply: float,
    sewage: float,
    profile: str,
) -> float:
    """Monetary tariff per m³ for OPEX and eco savings (same semantics)."""
    return water_cost_per_m3_for_profile(supply, sewage, profile)
