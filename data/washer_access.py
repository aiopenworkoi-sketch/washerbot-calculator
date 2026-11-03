from __future__ import annotations

from typing import Dict, FrozenSet

from domain.models import WasherModel

EXTRA_DRYERS_POWER_DELTA_KW: float = 11.0

EXTRA_DRYERS_SUPPORTED_CODES: FrozenSet[str] = frozenset(
    {"L360", "L360_MINI", "L370_PLUS", "L380_PLUS"}
)

WASHER_MODEL_LEGACY_ALIASES: Dict[str, str] = {
    "L_S90": "L_SG",
}


def resolve_model_code(model_code: str) -> str:
    """Map legacy catalog keys to active runtime keys."""
    return WASHER_MODEL_LEGACY_ALIASES.get(model_code, model_code)


def get_washer_model(model_code: str, catalog: Dict[str, WasherModel]) -> WasherModel:
    resolved = resolve_model_code(model_code)
    try:
        return catalog[resolved]
    except KeyError as exc:
        raise KeyError(f"Unknown washer model code: {model_code!r}") from exc


def supports_extra_dryers(model_code: str) -> bool:
    return resolve_model_code(model_code) in EXTRA_DRYERS_SUPPORTED_CODES


def effective_power_kw(
    model: WasherModel,
    *,
    extra_dryers_enabled: bool,
) -> float:
    base = float(model.power_kw)
    if extra_dryers_enabled and supports_extra_dryers(model.code):
        return base + EXTRA_DRYERS_POWER_DELTA_KW
    return base


def normalize_extra_dryers_enabled(model_code: str, extra_dryers_enabled: bool) -> bool:
    if not extra_dryers_enabled:
        return False
    return supports_extra_dryers(model_code)
