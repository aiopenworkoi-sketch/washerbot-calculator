"""Тарифы и плата за негативное воздействие на работу ЦСВ.

Правовая база (Правила холодного водоснабжения и водоотведения,
утв. постановлением Правительства РФ от 29.07.2013 № 644):

* п. 123(4) — плата за негативное воздействие на работу централизованной
  системы водоотведения для объектов с расходом менее 30 м³/сутки либо без
  контрольного канализационного колодца:
      П = 0,5 × Т × Q
* п. 203 — плата за сброс загрязняющих веществ в составе сточных вод сверх
  установленных нормативов состава сточных вод (те же критерии объекта):
      П = 2,0 × Т × Q

Оба платежа самостоятельные и могут начисляться одновременно (2,5 × Т).
Т — тариф на водоотведение без НДС, Q — объём сточных вод.
"""

from __future__ import annotations

from typing import Final, NamedTuple

NV_NORM_COEFFICIENT: Final[float] = 0.5
NV_OVER_COEFFICIENT: Final[float] = 2.0

NV_MODE_LABELS: Final[dict[str, str]] = {
    "off": "Не учитывать",
    "norm": "Стандарт — 0,5 × тариф (п. 123(4))",
    "over": "Сверх нормы — 2,0 × тариф (п. 203)",
    "both": "Оба платежа — 2,5 × тариф",
}


class EffectiveTariffs(NamedTuple):
    water_supply: float
    water_sewage: float
    elec_price: float


def effective_tariffs(
    region,
    *,
    water_supply_override: float | None = None,
    water_sewage_override: float | None = None,
    elec_price_override: float | None = None,
) -> EffectiveTariffs:
    """Тарифы региона с учётом ручного переопределения (значения — с НДС)."""

    def pick(value: float | None, fallback: float) -> float:
        if value is None:
            return float(fallback)
        return max(0.0, float(value))

    return EffectiveTariffs(
        water_supply=pick(water_supply_override, region.water_supply),
        water_sewage=pick(water_sewage_override, region.water_sewage),
        elec_price=pick(elec_price_override, region.elec_price),
    )


def nv_coefficient(*, norm_enabled: bool, over_enabled: bool) -> float:
    """Суммарный коэффициент к тарифу водоотведения (0 / 0,5 / 2,0 / 2,5)."""
    coefficient = 0.0
    if norm_enabled:
        coefficient += NV_NORM_COEFFICIENT
    if over_enabled:
        coefficient += NV_OVER_COEFFICIENT
    return coefficient


def nv_mode_key(*, norm_enabled: bool, over_enabled: bool) -> str:
    if norm_enabled and over_enabled:
        return "both"
    if norm_enabled:
        return "norm"
    if over_enabled:
        return "over"
    return "off"


def nv_mode_label(*, norm_enabled: bool, over_enabled: bool) -> str:
    return NV_MODE_LABELS[nv_mode_key(norm_enabled=norm_enabled, over_enabled=over_enabled)]
