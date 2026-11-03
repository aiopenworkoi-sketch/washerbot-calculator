from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import asdict, fields
from datetime import datetime, timezone
from typing import Any, Literal, Mapping, TypeVar

from data.catalogs import PROGRAMS_DEFAULT, REGIONS, WASHER_CATALOG
from data.programs import merge_loaded_programs, resolve_program_code, sort_programs
from data.washer_access import normalize_extra_dryers_enabled, resolve_model_code
from finance.water_discharge import (
    normalize_water_discharge_profile,
)
from domain.models import WashProgram
from domain.params import ProParams, SimpleParams
from finance.taxes import TAX_REGIMES_LABELS

SCENARIO_SCHEMA_VERSION = 1
ScenarioMode = Literal["simple", "pro"]

_SIMPLE_PROGRAM_CODES = tuple(p.code for p in PROGRAMS_DEFAULT)
_PRO_PROGRAM_CODES = _SIMPLE_PROGRAM_CODES

_PROGRAM_BY_CODE: dict[str, WashProgram] = {p.code: p for p in PROGRAMS_DEFAULT}

_T = TypeVar("_T")


class ScenarioValidationError(ValueError):
    """Raised when scenario payload cannot be applied safely."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify_filename_part(value: str, *, max_len: int = 40) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", value.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return "scenario"
    return cleaned[:max_len]


def _program_to_dict(program: WashProgram) -> dict[str, Any]:
    return {
        "code": program.code,
        "price_rub": float(program.price_rub),
        "share": float(program.share_default),
    }


def _programs_from_payload(
    raw_programs: Any,
    *,
    mode: ScenarioMode,
) -> list[WashProgram]:
    if not isinstance(raw_programs, list) or not raw_programs:
        raise ScenarioValidationError("Поле params.programs обязательно и должно быть списком.")

    allowed = set(_PRO_PROGRAM_CODES if mode == "pro" else _SIMPLE_PROGRAM_CODES)
    programs: list[WashProgram] = []
    for item in raw_programs:
        if not isinstance(item, dict):
            raise ScenarioValidationError("Каждая программа в params.programs должна быть объектом.")
        code = item.get("code")
        if not isinstance(code, str):
            raise ScenarioValidationError(f"Неизвестный или неподдерживаемый код программы: {code!r}.")
        code = resolve_program_code(code)
        if code not in allowed:
            raise ScenarioValidationError(f"Неизвестный или неподдерживаемый код программы: {code!r}.")
        template = _PROGRAM_BY_CODE[code]
        price = item.get("price_rub", template.price_rub)
        share = item.get("share", item.get("share_default", template.share_default))
        try:
            price_f = float(price)
            share_f = float(share)
        except (TypeError, ValueError) as exc:
            raise ScenarioValidationError(f"Некорректные price/share для программы {code}.") from exc
        programs.append(
            WashProgram(
                code=template.code,
                name=template.name,
                price_rub=price_f,
                duration_min=float(item.get("duration_min", template.duration_min)),
                water_factor=float(item.get("water_factor", template.water_factor)),
                elec_factor=float(item.get("elec_factor", template.elec_factor)),
                chem_factor=float(item.get("chem_factor", template.chem_factor)),
                share_default=share_f,
            )
        )
    return sort_programs(merge_loaded_programs(programs))


def _require_key(data: Mapping[str, Any], key: str) -> Any:
    if key not in data:
        raise ScenarioValidationError(f"Отсутствует обязательное поле params.{key}.")
    return data[key]


def _coerce_int(value: Any, *, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ScenarioValidationError(f"Поле params.{field_name} должно быть целым числом.") from exc


def _coerce_float(value: Any, *, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ScenarioValidationError(f"Поле params.{field_name} должно быть числом.") from exc


def _coerce_bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ScenarioValidationError(f"Поле params.{field_name} должно быть true/false.")


def _coerce_bool_optional(value: Any, *, field_name: str, default: bool) -> bool:
    if value is None:
        return default
    return _coerce_bool(value, field_name=field_name)


def _require_range(value: float, *, lo: float, hi: float, field_name: str) -> float:
    if not (lo <= value <= hi):
        raise ScenarioValidationError(
            f"Поле params.{field_name} должно быть в диапазоне {lo:g}…{hi:g} (получено {value:g})."
        )
    return value


def _validate_simple_ranges(params: SimpleParams) -> None:
    _require_range(params.cars_per_day_avg, lo=0.0, hi=1000.0, field_name="cars_per_day_avg")
    _require_range(params.n_robots, lo=1.0, hi=10.0, field_name="n_robots")
    _require_range(params.work_days_month, lo=1.0, hi=31.0, field_name="work_days_month")
    _require_range(params.horizon_months, lo=1.0, hi=600.0, field_name="horizon_months")
    _require_range(params.total_investment, lo=0.0, hi=1e10, field_name="total_investment")
    _require_range(params.admin_salary_gross, lo=0.0, hi=1e8, field_name="admin_salary_gross")
    _require_range(params.rent_month, lo=0.0, hi=1e8, field_name="rent_month")
    _require_range(params.other_fixed, lo=0.0, hi=1e8, field_name="other_fixed")


def _validate_pro_ranges(params: ProParams) -> None:
    _require_range(params.cars_per_day_avg, lo=0.0, hi=1000.0, field_name="cars_per_day_avg")
    _require_range(params.n_robots, lo=1.0, hi=10.0, field_name="n_robots")
    _require_range(params.work_days_month, lo=1.0, hi=31.0, field_name="work_days_month")
    _require_range(params.horizon_months, lo=1.0, hi=600.0, field_name="horizon_months")
    _require_range(params.seasonality_strength, lo=0.0, hi=1.0, field_name="seasonality_strength")
    _require_range(params.eco_water_recycle_pct, lo=0.0, hi=0.95, field_name="eco_water_recycle_pct")
    _require_range(params.scenario_pessim_factor, lo=0.1, hi=3.0, field_name="scenario_pessim_factor")
    _require_range(params.scenario_optim_factor, lo=0.1, hi=3.0, field_name="scenario_optim_factor")
    _require_range(params.amort_years_equipment, lo=0.0, hi=50.0, field_name="amort_years_equipment")
    _require_range(params.n_admins, lo=0.0, hi=20.0, field_name="n_admins")
    _require_range(params.n_managers, lo=0.0, hi=20.0, field_name="n_managers")

    capex_fields = (
        "capex_equipment", "capex_construction", "capex_engineering",
        "capex_premises", "capex_launch", "capex_other",
    )
    for field in capex_fields:
        _require_range(getattr(params, field), lo=0.0, hi=1e10, field_name=field)

    for field in (
        "admin_salary_gross", "manager_salary_gross", "rent_month", "utilities_extra",
        "security_month", "marketing_month", "maintenance_month", "insurance_month",
        "other_opex",
    ):
        _require_range(getattr(params, field), lo=0.0, hi=1e8, field_name=field)

    _require_range(params.credit_amount, lo=0.0, hi=1e10, field_name="credit_amount")
    _require_range(params.credit_rate_annual, lo=0.0, hi=1.0, field_name="credit_rate_annual")
    _require_range(params.credit_term_months, lo=0.0, hi=600.0, field_name="credit_term_months")
    _require_range(params.credit_grace_months, lo=0.0, hi=600.0, field_name="credit_grace_months")

    if params.use_credit and params.credit_amount > 0 and params.credit_term_months <= 0:
        raise ScenarioValidationError(
            "Для кредита укажите срок в месяцах (credit_term_months > 0)."
        )
    if params.credit_grace_months > params.credit_term_months:
        raise ScenarioValidationError(
            "Отсрочка по телу кредита не может превышать срок кредита."
        )
    capex_total = sum(getattr(params, field) for field in capex_fields)
    if params.use_credit and params.credit_amount > capex_total + 1e-6:
        raise ScenarioValidationError(
            "Сумма кредита не может превышать CAPEX проекта "
            f"({params.credit_amount:,.0f} ₽ > {capex_total:,.0f} ₽)."
        )


def _resolve_water_discharge_profile(raw: Mapping[str, Any]) -> str:
    if "water_discharge_profile" in raw:
        try:
            return normalize_water_discharge_profile(
                str(raw["water_discharge_profile"]),
                from_scenario=False,
            )
        except ValueError as exc:
            raise ScenarioValidationError(str(exc)) from exc
    return normalize_water_discharge_profile(None, from_scenario=True)


def serialize_simple_params(params: SimpleParams) -> dict[str, Any]:
    return {
        "model_code": params.model_code,
        "extra_dryers_enabled": params.extra_dryers_enabled,
        "water_discharge_profile": params.water_discharge_profile,
        "n_robots": params.n_robots,
        "region_key": params.region_key,
        "total_investment": params.total_investment,
        "cars_per_day_avg": params.cars_per_day_avg,
        "work_days_month": params.work_days_month,
        "programs": [_program_to_dict(p) for p in params.programs],
        "admin_salary_gross": params.admin_salary_gross,
        "rent_month": params.rent_month,
        "other_fixed": params.other_fixed,
        "tax_regime": params.tax_regime,
        "horizon_months": params.horizon_months,
    }


def serialize_pro_params(params: ProParams) -> dict[str, Any]:
    return {
        "model_code": params.model_code,
        "extra_dryers_enabled": params.extra_dryers_enabled,
        "water_discharge_profile": params.water_discharge_profile,
        "n_robots": params.n_robots,
        "region_key": params.region_key,
        "capex_equipment": params.capex_equipment,
        "capex_construction": params.capex_construction,
        "capex_engineering": params.capex_engineering,
        "capex_premises": params.capex_premises,
        "capex_launch": params.capex_launch,
        "capex_other": params.capex_other,
        "use_credit": params.use_credit,
        "credit_amount": params.credit_amount,
        "credit_rate_annual": params.credit_rate_annual,
        "credit_term_months": params.credit_term_months,
        "credit_grace_months": params.credit_grace_months,
        "cars_per_day_avg": params.cars_per_day_avg,
        "work_days_month": params.work_days_month,
        "seasonality_strength": params.seasonality_strength,
        "programs": [_program_to_dict(p) for p in params.programs],
        "n_admins": params.n_admins,
        "admin_salary_gross": params.admin_salary_gross,
        "n_managers": params.n_managers,
        "manager_salary_gross": params.manager_salary_gross,
        "rent_month": params.rent_month,
        "utilities_extra": params.utilities_extra,
        "security_month": params.security_month,
        "marketing_month": params.marketing_month,
        "maintenance_month": params.maintenance_month,
        "insurance_month": params.insurance_month,
        "other_opex": params.other_opex,
        "tax_regime": params.tax_regime,
        "amort_years_equipment": params.amort_years_equipment,
        "horizon_months": params.horizon_months,
        "scenario_pessim_factor": params.scenario_pessim_factor,
        "scenario_optim_factor": params.scenario_optim_factor,
        "eco_water_recycle_pct": params.eco_water_recycle_pct,
        "eco_chem_premium": params.eco_chem_premium,
    }


def build_scenario_payload(
    mode: ScenarioMode,
    params: SimpleParams | ProParams,
    *,
    title: str = "",
    note: str = "",
    created_at: str | None = None,
) -> dict[str, Any]:
    if mode == "simple":
        if not isinstance(params, SimpleParams):
            raise TypeError("simple mode requires SimpleParams")
        params_dict = serialize_simple_params(params)
    else:
        if not isinstance(params, ProParams):
            raise TypeError("pro mode requires ProParams")
        params_dict = serialize_pro_params(params)

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "mode": mode,
        "title": title.strip(),
        "note": note.strip(),
        "created_at": created_at or utc_now_iso(),
        "params": params_dict,
    }


def parse_scenario_json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ScenarioValidationError("Файл не является корректным JSON.") from exc
    if not isinstance(data, dict):
        raise ScenarioValidationError("Корневой элемент сценария должен быть JSON-объектом.")
    return data


def validate_scenario_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    version = payload.get("schema_version")
    if version != SCENARIO_SCHEMA_VERSION:
        raise ScenarioValidationError(
            f"Неподдерживаемая версия схемы: {version!r}. Ожидается {SCENARIO_SCHEMA_VERSION}."
        )

    mode = payload.get("mode")
    if mode not in ("simple", "pro"):
        raise ScenarioValidationError("Поле mode должно быть 'simple' или 'pro'.")

    raw_params = payload.get("params")
    if not isinstance(raw_params, dict):
        raise ScenarioValidationError("Поле params обязательно и должно быть объектом.")

    title = payload.get("title", "")
    note = payload.get("note", "")
    if title is not None and not isinstance(title, str):
        raise ScenarioValidationError("Поле title должно быть строкой.")
    if note is not None and not isinstance(note, str):
        raise ScenarioValidationError("Поле note должно быть строкой.")

    created_at = payload.get("created_at")
    if created_at is not None and not isinstance(created_at, str):
        raise ScenarioValidationError("Поле created_at должно быть строкой ISO.")

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "mode": mode,
        "title": (title or "").strip(),
        "note": (note or "").strip(),
        "created_at": created_at or utc_now_iso(),
        "params": raw_params,
    }


def deserialize_simple_params(raw: Mapping[str, Any]) -> SimpleParams:
    model_code = resolve_model_code(str(_require_key(raw, "model_code")))
    region_key = _require_key(raw, "region_key")
    tax_regime = _require_key(raw, "tax_regime")
    if model_code not in WASHER_CATALOG:
        raise ScenarioValidationError(f"Неизвестная модель: {model_code!r}.")
    if region_key not in REGIONS:
        raise ScenarioValidationError(f"Неизвестный регион: {region_key!r}.")
    if tax_regime not in TAX_REGIMES_LABELS:
        raise ScenarioValidationError(f"Неизвестный налоговый режим: {tax_regime!r}.")
    extra_dryers_enabled = normalize_extra_dryers_enabled(
        model_code,
        _coerce_bool_optional(
            raw.get("extra_dryers_enabled"),
            field_name="extra_dryers_enabled",
            default=False,
        ),
    )
    water_discharge_profile = _resolve_water_discharge_profile(raw)

    params = SimpleParams(
        model_code=str(model_code),
        extra_dryers_enabled=extra_dryers_enabled,
        n_robots=_coerce_int(_require_key(raw, "n_robots"), field_name="n_robots"),
        region_key=str(region_key),
        total_investment=_coerce_float(_require_key(raw, "total_investment"), field_name="total_investment"),
        cars_per_day_avg=_coerce_float(_require_key(raw, "cars_per_day_avg"), field_name="cars_per_day_avg"),
        work_days_month=_coerce_int(_require_key(raw, "work_days_month"), field_name="work_days_month"),
        programs=_programs_from_payload(_require_key(raw, "programs"), mode="simple"),
        admin_salary_gross=_coerce_float(_require_key(raw, "admin_salary_gross"), field_name="admin_salary_gross"),
        rent_month=_coerce_float(_require_key(raw, "rent_month"), field_name="rent_month"),
        other_fixed=_coerce_float(_require_key(raw, "other_fixed"), field_name="other_fixed"),
        tax_regime=str(tax_regime),
        horizon_months=_coerce_int(_require_key(raw, "horizon_months"), field_name="horizon_months"),
        water_discharge_profile=water_discharge_profile,
    )
    _validate_simple_ranges(params)
    return params


def deserialize_pro_params(raw: Mapping[str, Any]) -> ProParams:
    model_code = resolve_model_code(str(_require_key(raw, "model_code")))
    region_key = _require_key(raw, "region_key")
    tax_regime = _require_key(raw, "tax_regime")
    if model_code not in WASHER_CATALOG:
        raise ScenarioValidationError(f"Неизвестная модель: {model_code!r}.")
    if region_key not in REGIONS:
        raise ScenarioValidationError(f"Неизвестный регион: {region_key!r}.")
    if tax_regime not in TAX_REGIMES_LABELS:
        raise ScenarioValidationError(f"Неизвестный налоговый режим: {tax_regime!r}.")
    extra_dryers_enabled = normalize_extra_dryers_enabled(
        model_code,
        _coerce_bool_optional(
            raw.get("extra_dryers_enabled"),
            field_name="extra_dryers_enabled",
            default=False,
        ),
    )
    water_discharge_profile = _resolve_water_discharge_profile(raw)

    params = ProParams(
        model_code=str(model_code),
        extra_dryers_enabled=extra_dryers_enabled,
        n_robots=_coerce_int(_require_key(raw, "n_robots"), field_name="n_robots"),
        region_key=str(region_key),
        capex_equipment=_coerce_float(_require_key(raw, "capex_equipment"), field_name="capex_equipment"),
        capex_construction=_coerce_float(_require_key(raw, "capex_construction"), field_name="capex_construction"),
        capex_engineering=_coerce_float(_require_key(raw, "capex_engineering"), field_name="capex_engineering"),
        capex_premises=_coerce_float(_require_key(raw, "capex_premises"), field_name="capex_premises"),
        capex_launch=_coerce_float(_require_key(raw, "capex_launch"), field_name="capex_launch"),
        capex_other=_coerce_float(_require_key(raw, "capex_other"), field_name="capex_other"),
        use_credit=_coerce_bool(_require_key(raw, "use_credit"), field_name="use_credit"),
        credit_amount=_coerce_float(_require_key(raw, "credit_amount"), field_name="credit_amount"),
        credit_rate_annual=_coerce_float(_require_key(raw, "credit_rate_annual"), field_name="credit_rate_annual"),
        credit_term_months=_coerce_int(_require_key(raw, "credit_term_months"), field_name="credit_term_months"),
        credit_grace_months=_coerce_int(_require_key(raw, "credit_grace_months"), field_name="credit_grace_months"),
        cars_per_day_avg=_coerce_float(_require_key(raw, "cars_per_day_avg"), field_name="cars_per_day_avg"),
        work_days_month=_coerce_int(_require_key(raw, "work_days_month"), field_name="work_days_month"),
        seasonality_strength=_coerce_float(_require_key(raw, "seasonality_strength"), field_name="seasonality_strength"),
        programs=_programs_from_payload(_require_key(raw, "programs"), mode="pro"),
        n_admins=_coerce_int(_require_key(raw, "n_admins"), field_name="n_admins"),
        admin_salary_gross=_coerce_float(_require_key(raw, "admin_salary_gross"), field_name="admin_salary_gross"),
        n_managers=_coerce_int(_require_key(raw, "n_managers"), field_name="n_managers"),
        manager_salary_gross=_coerce_float(_require_key(raw, "manager_salary_gross"), field_name="manager_salary_gross"),
        rent_month=_coerce_float(_require_key(raw, "rent_month"), field_name="rent_month"),
        utilities_extra=_coerce_float(_require_key(raw, "utilities_extra"), field_name="utilities_extra"),
        security_month=_coerce_float(_require_key(raw, "security_month"), field_name="security_month"),
        marketing_month=_coerce_float(_require_key(raw, "marketing_month"), field_name="marketing_month"),
        maintenance_month=_coerce_float(_require_key(raw, "maintenance_month"), field_name="maintenance_month"),
        insurance_month=_coerce_float(_require_key(raw, "insurance_month"), field_name="insurance_month"),
        other_opex=_coerce_float(_require_key(raw, "other_opex"), field_name="other_opex"),
        tax_regime=str(tax_regime),
        amort_years_equipment=_coerce_int(_require_key(raw, "amort_years_equipment"), field_name="amort_years_equipment"),
        horizon_months=_coerce_int(_require_key(raw, "horizon_months"), field_name="horizon_months"),
        scenario_pessim_factor=_coerce_float(_require_key(raw, "scenario_pessim_factor"), field_name="scenario_pessim_factor"),
        scenario_optim_factor=_coerce_float(_require_key(raw, "scenario_optim_factor"), field_name="scenario_optim_factor"),
        eco_water_recycle_pct=_coerce_float(_require_key(raw, "eco_water_recycle_pct"), field_name="eco_water_recycle_pct"),
        eco_chem_premium=_coerce_bool(_require_key(raw, "eco_chem_premium"), field_name="eco_chem_premium"),
        water_discharge_profile=water_discharge_profile,
    )
    _validate_pro_ranges(params)
    return params


def params_from_scenario_payload(payload: Mapping[str, Any]) -> tuple[ScenarioMode, SimpleParams | ProParams]:
    validated = validate_scenario_payload(payload)
    mode: ScenarioMode = validated["mode"]  # type: ignore[assignment]
    raw_params = validated["params"]
    if mode == "simple":
        return mode, deserialize_simple_params(raw_params)
    return mode, deserialize_pro_params(raw_params)


def scenario_to_widget_state(mode: ScenarioMode, params: SimpleParams | ProParams) -> dict[str, Any]:
    """Map params dataclass to Streamlit widget session_state keys."""
    state: dict[str, Any] = {}
    if mode == "simple":
        if not isinstance(params, SimpleParams):
            raise TypeError("simple mode requires SimpleParams")
        state["s_model"] = WASHER_CATALOG[params.model_code].name
        state["s_extra_dryers"] = bool(params.extra_dryers_enabled)
        state["s_water_discharge_profile"] = params.water_discharge_profile
        state["s_n_robots"] = params.n_robots
        state["s_region"] = REGIONS[params.region_key].name
        state["s_invest"] = float(params.total_investment)
        state["s_cars"] = float(params.cars_per_day_avg)
        state["s_workdays"] = params.work_days_month
        for template in PROGRAMS_DEFAULT:
            program = next(
                (item for item in params.programs if item.code == template.code),
                None,
            )
            if program is not None:
                state[f"s_prog_price_{program.code}"] = int(program.price_rub)
                state[f"s_prog_share_{program.code}"] = int(round(program.share_default * 100))
            else:
                state[f"s_prog_price_{template.code}"] = int(template.price_rub)
                state[f"s_prog_share_{template.code}"] = 0
        state["s_admin_salary"] = float(params.admin_salary_gross)
        state["s_rent"] = float(params.rent_month)
        state["s_other_fixed"] = float(params.other_fixed)
        state["s_tax"] = TAX_REGIMES_LABELS[params.tax_regime]
        state["s_horizon"] = max(1, params.horizon_months // 12)
        return state

    if not isinstance(params, ProParams):
        raise TypeError("pro mode requires ProParams")
    state["p_model"] = WASHER_CATALOG[params.model_code].name
    state["p_extra_dryers"] = bool(params.extra_dryers_enabled)
    state["p_water_discharge_profile"] = params.water_discharge_profile
    state["p_n_robots"] = params.n_robots
    state["p_region"] = REGIONS[params.region_key].name
    state["p_capex_equip"] = float(params.capex_equipment)
    state["p_capex_smr"] = float(params.capex_construction)
    state["p_capex_eng"] = float(params.capex_engineering)
    state["p_capex_prem"] = float(params.capex_premises)
    state["p_capex_launch"] = float(params.capex_launch)
    state["p_capex_other"] = float(params.capex_other)
    state["p_use_credit"] = bool(params.use_credit)
    state["p_credit_amount"] = float(params.credit_amount)
    state["p_credit_rate"] = float(params.credit_rate_annual * 100.0)
    state["p_credit_term"] = params.credit_term_months
    state["p_credit_grace"] = params.credit_grace_months
    state["p_cars"] = float(params.cars_per_day_avg)
    state["p_workdays"] = params.work_days_month
    state["p_seas_strength"] = float(params.seasonality_strength)
    for template in PROGRAMS_DEFAULT:
        program = next(
            (item for item in params.programs if item.code == template.code),
            None,
        )
        if program is not None:
            state[f"p_prog_price_{program.code}"] = int(program.price_rub)
            state[f"p_prog_share_{program.code}"] = int(round(program.share_default * 100))
        else:
            state[f"p_prog_price_{template.code}"] = int(template.price_rub)
            state[f"p_prog_share_{template.code}"] = 0
    state["p_n_admins"] = params.n_admins
    state["p_admin_salary"] = float(params.admin_salary_gross)
    state["p_n_managers"] = params.n_managers
    state["p_manager_salary"] = float(params.manager_salary_gross)
    state["p_rent"] = float(params.rent_month)
    state["p_util"] = float(params.utilities_extra)
    state["p_security"] = float(params.security_month)
    state["p_marketing"] = float(params.marketing_month)
    state["p_maint"] = float(params.maintenance_month)
    state["p_insurance"] = float(params.insurance_month)
    state["p_other_opex"] = float(params.other_opex)
    state["p_tax"] = TAX_REGIMES_LABELS[params.tax_regime]
    state["p_amort"] = params.amort_years_equipment
    state["p_pessim"] = float(params.scenario_pessim_factor)
    state["p_optim"] = float(params.scenario_optim_factor)
    state["p_eco_recycle"] = int(round(params.eco_water_recycle_pct * 100))
    state["p_eco_chem"] = bool(params.eco_chem_premium)
    state["p_horizon"] = max(1, params.horizon_months // 12)
    return state


def scenario_payload_to_json(payload: Mapping[str, Any], *, compact: bool = False) -> str:
    if compact:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def scenario_download_filename(payload: Mapping[str, Any]) -> str:
    mode = str(payload.get("mode", "scenario"))
    title = str(payload.get("title") or "untitled")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"washerbot_{mode}_{_slugify_filename_part(title)}_{stamp}.json"


def params_dataclass_snapshot(params: SimpleParams | ProParams) -> dict[str, Any]:
    """Deep-ish snapshot for tests/debug without computed results."""
    return deepcopy(asdict(params))


def assert_params_roundtrip_equal(original: _T, restored: _T) -> None:
    """Compare dataclass params field-by-field (programs order-sensitive)."""
    if type(original) is not type(restored):
        raise AssertionError(f"Type mismatch: {type(original)} vs {type(restored)}")
    for field in fields(original):
        left = getattr(original, field.name)
        right = getattr(restored, field.name)
        if field.name == "programs":
            assert len(left) == len(right)
            for lp, rp in zip(left, right):
                assert lp.code == rp.code
                assert abs(lp.price_rub - rp.price_rub) < 1e-6
                assert abs(lp.share_default - rp.share_default) < 1e-6
            continue
        if isinstance(left, float):
            assert abs(left - right) < 1e-6, field.name
        else:
            assert left == right, field.name
