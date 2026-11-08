from __future__ import annotations

from typing import Dict, Final, Literal

Severity = Literal["good", "bad", "warn", "info"]


class UIClassNames:
    CARD: Final = "wb-card"
    CARD_TITLE: Final = "wb-card-title"
    INFO: Final = "wb-info"
    WARN: Final = "wb-warn"
    SUCCESS: Final = "wb-success"
    DANGER: Final = "wb-danger"
    METRIC: Final = "wb-metric"
    SIDEBAR_HEADING: Final = "wb-sidebar-heading"
    CONFIG_SUMMARY: Final = "wb-config-summary"


class SectionTitles:
    VERDICT: Final = "Инвестиционный вывод"
    KPI: Final = "Ключевые показатели"
    CASHFLOW: Final = "Окупаемость — накопленный денежный поток"
    REVENUE_EXPENSES: Final = "Выручка и расходы по месяцам"
    EXPENSE_BREAKDOWN: Final = "Структура расходов за 1-й год"
    SCENARIOS: Final = "Сценарии"
    SCENARIOS_SUB: Final = "Сравнение пессимистичного, базового и оптимистичного трафика"
    PL_MONTHLY: Final = "P&L по месяцам"
    DETAIL_MODEL: Final = "Детализация финансовой модели"
    DETAIL_DYNAMICS: Final = "Финансовая динамика"
    DETAIL_DYNAMICS_SUB: Final = "Помесячная выручка, EBITDA, прибыль и накопленный денежный поток"
    DETAIL_FINANCING: Final = "Финансирование"
    DETAIL_FINANCING_SUB: Final = "График погашения и параметры долговой нагрузки"
    DETAIL_COSTS: Final = "Структура затрат"
    DETAIL_COSTS_SUB: Final = "Распределение CAPEX и OPEX первого года"
    CAPEX_OPEX: Final = "Структура CAPEX и затрат (1-й год)"
    SENSITIVITY: Final = "Драйверы результата"
    SENSITIVITY_SUB: Final = "Ранжирование влияния параметров на NPV при +10% к параметру"
    BREAK_EVEN: Final = "Порог покрытия постоянных затрат"
    BREAK_EVEN_SUB: Final = (
        "Упрощённая оценка: OPEX + ЗП + налог + проценты по кредиту на авто/мес; "
        "отдельно от окупаемости капитала"
    )
    CAPACITY: Final = "Мощность и спрос"
    CAPACITY_SUB: Final = "Ограничения пропускной способности и потерянный спрос"
    CREDIT_SCHEDULE: Final = "График погашения кредита"
    ECOLOGY: Final = "Экологические показатели"
    ASSUMPTIONS: Final = "Ключевые риски и допущения"
    ASSUMPTIONS_SUB: Final = "Параметры модели, влияющие на интерпретацию результата"
    MEMO: Final = "Инвестиционный меморандум"
    MEMO_SUB: Final = "Структурированный вывод, риски и рекомендуемые действия"
    COMPARE: Final = "Сравнение конфигураций"
    COMPARE_SUB: Final = "Сопоставление 2–3 инвестиционных вариантов по ключевым метрикам"
    COMPARE_EMPTY: Final = "Добавьте минимум 2 конфигурации для сравнения"
    COMPARE_ADD: Final = "Добавить вариант"
    COMPARE_BASELINE: Final = "Базовый вариант"
    COMPARE_VARIANTS: Final = "Варианты для сравнения"
    COMPARE_DELTA_NOTE: Final = "Разница к базовому варианту указана под значением"
    RECOMMENDATIONS: Final = "Выводы и рекомендации"
    DETAIL_TABLES: Final = "Таблицы и экспорт"
    DETAIL_TABLES_SUB: Final = "4 формата выгрузки для отчёта и передачи"


class MemoGroupTitles:
    INVESTMENT: Final = "Инвестиционный вывод"
    DRIVERS: Final = "Ключевые драйверы"
    RISKS: Final = "Основные риски"
    OPERATIONS: Final = "Операционные ограничения"
    NEXT_ACTIONS: Final = "Следующие шаги"


class DetailTabLabels:
    DYNAMICS: Final = "Динамика"
    FINANCING: Final = "Финансы"
    COSTS: Final = "Затраты"


class SidebarSections:
    EQUIPMENT: Final = "Оборудование"
    LOCATION: Final = "Локация"
    INVESTMENT: Final = "Инвестиции"
    CAPEX: Final = "CAPEX по статьям"
    FINANCING: Final = "Финансирование"
    TRAFFIC: Final = "Трафик"
    PROGRAMS: Final = "Программы мойки"
    PROGRAMS_PRO: Final = "Программы (5 типов)"
    STAFF: Final = "Персонал"
    FIXED_COSTS: Final = "Постоянные расходы"
    OPEX: Final = "OPEX"
    TAXES: Final = "Налоги"
    AMORTIZATION: Final = "Амортизация"
    SCENARIOS: Final = "Сценарии"
    ECOLOGY: Final = "Экология"
    HORIZON: Final = "Горизонт"
    SCENARIO_SAVE: Final = "Сохранение"
    SCENARIO_FILE_IO: Final = "Импорт / экспорт JSON"
    SCENARIO_LIBRARY: Final = "Сохранённые в сессии"


