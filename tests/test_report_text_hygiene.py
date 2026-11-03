from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import replace

from app import calculate_pro, calculate_simple
from data.sample_params import build_sample_pro_params, build_sample_simple_params
from ui.compare_specs import build_variant_snapshot
from ui.pdf_exports import (
    build_comparison_pdf_artifact,
    build_pro_pdf_artifact,
    build_simple_pdf_artifact,
)
from ui.report_exports import (
    build_comparison_report_artifact,
    build_simple_report_artifact,
    build_single_report_artifact,
)
from ui.report_text import (
    format_presentation_multiplier,
    format_presentation_pct_value,
    format_presentation_ratio_pct,
    humanize_report_type,
    humanize_tax_regime,
    normalize_presentation_decimals,
    sanitize_report_visible_text,
)

BAD_VISIBLE_TOKENS = (
    "<b>",
    "</b>",
    "USN_INCOME",
    "pro_investment",
    "simple_investment",
    "%%",
    "presentation-only",
    "payback",
    "monthly capacity",
)

BAD_DECIMAL_PATTERNS = (
    r"\d+\.\d+%",
    r"×\d+\.\d+",
)

UI_TOKENS = (" в UI", " для интерфейса")


def _visible_text_from_html(html_bytes: bytes) -> str:
    text = html_bytes.decode("utf-8")
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def _visible_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Возвращает только те части PDF, где может лежать видимый текст: содержимое
    потоков без бинарных данных. Раньше сюда попадали сжатые шрифтовые потоки,
    из-за чего тест ловил «7.2%» в случайных байтах.
    """
    import re
    import zlib

    text_parts: list[str] = []
    pos = 0
    raw = pdf_bytes
    for match in re.finditer(rb"stream\r?\n", raw):
        text_parts.append(raw[pos:match.start()].decode("latin-1", "ignore"))
        end = raw.find(b"endstream", match.end())
        if end < 0:
            break
        body = raw[match.end():end]
        try:
            decoded = zlib.decompress(body)
        except Exception:
            decoded = b""
        if decoded:
            # оставляем только ASCII-фрагменты: операторы и строки текста
            ascii_runs = re.findall(rb"[\x09\x0a\x0d\x20-\x7e]{8,}", decoded)
            text_parts.append(b" ".join(ascii_runs).decode("latin-1", "ignore"))
        pos = end + len(b"endstream")
    text_parts.append(raw[pos:].decode("latin-1", "ignore"))
    return " ".join(" ".join(text_parts).split())


def _pdf_must_not_contain(pdf_bytes: bytes, needle: str) -> None:
    encoded = needle.encode("utf-8")
    assert encoded not in pdf_bytes
    assert encoded.lower() not in pdf_bytes.lower()


def _assert_no_bad_tokens(text: str, *, pdf: bool = False) -> None:
    lowered = text.lower()
    for token in BAD_VISIBLE_TOKENS:
        if pdf and token in ("%%", "<b>", "</b>"):
            continue
        assert token.lower() not in lowered, f"found {token!r} in visible text"
    for pattern in BAD_DECIMAL_PATTERNS:
        assert not re.search(pattern, text), f"found dot-decimal pattern {pattern!r}"
    for token in UI_TOKENS:
        assert token not in text, f"found internal UI token {token!r}"
    if not pdf:
        assert "%%" not in lowered
    assert not re.search(r"\d{1,3}(?:,\d{3})+", text), "comma-separated thousands found"


def test_presentation_formatters_russian_locale() -> None:
    assert format_presentation_ratio_pct(0.18) == "18,0 %"
    assert format_presentation_ratio_pct(1.454) == "145,4 %"
    assert format_presentation_pct_value(123.3) == "123,3 %"
    assert format_presentation_pct_value(0.0) == "0,0 %"
    assert format_presentation_multiplier(0.7) == "×0,70"
    assert format_presentation_multiplier(1.0) == "×1,00"
    assert format_presentation_multiplier(1.3) == "×1,30"


def test_normalize_presentation_decimals_rewrites_leaked_ui_values() -> None:
    raw = "IRR 18.0% · маржа 45.9% · сценарии ×0.70 — ×1.00 — ×1.30"
    normalized = normalize_presentation_decimals(raw)
    assert "18.0%" not in normalized
    assert "45.9%" not in normalized
    assert "×0.70" not in normalized
    assert "18,0 %" in normalized
    assert "45,9 %" in normalized
    assert "×0,70" in normalized
    assert "×1,00" in normalized
    assert "×1,30" in normalized


def test_sanitize_report_visible_text_strips_html_and_tokens() -> None:
    raw = (
        "<b>Цены ±10%</b> · USN_INCOME · presentation-only · "
        "monthly capacity · payback · 1,800 авто/мес · 286,564 ₽/мес · %% по кредиту · "
        "маржа 18.0% · ×0.70"
    )
    cleaned = sanitize_report_visible_text(raw)
    assert "<b>" not in cleaned
    assert "USN_INCOME" not in cleaned
    assert "presentation-only" not in cleaned
    assert "monthly capacity" not in cleaned
    assert "payback" not in cleaned
    assert "%%" not in cleaned
    assert "1 800" in cleaned
    assert "286 564" in cleaned
    assert "18,0 %" in cleaned
    assert "×0,70" in cleaned
    assert "УСН Доходы 6%" in cleaned
    assert " в UI" not in cleaned


def test_humanize_helpers() -> None:
    assert humanize_tax_regime("USN_INCOME") == "УСН Доходы 6%"
    assert humanize_report_type("pro_investment") == "Инвестиционный отчёт (Pro)"


def test_html_reports_visible_text_hygiene() -> None:
    simple = build_simple_report_artifact(calculate_simple(build_sample_simple_params()))
    pro = build_single_report_artifact(calculate_pro(build_sample_pro_params()))
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    comp = build_comparison_report_artifact(
        [
            build_variant_snapshot("base", "База", p1, r1),
            build_variant_snapshot("alt", "Альт", p2, calculate_pro(p2)),
        ],
        baseline_id="base",
    )
    for artifact in (simple, pro, comp):
        _assert_no_bad_tokens(_visible_text_from_html(artifact.content))
        assert humanize_report_type(artifact.report_type).lower() in _visible_text_from_html(
            artifact.content
        ).lower()


def test_pdf_reports_visible_text_hygiene() -> None:
    simple = build_simple_pdf_artifact(calculate_simple(build_sample_simple_params()))
    pro = build_pro_pdf_artifact(calculate_pro(build_sample_pro_params()))
    p1 = build_sample_pro_params()
    r1 = calculate_pro(p1)
    p2 = replace(deepcopy(p1), cars_per_day_avg=p1.cars_per_day_avg + 10)
    comp = build_comparison_pdf_artifact(
        [
            build_variant_snapshot("base", "База", p1, r1),
            build_variant_snapshot("alt", "Альт", p2, calculate_pro(p2)),
        ],
        baseline_id="base",
    )
    for artifact in (simple, pro, comp):
        visible = _visible_text_from_pdf(artifact.content)
        _assert_no_bad_tokens(visible, pdf=True)
        for token in ("USN_INCOME", "pro_investment", "simple_investment", "presentation-only", "payback", "monthly capacity"):
            _pdf_must_not_contain(artifact.content, token)
        _pdf_must_not_contain(artifact.content, "%% по")
        _pdf_must_not_contain(artifact.content, artifact.report_type)


def test_html_export_bytes_have_no_script_injection() -> None:
    artifacts = [
        build_simple_report_artifact(calculate_simple(build_sample_simple_params())),
        build_single_report_artifact(calculate_pro(build_sample_pro_params())),
    ]
    for artifact in artifacts:
        lowered = artifact.content.lower()
        assert b"<script" not in lowered
        assert b"kaspersky" not in lowered
