"""
US Port Towage Calculator
==========================
Calculates tug boat service costs for a vessel port call — docking, undocking,
and any shifting moves within port limits.

Rate Structure
--------------
  towage_total = tugs × (call_out_fee + rate_per_move × moves) × surcharge_multiplier

  - call_out_fee   : fixed fee per tug, per job (mobilisation)
  - rate_per_move  : variable fee per tug, per movement (docking or undocking)
  - moves          : default 2 (dock + undock); shifts add 2 per shift
  - tugs           : determined by vessel LOA — from port-specific table or global default
  - surcharge      : night / weekend / holiday multiplier (additive percentage)

Rate Driver
-----------
Primary: LOA (Length Over All, metres) → determines tug count
Secondary: port location determines base rate level

River Port Logic
----------------
New Orleans and Baton Rouge apply minimum tug counts due to Mississippi River current:
  - NOLA: minimum 2 tugs for LOA > 150m
  - Baton Rouge: minimum 2 tugs always (river current)
  - Columbia River (Portland OR): minimum 2 tugs always

Usage
-----
    from towage_calculator import calculate_towage

    # Basic call — LOA and port
    result = calculate_towage(port="New Orleans", vessel_loa=195.4)

    # With vessel IMO (auto-resolves LOA from ships register)
    result = calculate_towage(port="Houston", vessel_imo="9123456")

    # With night arrival and shifting
    import datetime as dt
    result = calculate_towage(
        port="Baton Rouge",
        vessel_loa=195.4,
        moves=4,                             # dock + 1 shift + undock
        arrival_datetime=dt.datetime(2025, 3, 8, 2, 30),
    )
    result.print_summary()
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent.parent / "data"
_RATES_FILE = _DATA_DIR / "towage_rates.json"

# Vessel resolver from pilotage module (shared utility)
# parents[2] = port_expenses/, then 02_pilotage/src/
_PILOTAGE_SRC = Path(__file__).parents[2] / "02_pilotage" / "src"
if str(_PILOTAGE_SRC) not in sys.path:
    sys.path.insert(0, str(_PILOTAGE_SRC))

try:
    from vessel_resolver import VesselParams, VesselNotFoundError, resolve_vessel
    _VESSEL_RESOLVER_AVAILABLE = True
except ImportError:
    _VESSEL_RESOLVER_AVAILABLE = False
    logger.warning("vessel_resolver not available — IMO lookup disabled for towage")


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

@dataclass
class TowageLineItem:
    description: str
    tugs: int
    rate_type: str          # "call_out" | "move" | "surcharge"
    rate_per_tug: float
    total: float
    direction: str = ""     # "inbound" | "outbound" | "shift" | ""


@dataclass
class TowageResult:
    port: str
    vessel_imo: Optional[str]
    vessel_name: Optional[str]
    vessel_loa_m: Optional[float]
    vessel_grt: Optional[int]
    moves: int
    arrival_datetime: Optional[dt.datetime]

    tugs_required: int = 0
    rate_per_tug_per_move: float = 0.0
    call_out_fee_per_tug: float = 0.0
    surcharge_pct: float = 0.0
    surcharge_reason: str = ""

    line_items: list[TowageLineItem] = field(default_factory=list)

    base_total: float = 0.0
    surcharge_amount: float = 0.0
    towage_total: float = 0.0

    confidence: str = "medium"
    source: str = "towage_rates.json v0.1.0-draft"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "vessel_imo": self.vessel_imo,
            "vessel_name": self.vessel_name,
            "vessel_loa_m": self.vessel_loa_m,
            "vessel_grt": self.vessel_grt,
            "moves": self.moves,
            "tugs_required": self.tugs_required,
            "rate_per_tug_per_move": self.rate_per_tug_per_move,
            "call_out_fee_per_tug": self.call_out_fee_per_tug,
            "surcharge_pct": self.surcharge_pct,
            "surcharge_reason": self.surcharge_reason,
            "base_total": self.base_total,
            "surcharge_amount": self.surcharge_amount,
            "towage_total": self.towage_total,
            "confidence": self.confidence,
            "source": self.source,
            "warnings": self.warnings,
        }

    def print_summary(self) -> None:
        print(f"\n{'='*65}")
        print(f"  TOWAGE ESTIMATE")
        print(f"  Port    : {self.port}")
        if self.vessel_name:
            print(f"  Vessel  : {self.vessel_name}")
        loa_str = f"{self.vessel_loa_m:.1f} m" if self.vessel_loa_m else "n/a"
        grt_str = f"{self.vessel_grt:,}" if self.vessel_grt else "n/a"
        print(f"  LOA     : {loa_str}   GRT: {grt_str}")
        print(f"  Tugs    : {self.tugs_required}   Moves: {self.moves}")
        if self.arrival_datetime:
            day = self.arrival_datetime.strftime("%A %Y-%m-%d %H:%M")
            print(f"  Arrival : {day}" + (f"  [{self.surcharge_reason}]" if self.surcharge_reason else ""))
        print(f"{'='*65}")
        print(f"  {'Description':<38} {'Tugs':>5} {'Amount':>16}")
        print(f"  {'-'*59}")
        for li in self.line_items:
            tug_str = f"×{li.tugs}" if li.tugs else ""
            print(f"  {li.description:<38} {tug_str:>5} ${li.total:>14,.2f}")
        print(f"  {'-'*59}")
        if self.surcharge_amount:
            print(f"  {'Base towage':<38} {'':>5} ${self.base_total:>14,.2f}")
            print(f"  {f'Surcharge ({self.surcharge_pct:.0f}%)':<38} {'':>5} ${self.surcharge_amount:>14,.2f}")
        print(f"  {'TOTAL TOWAGE':<38} {'':>5} ${self.towage_total:>14,.2f}")
        print(f"{'='*65}")
        if self.warnings:
            print("  WARNINGS:")
            for w in self.warnings:
                print(f"    * {w}")
        print(f"  Confidence: {self.confidence}  |  Source: {self.source}\n")


# ---------------------------------------------------------------------------
# Catalog loader
# ---------------------------------------------------------------------------

_rates_cache: Optional[dict] = None


def _load_rates() -> dict:
    global _rates_cache
    if _rates_cache is not None:
        return _rates_cache
    if not _RATES_FILE.exists():
        raise FileNotFoundError(f"Towage rates file not found: {_RATES_FILE}")
    _rates_cache = json.loads(_RATES_FILE.read_text(encoding="utf-8"))
    return _rates_cache


def _resolve_port(port: str) -> Optional[dict]:
    """Find port record by name or alias (case-insensitive)."""
    rates = _load_rates()
    port_lower = port.lower().strip()
    for key, pdata in rates.get("ports", {}).items():
        if port_lower == key or port_lower in [a.lower() for a in pdata.get("aliases", [])]:
            return pdata
        # Partial match
        if any(port_lower in a.lower() or a.lower() in port_lower
               for a in pdata.get("aliases", [])):
            return pdata
    return None


def _get_loa_tier(port_data: dict, loa_m: float) -> Optional[dict]:
    """Find the LOA tier that matches the vessel's LOA."""
    for tier in port_data.get("loa_tiers", []):
        if tier["loa_min_m"] <= loa_m <= tier["loa_max_m"]:
            return tier
    # Above all tiers — use last tier
    tiers = port_data.get("loa_tiers", [])
    return tiers[-1] if tiers else None