class ExportLabels:
    SIMPLE_TABLE: Final = "Помесячная детализация модели"
    PRO_TABLE: Final = "Помесячная детализация модели"
    BOARD_HTML_TITLE: Final = "HTML отчёт"
    BOARD_HTML_SUB: Final = "Для браузера"
    BOARD_PDF_TITLE: Final = "PDF отчёт"
    BOARD_PDF_SUB: Final = "Для печати и отправки"
    BOARD_ZIP_TITLE: Final = "ZIP pack"
    BOARD_ZIP_SUB: Final = "Полный пакет файлов"
    BOARD_CSV_TITLE: Final = "CSV данные"
    BOARD_CSV_SUB: Final = "Помесячная детализация"
    DOWNLOAD_CSV: Final = "Скачать CSV для отчёта"
    DOWNLOAD_HTML_SINGLE: Final = "Скачать HTML инвестиционный отчёт"
    DOWNLOAD_HTML_SIMPLE: Final = "Скачать HTML отчёт Simple"
    DOWNLOAD_HTML_COMPARE: Final = "Скачать HTML отчёт сравнения"
    DOWNLOAD_CSV_COMPARE: Final = "Скачать CSV матрицу сравнения"
    DOWNLOAD_PDF_SIMPLE: Final = "Скачать PDF отчёт Simple"
    DOWNLOAD_PDF_SINGLE: Final = "Скачать PDF инвестиционный отчёт"
    DOWNLOAD_PDF_COMPARE: Final = "Скачать PDF отчёт сравнения"
    DOWNLOAD_INVESTOR_PACK_PRO: Final = "Скачать ZIP investor pack (Pro)"
    DOWNLOAD_INVESTOR_PACK_SIMPLE: Final = "Скачать ZIP investor pack (Simple)"
    EXPORT_SUMMARY: Final = (
        "Выгрузки для передачи результатов и внешнего sharing."
    )
    EXPORT_FIELDS_NOTE: Final = (
        "Отчёты собираются из текущих KPI, memo и compare matrix; CSV — помесячная детализация."
    )
    EXPORT_HTML_SINGLE_DESC: Final = (
        "Отчёт по одной конфигурации: вывод, KPI, memo, сценарии и мощность."
    )
    EXPORT_HTML_COMPARE_DESC: Final = (
        "Сравнение 2–3 вариантов: trade-offs и матрица метрик."
    )
    EXPORT_CSV_COMPARE_DESC: Final = "Матрица сравнения для Excel/BI."
    EXPORT_COMPARE_EMPTY: Final = (
        "Для отчёта сравнения добавьте минимум 2 конфигурации в блоке «Сравнение конфигураций»."
    )
    EXPORT_SIMPLE_SUMMARY: Final = "Выгрузки Simple mode для отчёта и sharing."
    EXPORT_SIMPLE_FIELDS_NOTE: Final = (
        "Компактный отчёт и помесячный CSV по упрощённой модели."
    )
    EXPORT_HTML_SIMPLE_DESC: Final = (
        "Компактный отчёт: вывод, KPI, допущения и наблюдения."
    )
    EXPORT_PDF_SIMPLE_DESC: Final = "Печатная PDF-версия."
    EXPORT_PDF_SINGLE_DESC: Final = "Печатная PDF-версия."
    EXPORT_PDF_COMPARE_DESC: Final = "PDF сравнения вариантов."
    EXPORT_HTML_SHORT: Final = "Интерактивный отчёт для браузера."
    EXPORT_PDF_SHORT: Final = "Печать и пересылка внешним адресатам."
    EXPORT_ZIP_SHORT: Final = "Готовый пакет PDF/HTML/CSV."
    EXPORT_CSV_SHORT: Final = "Помесячные данные модели."
    EXPORT_INVESTOR_PACK_PRO_DESC: Final = (
        "ZIP для инвестора: отчёты, CSV и compare-файлы при наличии вариантов."
    )
    EXPORT_INVESTOR_PACK_SIMPLE_DESC: Final = "ZIP: PDF/HTML отчёт и помесячный CSV."


ADVISORY_CSS_MAP: Dict[Severity, str] = {
    "good": UIClassNames.SUCCESS,
    "bad": UIClassNames.DANGER,
    "warn": UIClassNames.WARN,
    "info": UIClassNames.INFO,
}

# Emoji-free advisory markers (severity conveyed by CSS class).
ADVISORY_ICON_MAP: Dict[Severity, str] = {
    "good": "",
    "bad": "",
    "warn": "",
    "info": "",
}


def format_sidebar_heading(title: str) -> str:
    return f'<p class="{UIClassNames.SIDEBAR_HEADING}">{title}</p>'
