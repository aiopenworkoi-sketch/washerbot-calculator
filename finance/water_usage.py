from __future__ import annotations

from typing import Final, Tuple

from finance.water_discharge import WATER_PROFILE_TYPICAL_CAR_WASH_LT30

WATER_DISCHARGE_LT30_THRESHOLD_M3: Final = 30.0


def estimated_water_m3_per_day(cars_per_day: float, water_per_wash_l: float) -> float:
    """Conservative guardrail: base model water per wash, no recycle or mix factors."""
    return max(0.0, float(cars_per_day)) * max(0.0, float(water_per_wash_l)) / 1000.0


def is_typical_lt30_profile_exceeded(
    *,
    profile: str,
    cars_per_day: float,
    water_per_wash_l: float,
) -> bool:
    if profile != WATER_PROFILE_TYPICAL_CAR_WASH_LT30:
        return False
    return (
        estimated_water_m3_per_day(cars_per_day, water_per_wash_l)
        > WATER_DISCHARGE_LT30_THRESHOLD_M3
    )


def format_estimated_water_m3_per_day(cars_per_day: float, water_per_wash_l: float) -> str:
    value = estimated_water_m3_per_day(cars_per_day, water_per_wash_l)
    return f"{value:.2f}".replace(".", ",")


def water_usage_assumption_note(
    *,
    profile: str,
    cars_per_day: float,
    water_per_wash_l: float,
) -> str:
    if is_typical_lt30_profile_exceeded(
        profile=profile,
        cars_per_day=cars_per_day,
        water_per_wash_l=water_per_wash_l,
    ):
        return (
            "превышает лимит профиля (<30 м³/сутки) — проверьте применимость; "
            "оценка без recycle и mix-факторов"
        )
    return "без recycle и mix-факторов; базовый water_per_wash_l модели"


def water_lt30_warning_message(cars_per_day: float, water_per_wash_l: float) -> str:
    estimate = format_estimated_water_m3_per_day(cars_per_day, water_per_wash_l)
    return (
        f"Оценочный расход воды {estimate} м³/сутки превышает 30 м³/сутки. "
        'Профиль "Типовая автомойка (<30 м³/сутки)" может быть неприменим.'
    )


def water_usage_info_caption(cars_per_day: float, water_per_wash_l: float) -> str:
    estimate = format_estimated_water_m3_per_day(cars_per_day, water_per_wash_l)
    return f"Оценочный расход воды: {estimate} м³/сутки"


def water_usage_assumption_value(cars_per_day: float, water_per_wash_l: float) -> str:
    # Единица измерения уже есть в подписи строки — дублировать не нужно
    return format_estimated_water_m3_per_day(cars_per_day, water_per_wash_l)
