from __future__ import annotations

import uuid
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, List, Tuple

import streamlit as st

from domain.params import ProParams
from domain.results import ProResult
MAX_COMPARE_VARIANTS = 3

SESSION_VARIANTS_KEY = "pro_compare_variants"
SESSION_BASELINE_KEY = "pro_compare_baseline_id"
SESSION_DRAFT_NAME_KEY = "pro_compare_draft_name"
SESSION_COMPARE_EXPORT_KEY = "pro_compare_export_state"
# Backward-compatible alias for legacy session keys/tests.
SESSION_SNAPSHOTS_KEY = SESSION_COMPARE_EXPORT_KEY


@dataclass(frozen=True)
class CompareExportState:
    snapshots: Tuple[Any, ...]
    baseline_id: str
    variant_ids: Tuple[str, ...]


@dataclass
class CompareVariantRecord:
    variant_id: str
    label: str
    params: ProParams


def _clear_compare_export_state() -> None:
    if SESSION_COMPARE_EXPORT_KEY in st.session_state:
        del st.session_state[SESSION_COMPARE_EXPORT_KEY]


def _write_compare_export_state(
    snapshots: Tuple[Any, ...],
    *,
    baseline_id: str,
    variant_ids: Tuple[str, ...],
) -> None:
    init_compare_state()
    st.session_state[SESSION_COMPARE_EXPORT_KEY] = {
        "variant_ids": variant_ids,
        "baseline_id": baseline_id,
        "snapshots": snapshots,
    }


def set_compare_snapshots_cache(
    snapshots: Tuple[Any, ...],
    *,
    baseline_id: str,
) -> None:
    init_compare_state()
    variant_ids = tuple(s.variant_id for s in snapshots)
    _write_compare_export_state(
        snapshots,
        baseline_id=baseline_id,
        variant_ids=variant_ids,
    )


def has_compare_variants_ready() -> bool:
    return len(get_compare_variants()) >= 2


def compare_export_state_from_snapshots(
    snapshots: Tuple[Any, ...],
    *,
    baseline_id: str,
) -> CompareExportState:
    variant_ids = tuple(snapshot.variant_id for snapshot in snapshots)
    return CompareExportState(
        snapshots=tuple(snapshots),
        baseline_id=baseline_id,
        variant_ids=variant_ids,
    )


def resolve_compare_export_state(
    *,
    compare_export_state: CompareExportState | None = None,
) -> CompareExportState | None:
    if compare_export_state is not None:
        return compare_export_state
    return get_compare_export_state()


def get_compare_export_state() -> CompareExportState | None:
    """
    Read compare export state from session store.

    Availability is driven by saved compare variants + synced export snapshots,
    not by whether the compare UI block was rendered in the current rerun.
    """
    init_compare_state()
    variants = get_compare_variants()
    if len(variants) < 2:
        return None

    variant_ids = tuple(v.variant_id for v in variants)
    baseline_id = get_compare_baseline_id() or variants[0].variant_id
    export = st.session_state.get(SESSION_COMPARE_EXPORT_KEY)
    if not export:
        return None
    if export.get("variant_ids") != variant_ids:
        return None

    snapshots = export.get("snapshots")
    if not snapshots:
        return None

    resolved_baseline = export.get("baseline_id") or baseline_id
    if resolved_baseline not in variant_ids:
        resolved_baseline = baseline_id

    return CompareExportState(
        snapshots=tuple(snapshots),
        baseline_id=resolved_baseline,
        variant_ids=variant_ids,
    )


def get_compare_snapshots_cache() -> Tuple[Tuple[Any, ...], str] | None:
    state = get_compare_export_state()
    if state is None:
        return None
    return state.snapshots, state.baseline_id


