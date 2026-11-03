from __future__ import annotations

from typing import Literal

import streamlit as st

from domain.params import ProParams, SimpleParams
from ui.presentation_mode import is_presentation_mode
from ui.scenario_io import (
    ScenarioValidationError,
    build_scenario_payload,
    parse_scenario_json,
    scenario_download_filename,
    scenario_payload_to_json,
    validate_scenario_payload,
)
from ui.scenario_state import (
    consume_scenario_flash,
    delete_session_scenario,
    list_session_scenarios,
    queue_scenario_apply,
    save_scenario_to_session,
)
from ui.ui_labels import SidebarSections, format_sidebar_heading

ScenarioMode = Literal["simple", "pro"]


def _render_scenario_flash() -> None:
    message = consume_scenario_flash()
    if message:
        st.sidebar.success(message)


def render_scenario_sidebar_block(
    mode: ScenarioMode,
    params: SimpleParams | ProParams,
) -> None:
    """Mobile-first scenario save/load block at the bottom of the sidebar."""
    presentation = is_presentation_mode()
    expanded = False

    with st.expander("Сценарии", expanded=expanded):
        st.markdown('<div class="wb-scenario-mobile-zone">', unsafe_allow_html=True)
        _render_scenario_flash()

        if presentation:
            st.caption(
                "В режиме презентации доступны только выгрузка и загрузка JSON. "
                "Полный менеджер — в рабочем режиме."
            )

        default_title = st.session_state.get("wb_scenario_draft_title", "")
        if not presentation:
            default_title = st.text_input(
                "Название сценария",
                value=default_title,
                key="wb_scenario_name_input",
                placeholder="Например: Москва, 2 робота",
            )
            st.session_state["wb_scenario_draft_title"] = default_title
            note = st.text_area(
                "Заметка (необязательно)",
                value=st.session_state.get("wb_scenario_draft_note", ""),
                key="wb_scenario_note_input",
                height=68,
            )
            st.session_state["wb_scenario_draft_note"] = note
        else:
            note = ""

        payload = build_scenario_payload(
            mode,
            params,
            title=default_title or f"{'Простой' if mode == 'simple' else 'Pro'} сценарий",
            note=note if not presentation else "",
        )
        pretty_json = scenario_payload_to_json(payload, compact=False)
        filename = scenario_download_filename(payload)

        if not presentation:
            st.markdown(
                format_sidebar_heading(SidebarSections.SCENARIO_SAVE),
                unsafe_allow_html=True,
            )
            if st.button(
                "Сохранить в сессию",
                key=f"wb_scenario_save_session_{mode}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    record = save_scenario_to_session(
                        default_title
                        or f"{'Простой' if mode == 'simple' else 'Pro'} {len(list_session_scenarios()) + 1}",
                        mode,
                        params,
                        note=note,
                    )
                    st.session_state["wb_scenario_draft_title"] = record.name
                    st.success(f"Сохранено: «{record.name}»")
                except ScenarioValidationError as exc:
                    st.error(str(exc))

        st.markdown(
            format_sidebar_heading(SidebarSections.SCENARIO_FILE_IO),
            unsafe_allow_html=True,
        )
        st.download_button(
            "Скачать JSON",
            data=pretty_json,
            file_name=filename,
            mime="application/json",
            key=f"wb_scenario_dl_{mode}",
            use_container_width=True,
        )
        with st.expander("Дополнительно: компактный JSON", expanded=False):
            st.caption("Тот же сценарий в более коротком формате для пересылки.")
            st.download_button(
                "Скачать компактный JSON",
                data=scenario_payload_to_json(payload, compact=True),
                file_name=filename.replace(".json", "_compact.json"),
                mime="application/json",
                key=f"wb_scenario_dl_compact_{mode}",
                use_container_width=True,
            )
        with st.expander("Загрузить JSON", expanded=False):
            uploaded = st.file_uploader(
                "Загрузить JSON-сценарий",
                type=["json"],
                key=f"wb_scenario_upload_{mode}",
                label_visibility="collapsed",
            )
            if uploaded is not None:
                try:
                    text = uploaded.getvalue().decode("utf-8")
                    raw = parse_scenario_json(text)
                    validated = validate_scenario_payload(raw)
                    queue_scenario_apply(validated)
                    st.rerun()
                except UnicodeDecodeError:
                    st.error("Файл должен быть в кодировке UTF-8.")
                except ScenarioValidationError as exc:
                    st.error(str(exc))

        if not presentation:
            records = list_session_scenarios()
            with st.expander(SidebarSections.SCENARIO_LIBRARY, expanded=False):
                if records:
                    for record in reversed(records):
                        label = f"**{record.name}** · {record.mode}"
                        st.markdown(label)
                        if record.payload.get("note"):
                            st.caption(str(record.payload["note"]))
                        btn_load, btn_del = st.columns(2, gap="small")
                        with btn_load:
                            if st.button(
                                "Загрузить",
                                key=f"wb_sc_load_{record.scenario_id}",
                                use_container_width=True,
                            ):
                                queue_scenario_apply(record.payload)
                                st.rerun()
                        with btn_del:
                            if st.button(
                                "Удалить",
                                key=f"wb_sc_del_{record.scenario_id}",
                                use_container_width=True,
                            ):
                                delete_session_scenario(record.scenario_id)
                                st.rerun()
                else:
                    st.caption("В этой сессии пока нет сохранённых сценариев.")
        st.markdown("</div>", unsafe_allow_html=True)
