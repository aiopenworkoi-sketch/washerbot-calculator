"""Переключение темы оформления: инициализация и кнопка в шапке."""

from __future__ import annotations

import streamlit as st

from ui.theme_tokens import (
    DEFAULT_THEME,
    get_active_theme,
    set_active_theme,
)

SESSION_KEY = "ui_theme"


def init_theme() -> str:
    """Читает тему из session_state и активирует её. Вызывать до inject_css."""
    theme = st.session_state.get(SESSION_KEY, DEFAULT_THEME)
    return set_active_theme(str(theme))


def render_theme_toggle() -> None:
    """Кнопка-переключатель в правом верхнем углу шапки."""
    theme = get_active_theme()
    is_dark = theme == "dark"
    label = "☀️ Светлая" if is_dark else "🌙 Тёмная"
    with st.container(key="wb_theme_switch"):
        if st.button(
            label,
            key="wb_theme_toggle_btn",
            help="Переключить тему оформления: тёмная / светлая",
            use_container_width=True,
        ):
            st.session_state[SESSION_KEY] = "light" if is_dark else "dark"
            st.rerun()


__all__ = ["init_theme", "render_theme_toggle", "SESSION_KEY"]
