from __future__ import annotations

from dataclasses import dataclass
from typing import List

from domain.models import WashProgram


@dataclass
class SimpleParams:
    # Оборудование
    model_code: str
    n_robots: int                       # количество роботов на одной площадке

    # Локация
    region_key: str

    # Инвестиции (общая сумма CAPEX — без разбивки)
    total_investment: float             # ₽ — все вложения единой суммой

    # Трафик
    cars_per_day_avg: float             # авто/день в среднем по году (на ОДИН робот)
    work_days_month: int                # рабочих дней в месяце

    # Программы (3 шт., с ценой и долей)
    programs: List[WashProgram]

    # Персонал
    admin_salary_gross: float           # ЗП администратора, ₽/мес (gross)

    # Постоянные расходы (на площадку, не на робот)
    rent_month: float                   # аренда, ₽/мес
    other_fixed: float                  # прочее (охрана, маркетинг, связь), ₽/мес

    # Налоги
    tax_regime: str                     # "USN_INCOME" | "USN_PROFIT" | "PATENT"

    # Горизонт
    horizon_months: int                 # обычно 60

    # Конфигурация
    water_discharge_profile: str = "typical_car_wash_lt30"
    extra_dryers_enabled: bool = False  # доп. сушки (+11 кВт), только для части моделей


@dataclass
class ProParams:
    # Оборудование
    model_code: str
    n_robots: int

    # Локация
    region_key: str

    # CAPEX по статьям
    capex_equipment: float              # оборудование (роботы)
    capex_construction: float           # СМР, фундамент, навес
    capex_engineering: float            # инженерные сети (вода, эл-во, водоотведение)
    capex_premises: float               # помещение (доработка/покупка)
    capex_launch: float                 # запуск, маркетинг, ПНР
    capex_other: float                  # прочее, резерв

    # Кредит
    use_credit: bool
    credit_amount: float
    credit_rate_annual: float           # годовая ставка
    credit_term_months: int
    credit_grace_months: int            # отсрочка тела

    # Трафик
    cars_per_day_avg: float             # на 1 робот, среднее по году
    work_days_month: int
    seasonality_strength: float         # 0..1, насколько включать сезонность (1 = полная, 0 = выкл)

    # Программы (5 шт. — расширенный набор для PRO)
    programs: List[WashProgram]

    # Персонал
    n_admins: int                       # администраторов на площадку
    admin_salary_gross: float
    n_managers: int                     # управляющих (на 3+ роботов)
    manager_salary_gross: float

    # OPEX детально
    rent_month: float
    utilities_extra: float              # эл-во подсобное, отопление, интернет (помимо мойки)
    security_month: float
    marketing_month: float
    maintenance_month: float            # ТО, расходники
    insurance_month: float              # страховка оборудования
    other_opex: float

    # Налоги
    tax_regime: str

    # Амортизация
    amort_years_equipment: int          # срок амортизации оборудования (для налога)

    # Горизонт и сценарии
    horizon_months: int
    scenario_pessim_factor: float       # множитель трафика для пессим. сценария (например 0.7)
    scenario_optim_factor: float        # для оптимистичного (например 1.3)

    # Экологический модуль
    eco_water_recycle_pct: float        # 0..0.95 — % оборотной воды
    eco_chem_premium: bool              # биоразлагаемая химия (+15% к стоимости)

    # Конфигурация
    water_discharge_profile: str = "typical_car_wash_lt30"
    extra_dryers_enabled: bool = False  # доп. сушки (+11 кВт), только для части моделей
