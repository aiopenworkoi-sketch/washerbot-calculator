"""Темы интерфейса: тёмная (по умолчанию) и светлая «белая бумага».

Палитра светлой темы взята с референсного PDF (белый лист, кремовые шапки,
золото #B08828), роли адаптированы под экран.

Все цвета — через единый реестр THEMES. В коде используется `BRAND` —
динамический прокси, который отдаёт значения активной темы, поэтому
существующие обращения `brand["text"]` работают без изменений.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, Mapping

DARK: Dict[str, str] = {
    # акценты и статусы
    "primary": "#2E86FF",
    "on_primary": "#FFFFFF",
    "accent": "#7C93B8",
    "cyan": "#6E8FA8",
    "purple": "#8B93A8",
    "green": "#4FA882",
    "red": "#C96B6B",
    "yellow": "#B89A4A",
    # поверхности
    "bg": "#0A0E14",
    "bg2": "#10161F",
    "card": "#161D28",
    "surface": "#131A24",
    "surface2": "#1A222E",
    "surface_muted": "#0E1319",
    # границы
    "border": "#5A6C86",
    "border_subtle": "rgba(138, 152, 168, 0.16)",
    "border_default": "rgba(42, 52, 65, 0.48)",
    # текст
    "text": "#ECEFF4",
    "text2": "#B8C0CC",
    "muted": "#8A94A4",
    # графики
    "chart_1": "#2E86FF",
    "chart_2": "#7C93B8",
    "chart_3": "#4FA882",
    "chart_4": "#B89A4A",
    "chart_5": "#C96B6B",
    "chart_grid": "rgba(138, 152, 168, 0.18)",
}

LIGHT: Dict[str, str] = {
    # поверхности: белый лист + кремовые карточки (референс PDF)
    "bg": "#FFFFFF",
    "bg2": "#FBF7EC",
    "card": "#FBF7EC",
    "surface": "#F6F0DF",
    "surface2": "#FFFFFF",
    "surface_muted": "#F7F2E4",
    # текст
    "text": "#1F1B16",
    "text2": "#4B4438",
    "muted": "#6E6656",
    # границы: интерактивные ≥3:1 на белом
    "border": "#8F8261",
    "border_subtle": "rgba(143, 130, 97, 0.24)",
    "border_default": "rgba(143, 130, 97, 0.45)",
    # акценты и статусы
    "primary": "#B08828",
    "on_primary": "#1F1B16",
    "accent": "#8A6A1E",
    "cyan": "#3E7C74",
    "purple": "#6B5B7A",
    "green": "#2F6B4F",
    "red": "#A63D3D",
    "yellow": "#8A6A1E",
    # графики: контрастны на белом
    "chart_1": "#B08828",
    "chart_2": "#4F6B8A",
    "chart_3": "#2F6B4F",
    "chart_4": "#8A6A1E",
    "chart_5": "#A63D3D",
    "chart_grid": "rgba(31, 27, 22, 0.12)",
}

THEMES: Dict[str, Dict[str, str]] = {"dark": DARK, "light": LIGHT}
THEME_LABELS: Dict[str, str] = {"dark": "Тёмная", "light": "Светлая"}
DEFAULT_THEME = "dark"

_active_theme: str = DEFAULT_THEME


def set_active_theme(name: str) -> str:
    """Переключает активную тему; неизвестное имя → тёмная."""
    global _active_theme
    _active_theme = name if name in THEMES else DEFAULT_THEME
    return _active_theme


def get_active_theme() -> str:
    return _active_theme


def get_brand() -> Dict[str, str]:
    return THEMES[_active_theme]


def is_light() -> bool:
    return _active_theme == "light"


def rgba(color: str, alpha: float) -> str:
    """rgba() из hex-цвета темы: rgba('#2E86FF', 0.2) → 'rgba(46, 134, 255, 0.2)'."""
    value = str(color).strip()
    if value.startswith("#") and len(value) == 7:
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
        return f"rgba({r}, {g}, {b}, {alpha:g})"
    return value


class _BrandProxy(Mapping[str, str]):
    """Динамический словарь активной темы: BRAND['text'] всегда актуален."""

    def __getitem__(self, key: str) -> str:
        return THEMES[_active_theme][key]

    def __iter__(self) -> Iterator[str]:
        return iter(THEMES[_active_theme])

    def __len__(self) -> int:
        return len(THEMES[_active_theme])

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        return THEMES[_active_theme].get(key, default)

    def __repr__(self) -> str:  # pragma: no cover - отладка
        return f"BRAND(theme={_active_theme!r})"


BRAND: Mapping[str, str] = _BrandProxy()

__all__ = [
    "BRAND",
    "DARK",
    "LIGHT",
    "THEMES",
    "THEME_LABELS",
    "DEFAULT_THEME",
    "get_active_theme",
    "get_brand",
    "is_light",
    "rgba",
    "set_active_theme",
]
