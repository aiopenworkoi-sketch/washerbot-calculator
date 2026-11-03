from __future__ import annotations

import html
from typing import Sequence

import streamlit as st

from ui.export_manifest import ExportActionSpec, ExportManifestGroup, PRIMARY_BOARD_GROUP_ID


def _infer_format_badge(action: ExportActionSpec) -> str:
    if action.format_badge:
        return action.format_badge
    action_id = action.action_id
    if "html" in action_id:
        return "HTML"
    if "pdf" in action_id:
        return "PDF"
    if "pack" in action_id or action.mime == "application/zip":
        return "ZIP"
    if "csv" in action_id or action.mime == "text/csv":
        return "CSV"
    return "FILE"


def export_action_rows(actions: Sequence[ExportActionSpec]) -> tuple[tuple[ExportActionSpec, ...], ...]:
    """Split actions into stable rows: pairs of half-width, or single full-width."""
    rows: list[list[ExportActionSpec]] = []
    pending_half: list[ExportActionSpec] = []
    for action in actions:
        if action.layout_hint == "full":
            if pending_half:
                rows.append(pending_half)
                pending_half = []
            rows.append([action])
            continue
        pending_half.append(action)
        if len(pending_half) == 2:
            rows.append(pending_half)
            pending_half = []
    if pending_half:
        rows.append(pending_half)
    return tuple(tuple(row) for row in rows)


def export_action_rows_compact(
    actions: Sequence[ExportActionSpec],
    *,
    columns: int = 3,
) -> tuple[tuple[ExportActionSpec, ...], ...]:
    """Dense grid rows for compact export action board."""
    if columns < 1:
        columns = 1
    rows: list[list[ExportActionSpec]] = []
    pending: list[ExportActionSpec] = []
    for action in actions:
        if action.layout_hint == "full":
            if pending:
                rows.append(pending)
                pending = []
            rows.append([action])
            continue
        pending.append(action)
        if len(pending) >= columns:
            rows.append(pending)
            pending = []
    if pending:
        rows.append(pending)
    return tuple(tuple(row) for row in rows)


def export_action_rows_board(
    actions: Sequence[ExportActionSpec],
) -> tuple[tuple[ExportActionSpec, ...], ...]:
    """Fixed 2x2 board rows for the four primary export actions."""
    ordered = sorted(actions, key=lambda action: (action.sort_order, action.action_id))
    if len(ordered) == 4:
        return ((ordered[0], ordered[1]), (ordered[2], ordered[3]))
    return export_action_rows(ordered)


def render_export_action_tile(action: ExportActionSpec) -> None:
    """Primary export tile: format chip, title, one-line hint, integrated download."""
    badge = html.escape(_infer_format_badge(action))
    title = html.escape(action.label)
    sub = html.escape(action.description)
    disabled_class = "" if action.available else " wb-export-tile--disabled"
    st.markdown(
        f'<div class="wb-export-tile wb-export-tile--board{disabled_class}" '
        f'data-export-format="{badge}">'
        f'<div class="wb-export-tile-head">'
        f'<span class="wb-export-badge">{badge}</span>'
        f'<span class="wb-export-tile-title">{title}</span>'
        f"</div>"
        f'<p class="wb-export-tile-hint">{sub}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )
    if action.available:
        st.download_button(
            label=action.label,
            data=action.content,
            file_name=action.filename,
            mime=action.mime,
            key=action.widget_key,
            use_container_width=True,
        )
    else:
        reason = action.unavailable_reason or "Недоступно"
        st.button(
            reason,
            disabled=True,
            use_container_width=True,
            key=f"{action.widget_key}_disabled",
        )


def render_export_action_card(action: ExportActionSpec) -> None:
    """Compact action tile for secondary compare exports."""
    badge = html.escape(_infer_format_badge(action))
    hint_html = ""
    if action.description:
        hint_html = (
            f'<p class="wb-export-tile-hint">{html.escape(action.description)}</p>'
        )
    st.markdown(
        f'<div class="wb-export-tile wb-export-tile--secondary" data-export-format="{badge}">'
        f'<div class="wb-export-tile-head">'
        f'<span class="wb-export-badge">{badge}</span>'
        f"</div>"
        f"{hint_html}"
        f"</div>",
        unsafe_allow_html=True,
    )
    if action.available:
        st.download_button(
            label=action.label,
            data=action.content,
            file_name=action.filename,
            mime=action.mime,
            key=action.widget_key,
            use_container_width=True,
        )
    else:
        reason = action.unavailable_reason or "Недоступно"
        st.button(
            reason,
            disabled=True,
            use_container_width=True,
            key=f"{action.widget_key}_disabled",
        )


def render_export_board(actions: Sequence[ExportActionSpec]) -> None:
    """Premium 2x2 export board (stacks to one column on narrow screens)."""
    board_actions = sorted(
        actions,
        key=lambda action: (action.sort_order, action.action_id),
    )
    st.markdown('<div class="wb-export-board">', unsafe_allow_html=True)
    for row in export_action_rows_board(board_actions):
        columns = st.columns(2, gap="small")
        for column, action in zip(columns, row):
            with column:
                render_export_action_tile(action)
    st.markdown("</div>", unsafe_allow_html=True)


def render_export_secondary_group(group: ExportManifestGroup) -> None:
    """Secondary exports below the primary board (compare matrix)."""
    available_actions = sorted(
        [action for action in group.actions if action.available],
        key=lambda action: (action.sort_order, action.action_id),
    )
    st.markdown(
        f'<div class="wb-export-secondary wb-export-group wb-export-group--secondary" '
        f'data-group-id="{html.escape(group.group_id)}">'
        f'<p class="wb-export-group-title">{html.escape(group.title)}</p>',
        unsafe_allow_html=True,
    )

    if not available_actions:
        if group.empty_message:
            st.markdown(
                f'<div class="wb-export-compare-empty wb-compare-empty">'
                f"{html.escape(group.empty_message)}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    column_target = 3 if len(available_actions) >= 3 else 2
    for row in export_action_rows_compact(available_actions, columns=column_target):
        columns = st.columns(len(row), gap="small")
        for column, action in zip(columns, row):
            with column:
                render_export_action_card(action)

    st.markdown("</div>", unsafe_allow_html=True)


def render_export_group_grid(group: ExportManifestGroup) -> None:
    """Legacy group renderer — kept for tests and secondary compare layouts."""
    if group.group_id == PRIMARY_BOARD_GROUP_ID:
        render_export_board(group.actions)
        return
    render_export_secondary_group(group)
