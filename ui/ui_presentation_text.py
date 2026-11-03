from __future__ import annotations

import re

_DOT_DECIMAL_PERCENT_RE = re.compile(r"(?<![\d,])(\d+)\.(\d+)%")
_MULTIPLIER_DOT_DECIMAL_RE = re.compile(r"×(\d+)\.(\d+)")

_PHRASE_REPLACEMENTS = (
    ("UI-only", "упрощённая"),
    ("UI-only оценка", "упрощённая оценка"),
    ("presentation-only", "упрощённая"),
    ("monthly capacity", "месячной пропускной способности"),
    ("отдельно от payback", "отдельно от окупаемости капитала"),
    (" (payback)", " (окупаемости капитала)"),
    ("payback", "окупаемость"),
    ("%% по", "проценты по"),
    ("equity ", "собств. "),
)


def normalize_ui_decimal_text(text: str) -> str:
    if not text:
        return text
    normalized = _DOT_DECIMAL_PERCENT_RE.sub(r"\1,\2 %", text)
    normalized = _MULTIPLIER_DOT_DECIMAL_RE.sub(r"×\1,\2", normalized)
    return normalized


def sanitize_ui_visible_text(text: str) -> str:
    if not text:
        return text
    result = str(text)
    for old, new in _PHRASE_REPLACEMENTS:
        result = result.replace(old, new)
    return normalize_ui_decimal_text(result)
