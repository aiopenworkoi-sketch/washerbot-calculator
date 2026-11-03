from __future__ import annotations

from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from ui.branding import logo_img_html
from ui.display_fallbacks import (
    has_finite_irr,
    is_missing_numeric,
    is_missing_payback_months,
    missing_placeholder,
)
from ui.text_fallbacks import coerce_visible_text
from ui.theme_tokens import BRAND


def fmt_money(value: float, decimals: int = 0, suffix: str = "₽") -> str:
    """Форматирует число как деньги с разделением тысяч."""
    if is_missing_numeric(value):
        return missing_placeholder()
    sign = "-" if value < 0 else ""
    v = abs(float(value))
    if decimals == 0:
        s = f"{v:,.0f}".replace(",", " ")
    else:
        s = f"{v:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return f"{sign}{s} {suffix}".strip()


def fmt_money_compact(value: float) -> str:
    """Форматирует крупные суммы: 1.5 млн, 2.3 млрд."""
    if is_missing_numeric(value):
        return missing_placeholder()
    v = abs(float(value))
    sign = "-" if value < 0 else ""
    if v >= 1e9:
        return f"{sign}{v/1e9:.2f} млрд ₽".replace(".", ",")
    if v >= 1e6:
        return f"{sign}{v/1e6:.2f} млн ₽".replace(".", ",")
    if v >= 1e3:
        return f"{sign}{v/1e3:.0f} тыс. ₽"
    return f"{sign}{v:.0f} ₽"


def fmt_pct(value: float, decimals: int = 1) -> str:
    """Форматирует число как процент."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"{value*100:.{decimals}f} %".replace(".", ",")


def fmt_ratio_pct(value: float, decimals: int = 1) -> str:
    """Форматирует долю (0..1) как процент: 12,3 %."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"{value * 100:.{decimals}f} %".replace(".", ",")


def fmt_percent_value(value: float, decimals: int = 1) -> str:
    """Форматирует уже масштабированный процент (0..100): 12,3 %."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"{value:.{decimals}f} %".replace(".", ",")


def fmt_irr(value: float) -> str:
    """IRR в KPI-карточках с fallback на — для NaN."""
    return fmt_pct(value) if has_finite_irr(value) else missing_placeholder()


def fmt_volume_m3(value: float) -> str:
    """Объём воды с разделением тысяч."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"{value:,.0f} м³".replace(",", " ")


def fmt_int(value: float) -> str:
    """Форматирует целое с разделителями тысяч."""
    if is_missing_numeric(value):
        return missing_placeholder()
    return f"{int(round(value)):,}".replace(",", " ")


def fmt_months(months: float) -> str:
    """Форматирует число месяцев в 'X лет Y мес'."""
    if is_missing_payback_months(months):
        return missing_placeholder()
    years = int(months // 12)
    rem = int(round(months - years * 12))
    # 35,9 мес — это 3 года, а не «2 года 12 мес»
    if rem == 12:
        years += 1
        rem = 0
    if years == 0:
        return f"{rem} мес"
    if rem == 0:
        return f"{years} {_year_word(years)}"
    return f"{years} {_year_word(years)} {rem} мес"


def _year_word(years: int) -> str:
    """Склонение слова 'год'."""
    if 11 <= (years % 100) <= 19:
        return "лет"
    last = years % 10
    if last == 1:
        return "год"
    if 2 <= last <= 4:
        return "года"
    return "лет"


PLOTLY_PRESENTATION_CONFIG: dict = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}


def style_plotly(fig: go.Figure, height: int = 400, title: str = "") -> go.Figure:
    """Применяет тёмный investor/demo стиль к графику."""
    grid_color = "rgba(42, 52, 65, 0.42)"
    layout_kwargs = dict(
        template="plotly_dark",
        paper_bgcolor=BRAND["bg2"],
        plot_bgcolor=BRAND["bg2"],
        font=dict(
            family="Inter, system-ui, -apple-system, sans-serif",
            size=13,
            color=BRAND["text"],
        ),
        height=height,
        margin=dict(l=48, r=24, t=44 if title else 28, b=48),
        legend=dict(
            bgcolor="rgba(17,24,39,0.55)",
            bordercolor=BRAND["border"],
            borderwidth=0,
            font=dict(color=BRAND["text"], size=12),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            xanchor="left",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=BRAND["card"],
            bordercolor=BRAND["border"],
            font=dict(color=BRAND["text"], size=12),
        ),
    )
    clean_title = title.strip() if title else ""
    if clean_title and clean_title.lower() not in {"undefined", "none"}:
        layout_kwargs["title"] = dict(
            text=clean_title,
            font=dict(size=16, color=BRAND["text"], family="Inter"),
            x=0.02,
            xanchor="left",
        )
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid_color,
        gridwidth=0.5,
        zeroline=False,
        showline=False,
        tickfont=dict(color=BRAND["text2"], size=11),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        gridwidth=0.5,
        zeroline=True,
        zerolinecolor="rgba(122,132,148,0.55)",
        zerolinewidth=1,
        showline=False,
        tickfont=dict(color=BRAND["text2"], size=11),
    )
    return fig


