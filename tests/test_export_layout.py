from __future__ import annotations

from ui.export_layout import export_action_rows, export_action_rows_board, export_action_rows_compact
from ui.export_manifest import ExportActionSpec


def _action(action_id: str, *, layout_hint: str = "half") -> ExportActionSpec:
    return ExportActionSpec(
        action_id=action_id,
        label=action_id,
        description="",
        filename=f"{action_id}.bin",
        mime="application/octet-stream",
        content=b"1",
        widget_key=f"dl_{action_id}",
        layout_hint=layout_hint,
    )


def test_export_action_rows_pairs_half_width_actions() -> None:
    rows = export_action_rows((_action("a"), _action("b"), _action("c")))
    assert rows == ((_action("a"), _action("b")), (_action("c"),))


def test_export_action_rows_splits_full_width_rows() -> None:
    rows = export_action_rows(
        (
            _action("html"),
            _action("pdf"),
            _action("pack", layout_hint="full"),
            _action("csv", layout_hint="full"),
        )
    )
    assert rows == (
        (_action("html"), _action("pdf")),
        (_action("pack", layout_hint="full"),),
        (_action("csv", layout_hint="full"),),
    )


def test_export_action_rows_flushes_pending_half_before_full() -> None:
    rows = export_action_rows((_action("html"), _action("pack", layout_hint="full")))
    assert rows == ((_action("html"),), (_action("pack", layout_hint="full"),))


def test_compare_export_rows_are_two_plus_one() -> None:
    rows = export_action_rows(
        (
            _action("pro_compare_html"),
            _action("pro_compare_pdf"),
            _action("pro_compare_csv"),
        )
    )
    assert len(rows) == 2
    assert len(rows[0]) == 2
    assert len(rows[1]) == 1
    assert rows[1][0].action_id == "pro_compare_csv"


def test_export_action_rows_board_is_two_by_two() -> None:
    actions = tuple(_action(f"a{i}") for i in range(4))
    rows = export_action_rows_board(actions)
    assert rows == ((actions[0], actions[1]), (actions[2], actions[3]))


def test_export_action_rows_compact_groups_three() -> None:
    rows = export_action_rows_compact(
        (_action("a"), _action("b"), _action("c"), _action("d")),
        columns=3,
    )
    assert rows == ((_action("a"), _action("b"), _action("c")), (_action("d"),))


def test_export_action_rows_compact_respects_full_width() -> None:
    rows = export_action_rows_compact(
        (_action("a"), _action("pack", layout_hint="full"), _action("b")),
        columns=3,
    )
    assert rows == ((_action("a"),), (_action("pack", layout_hint="full"),), (_action("b"),))
