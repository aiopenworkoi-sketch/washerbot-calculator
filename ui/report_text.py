from __future__ import annotations

import html
import re
from typing import Iterable

from finance.taxes import TAX_REGIMES_LABELS
from ui.display_fallbacks import is_missing_numeric
from ui.renderers import missing_placeholder

REPORT_TYPE_LABELS: dict[str, str] = {
    "simple_investment": "Инвестиционный отчёт (Simple)",
    "pro_investment": "Инвестиционный отчёт (Pro)",
    "simple_investment_executive": "Исполнительное резюме (Simple)",
    "pro_investment_executive": "Исполнительное резюме (Pro)",
    "pro_comparison": "Сравнительный отчёт (Pro)",
    "comparison_matrix": "Матрица сравнения",
}

_INLINE_TAG_RE = re.compile(r"<[^>]+>")
_COMMA_THOUSANDS_RE = re.compile(r"(?<!\d)(?P<num>\d{1,3}(?:,\d{3})+)(?!\d)")
_DOT_DECIMAL_PERCENT_RE = re.compile(r"(?<![\d,])(\d+)\.(\d+)%")
_MULTIPLIER_DOT_DECIMAL_RE = re.compile(r"×(\d+)\.(\d+)")


def humanize_tax_regime(code: str) -> str:
    return TAX_REGIMES_LABELS.get(code, code)


def humanize_report_type(code: str) -> str:
    return REPORT_TYPE_LABELS.get(code, code.replace("_", " "))


def format_presentation_ratio_pct(value: float, *, decimals: int = 1) -> str:
    """Format a 0..1 ratio for HTML/PDF visible text: 0.18 -> '18,0 %'."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"{value * 100:.{decimals}f} %".replace(".", ",")


def format_presentation_pct_value(value: float, *, decimals: int = 1) -> str:
    """Format a 0..100 percent for HTML/PDF visible text: 145.4 -> '145,4 %'."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"{value:.{decimals}f} %".replace(".", ",")


def format_presentation_multiplier(value: float, *, decimals: int = 2) -> str:
    """Format a traffic multiplier for HTML/PDF visible text: 0.7 -> '×0,70'."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"×{value:.{decimals}f}".replace(".", ",")


def strip_inline_html(text: str) -> str:
    if not text:
        return text
    cleaned = _INLINE_TAG_RE.sub("", text)
    return html.unescape(cleaned).strip()


def format_report_int(value: float) -> str:
    from ui.renderers import fmt_int

    return fmt_int(value)


def format_report_money_per_unit(value: float, *, suffix: str) -> str:
    from ui.renderers import fmt_money

    return fmt_money(value, suffix=suffix)


def normalize_presentation_decimals(text: str) -> str:
    """Normalize dot-decimal percents and multipliers in presentation text."""
    if not text:
        return text
    normalized = _DOT_DECIMAL_PERCENT_RE.sub(r"\1,\2 %", text)
    return _MULTIPLIER_DOT_DECIMAL_RE.sub(r"×\1,\2", normalized)


def _normalize_comma_thousands(text: str) -> str:
    return _COMMA_THOUSANDS_RE.sub(
        lambda match: match.group("num").replace(",", " "),
        text,
    )


def _normalize_internal_phrases(text: str) -> str:
    replacements = (
        (
            "Порог покрытия затрат в UI — presentation-only оценка по средним месячным потокам.",
            "Порог покрытия затрат — упрощённая оценка по средним месячным потокам.",
        ),
        (
            "Порог покрытия затрат в UI — упрощённая оценка для интерфейса оценка по средним месячным потокам.",
            "Порог покрытия затрат — упрощённая оценка по средним месячным потокам.",
        ),
        ("presentation-only", "упрощённая"),
        ("monthly capacity", "месячной пропускной способности"),
        ("capacity = 0", "нулевой мощности"),
        ("Перегруз capacity:", "Перегруз мощности:"),
        ("отдельно от payback", "отдельно от окупаемости капитала"),
        (" payback", " окупаемости капитала"),
        ("%% по", "проценты по"),
        (" в UI — ", " — "),
        (" для интерфейса", ""),
    )
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def sanitize_report_visible_text(text: str) -> str:
    """Plain-text hygiene for HTML/PDF report bodies (not machine export ids)."""
    if not text:
        return text

    result = strip_inline_html(str(text))

    for code, label in TAX_REGIMES_LABELS.items():
        result = result.replace(code, label)
    for code, label in REPORT_TYPE_LABELS.items():
        result = result.replace(code, label)

    result = _normalize_internal_phrases(result)
    result = normalize_presentation_decimals(result)
    return _normalize_comma_thousands(result).strip()


def sanitize_report_texts(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sanitize_report_visible_text(value) for value in values)
