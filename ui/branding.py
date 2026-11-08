"""
Брендинг интерфейса: логотип Washing Robots Solutions.

В интерфейсе используется светлая версия логотипа (белые буквы, прозрачный фон) —
она рассчитана на тёмную тему. Файлы лежат в assets/, в разметку попадают как
data-URI, поэтому работают и в Streamlit, и в статичных отчётах.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Светлая версия для тёмной темы; тёмная — запасной вариант для светлых документов.
LOGO_LIGHT_PATH = _ASSETS / "logo_light.png"
LOGO_DARK_PATH = _ASSETS / "logo.png"
LOGO_ALT = "Washing Robots Solutions"


@lru_cache(maxsize=2)
def _data_uri(path_str: str) -> str:
    try:
        raw = Path(path_str).read_bytes()
    except OSError:
        return ""
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def logo_data_uri(*, light: bool = True) -> str:
    path = LOGO_LIGHT_PATH if light else LOGO_DARK_PATH
    return _data_uri(str(path))


def logo_available() -> bool:
    return bool(logo_data_uri())


def logo_img_html(*, height: int = 40, margin: str = "0", opacity: float = 1.0) -> str:
    """Логотип под активную тему: белый — на тёмной, тёмный — на светлой."""
    from ui.theme_palette import is_light

    uri = logo_data_uri(light=not is_light())
    if not uri:
        return ""
    return (
        f'<img src="{uri}" alt="{LOGO_ALT}" '
        f'style="height:{height}px;width:auto;display:block;'
        f'margin:{margin};opacity:{opacity};" />'
    )


def sidebar_logo_html() -> str:
    """Логотип для верха боковой панели."""
    return logo_img_html(height=40, margin="2px 0 14px")


def document_logo_html(*, height: int = 22, margin: str = "0 0 10px") -> str:
    """
    Логотип для отчётов: тёмная (исходная) версия — документы печатаются
    на белом фоне, белый текст там не виден.
    """
    uri = logo_data_uri(light=False)
    if not uri:
        return ""
    return (
        f'<img src="{uri}" alt="{LOGO_ALT}" '
        f'style="height:{height}px;width:auto;display:block;margin:{margin};" />'
    )


def document_logo_path() -> Path | None:
    """Путь к файлу логотипа для PDF-движка (reportlab)."""
    return LOGO_DARK_PATH if LOGO_DARK_PATH.is_file() else None
