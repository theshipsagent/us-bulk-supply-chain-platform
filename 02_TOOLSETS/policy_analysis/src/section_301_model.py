"""Section 301 shipping fee impact calculator.

Models the fees imposed under Section 301 of the Trade Act (as applied to
Chinese-built/operated/owned vessels calling US ports). These fees target
vessels with Chinese maritime nexus and impose per-voyage or per-net-ton
charges that significantly increase port call costs.

The fee structure was announced by USTR in 2025 and phases in over 3 years.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Fee schedule (aligned with USTR Final Rule, April 2025)
# ---------------------------------------------------------------------------

@dataclass
class FeeScheduleEntry:
    """A single fee schedule entry for a vessel category."""
    category: str               # "chinese_built", "chinese_operated", "chinese_owned"
    vessel_type: str            # "container", "bulk", "tanker", "roro", "car_carrier"
    phase: int                  # 1, 2, 3
    effective_year: int
    fee_type: str               # "per_voyage" or "per_net_ton"
    fee_amount: float
    max_fee: float = 0.0        # cap per vessel per voyage
    exemptions: list[str] = field(default_factory=list)
    notes: str = ""


# Approximate fee schedule based on published USTR framework
_FEE_SCHEDULE: list[FeeScheduleEntry] = [
    # Phase 1 — Chinese-built vessels (2025)
    FeeScheduleEntry("chinese_built", "container", 1, 2025, "per_net_ton", 50.0, 1_500_000),
    FeeScheduleEntry("chinese_built", "bulk", 1, 2025, "per_voyage", 500_000.0),
    FeeScheduleEntry("chinese_built", "tanker", 1, 2025, "per_voyage", 500_000.0),
    FeeScheduleEntry("chinese_built", "roro", 1, 2025, "per_voyage", 350_000.0),
    FeeScheduleEntry("chinese_built", "car_carrier", 1, 2025, "per_net_ton", 45.0, 1_000_000),

    # Phase 2 — Escalation (2026)
    FeeScheduleEntry("chinese_built", "container", 2, 2026, "per_net_ton", 75.0, 2_000_000),
    FeeScheduleEntry("chinese_built", "bulk", 2, 2026, "per_voyage", 750_000.0),
    FeeScheduleEntry("chinese_built", "tanker", 2, 2026, "per_voyage", 750_000.0),
    FeeScheduleEntry("chinese_built", "roro", 2, 2026, "per_voyage", 500_000.0),
    FeeScheduleEntry("chinese_built", "car_carrier", 2, 2026, "per_net_ton", 60.0, 1_500_000),

    # Phase 3 — Full implementation (2027+)
    FeeScheduleEntry("chinese_built", "container", 3, 2027, "per_net_ton", 100.0, 3_000_000),
    FeeScheduleEntry("chinese_built", "bulk", 3, 2027, "per_voyage", 1_000_000.0),
    FeeScheduleEntry("chinese_built", "tanker", 3, 2027, "per_voyage", 1_000_000.0),
    FeeScheduleEntry("chinese_built", "roro", 3, 2027, "per_voyage", 750_000.0),
    FeeScheduleEntry("chinese_built", "car_carrier", 3, 2027, "per_net_ton", 80.0, 2_000_000),

    # Chinese-operated vessels — lower rates
    FeeScheduleEntry("chinese_operated", "container", 1, 2025, "per_net_ton", 35.0, 1_000_000),
    FeeScheduleEntry("chinese_operated", "bulk", 1, 2025, "per_voyage", 350_000.0),
    FeeScheduleEntry("chinese_operated", "tanker", 1, 2025, "per_voyage", 350_000.0),
    FeeScheduleEntry("chinese_operated", "container", 2, 2026, "per_net_ton", 50.0, 1_500_000),
    FeeScheduleEntry("chinese_operated", "bulk", 2, 2026, "per_voyage", 500_000.0),
    FeeScheduleEntry("chinese_operated", "container", 3, 2027, "per_net_ton", 70.0, 2_000_000),
    FeeScheduleEntry("chinese_operated", "bulk", 3, 2027, "per_voyage", 750_000.0),
]


@dataclass
class Section301Assessment:
    """Result of a Section 301 fee assessment for a vessel."""
    vessel_name: str
    vessel_nrt: int
    vessel_type: str
    category: str                   # chinese_built, chinese_operated, etc.
    phase: int
    fee_type: str
    calculated_fee: float
    fee_cap: float
    applied_fee: float              # min(calculated, cap)
    fee_per_ton_cargo: float = 0.0  # impact on per-ton landed cost
    cargo_tons: float = 0.0
    exemptions_applied: list[str] = field(default_factory=list)
    is_exempt: bool = False
    notes: str = ""


def assess_section_301(
    vessel_name: str,
    vessel_nrt: int,
    vessel_type: str,
    category: str,
    phase: int = 1,
    cargo_tons: float = 0.0,
) -> Section301Assessment:
    """Calculate the Section 301 fee for a vessel port call.

    Parameters
    ----------
    vessel_name : str
        Vessel name for reference.
    vessel_nrt : int
        Net registered tonnage.
    vessel_type : str
        One of: container, bulk, tanker, roro, car_carrier.
    category : str
        Chinese nexus category: chinese_built, chinese_operated, chinese_owned.
    phase : int
        Phase (1, 2, or 3).
    cargo_tons : float
        Cargo quantity for per-ton impact calculation.
    """
    # Find matching fee entry
    entry = _find_fee_entry(category, vessel_type, phase)

    if entry is None:
        return Section301Assessment(
            vessel_name=vessel_name,
            vessel_nrt=vessel_nrt,
            vessel_type=vessel_type,
            category=category,
            phase=phase,
            fee_type="none",
            calculated_fee=0.0,
            fee_cap=0.0,
            applied_fee=0.0,
            notes="No applicable fee schedule found for this vessel category/type/phase.",
        )

    if entry.fee_type == "per_net_ton":
        calculated = entry.fee_amount * vessel_nrt
    else:  # per_voyage
        calculated = entry.fee_amount

    applied = min(calculated, entry.max_fee) if entry.max_fee > 0 else calculated

    fee_per_ton = applied / cargo_tons if cargo_tons > 0 else 0.0

    return Section301Assessment(
        vessel_name=vessel_name,
        vessel_nrt=vessel_nrt,
        vessel_type=vessel_type,
        category=category,
        phase=phase,
        fee_type=entry.fee_type,
        calculated_fee=round(calculated, 2),
        fee_cap=entry.max_fee,
        applied_fee=round(applied, 2),
        fee_per_ton_cargo=round(fee_per_ton, 2),
        cargo_tons=cargo_tons,
    )


def compare_phases(
    vessel_nrt: int,
    vessel_type: str,
    category: str,
    cargo_tons: float = 30_000.0,
) -> list[Section301Assessment]:
    """Compare fee impact across all three phases."""
    return [
        assess_section_301(
            vessel_name="Comparison",
            vessel_nrt=vessel_nrt,
            vessel_type=vessel_type,
            category=category,
            phase=p,
            cargo_tons=cargo_tons,
        )
        for p in [1, 2, 3]
    ]


def estimate_annual_impact(
    vessel_nrt: int,
    vessel_type: str,
    category: str,
    calls_per_year: int = 12,
    cargo_per_call: float = 30_000.0,
    phase: int = 1,
) -> dict[str, Any]:
    """Estimate annual financial impact of Section 301 fees."""
    single = assess_section_301(
        vessel_name="Annual Impact",
        vessel_nrt=vessel_nrt,
        vessel_type=vessel_type,
        category=category,
        phase=phase,
        cargo_tons=cargo_per_call,
    )
    annual_fee = single.applied_fee * calls_per_year
    annual_cargo = cargo_per_call * calls_per_year

    return {
        "fee_per_call": single.applied_fee,
        "calls_per_year": calls_per_year,
        "annual_fee": round(annual_fee, 2),
        "annual_cargo_tons": annual_cargo,
        "impact_per_ton": round(annual_fee / annual_cargo, 2) if annual_cargo > 0 else 0,
        "phase": phase,
        "category": category,
        "vessel_type": vessel_type,
    }


def _find_fee_entry(
    category: str, vessel_type: str, phase: int
) -> FeeScheduleEntry | None:
    """Find matching fee schedule entry."""
    for entry in _FEE_SCHEDULE:
        if (
            entry.category == category
            and entry.vessel_type == vessel_type
            and entry.phase == phase
        ):
            return entry
    return None


def get_fee_schedule() -> list[dict[str, Any]]:
    """Return the complete fee schedule as a list of dicts."""
    return [
        {
            "category": e.category,
            "vessel_type": e.vessel_type,
            "phase": e.phase,
            "year": e.effective_year,
            "fee_type": e.fee_type,
            "fee_amount": e.fee_amount,
            "max_fee": e.max_fee,
        }
        for e in _FEE_SCHEDULE
    ]
