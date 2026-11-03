from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from domain.models import WashProgram
from finance.capacity import weighted_program_duration_minutes


@dataclass(frozen=True)
class ProgramMixMetrics:
    program_count: int
    total_share: float
    avg_check: float
    avg_water_factor: float
    avg_elec_factor: float
    avg_chem_factor: float
    weighted_duration_min: float


def compute_program_mix(programs: Sequence[WashProgram]) -> ProgramMixMetrics:
    if not programs:
        raise ValueError("programs must not be empty")

    total_share = sum(p.share_default for p in programs) or 1.0
    avg_check = sum(p.price_rub * p.share_default for p in programs) / total_share
    avg_water_factor = sum(p.water_factor * p.share_default for p in programs) / total_share
    avg_elec_factor = sum(p.elec_factor * p.share_default for p in programs) / total_share
    avg_chem_factor = sum(p.chem_factor * p.share_default for p in programs) / total_share
    weighted_duration_min = weighted_program_duration_minutes(
        [p.duration_min for p in programs],
        [p.share_default for p in programs],
    )
    return ProgramMixMetrics(
        program_count=len(programs),
        total_share=float(total_share),
        avg_check=float(avg_check),
        avg_water_factor=float(avg_water_factor),
        avg_elec_factor=float(avg_elec_factor),
        avg_chem_factor=float(avg_chem_factor),
        weighted_duration_min=float(weighted_duration_min),
    )
