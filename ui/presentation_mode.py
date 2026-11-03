from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Literal

import streamlit as st

from ui.presentation_query import read_presentation_query_directive, resolve_presentation_mode
from ui.text_fallbacks import coerce_visible_text

_PRESENTATION_QUERY_KEYS = ("present", "presentation", "demo")
_USER_SET_KEY = "presentation_mode_user_set"
_SESSION_FLAG_KEY = "presentation_mode"
_SIDEBAR_PULSE_KEY = "wb_sidebar_pulse"
_DEV_NOTE_KEY = "wb_dev_runtime_note"


Tier = Literal["secondary", "utility", "tertiary"]


def _query_params_mapping() -> dict[str, object]:
    try:
        return dict(st.query_params)
    except Exception:
        return {}


def _query_directive() -> str:
    return read_presentation_query_directive(_query_params_mapping())


def clear_presentation_query_params() -> None:
    """Remove presentation-related query params from the URL."""
    try:
        qp = st.query_params
        for key in _PRESENTATION_QUERY_KEYS:
            if key in qp:
                del qp[key]
    except Exception:
        pass


def init_presentation_mode() -> None:
    """Sync presentation mode from URL; respect explicit ?present=0 override."""
    directive = _query_directive()
    if directive == "off":
        st.session_state[_SESSION_FLAG_KEY] = False
        st.session_state[_USER_SET_KEY] = True
        clear_presentation_query_params()
        return

    resolved = resolve_presentation_mode(
        directive=directive,  # type: ignore[arg-type]
        user_set=bool(st.session_state.get(_USER_SET_KEY)),
        session_value=bool(st.session_state.get(_SESSION_FLAG_KEY, False)),
    )
    st.session_state[_SESSION_FLAG_KEY] = resolved
    if directive == "on":
        return
    if not st.session_state.get(_USER_SET_KEY):
        st.session_state[_SESSION_FLAG_KEY] = False


def is_presentation_mode() -> bool:
    return bool(st.session_state.get(_SESSION_FLAG_KEY, False))


def disable_presentation_mode() -> None:
    st.session_state[_SESSION_FLAG_KEY] = False
    st.session_state[_USER_SET_KEY] = True
    clear_presentation_query_params()


def enable_presentation_mode() -> None:
    st.session_state[_SESSION_FLAG_KEY] = True
    st.session_state[_USER_SET_KEY] = True


def set_presentation_mode(enabled: bool) -> None:
    if enabled:
        enable_presentation_mode()
    else:
        disable_presentation_mode()


def request_sidebar_attention() -> None:
    st.session_state[_SIDEBAR_PULSE_KEY] = True


def render_presentation_flag() -> None:
    if is_presentation_mode():
        st.markdown(
            '<div class="wb-presentation-flag" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )


def render_presentation_sidebar_marker() -> None:
    """Markers inside sidebar for scoped CSS (no layout hiding)."""
    markers: list[str] = []
    if is_presentation_mode():
        markers.append('<div class="wb-presentation-sidebar-marker" aria-hidden="true"></div>')
    if st.session_state.pop(_SIDEBAR_PULSE_KEY, False):
        markers.append('<div class="wb-sidebar-pulse-marker" aria-hidden="true"></div>')
    if markers:
        st.markdown("".join(markers), unsafe_allow_html=True)


def render_presentation_recovery_control() -> None:
    if not is_presentation_mode():
        return
    st.markdown('<div class="wb-presentation-recovery">', unsafe_allow_html=True)
    row = st.columns([1, 2.6, 1], gap="small")
    with row[1]:
        btn_a, btn_b = st.columns(2, gap="small")
        with btn_a:
            if st.button(
                "Открыть панель настроек",
                key="wb_open_settings_panel",
                use_container_width=True,
                help="Подсветить боковую панель слева с параметрами расчёта",
            ):
                request_sidebar_attention()
                st.rerun()
        with btn_b:
            if st.button(
                "Вернуться к рабочему режиму",
                key="wb_exit_presentation_mode",
                type="primary",
                use_container_width=True,
                help="Отключить режим презентации",
            ):
                disable_presentation_mode()
                st.rerun()
        st.caption(
            "Настройки — в панели слева. Если панель свёрнута, нажмите ▸ у левого края экрана."
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_dev_runtime_note() -> None:
    """Optional local verification banner (WB_DEV=1 or ?dev=1)."""
    try:
        dev_query = str(st.query_params.get("dev", "")).lower() in {"1", "true", "yes", "on"}
    except Exception:
        dev_query = False
    if os.environ.get("WB_DEV") != "1" and not dev_query:
        return
    if st.session_state.get(_DEV_NOTE_KEY):
        return
    st.session_state[_DEV_NOTE_KEY] = True
    st.caption(
        "DEV: после изменений UI shell перезапустите Streamlit. "
        "Проверьте / и /?present=1. См. DEV.md."
    )


def render_presentation_mode_controls() -> None:
    init_presentation_mode()
    row = st.columns([1.6, 1, 1.6], gap="small")
    with row[1]:
        enabled = st.toggle(
            "Режим презентации",
            value=is_presentation_mode(),
            key="wb_presentation_mode_toggle",
            help="Фокус на hero, KPI и сценарии; вторичные блоки свёрнуты",
        )
    if enabled != is_presentation_mode():
        set_presentation_mode(enabled)
        st.rerun()
    if is_presentation_mode():
        render_presentation_recovery_control()
    render_dev_runtime_note()


@contextmanager
def presentation_secondary_panel(
    title: str,
    *,
    subtitle: str | None = None,
    tier: Tier = "secondary",
) -> Iterator[None]:
    """In presentation mode wrap content in a collapsed expander; otherwise pass through."""
    if not is_presentation_mode():
        yield
        return

    clean_title = coerce_visible_text(title) or "Дополнительно"
    clean_sub = coerce_visible_text(subtitle) if subtitle else ""
    label = clean_title if not clean_sub else f"{clean_title} — {clean_sub}"

    with st.expander(label, expanded=False):
        st.markdown(
            f'<div class="wb-tier-panel wb-tier-panel--{tier}">',
            unsafe_allow_html=True,
        )
        yield
        st.markdown("</div>", unsafe_allow_html=True)