def _get_surcharge_pct(
    port_data: dict,
    arrival: Optional[dt.datetime],
) -> tuple[float, str]:
    """Return (surcharge_pct, reason_string) for night/weekend/holiday."""
    if arrival is None:
        return 0.0, ""

    surchg_cfg = port_data.get("surcharges", {})
    night_pct = surchg_cfg.get("night_pct", 0.0)
    weekend_pct = surchg_cfg.get("weekend_pct", 0.0)
    holiday_pct = surchg_cfg.get("holiday_pct", 0.0)

    is_night = arrival.hour >= 18 or arrival.hour < 6
    is_weekend = arrival.weekday() >= 5

    # Additive: night + weekend stack if both apply
    total_pct = 0.0
    reasons = []

    if is_night:
        total_pct += night_pct
        reasons.append(f"NIGHT +{night_pct:.0f}%")
    if is_weekend:
        total_pct += weekend_pct
        reasons.append(f"WEEKEND +{weekend_pct:.0f}%")

    # Cap at holiday rate if both night + weekend push above it
    if holiday_pct > 0 and total_pct > holiday_pct:
        total_pct = holiday_pct
        reasons = [f"NIGHT+WEEKEND capped at holiday rate +{holiday_pct:.0f}%"]

    return total_pct, " | ".join(reasons)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_towage(
    port: str,
    vessel_loa: Optional[float] = None,      # LOA in metres
    vessel_imo: Optional[str] = None,
    vessel_grt: Optional[int] = None,
    moves: int = 2,                           # default: dock + undock
    arrival_datetime: Optional[dt.datetime] = None,
    force_web_lookup: bool = False,
) -> TowageResult:
    """Calculate tug boat service costs for a port call.

    Parameters
    ----------
    port : str
        Port name — e.g. "New Orleans", "Houston", "Savannah"
    vessel_loa : float, optional
        Length Over All in metres. Primary rate driver.
    vessel_imo : str, optional
        IMO number — triggers vessel parameter auto-lookup.
    vessel_grt : int, optional
        GRT — used for size context and warnings only (LOA drives towage).
    moves : int
        Total pilotage moves. Default 2 (dock + undock).
        Add 2 per shift (e.g. moves=4 for dock + 1 shift + undock).
    arrival_datetime : datetime, optional
        Arrival date/time — used to evaluate night/weekend surcharges.
    force_web_lookup : bool
        Force web lookup for vessel data even if found locally.

    Returns
    -------
    TowageResult
    """
    warnings: list[str] = []
    vessel_name: Optional[str] = None

    # -------------------------------------------------------------------------
    # Step 1: Resolve vessel LOA
    # -------------------------------------------------------------------------
    if vessel_imo and vessel_loa is None:
        if _VESSEL_RESOLVER_AVAILABLE:
            try:
                params = resolve_vessel(imo=vessel_imo, force_web=force_web_lookup)
                vessel_loa = params.loa_m
                vessel_name = params.name
                if vessel_grt is None:
                    vessel_grt = params.grt
                warnings.extend(params.warnings)
                if vessel_loa is None:
                    warnings.append(
                        f"LOA not available for IMO {vessel_imo} — cannot determine tug count. "
                        "Provide vessel_loa= manually."
                    )
            except VesselNotFoundError as e:
                warnings.append(str(e))
        else:
            warnings.append("Vessel resolver not available — provide vessel_loa= manually.")

    # -------------------------------------------------------------------------
    # Step 2: Resolve port
    # -------------------------------------------------------------------------
    port_data = _resolve_port(port)
    if port_data is None:
        result = TowageResult(
            port=port, vessel_imo=vessel_imo, vessel_name=vessel_name,
            vessel_loa_m=vessel_loa, vessel_grt=vessel_grt,
            moves=moves, arrival_datetime=arrival_datetime,
            confidence="low", warnings=warnings,
        )
        result.warnings.append(
            f"Port '{port}' not found in towage rates catalog. "
            "Add it to towage_rates.json or provide rates manually."
        )
        return result

    # -------------------------------------------------------------------------
    # Step 3: Check LOA available
    # -------------------------------------------------------------------------
    if vessel_loa is None:
        result = TowageResult(
            port=port, vessel_imo=vessel_imo, vessel_name=vessel_name,
            vessel_loa_m=None, vessel_grt=vessel_grt,
            moves=moves, arrival_datetime=arrival_datetime,
            confidence="low", warnings=warnings,
        )
        result.warnings.append(
            "Vessel LOA required for towage calculation. "
            "Provide vessel_loa= or vessel_imo= to auto-resolve."
        )
        return result

    # -------------------------------------------------------------------------
    # Step 4: Look up LOA tier
    # -------------------------------------------------------------------------
    tier = _get_loa_tier(port_data, vessel_loa)
    if tier is None:
        result = TowageResult(
            port=port, vessel_imo=vessel_imo, vessel_name=vessel_name,
            vessel_loa_m=vessel_loa, vessel_grt=vessel_grt,
            moves=moves, arrival_datetime=arrival_datetime,
            confidence="low", warnings=warnings,
        )
        result.warnings.append(f"No LOA tier found for {vessel_loa}m at {port}.")
        return result

    tugs = tier["tugs"]
    rate_per_move = tier["rate_per_tug_per_move_usd"]
    call_out = tier["call_out_fee_per_tug_usd"]

    # -------------------------------------------------------------------------
    # Step 5: Night / weekend surcharge
    # -------------------------------------------------------------------------
    surcharge_pct, surcharge_reason = _get_surcharge_pct(port_data, arrival_datetime)

    # -------------------------------------------------------------------------
    # Step 6: Build line items
    # -------------------------------------------------------------------------
    line_items: list[TowageLineItem] = []

    # Call-out fee (per tug, once per job — not per move)
    call_out_total = tugs * call_out
    line_items.append(TowageLineItem(
        description=f"Call-out fee ({tugs} tug{'s' if tugs > 1 else ''})",
        tugs=tugs,
        rate_type="call_out",
        rate_per_tug=call_out,
        total=round(call_out_total, 2),
    ))

    # Move charges
    move_labels = []
    if moves >= 2:
        move_labels.append("Docking (inbound)")
        move_labels.append("Undocking (outbound)")
    for i in range(2, moves):
        move_labels.append(f"Shift move {i - 1}")

    for label in move_labels:
        move_total = tugs * rate_per_move
        line_items.append(TowageLineItem(
            description=label,
            tugs=tugs,
            rate_type="move",
            rate_per_tug=rate_per_move,
            total=round(move_total, 2),
            direction="inbound" if "Docking" in label else "outbound" if "Undocking" in label else "shift",
        ))

    base_total = round(sum(li.total for li in line_items), 2)

    # Apply surcharge to total (not itemised per line)
    surcharge_amount = round(base_total * surcharge_pct / 100, 2) if surcharge_pct else 0.0
    towage_total = round(base_total + surcharge_amount, 2)

    # -------------------------------------------------------------------------
    # Step 7: Warnings
    # -------------------------------------------------------------------------
    if vessel_grt and vessel_grt > 100_000:
        warnings.append(
            f"Very large vessel (GRT {vessel_grt:,}) — verify tug count with port authority. "
            "Some terminals require additional assist tugs for vessels above 100,000 GRT."
        )
    if tier.get("notes"):
        warnings.append(tier["notes"])
    for rule in port_data.get("port_specific_rules", []):
        warnings.append(rule)

    return TowageResult(
        port=port_data.get("display_name", port),
        vessel_imo=vessel_imo,
        vessel_name=vessel_name,
        vessel_loa_m=vessel_loa,
        vessel_grt=vessel_grt,
        moves=moves,
        arrival_datetime=arrival_datetime,
        tugs_required=tugs,
        rate_per_tug_per_move=rate_per_move,
        call_out_fee_per_tug=call_out,
        surcharge_pct=surcharge_pct,
        surcharge_reason=surcharge_reason,
        line_items=line_items,
        base_total=base_total,
        surcharge_amount=surcharge_amount,
        towage_total=towage_total,
        confidence=port_data.get("confidence", "medium"),
        source=f"towage_rates.json v0.1.0-draft | {port_data.get('display_name', port)}",
        warnings=warnings,
    )
