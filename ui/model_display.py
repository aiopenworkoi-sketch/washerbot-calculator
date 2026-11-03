from __future__ import annotations

from data.catalogs import WASHER_CATALOG
from data.washer_access import effective_power_kw, get_washer_model


def format_effective_power_kw(model_code: str, *, extra_dryers_enabled: bool) -> str:
    model = get_washer_model(model_code, WASHER_CATALOG)
    power = effective_power_kw(model, extra_dryers_enabled=extra_dryers_enabled)
    if extra_dryers_enabled:
        return f"{power:.0f} кВт (с доп. сушками)"
    return f"{power:.0f} кВт"


def format_model_config_power_line(model_code: str, *, extra_dryers_enabled: bool) -> str:
    model = get_washer_model(model_code, WASHER_CATALOG)
    power = effective_power_kw(model, extra_dryers_enabled=extra_dryers_enabled)
    if extra_dryers_enabled:
        return f"Установленная мощность: {power:.0f} кВт (база {model.power_kw:.0f} + доп. сушки)"
    return f"Установленная мощность: {power:.0f} кВт"
