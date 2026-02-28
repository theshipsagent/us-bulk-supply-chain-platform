"""Tug and towage cost calculator.

Models harbour towage (assist tugs for docking/undocking) and river towage
requirements for various vessel types at US ports. Rates are based on
vessel GT (gross tonnage) brackets and number of tugs required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TowageRate:
    """Towage rate schedule for a port."""
    port: str
    gt_min: int
    gt_max: int
    rate_per_tug: float          # $ per tug per movement
    min_tugs: int = 1
    max_tugs: int = 3
    overtime_pct: float = 50.0   # overtime surcharge %
    standby_rate_per_hour: float = 0.0
    notes: str = ""


# ---------------------------------------------------------------------------
# Reference rates by port and GT bracket (approximate 2024/2025)
# ---------------------------------------------------------------------------

_TOWAGE_SCHEDULES: list[TowageRate] = [
    # New Orleans
    TowageRate("New Orleans", 0, 10_000, 4_500, 1, 2),
    TowageRate("New Orleans", 10_001, 25_000, 6_800, 2, 3),
    TowageRate("New Orleans", 25_001, 50_000, 9_200, 2, 3),
    TowageRate("New Orleans", 50_001, 80_000, 12_500, 2, 4),
    TowageRate("New Orleans", 80_001, 999_999, 16_000, 3, 4),
    # Houston
    TowageRate("Houston", 0, 10_000, 5_000, 1, 2),
    TowageRate("Houston", 10_001, 25_000, 7_500, 2, 3),
    TowageRate("Houston", 25_001, 50_000, 10_000, 2, 3),
    TowageRate("Houston", 50_001, 80_000, 13_500, 2, 4),
    TowageRate("Houston", 80_001, 999_999, 17_000, 3, 4),
    # Baton Rouge
    TowageRate("Baton Rouge", 0, 10_000, 4_000, 1, 2),
    TowageRate("Baton Rouge", 10_001, 25_000, 6_200, 2, 3),
    TowageRate("Baton Rouge", 25_001, 50_000, 8_500, 2, 3),
    TowageRate("Baton Rouge", 50_001, 80_000, 11_500, 2, 4),
    TowageRate("Baton Rouge", 80_001, 999_999, 14_500, 3, 4),
    # Mobile
    TowageRate("Mobile", 0, 10_000, 3_800, 1, 2),
    TowageRate("Mobile", 10_001, 25_000, 5_800, 2, 3),
    TowageRate("Mobile", 25_001, 50_000, 8_000, 2, 3),
    TowageRate("Mobile", 50_001, 80_000, 10_800, 2, 3),
    TowageRate("Mobile", 80_001, 999_999, 13_500, 3, 4),
    # Tampa
    TowageRate("Tampa", 0, 10_000, 3_500, 1, 2),
    TowageRate("Tampa", 10_001, 25_000, 5_500, 2, 3),
    TowageRate("Tampa", 25_001, 50_000, 7_800, 2, 3),
    TowageRate("Tampa", 50_001, 80_000, 10_200, 2, 3),
    TowageRate("Tampa", 80_001, 999_999, 13_000, 3, 4),
    # Norfolk
    TowageRate("Norfolk", 0, 10_000, 3_600, 1, 2),
    TowageRate("Norfolk", 10_001, 25_000, 5_600, 2, 3),
    TowageRate("Norfolk", 25_001, 50_000, 7_500, 2, 3),
    TowageRate("Norfolk", 50_001, 80_000, 10_000, 2, 3),
    TowageRate("Norfolk", 80_001, 999_999, 12_800, 3, 4),
    # Lake Charles
    TowageRate("Lake Charles", 0, 10_000, 4_200, 1, 2),
    TowageRate("Lake Charles", 10_001, 25_000, 6_500, 2, 3),
    TowageRate("Lake Charles", 25_001, 50_000, 8_800, 2, 3),
    TowageRate("Lake Charles", 50_001, 80_000, 11_800, 2, 4),
    TowageRate("Lake Charles", 80_001, 999_999, 15_000, 3, 4),
]


def _find_rate(port: str, gt: int) -> TowageRate | None:
    """Find the applicable towage rate for a port and GT."""
    port_lc = port.lower()
    for rate in _TOWAGE_SCHEDULES:
        if rate.port.lower() == port_lc and rate.gt_min <= gt <= rate.gt_max:
            return rate
    return None


def _available_ports() -> list[str]:
    """Return unique ports with towage data."""
    return sorted({r.port for r in _TOWAGE_SCHEDULES})


@dataclass
class TowageEstimate:
    """Itemised towage cost estimate."""
    port: str
    vessel_gt: int
    num_tugs: int
    movements: int                  # typically 2 (dock + undock)
    rate_per_tug: float
    base_cost: float
    overtime_surcharge: float
    standby_cost: float
    total: float
    notes: str = ""


def calculate_towage(
    port: str,
    vessel_gt: int,
    num_tugs: int | None = None,
    movements: int = 2,
    overtime: bool = False,
    standby_hours: float = 0.0,
) -> TowageEstimate:
    """Calculate harbour towage cost.

    Parameters
    ----------
    port : str
        Port name (must match reference data).
    vessel_gt : int
        Vessel gross tonnage.
    num_tugs : int, optional
        Override number of tugs. If None, uses default for GT bracket.
    movements : int
        Number of tug movements (default 2: dock + undock).
    overtime : bool
        Whether overtime rates apply (weekends, holidays, night).
    standby_hours : float
        Tug standby time in hours (e.g. waiting at anchorage).
    """
    rate = _find_rate(port, vessel_gt)
    if rate is None:
        available = ", ".join(_available_ports())
        raise ValueError(
            f"No towage rate found for port='{port}', GT={vessel_gt}. "
            f"Available ports: {available}"
        )

    tugs = num_tugs if num_tugs is not None else rate.min_tugs
    tugs = max(rate.min_tugs, min(tugs, rate.max_tugs))

    base = rate.rate_per_tug * tugs * movements
    ot_surcharge = base * (rate.overtime_pct / 100.0) if overtime else 0.0
    standby = standby_hours * rate.standby_rate_per_hour * tugs
    total = base + ot_surcharge + standby

    return TowageEstimate(
        port=port,
        vessel_gt=vessel_gt,
        num_tugs=tugs,
        movements=movements,
        rate_per_tug=rate.rate_per_tug,
        base_cost=round(base, 2),
        overtime_surcharge=round(ot_surcharge, 2),
        standby_cost=round(standby, 2),
        total=round(total, 2),
    )


def list_ports() -> list[dict[str, Any]]:
    """Return available ports with GT bracket summaries."""
    ports: dict[str, list[TowageRate]] = {}
    for r in _TOWAGE_SCHEDULES:
        ports.setdefault(r.port, []).append(r)

    result = []
    for port, rates in sorted(ports.items()):
        result.append({
            "port": port,
            "brackets": len(rates),
            "min_rate": min(r.rate_per_tug for r in rates),
            "max_rate": max(r.rate_per_tug for r in rates),
        })
    return result
