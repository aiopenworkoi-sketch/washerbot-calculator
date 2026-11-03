from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class WasherModel:
    code: str
    name: str
    description: str
    price_rub: float

    # Производительность
    cars_per_hour: int          # авто/час при средней программе
    cycle_time_min: float       # время цикла, мин

    # Ресурсы на цикл (средняя программа)
    water_per_wash_l: float     # литров воды на 1 авто
    elec_per_wash_kwh: float    # кВт·ч на 1 авто
    chem_per_wash_rub: float    # ₽ химии на 1 авто (расходники)

    # Эксплуатация
    power_kw: float             # установленная мощность, кВт
    space_required_m2: float    # требуемая площадь, м²

    # Технические особенности
    features: List[str]


@dataclass
class WashProgram:
    code: str
    name: str
    price_rub: float            # средний чек
    duration_min: float         # длительность, мин
    water_factor: float         # множитель к базовому расходу воды
    elec_factor: float          # множитель к базовому расходу электричества
    chem_factor: float          # множитель к базовому расходу химии
    share_default: float        # доля по умолчанию


@dataclass(frozen=True)
class Region:
    key: str
    name: str
    water_supply: float          # ₽/м³
    water_sewage: float          # ₽/м³
    elec_price: float            # ₽/кВт·ч (тариф для бизнеса)
    rent_per_m2: float           # ₽/м²/мес (среднее по рынку под автомойку)