def sync_compare_snapshots_cache(
    calculate_pro_fn: Callable[[ProParams], ProResult],
) -> None:
    """
  Refresh compare snapshots from session variants.

  Called from app orchestration (render_pro_ui), not from export or compare render.
  """
    from ui.compare_specs import build_variant_snapshot

    init_compare_state()
    variants = get_compare_variants()
    if len(variants) < 2:
        _clear_compare_export_state()
        return

    baseline_id = get_compare_baseline_id() or variants[0].variant_id
    variant_ids = tuple(v.variant_id for v in variants)
    export = st.session_state.get(SESSION_COMPARE_EXPORT_KEY)
    if (
        export
        and export.get("variant_ids") == variant_ids
        and export.get("snapshots")
    ):
        if export.get("baseline_id") != baseline_id:
            _write_compare_export_state(
                tuple(export["snapshots"]),
                baseline_id=baseline_id,
                variant_ids=variant_ids,
            )
        return

    snapshots = tuple(
        build_variant_snapshot(
            variant.variant_id,
            variant.label,
            variant.params,
            calculate_pro_fn(variant.params),
        )
        for variant in variants
    )
    _write_compare_export_state(
        snapshots,
        baseline_id=baseline_id,
        variant_ids=variant_ids,
    )


def is_compare_export_available() -> bool:
    return get_compare_export_state() is not None

def init_compare_state() -> None:
    if SESSION_VARIANTS_KEY not in st.session_state:
        st.session_state[SESSION_VARIANTS_KEY] = []
    if SESSION_BASELINE_KEY not in st.session_state:
        st.session_state[SESSION_BASELINE_KEY] = None
    if SESSION_DRAFT_NAME_KEY not in st.session_state:
        st.session_state[SESSION_DRAFT_NAME_KEY] = ""


def get_compare_variants() -> List[CompareVariantRecord]:
    init_compare_state()
    return list(st.session_state[SESSION_VARIANTS_KEY])


def get_compare_baseline_id() -> str | None:
    init_compare_state()
    return st.session_state[SESSION_BASELINE_KEY]


def set_compare_draft_name(name: str) -> None:
    init_compare_state()
    st.session_state[SESSION_DRAFT_NAME_KEY] = name


def get_compare_draft_name() -> str:
    init_compare_state()
    return st.session_state[SESSION_DRAFT_NAME_KEY]


def set_compare_baseline(variant_id: str) -> None:
    init_compare_state()
    ids = {v.variant_id for v in get_compare_variants()}
    if variant_id in ids:
        st.session_state[SESSION_BASELINE_KEY] = variant_id
        export = st.session_state.get(SESSION_COMPARE_EXPORT_KEY)
        if export and variant_id in tuple(export.get("variant_ids", ())):
            _write_compare_export_state(
                tuple(export["snapshots"]),
                baseline_id=variant_id,
                variant_ids=tuple(export["variant_ids"]),
            )

def add_compare_variant(params: ProParams, label: str) -> bool:
    init_compare_state()
    variants: list = st.session_state[SESSION_VARIANTS_KEY]
    if len(variants) >= MAX_COMPARE_VARIANTS:
        return False
    clean_label = label.strip() or f"Вариант {len(variants) + 1}"
    variant_id = uuid.uuid4().hex[:8]
    variants.append(
        CompareVariantRecord(
            variant_id=variant_id,
            label=clean_label,
            params=deepcopy(params),
        )
    )
    if st.session_state[SESSION_BASELINE_KEY] is None:
        st.session_state[SESSION_BASELINE_KEY] = variant_id
    _clear_compare_export_state()
    return True


def remove_compare_variant(variant_id: str) -> None:
    init_compare_state()
    variants: list = st.session_state[SESSION_VARIANTS_KEY]
    st.session_state[SESSION_VARIANTS_KEY] = [
        v for v in variants if v.variant_id != variant_id
    ]
    if st.session_state[SESSION_BASELINE_KEY] == variant_id:
        remaining = st.session_state[SESSION_VARIANTS_KEY]
        st.session_state[SESSION_BASELINE_KEY] = (
            remaining[0].variant_id if remaining else None
        )
    _clear_compare_export_state()
