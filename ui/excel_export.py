"""Excel-экспорт финансовой модели (openpyxl)."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from data.catalogs import REGIONS, WASHER_CATALOG
from domain.results import ProResult
from finance.taxes import TAX_REGIMES_LABELS

_HEADER_FILL = PatternFill("solid", fgColor="1F3350")
_HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
_TITLE_FONT = Font(bold=True, size=14)
_MONEY = "#,##0"
_PCT = "0,0%"


def _write_header(ws, row: int, values: list[str]) -> None:
    for col, value in enumerate(values, 1):
        cell = ws.cell(row=row, column=col, value=value)
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)


def _autosize(ws, widths: dict[int, int] | None = None) -> None:
    for col in range(1, ws.max_column + 1):
        letter = get_column_letter(col)
        if widths and col in widths:
            ws.column_dimensions[letter].width = widths[col]
        else:
            longest = 0
            for cell in ws[letter]:
                if cell.value is not None:
                    longest = max(longest, len(str(cell.value)))
            ws.column_dimensions[letter].width = min(max(12, longest + 2), 42)


def build_pro_excel_bytes(res: ProResult) -> bytes:
    """Книга Excel: сводка, помесячный расчёт, допущения."""
    wb = Workbook()

    # ── Сводка
    ws = wb.active
    ws.title = "Сводка"
    ws["A1"] = "WasherBot — финансовая модель робот-мойки"
    ws["A1"].font = _TITLE_FONT
    ws["A2"] = "Данные на 2026 год. Суммы — ₽, цены с НДС."
    ws["A2"].font = Font(color="666666", size=10)

    p = res.params
    summary: list[tuple[str, Any, str]] = [
        ("Окупаемость, мес", res.payback_months, "0.0"),
        ("NPV, ₽", res.npv, _MONEY),
        ("IRR, % годовых", res.irr, "0.0%"),
        ("Выручка, ₽/мес", res.avg_revenue_month, _MONEY),
        ("Прибыль, ₽/мес", res.avg_profit_month, _MONEY),
        ("EBITDA, ₽/мес", res.avg_ebitda_month, _MONEY),
        ("Маржа чистая", res.margin_net, _PCT),
        ("CAPEX, ₽", res.capex_total, _MONEY),
        ("Собственные средства, ₽", res.own_funds, _MONEY),
        ("Регион", REGIONS[p.region_key].name, "@"),
        ("Горизонт, мес", p.horizon_months, "0"),
        ("Модель", WASHER_CATALOG[p.model_code].name, "@"),
        ("НВ на ЦСВ", str(bool(getattr(p, "nv_norm_enabled", False))), "@"),
        ("Сверхнорматив", str(bool(getattr(p, "nv_over_enabled", False))), "@"),
        (
            "Остаточная стоимость",
            "×%s EBITDA" % getattr(p, "terminal_multiple", 3.0)
            if getattr(p, "include_terminal_value", False)
            else "не учитывается",
            "@",
        ),
    ]
    _write_header(ws, 4, ["Показатель", "Значение"])
    for i, (label, value, fmt) in enumerate(summary, start=5):
        ws.cell(row=i, column=1, value=label)
        cell = ws.cell(row=i, column=2, value=value)
        if fmt not in ("@", "0"):
            cell.number_format = fmt
    _autosize(ws, {1: 34, 2: 22})

    # ── Помесячно
    ws2 = wb.create_sheet("Помесячно")
    headers = [
        "Месяц", "Авто", "Выручка", "Переменные", "OPEX", "ЗП и взносы",
        "EBITDA", "Амортизация", "Проценты", "Налоги", "Прибыль", "Накопленный поток",
    ]
    _write_header(ws2, 1, headers)
    n = len(res.months)
    for i in range(n):
        row = i + 2
        values = [
            int(res.months[i]),
            float(res.cars_per_month[i]),
            float(res.revenue_month[i]),
            float(res.var_costs_month[i]),
            float(res.opex_month[i]),
            float(res.salary_total_month[i]),
            float(res.ebitda_month[i]),
            float(res.amortization_month[i]),
            float(res.credit_interest_month[i]),
            float(res.tax_month[i]),
            float(res.profit_month[i]),
            float(res.cumulative[i + 1]) if i + 1 < len(res.cumulative) else 0.0,
        ]
        for col, value in enumerate(values, 1):
            cell = ws2.cell(row=row, column=col, value=value)
            if col >= 3:
                cell.number_format = _MONEY
            elif col == 2:
                cell.number_format = "#,##0"
    ws2.freeze_panes = "A2"
    _autosize(ws2)

    # ── Допущения
    ws3 = wb.create_sheet("Допущения")
    _write_header(ws3, 1, ["Допущение", "Значение"])
    rows = [
        ("Тариф воды, ₽/м³", getattr(p, "water_supply_override", None) or "регион"),
        ("Тариф водоотведения, ₽/м³", getattr(p, "water_sewage_override", None) or "регион"),
        ("Тариф электроэнергии, ₽/кВт·ч", getattr(p, "elec_price_override", None) or "регион"),
        ("Рециклинг воды, %", float(p.eco_water_recycle_pct)),
        ("Налоговый режим", TAX_REGIMES_LABELS.get(p.tax_regime, p.tax_regime)),
        ("Ставка кредита", float(p.credit_rate_annual)),
        ("Ставка дисконтирования", 0.18),
        ("НВ на ЦСВ (0,5)", bool(getattr(p, "nv_norm_enabled", False))),
        ("Сверхнорматив (2,0)", bool(getattr(p, "nv_over_enabled", False))),
        ("Налог на имущество, ₽/мес", float(getattr(p, "property_tax_month", 0.0))),
        ("Земельный налог, ₽/мес", float(getattr(p, "land_tax_month", 0.0))),
        ("Взносы ИП, ₽/мес", float(getattr(p, "ip_contributions_month", 0.0))),
    ]
    for i, (label, value) in enumerate(rows, start=2):
        ws3.cell(row=i, column=1, value=label)
        ws3.cell(row=i, column=2, value=value)
    ws3.cell(row=len(rows) + 3, column=1, value=(
        "Не учтено: инфляция тарифов, терминальная стоимость (если выключена), "
        "региональные льготы. Цены — 2026 год, с НДС."
    ))
    _autosize(ws3, {1: 40, 2: 24})

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
