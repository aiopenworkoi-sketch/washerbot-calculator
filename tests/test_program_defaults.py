from __future__ import annotations

import pytest

from data.programs import PROGRAMS_DEFAULT, resolve_program_code, sort_programs
from domain.models import WashProgram
from ui.scenario_io import _programs_from_payload


def test_program_defaults_prices_and_shares() -> None:
    by_code = {program.code: program for program in PROGRAMS_DEFAULT}
    assert by_code["exterior_only"].name == "Техническая"
    assert by_code["exterior_only"].price_rub == 100
    assert by_code["EXPRESS"].price_rub == 300
    assert by_code["STANDARD"].price_rub == 500
    assert by_code["PREMIUM"].price_rub == 900
    assert by_code["vip"].name == "VIP"
    assert by_code["vip"].price_rub == 1200
    total_share = sum(program.share_default for program in PROGRAMS_DEFAULT)
    assert total_share == pytest.approx(1.0)
    assert by_code["exterior_only"].share_default == pytest.approx(0.10)
    assert by_code["EXPRESS"].share_default == pytest.approx(0.35)
    assert by_code["STANDARD"].share_default == pytest.approx(0.30)
    assert by_code["PREMIUM"].share_default == pytest.approx(0.15)
    assert by_code["vip"].share_default == pytest.approx(0.10)


def test_program_catalog_order() -> None:
    names = [program.name for program in PROGRAMS_DEFAULT]
    assert names == ["Техническая", "Экспресс", "Стандарт", "Премиум", "VIP"]


def test_legacy_program_code_alias_loads() -> None:
    raw = [
        {"code": "body_only", "price_rub": 100, "share": 0.1},
        {"code": "EXPRESS", "price_rub": 300, "share": 0.35},
        {"code": "STANDARD", "price_rub": 500, "share": 0.30},
        {"code": "PREMIUM", "price_rub": 900, "share": 0.15},
        {"code": "vip", "price_rub": 1200, "share": 0.10},
    ]
    programs = _programs_from_payload(raw, mode="pro")
    assert programs[0].code == "exterior_only"
    assert programs[0].name == "Техническая"
    assert resolve_program_code("body_only") == "exterior_only"


def test_sort_programs_uses_catalog_order() -> None:
    shuffled = [
        WashProgram("vip", "VIP", 1200, 10, 1.3, 1.3, 1.5, 0.1),
        WashProgram("EXPRESS", "Экспресс", 300, 3, 0.6, 0.6, 0.5, 0.35),
    ]
    ordered = sort_programs(shuffled)
    assert [program.code for program in ordered] == ["EXPRESS", "vip"]
