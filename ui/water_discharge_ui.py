from __future__ import annotations

import streamlit as st

from finance.water_discharge import (
    PUBLIC_WATER_DISCHARGE_PROFILES,
    WATER_DISCHARGE_DEFAULT_PROFILE,
    is_legacy_water_discharge_profile,
)
from finance.water_usage import (
    is_typical_lt30_profile_exceeded,
    water_lt30_warning_message,
    water_usage_info_caption,
)


def render_water_discharge_usage_guardrail(
    *,
    profile: str,
    cars_per_day: float,
    water_per_wash_l: float,
) -> None:
    if is_typical_lt30_profile_exceeded(
        profile=profile,
        cars_per_day=cars_per_day,
        water_per_wash_l=water_per_wash_l,
    ):
        st.warning(water_lt30_warning_message(cars_per_day, water_per_wash_l))
    else:
        st.caption(water_usage_info_caption(cars_per_day, water_per_wash_l))


def render_water_discharge_profile_selector(*, key_prefix: str) -> str:
    """Public 3-profile selector; legacy profile stays until user updates explicitly."""
    profile_key = f"{key_prefix}_water_discharge_profile"
    if profile_key not in st.session_state:
        st.session_state[profile_key] = WATER_DISCHARGE_DEFAULT_PROFILE

    stored = str(st.session_state[profile_key])
    public_keys = [item[0] for item in PUBLIC_WATER_DISCHARGE_PROFILES]
    public_labels = [item[1] for item in PUBLIC_WATER_DISCHARGE_PROFILES]

    if is_legacy_water_discharge_profile(stored):
        st.info(
            "Сценарий использует legacy-профиль водоотведения (вода + 0.5× канализация). "
            "Расчёт сохранён для совместимости. Выберите актуальный профиль ниже, чтобы обновить."
        )
        with st.expander("Обновить профиль водоотведения", expanded=False):
            idx = public_keys.index(WATER_DISCHARGE_DEFAULT_PROFILE)
            selected_label = st.selectbox(
                "Новый профиль",
                options=public_labels,
                index=idx,
                key=f"{key_prefix}_water_discharge_migrate",
            )
            if st.button("Применить профиль", key=f"{key_prefix}_water_discharge_apply"):
                st.session_state[profile_key] = public_keys[
                    public_labels.index(selected_label)
                ]
                st.rerun()
        return stored

    idx = public_keys.index(stored) if stored in public_keys else public_keys.index(
        WATER_DISCHARGE_DEFAULT_PROFILE
    )
    selected_label = st.selectbox(
        "Профиль водоотведения",
        options=public_labels,
        index=idx,
        key=f"{key_prefix}_water_discharge_select",
        help=(
            "Влияет на стоимость м³ воды в переменных расходах и eco-оценке. "
            "Оценка суточного расхода — в блоке «Трафик»."
        ),
    )
    profile = public_keys[public_labels.index(selected_label)]
    st.session_state[profile_key] = profile
    return profile