def empty_chart(message: str = "Нет данных") -> go.Figure:
    """Пустой график с сообщением."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color=BRAND["muted"]),
    )
    fig.update_layout(
        paper_bgcolor=BRAND["bg2"],
        plot_bgcolor=BRAND["bg2"],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def render_header(mode: str):
    """Рендер шапки. mode = 'simple' | 'pro'."""
    badge_text = "Простой расчёт" if mode == "simple" else "Углублённый расчёт"
    subtitle = (
        "Быстрая оценка окупаемости робот-мойки Leisuwash"
        if mode == "simple"
        else "Финансовое моделирование автомойки с детальной аналитикой"
    )
    logo_html = logo_img_html(height=48, margin="0 0 12px")
    brand_html = logo_html or '<h1 class="wb-title">WasherBot</h1>'

    html = f"""
    <div class="wb-header">
        <div class="wb-header-row">
            <div class="wb-header-left">
                {brand_html}
                <div class="wb-badge">{badge_text}</div>
                <p class="wb-subtitle">{subtitle}</p>
            </div>
            <div class="wb-header-right">
                <a href="tel:+74997693910">+7 (499) 769-39-10</a><br>
                <a href="mailto:info@washerbot.ru">info@washerbot.ru</a><br>
                <a href="https://washerbot.ru" target="_blank">washerbot.ru</a>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_mode_switcher() -> str:
    """
    Рендер переключателя Простой / Углублённый.
    Сохраняет выбор в session_state.
    """
    if "mode" not in st.session_state:
        st.session_state.mode = "simple"

    st.markdown('<div class="wb-mode-tabs">', unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="small")

    with col1:
        if st.button(
            "Простой",
            type="primary" if st.session_state.mode == "simple" else "secondary",
            use_container_width=True,
            key="btn_mode_simple",
        ):
            st.session_state.mode = "simple"
            st.rerun()

    with col2:
        if st.button(
            "Углублённый",
            type="primary" if st.session_state.mode == "pro" else "secondary",
            use_container_width=True,
            key="btn_mode_pro",
        ):
            st.session_state.mode = "pro"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    hint = (
        "Базовые параметры — быстрая оценка"
        if st.session_state.mode == "simple"
        else "Сценарии, кредит, налоги, чувствительность, экология"
    )
    st.markdown(
        f'<div class="wb-mode-info">{hint}</div>',
        unsafe_allow_html=True,
    )

    return st.session_state.mode


def render_footer():
    """Рендер футера."""
    html = f"""
    <div class="wb-footer">
        <div class="wb-footer-grid">
            <div class="wb-footer-copy">
                <p class="wb-footer-kicker">Экспертная поддержка WasherBot</p>
                <h3>Получите персональный расчёт и подбор оборудования</h3>
                <p class="wb-footer-support">
                    Подберём модель Leisuwash под ваш регион, трафик и бюджет —
                    с учётом площадки, CAPEX и целевой окупаемости.
                </p>
            </div>
            <div class="wb-footer-contact">
                <a class="wb-footer-pill" href="tel:+74997693910">+7 (499) 769-39-10</a>
                <a class="wb-footer-pill" href="mailto:info@washerbot.ru">info@washerbot.ru</a>
                <a class="wb-footer-cta" href="https://washerbot.ru" target="_blank" rel="noopener">
                    washerbot.ru
                </a>
            </div>
        </div>
        <p class="wb-footer-legal">
            © {datetime.now().year} WasherBot. Расчёт носит ориентировочный характер.
        </p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric(
    label: str,
    value: str,
    hint: str = "",
    status: str = "",
    emphasis: str = "",
):
    """Рендер одной метрики в фирменном стиле."""
    label_clean = coerce_visible_text(label) or ""
    value_clean = coerce_visible_text(value) or missing_placeholder()
    hint_clean = coerce_visible_text(hint)
    cls = "wb-metric"
    if emphasis == "primary":
        cls += " wb-metric--primary"
    elif emphasis == "secondary":
        cls += " wb-metric--secondary"
    if status:
        cls += f" {status}"
    html = f"""
    <div class="{cls}">
        <div class="wb-metric-label">{label_clean}</div>
        <div class="wb-metric-value">{value_clean}</div>
        {f'<div class="wb-metric-hint">{hint_clean}</div>' if hint_clean else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
