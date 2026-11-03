from __future__ import annotations

from typing import Any


def is_visible_text(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    lowered = text.lower()
    return lowered not in {"undefined", "none", "null", "nan"}


def coerce_visible_text(value: Any, *, default: str | None = None) -> str | None:
    if not is_visible_text(value):
        return default
    return str(value).strip()


def join_visible_parts(parts: list[Any], *, sep: str = " ") -> str | None:
    visible = [coerce_visible_text(part) for part in parts]
    cleaned = [part for part in visible if part]
    if not cleaned:
        return None
    return sep.join(cleaned)
