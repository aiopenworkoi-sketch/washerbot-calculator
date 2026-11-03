from __future__ import annotations

from typing import Dict, Final

# Упрощённая налоговая модель: ставки ориентированы на 2026 год,
# без полного нормативного покрытия (НДФЛ без прогрессии, патент — оценка и т.д.).
TAX_MODEL_BASELINE_YEAR: Final[int] = 2026
TAX_MODEL_SIMPLIFIED_NOTE: Final[str] = (
    "Упрощённая модель: ключевые ставки ориентированы на 2026 год; "
    "без прогрессии НДФЛ, без региональных уточнений патента и пр."
)

MROT_2026 = 27093                # МРОТ 2026, ₽/мес (ФЗ, с 01.01.2026)
INSURANCE_RATE_BASE = 0.30       # 30% — общий тариф
INSURANCE_RATE_SME = 0.15        # 15% — пониженный тариф для МСП из перечня (свыше 1,5 МРОТ)
SME_REDUCED_TARIFF_MROT_MULTIPLIER: Final[float] = 1.5
# Автомойка (ОКВЭД 45.20) не входит в перечень приоритетных видов деятельности
# (распоряжение Правительства РФ от 27.12.2025 № 4125-р, 54 вида), поэтому по
# умолчанию считаем взносы по общему тарифу 30%. Флаг можно включить для клиентов,
# чей ОКВЭД есть в перечне.
SME_REDUCED_TARIFF_OKVED_ELIGIBLE: Final[bool] = False
NDFL_RATE_DEFAULT = 0.13         # НДФЛ 13% (для упрощения, без прогрессии)

# УСН
USN_INCOME_RATE = 0.06           # 6%
USN_PROFIT_RATE = 0.15           # 15%
USN_MIN_TAX_RATE = 0.01          # минимальный налог 1% от дохода
# Освобождение от НДС при УСН: 2026–2029 — 20 млн ₽ (ст. 145 НК РФ в ред. 425-ФЗ)
USN_VAT_THRESHOLD = 20_000_000
USN_VAT_RATE_5 = 0.05            # пониженная ставка НДС на УСН (20–272,5 млн)
USN_VAT_RATE_7 = 0.07            # пониженная ставка НДС на УСН (272,5–490,5 млн)
USN_VAT_5_MAX = 272_500_000      # 250 млн × коэффициент-дефлятор 1,09
USN_VAT_7_MAX = 490_500_000      # 450 млн × коэффициент-дефлятор 1,09
# Доля налога УСН «доходы», на которую можно уменьшить налог взносами (п. 3.1 ст. 346.21 НК РФ)
USN_INCOME_INSURANCE_DEDUCTION_CAP = 0.5

# ОСНО
OSNO_PROFIT_RATE = 0.25          # налог на прибыль 25% (с 2025)
OSNO_VAT_RATE = 0.22             # НДС 22% (с 01.01.2026, 425-ФЗ)

# Патент (ПСН) — только для ИП. Стоимость = 6% от потенциально возможного дохода,
# который устанавливается законом субъекта РФ. Значения на 2026 год:
#   Москва — закон № 53, ПД 1 320 000 ₽ × дефлятор 1,253 × 6% = 99 238 ₽/год
#   Санкт-Петербург — закон № 551-98, патент ≈ 105 252 ₽/год
# Для остальных регионов в таблице нет проверенного значения — берём московскую
# оценку как консервативную; в UI это помечено как ориентир.
PATENT_COST_YEAR_BY_REGION: Final[Dict[str, float]] = {
    "MSK": 99_238.0,
    "SPB": 105_252.0,
}
PATENT_COST_YEAR_DEFAULT: Final[float] = 99_238.0
PATENT_COST_MONTH = PATENT_COST_YEAR_DEFAULT / 12.0  # обратная совместимость


def patent_cost_month_for_region(region_key: str) -> float:
    """Стоимость патента в месяц для региона (оценка 2026)."""
    year = PATENT_COST_YEAR_BY_REGION.get(str(region_key))
    if year is None:
        year = PATENT_COST_YEAR_DEFAULT
    return float(year) / 12.0


TAX_REGIMES_LABELS = {
    "USN_INCOME": "УСН Доходы 6%",
    "USN_PROFIT": "УСН Доходы−Расходы 15%",
    "PATENT": "Патент",
    "OSNO": "ОСНО",
}


def insurance_contributions_sme(
    monthly_salary: float,
    *,
    eligible_okved: bool = SME_REDUCED_TARIFF_OKVED_ELIGIBLE,
) -> float:
    """
    Страховые взносы с зарплаты сотрудника за месяц.

    Общий тариф — 30% со всей суммы.
    Пониженный тариф 15% (только МСП из перечня 4125-р) применяется к выплатам
    свыше 1,5 МРОТ; до этого порога — 30%.
    """
    if monthly_salary <= 0:
        return 0.0
    mrot = MROT_2026
    if not eligible_okved:
        return monthly_salary * INSURANCE_RATE_BASE
    threshold = mrot * SME_REDUCED_TARIFF_MROT_MULTIPLIER
    if monthly_salary <= threshold:
        return monthly_salary * INSURANCE_RATE_BASE
    return threshold * INSURANCE_RATE_BASE + (monthly_salary - threshold) * INSURANCE_RATE_SME


def ndfl_amount(monthly_salary_gross: float) -> float:
    """НДФЛ 13% для упрощения (без прогрессии — у админа ЗП ниже порога)."""
    return max(0.0, monthly_salary_gross * NDFL_RATE_DEFAULT)


def calculate_tax(
    revenue_year: float,
    profit_year: float,
    tax_regime: str,
    region_key: str = "MSK",
) -> Dict[str, float]:
    """
    УСТАРЕЛО. Оставлено только для обратной совместимости внешних вызовов.
    Актуальный расчёт — finance.taxation.calculate_tax_for_year().
    """
    result = {"tax": 0.0, "vat": 0.0, "total": 0.0, "regime": tax_regime}

    if tax_regime == "USN_INCOME":
        tax = revenue_year * USN_INCOME_RATE
        vat = 0.0
        if revenue_year > USN_VAT_THRESHOLD:
            if revenue_year <= USN_VAT_5_MAX:
                vat = revenue_year * USN_VAT_RATE_5
            else:
                vat = revenue_year * USN_VAT_RATE_7
        result["tax"] = tax
        result["vat"] = vat
        result["total"] = tax + vat

    elif tax_regime == "USN_PROFIT":
        tax_normal = max(0.0, profit_year) * USN_PROFIT_RATE
        tax_min = revenue_year * USN_MIN_TAX_RATE
        tax = max(tax_normal, tax_min)
        vat = 0.0
        if revenue_year > USN_VAT_THRESHOLD:
            if revenue_year <= USN_VAT_5_MAX:
                vat = revenue_year * USN_VAT_RATE_5
            else:
                vat = revenue_year * USN_VAT_RATE_7
        result["tax"] = tax
        result["vat"] = vat
        result["total"] = tax + vat

    elif tax_regime == "PATENT":
        result["tax"] = PATENT_COST_MONTH * 12
        result["vat"] = 0.0
        result["total"] = result["tax"]

    elif tax_regime == "OSNO":
        tax = max(0.0, profit_year) * OSNO_PROFIT_RATE
        vat = revenue_year * OSNO_VAT_RATE
        result["tax"] = tax
        result["vat"] = vat
        result["total"] = tax + vat

    return result
