from __future__ import annotations

from ui.ui_labels import SectionTitles
from ui.ui_presentation_text import normalize_ui_decimal_text, sanitize_ui_visible_text


def test_normalize_ui_decimal_percent() -> None:
    assert normalize_ui_decimal_text("IRR 18.0% · маржа 145.4%") == "IRR 18,0 % · маржа 145,4 %"


def test_sanitize_ui_visible_text_replaces_internal_tokens() -> None:
    raw = (
        "UI-only оценка · presentation-only · payback · monthly capacity · "
        "отдельно от payback · %% по кредиту"
    )
    cleaned = sanitize_ui_visible_text(raw)
    assert "UI-only" not in cleaned
    assert "presentation-only" not in cleaned
    assert "payback" not in cleaned
    assert "monthly capacity" not in cleaned
    assert "%%" not in cleaned


def test_break_even_subtitle_is_russian() -> None:
    sub = SectionTitles.BREAK_EVEN_SUB
    assert "UI-only" not in sub
    assert "payback" not in sub
    assert "%%" not in sub
