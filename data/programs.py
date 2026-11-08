from __future__ import annotations

from typing import Dict, Final, List

from domain.models import WashProgram

PROGRAM_CODE_ALIASES: Final[Dict[str, str]] = {
    "body_only": "exterior_only",
}

WASH_PROGRAMS: List[WashProgram] = [
    WashProgram(
        code="exterior_only",
        name="Техническая",
        price_rub=250,
        duration_min=4.0,
        water_factor=0.7,
        elec_factor=0.7,
        chem_factor=0.6,
        share_default=0.10,
    ),
    WashProgram(
        code="EXPRESS",
        name="Экспресс",
        price_rub=350,
        duration_min=3.0,
        water_factor=0.6,
        elec_factor=0.6,
        chem_factor=0.5,
        share_default=0.35,
    ),
    WashProgram(
        code="STANDARD",
        name="Стандарт",
        price_rub=550,
        duration_min=5.0,
        water_factor=1.0,
        elec_factor=1.0,
        chem_factor=1.0,
        share_default=0.30,
    ),
    WashProgram(
        code="PREMIUM",
        name="Премиум",
        price_rub=1000,
        duration_min=8.0,
        water_factor=1.4,
        elec_factor=1.3,
        chem_factor=1.8,
        share_default=0.15,
    ),
    WashProgram(
        code="vip",
        name="VIP",
        price_rub=1500,
        duration_min=10.0,
        water_factor=1.3,
        elec_factor=1.3,
        chem_factor=1.5,
        share_default=0.10,
    ),
]

PROGRAMS_DEFAULT = WASH_PROGRAMS

_PROGRAM_ORDER = {program.code: index for index, program in enumerate(WASH_PROGRAMS)}


def resolve_program_code(code: str) -> str:
    return PROGRAM_CODE_ALIASES.get(code, code)


def sort_programs(programs: List[WashProgram]) -> List[WashProgram]:
    return sorted(programs, key=lambda program: _PROGRAM_ORDER.get(program.code, 999))


def merge_loaded_programs(loaded: List[WashProgram]) -> List[WashProgram]:
    """Fill missing catalog programs with 0% share for backward-compatible scenarios."""
    by_code = {program.code: program for program in loaded}
    merged: List[WashProgram] = []
    for template in WASH_PROGRAMS:
        if template.code in by_code:
            merged.append(by_code[template.code])
            continue
        merged.append(
            WashProgram(
                code=template.code,
                name=template.name,
                price_rub=template.price_rub,
                duration_min=template.duration_min,
                water_factor=template.water_factor,
                elec_factor=template.elec_factor,
                chem_factor=template.chem_factor,
                share_default=0.0,
            )
        )
    return merged
