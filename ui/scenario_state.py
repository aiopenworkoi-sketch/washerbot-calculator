from __future__ import annotations

import uuid
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

import streamlit as st

from domain.params import ProParams, SimpleParams
from finance.water_discharge import is_legacy_water_discharge_profile, water_discharge_profile_label
from ui.scenario_io import (
    ScenarioValidationError,
    build_scenario_payload,
    params_from_scenario_payload,
    scenario_to_widget_state,
    utc_now_iso,
    validate_scenario_payload,
)

SESSION_LIBRARY_KEY = "wb_scenario_library"
PENDING_APPLY_KEY = "wb_scenario_pending_apply"
FLASH_MESSAGE_KEY = "wb_scenario_flash_message"

ScenarioMode = Literal["simple", "pro"]


@dataclass
class ScenarioRecord:
    scenario_id: str
    name: str
    mode: ScenarioMode
    payload: dict[str, Any]
    saved_at: str


def _init_library() -> None:
    if SESSION_LIBRARY_KEY not in st.session_state:
        st.session_state[SESSION_LIBRARY_KEY] = []


def list_session_scenarios() -> list[ScenarioRecord]:
    _init_library()
    raw = st.session_state.get(SESSION_LIBRARY_KEY, [])
    records: list[ScenarioRecord] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        records.append(
            ScenarioRecord(
                scenario_id=str(item.get("scenario_id", "")),
                name=str(item.get("name", "")),
                mode=item.get("mode", "simple"),  # type: ignore[arg-type]
                payload=dict(item.get("payload", {})),
                saved_at=str(item.get("saved_at", "")),
            )
        )
    return records


def _write_library(records: list[ScenarioRecord]) -> None:
    st.session_state[SESSION_LIBRARY_KEY] = [
        {
            "scenario_id": r.scenario_id,
            "name": r.name,
            "mode": r.mode,
            "payload": deepcopy(r.payload),
            "saved_at": r.saved_at,
        }
        for r in records
    ]


def save_scenario_to_session(
    name: str,
    mode: ScenarioMode,
    params: SimpleParams | ProParams,
    *,
    note: str = "",
) -> ScenarioRecord:
    _init_library()
    clean_name = name.strip()
    if not clean_name:
        raise ScenarioValidationError("Укажите имя сценария.")

    payload = build_scenario_payload(mode, params, title=clean_name, note=note)
    record = ScenarioRecord(
        scenario_id=uuid.uuid4().hex[:12],
        name=clean_name,
        mode=mode,
        payload=payload,
        saved_at=utc_now_iso(),
    )
    records = list_session_scenarios()
    records.append(record)
    _write_library(records)
    return record


def delete_session_scenario(scenario_id: str) -> bool:
    records = list_session_scenarios()
    next_records = [r for r in records if r.scenario_id != scenario_id]
    if len(next_records) == len(records):
        return False
    _write_library(next_records)
    return True


def duplicate_session_scenario(scenario_id: str) -> ScenarioRecord | None:
    records = list_session_scenarios()
    source = next((r for r in records if r.scenario_id == scenario_id), None)
    if source is None:
        return None
    copy_name = f"{source.name} (копия)"
    payload = deepcopy(source.payload)
    payload["title"] = copy_name
    payload["created_at"] = utc_now_iso()
    record = ScenarioRecord(
        scenario_id=uuid.uuid4().hex[:12],
        name=copy_name,
        mode=source.mode,
        payload=payload,
        saved_at=utc_now_iso(),
    )
    records.append(record)
    _write_library(records)
    return record


def get_session_scenario(scenario_id: str) -> ScenarioRecord | None:
    return next((r for r in list_session_scenarios() if r.scenario_id == scenario_id), None)


def queue_scenario_apply(payload: dict[str, Any]) -> None:
    validated = validate_scenario_payload(payload)
    st.session_state[PENDING_APPLY_KEY] = deepcopy(validated)


def set_scenario_flash(message: str) -> None:
    st.session_state[FLASH_MESSAGE_KEY] = message


def consume_scenario_flash() -> str | None:
    message = st.session_state.pop(FLASH_MESSAGE_KEY, None)
    if isinstance(message, str) and message.strip():
        return message
    return None


def apply_pending_scenario_hydration() -> bool:
    """Apply queued scenario to widget keys before sidebar render. Returns True if applied."""
    pending = st.session_state.pop(PENDING_APPLY_KEY, None)
    if not isinstance(pending, dict):
        return False

    try:
        mode, params = params_from_scenario_payload(pending)
        widget_state = scenario_to_widget_state(mode, params)
    except ScenarioValidationError as exc:
        set_scenario_flash(f"Не удалось применить сценарий: {exc}")
        return False

    st.session_state["mode"] = mode
    for key, value in widget_state.items():
        st.session_state[key] = value

    title = pending.get("title") or "Сценарий"
    flash = f"Загружен сценарий «{title}» ({mode})."
    if is_legacy_water_discharge_profile(params.water_discharge_profile):
        flash += (
            f" Используется legacy-профиль водоотведения "
            f"({water_discharge_profile_label(params.water_discharge_profile)})."
        )
    set_scenario_flash(flash)
    return True
