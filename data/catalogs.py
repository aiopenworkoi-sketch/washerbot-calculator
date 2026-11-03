from __future__ import annotations

from typing import Dict, List

import numpy as np

from data.programs import PROGRAMS_DEFAULT, WASH_PROGRAMS
from domain.models import Region, WasherModel


WASHER_CATALOG: Dict[str, WasherModel] = {
    "L360": WasherModel(
        code="L360",
        name="Leisuwash 360",
        description="Бесконтактная мойка премиум-класса. 3D-сканирование, "
                    "защита от удара. Лидер по качеству мойки.",
        price_rub=14_500_000,
        cars_per_hour=10,
        cycle_time_min=5.5,
        # Источник: leisuwasher.com — 120 л на цикл (мойка 4–6 мин)
        water_per_wash_l=120,
        elec_per_wash_kwh=2.2,
        chem_per_wash_rub=42,
        power_kw=22,
        space_required_m2=42,
        features=["3D-сканер", "Защита от удара", "Сушка турбо", "Нанопокрытие"],
    ),
    "L360_MINI": WasherModel(
        code="L360_MINI",
        name="Leisuwash 360 Mini",
        description="Компактная версия 360. Подходит для участков с ограниченной "
                    "площадью. Сохраняет качество мойки старшей модели.",
        price_rub=11_500_000,
        cars_per_hour=9,
        cycle_time_min=6.0,
        water_per_wash_l=70,
        elec_per_wash_kwh=1.8,
        chem_per_wash_rub=36,
        power_kw=18,
        space_required_m2=32,
        features=["3D-сканер", "Компактность", "Сушка", "Меньшая мощность"],
    ),
    "L370_PLUS": WasherModel(
        code="L370_PLUS",
        name="Leisuwash 370 Plus",
        description="Установка семейства Plus с усиленной конфигурацией. "
                    "Баланс производительности и компактности.",
        price_rub=13_200_000,
        cars_per_hour=12,
        cycle_time_min=5.0,
        water_per_wash_l=110,
        elec_per_wash_kwh=2.5,
        chem_per_wash_rub=45,
        power_kw=28,
        space_required_m2=45,
        features=["3D-сканер", "Усиленная сушка", "Авто-диагностика", "Нанопокрытие"],
    ),
    "L380_PLUS": WasherModel(
        code="L380_PLUS",
        name="Leisuwash 380 Plus",
        description="Высокопроизводительная установка с улучшенной системой сушки. "
                    "Оптимальный баланс цены и качества.",
        price_rub=13_200_000,
        cars_per_hour=12,
        cycle_time_min=4.8,
        # Источник: leisuwasher.com — 100–200 л на автомобиль, берём середину 120 л
        water_per_wash_l=120,
        elec_per_wash_kwh=2.5,
        chem_per_wash_rub=45,
        power_kw=24,
        space_required_m2=45,
        features=["3D-сканер", "Усиленная сушка", "Авто-диагностика", "Нанопокрытие"],
    ),
    "L_SG": WasherModel(
        code="L_SG",
        name="Leisuwash SG",
        description="Бюджетная щёточная мойка. Высокая скорость обслуживания, "
                    "проста в обслуживании.",
        price_rub=8_500_000,
        cars_per_hour=14,
        cycle_time_min=4.0,
        water_per_wash_l=100,
        elec_per_wash_kwh=2.0,
        chem_per_wash_rub=38,
        power_kw=22,
        space_required_m2=38,
        features=["Щётки + бесконтакт", "Высокая скорость", "Простое обслуживание"],
    ),
    "L_DG": WasherModel(
        code="L_DG",
        name="Leisuwash DG",
        description="Двухпостовая роботизированная мойка. Параллельная обработка "
                    "двух авто, повышенная пропускная способность.",
        price_rub=22_000_000,
        cars_per_hour=18,
        cycle_time_min=3.3,
        water_per_wash_l=95,
        elec_per_wash_kwh=2.8,
        chem_per_wash_rub=48,
        power_kw=32,
        space_required_m2=68,
        features=["Двойной пост", "Параллельная мойка", "3D-сканер", "Премиум-сушка"],
    ),
}

DEFAULT_MODEL = "L380_PLUS"


# Сезонность робот-мойки: высокий сезон — с ноября по май (реагенты, слякоть,
# распутица), низкий — июнь–октябрь. Внутри сезона пик в марте и декабре.
SEASONALITY = np.array([
    1.15,  # Янв — сезон
    1.18,  # Фев — сезон
    1.20,  # Мар — пик (распутица)
    1.15,  # Апр — сезон
    1.05,  # Май — конец сезона
    0.80,  # Июн — спад
    0.70,  # Июл — минимум (сухо)
    0.75,  # Авг — низкий
    0.85,  # Сен — низкий
    0.95,  # Окт — выход на сезон
    1.20,  # Ноя — старт сезона
    1.25,  # Дек — пик (мокрый снег)
])


REGIONS: Dict[str, Region] = {
    # Москва, 2026: питьевая вода для прочих потребителей 65,77 ₽/м³ (без НДС),
    # водоотведение хоз-бытовых стоков 37,26 ₽/м³ — приказы ДЭПиР Москвы
    # (Мосводоканал). Плата за НВ и сверхнорматив добавляется профилем водоотведения.
    "MSK": Region("MSK", "Москва", 65.77, 37.26, 8.40, 1800),
    "SPB": Region("SPB", "Санкт-Петербург", 45.20, 33.80, 7.20, 1400),
    "EKB": Region("EKB", "Екатеринбург", 38.90, 28.60, 6.40, 900),
    "NSK": Region("NSK", "Новосибирск", 35.40, 26.10, 5.80, 850),
    "KZN": Region("KZN", "Казань", 32.80, 24.50, 6.10, 800),
    "NN":  Region("NN",  "Нижний Новгород", 36.20, 27.00, 6.30, 850),
    "ROV": Region("ROV", "Ростов-на-Дону", 38.10, 29.30, 6.60, 900),
    "KRD": Region("KRD", "Краснодар", 41.50, 31.20, 6.50, 1000),
    "SOC": Region("SOC", "Сочи", 48.70, 36.40, 6.80, 1500),
}

DEFAULT_REGION = "MSK"
