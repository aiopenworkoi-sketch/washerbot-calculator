from __future__ import annotations

import os
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Iterable, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ui.report_text import humanize_report_type
from ui.theme_palette import BRAND, is_light


def _pdf_palette() -> dict[str, str]:
    """Палитра PDF под активную тему интерфейса."""
    if is_light():
        return {
            "bg": "#FFFFFF",
            "title": "#0B2545",
            "text": "#0F172A",
            "muted": "#64748B",
            "muted2": "#5F6B7A",
            "accent": "#13315C",
            "head": "#F1F5F9",
            "border": "#E2E8F0",
        }
    return {
        "bg": BRAND["bg"],
        "title": "#FFFFFF",
        "text": BRAND["text"],
        "muted": BRAND["muted"],
        "muted2": BRAND["muted"],
        "accent": BRAND["accent"],
        "head": BRAND["surface2"],
        "border": "#24344F",
    }

_FONT_NAME = "WasherBotPDF"
_FONT_BOLD = "WasherBotPDF-Bold"


@lru_cache(maxsize=1)
def _register_fonts() -> tuple[str, str]:
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "arial.ttf",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "Arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    bold_candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "arialbd.ttf",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "Arialbd.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    regular = next((p for p in candidates if p.is_file()), None)
    bold = next((p for p in bold_candidates if p.is_file()), regular)
    if regular is None:
        raise RuntimeError("Cyrillic-capable TTF font not found for PDF export")
    pdfmetrics.registerFont(TTFont(_FONT_NAME, str(regular)))
    if bold is not None:
        pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(bold)))
    else:
        pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(regular)))
    return _FONT_NAME, _FONT_BOLD


def pdf_styles() -> dict[str, ParagraphStyle]:
    body_font, bold_font = _register_fonts()
    P = _pdf_palette()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "WBTitle",
            parent=base["Heading1"],
            fontName=bold_font,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor(P["title"]),
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "WBSubtitle",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor(P["muted"]),
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "WBMeta",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(P["muted2"]),
            spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "WBSection",
            parent=base["Heading2"],
            fontName=bold_font,
            fontSize=12,
            leading=15,
            textColor=colors.HexColor(P["accent"]),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "WBBody",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(P["text"]),
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "WBBullet",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=9,
            leading=12,
            leftIndent=12,
            bulletIndent=0,
            spaceAfter=3,
            textColor=colors.HexColor(P["text"]),
        ),
        "disclaimer": ParagraphStyle(
            "WBDisclaimer",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(P["muted"]),
            spaceAfter=3,
        ),
    }


def _escape_pdf_text(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def best_recommendation(actions: Sequence[str]) -> str:
    """Первая «инвесторская» рекомендация: без внутренних QA-формулировок."""
    if not actions:
        return ""
    priority = ("Подготовить", "Пересчитать", "Скорректировать", "Проработать", "Пересмотреть", "Оценить")
    for prefix in priority:
        for action in actions:
            if action.startswith(prefix):
                return action
    return actions[0]


def pdf_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_escape_pdf_text(text), style)


def pdf_bullets(items: Sequence[str], styles: dict[str, ParagraphStyle]) -> list:
    flowables = []
    for item in items:
        if not item:
            continue
        flowables.append(
            Paragraph(f"• {_escape_pdf_text(item)}", styles["bullet"])
        )
    return flowables


def pdf_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    col_widths: Sequence[float] | None = None,
) -> Table:
    body_font, bold_font = _register_fonts()
    P = _pdf_palette()
    # Ячейки оборачиваем в Paragraph: иначе reportlab рисует строку одной линией
    # и длинный текст вылезает за колонку/страницу.
    cell_style = ParagraphStyle(
        "WBCell",
        fontName=body_font,
        fontSize=8,
        leading=10,
        wordWrap="CJK",
        spaceAfter=0,
        spaceBefore=0,
        textColor=colors.HexColor(P["text"]),
    )
    head_style = ParagraphStyle(
        "WBHead",
        parent=cell_style,
        fontName=bold_font,
        textColor=colors.HexColor(P["title"]),
    )

    def _cell(value: str, *, header: bool = False) -> Paragraph:
        text = _escape_pdf_text(str(value))
        return Paragraph(text, head_style if header else cell_style)

    data = [[_cell(h, header=True) for h in headers]]
    data.extend([[_cell(v) for v in row] for row in rows])

    table = Table(
        data,
        colWidths=col_widths,
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), body_font),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(P["head"])),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(P["text"])),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor(P["border"])),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _cover_logo() -> list:
    """Логотип на обложке; пустой список, если файла нет."""
    from ui.branding import LOGO_LIGHT_PATH, document_logo_path

    path = LOGO_LIGHT_PATH if not is_light() else document_logo_path()
    if path is None:
        return []
    try:
        from reportlab.platypus import Image as PdfImage

        height = 36.0
        img = PdfImage(str(path))
        width = height * img.imageWidth / img.imageHeight
        img.drawHeight = height
        img.drawWidth = width
        img.hAlign = "LEFT"
        return [img, Spacer(1, 4 * mm)]
    except Exception:
        return []


def pdf_cover_block(
    title: str,
    subtitle: str,
    report_type: str,
    generated_at: str,
    styles: dict[str, ParagraphStyle],
    *,
    mode_label: str = "",
    status_label: str = "",
) -> list:
    meta_parts = [
        f"Тип: {humanize_report_type(report_type)}",
        f"Сформирован: {generated_at}",
    ]
    if mode_label:
        meta_parts.insert(0, f"Режим: {mode_label}")
    logo_flowables = _cover_logo()
    if not logo_flowables:
        logo_flowables = [pdf_paragraph("WasherBot · Investment Analytics", styles["meta"])]
    flowables = [
        *logo_flowables,
        pdf_paragraph(title, styles["title"]),
        pdf_paragraph(subtitle, styles["subtitle"]),
    ]
    if status_label:
        flowables.append(pdf_paragraph(status_label, styles["meta"]))
    flowables.append(pdf_paragraph(" · ".join(meta_parts), styles["meta"]))
    flowables.append(Spacer(1, 4 * mm))
    return flowables


def _paint_page_background(canvas, doc) -> None:
    """Тёмный фон страницы для тёмной темы."""
    if is_light():
        return
    palette = _pdf_palette()
    canvas.saveState()
    canvas.setFillColor(colors.HexColor(palette["bg"]))
    canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    canvas.restoreState()


def build_pdf_bytes(flowables: Iterable) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="WasherBot Report",
    )
    doc.build(
        list(flowables),
        onFirstPage=_paint_page_background,
        onLaterPages=_paint_page_background,
    )
    content = buffer.getvalue()
    if not content.startswith(b"%PDF-"):
        raise RuntimeError("PDF generation failed: invalid PDF header")
    return content
