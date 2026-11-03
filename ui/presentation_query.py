from __future__ import annotations

from typing import Literal, Mapping

PresentationDirective = Literal["on", "off", "none"]

_PRESENTATION_QUERY_KEYS = ("present", "presentation", "demo")
_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})


def _normalize_query_value(raw: object) -> str:
    if raw is None:
        return ""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    return str(raw).strip().lower()


def read_presentation_query_directive(
    query: Mapping[str, object],
) -> PresentationDirective:
    """Parse presentation query params into a single directive."""
    saw_on = False
    for key in _PRESENTATION_QUERY_KEYS:
        if key not in query:
            continue
        value = _normalize_query_value(query.get(key))
        if value in _FALSY:
            return "off"
        if value in _TRUTHY:
            saw_on = True
    if saw_on:
        return "on"
    return "none"


def resolve_presentation_mode(
    *,
    directive: PresentationDirective,
    user_set: bool,
    session_value: bool,
) -> bool:
    """Resolve presentation flag from URL directive and session preferences."""
    if directive == "on":
        return True
    if directive == "off":
        return False
    if user_set:
        return session_value
    return False
