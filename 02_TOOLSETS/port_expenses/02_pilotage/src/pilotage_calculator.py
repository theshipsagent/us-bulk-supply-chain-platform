"""
US Port Pilotage Calculator
============================
Calculates compulsory pilotage costs for cargo vessel port calls and river transits
at US ports. Covers bar pilots, harbour pilots, and river pilots across Gulf, East
Coast, Pacific, and Great Lakes.

Rate Types
----------
GRT_TIER
    Flat fee per GRT band × number of movements.
    Used by: most US bar and harbour pilot associations.

DRAFT_PER_FOOT
    draft(ft) × rate_per_ft with a minimum charge floor, then a standing
    surcharge percentage added.  The surcharge_pct is ALWAYS applied —
    it is a general/fuel surcharge built into the tariff, NOT conditional
    on time of day.
    Used by: Mississippi River associations (Associated Branch, Crescent,
    NOLA-BR Steamship Pilots).

HOURLY
    Hourly rate × estimated transit hours.
    Used by: Great Lakes Pilotage (federal — 46 CFR Part 401).

Mississippi River — Three Separate Associations
-----------------------------------------------
A vessel transiting from sea to Baton Rouge pays ALL THREE independently:

  Sea Buoy → Head of Passes     Association: Associated Branch Pilots
  Head of Passes → New Orleans  Association: Crescent River Port Pilots
  New Orleans → Baton Rouge     Association: NOLA-BR Steamship Pilots
  Baton Rouge → Above BR        Association: NOLA-BR Steamship Pilots (same, higher rate)

Each association is a distinct legal entity with its own published tariff.
A vessel calling only at New Orleans pays segments 1 + 2 inbound and 2 + 1 outbound.

Surcharge Logic — Key Human Rules
----------------------------------
Mississippi River (DRAFT_PER_FOOT)
  • The surcharge_pct (15%, 12%, 10%) is ALWAYS applied — it is a standing
    general/fuel surcharge in the tariff, not a night/weekend charge.
  • Night-at-the-bar or anchorage delays are captured via detention_hours, not
    an additional surcharge.

GRT-Tier Ports
  • Night surcharge: applies only to the MOVEMENT that occurs at night.
    Inbound (arrival): based on arrival_datetime.
    Outbound (departure): based on departure_datetime.
    If departure_datetime not supplied, outbound night surcharge is NOT applied
    (conservative — warn user).
  • Deep-draft surcharge: applies only when the vessel is ACTUALLY drawing
    the deep draft at the time of that movement.
    Provide arrival_draft_ft for inbound, departure_draft_ft for outbound.
    If only one draft is supplied, surcharge is applied only to that direction.

Usage
-----
    from pilotage_calculator import calculate_pilotage

    # Standard port call (GRT-tier):
    result = calculate_pilotage(port="Savannah", vessel_grt=35000, direction="both")

    # GRT-tier with night arrival and daytime departure:
    result = calculate_pilotage(
        port="Houston",
        vessel_grt=35000,
        vessel_draft_ft=41.5,
        direction="both",
        arrival_datetime=datetime(2025, 3, 8, 23, 0),
        departure_datetime=datetime(2025, 3, 10, 10, 0),  # daytime — no night surcharge
    )

    # Mississippi River transit (draft-per-foot):
    result = calculate_pilotage(
        route="sea_to_nola",
        vessel_draft_ft=39.4,
        vessel_grt=35000,
    )

    # Full audit trail (hand-checkable):
    result.print_math_check()
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    from .vessel_resolver import VesselParams, VesselNotFoundError, resolve_vessel
except ImportError:
    from vessel_resolver import VesselParams, VesselNotFoundError, resolve_vessel  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent.parent / "data"
_CATALOG_FILE = _DATA_DIR / "pilot_associations_catalog.json"


# ---------------------------------------------------------------------------
# Rate type constants
# ---------------------------------------------------------------------------

GRT_TIER = "grt_tier"
DRAFT_PER_FOOT = "draft_per_foot"
HOURLY = "hourly"


# ---------------------------------------------------------------------------
# Hard-coded Mississippi River zone data
# (Draft-per-foot basis — three separate associations)
# Source: Legacy port_cost_model/pilotage_calculator.py (2024/2025 tariff card rates)
# Action: Pull current tariff PDFs from each association to verify
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MissZone:
    zone_id: str
    name: str
    association: str
    rate_per_foot: float        # USD per foot of draft
    min_charge: float           # Minimum charge floor (applies if vessel is in ballast)
    surcharge_pct: float        # ALWAYS-APPLIED standing surcharge (fuel/general)
    detention_per_hour: float   # Pilot waiting-time rate (USD/hr)
    cancellation_fee: float     # Cancellation after pilot boards
    mile_from: Optional[float] = None   # River mile from Head of Passes
    mile_to: Optional[float] = None
    association_contact: str = ""
    tariff_url: str = ""


MISS_ZONES: dict[str, MissZone] = {
    "bar_to_hop": MissZone(
        zone_id="bar_to_hop",
        name="Sea Buoy → Head of Passes",
        association="Associated Branch Pilots",
        rate_per_foot=135.0,
        min_charge=3_800.0,
        surcharge_pct=15.0,
        detention_per_hour=450.0,
        cancellation_fee=2_500.0,
        mile_from=-12.0,   # approx. sea buoy
        mile_to=0.0,       # Head of Passes = AHP Mile 0
        tariff_url="https://www.nobra.com/tariff",
    ),
    "hop_to_nola": MissZone(
        zone_id="hop_to_nola",
        name="Head of Passes → New Orleans",
        association="Crescent River Port Pilots",
        rate_per_foot=155.0,
        min_charge=4_200.0,
        surcharge_pct=12.0,
        detention_per_hour=500.0,
        cancellation_fee=2_800.0,
        mile_from=0.0,
        mile_to=95.0,     # Crescent City (NOLA) approx. AHP Mile 95
        tariff_url="https://www.crescentpilots.com",
    ),
    "nola_to_br": MissZone(
        zone_id="nola_to_br",
        name="New Orleans → Baton Rouge",
        association="New Orleans–Baton Rouge Steamship Pilots",
        rate_per_foot=165.0,
        min_charge=4_500.0,
        surcharge_pct=10.0,
        detention_per_hour=525.0,
        cancellation_fee=3_000.0,
        mile_from=95.0,
        mile_to=228.0,   # Baton Rouge approx. AHP Mile 228
        tariff_url="https://www.nobra.com/tariff",
    ),
    "br_to_above": MissZone(
        zone_id="br_to_above",
        name="Baton Rouge → Plantation/Above",
        association="New Orleans–Baton Rouge Steamship Pilots",
        rate_per_foot=180.0,
        min_charge=4_800.0,
        surcharge_pct=10.0,
        detention_per_hour=550.0,
        cancellation_fee=3_200.0,
        mile_from=228.0,
        mile_to=305.0,
        tariff_url="https://www.nobra.com/tariff",
    ),
}

# Route templates: list of zone_ids traversed (inbound sequence)
MISS_ROUTE_TEMPLATES: dict[str, list[str]] = {
    "sea_to_nola":      ["bar_to_hop", "hop_to_nola"],
    "sea_to_br":        ["bar_to_hop", "hop_to_nola", "nola_to_br"],
    "sea_to_above_br":  ["bar_to_hop", "hop_to_nola", "nola_to_br", "br_to_above"],
    "nola_only":        ["hop_to_nola"],        # Already inside, going to NOLA only
    "nola_to_br":       ["nola_to_br"],
    "hop_to_br":        ["hop_to_nola", "nola_to_br"],
}

# Port → route mapping (Mississippi destinations from sea)
MISS_PORT_ROUTES: dict[str, str] = {
    # New Orleans area
    "new orleans": "sea_to_nola",     "nola": "sea_to_nola",
    "new orleans la": "sea_to_nola",  "avondale": "sea_to_nola",
    "westwego": "sea_to_nola",        "gretna": "sea_to_nola",
    "harvey": "sea_to_nola",          "chalmette": "sea_to_nola",
    "meraux": "sea_to_nola",          "arabi": "sea_to_nola",
    "violet": "sea_to_nola",          "convent": "sea_to_nola",
    "st james": "sea_to_nola",
    # Baton Rouge area
    "baton rouge": "sea_to_br",       "baton rouge la": "sea_to_br",
    "port allen": "sea_to_br",        "plaquemine": "sea_to_br",
    "geismar": "sea_to_br",           "burnside": "sea_to_br",
    "donaldsonville": "sea_to_br",    "lutcher": "sea_to_br",
    "gramercy": "sea_to_br",          "reserve": "sea_to_br",
    "norco": "sea_to_br",             "destrehan": "sea_to_br",
    # Above Baton Rouge
    "st francisville": "sea_to_above_br", "angola": "sea_to_above_br",
    "natchez": "sea_to_above_br",     "vicksburg": "sea_to_above_br",
    "greenville": "sea_to_above_br",  "memphis": "sea_to_above_br",
}


# ---------------------------------------------------------------------------
# Output data models
# ---------------------------------------------------------------------------

@dataclass
class PilotageLineItem:
    """
    Single pilotage charge — one zone or one association per movement direction.

    calc_steps: ordered list of (label, formula_string) tuples that show every
    arithmetic step, suitable for a hand-checkable audit trail.
    """
    association: str
    zone_name: str
    rate_type: str                      # GRT_TIER | DRAFT_PER_FOOT | HOURLY | surcharge
    rate_basis_description: str         # Human-readable: "$155/ft × 39.4 ft draft" etc.
    gross_charge: float
    surcharge_pct: float
    surcharge_amount: float
    detention_hours: float
    detention_charge: float
    total: float
    direction: str                      # "inbound" | "outbound"
    confidence: str                     # "high" | "medium" | "low"
    source: str
    min_charge_applied: bool = False    # True when minimum floor was triggered
    calc_steps: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class PilotageResult:
    """Full pilotage estimate for a port call or river transit."""
    port: Optional[str]
    route: Optional[str]
    vessel_imo: Optional[str]
    vessel_name: Optional[str]
    vessel_grt: Optional[int]
    vessel_draft_ft: Optional[float]      # Arrival (inbound) draft
    departure_draft_ft: Optional[float]   # Departure (outbound) draft — may differ
    movements: int
    direction: str
    arrival_datetime: Optional[dt.datetime] = None
    departure_datetime: Optional[dt.datetime] = None

    line_items: list[PilotageLineItem] = field(default_factory=list)

    subtotal_inbound: float = 0.0
    subtotal_outbound: float = 0.0
    pilotage_total: float = 0.0

    overall_confidence: str = "medium"
    warnings: list[str] = field(default_factory=list)
    source_catalog: str = "pilot_associations_catalog.json v0.1.0-draft"

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "route": self.route,
            "vessel_imo": self.vessel_imo,
            "vessel_name": self.vessel_name,
            "vessel_grt": self.vessel_grt,
            "vessel_draft_ft": self.vessel_draft_ft,
            "departure_draft_ft": self.departure_draft_ft,
            "movements": self.movements,
            "direction": self.direction,
            "arrival_datetime": self.arrival_datetime.isoformat() if self.arrival_datetime else None,
            "departure_datetime": self.departure_datetime.isoformat() if self.departure_datetime else None,
            "line_items": [
                {
                    "association": li.association,
                    "zone": li.zone_name,
                    "rate_type": li.rate_type,
                    "rate_basis": li.rate_basis_description,
                    "gross_charge": li.gross_charge,
                    "surcharge_pct": li.surcharge_pct,
                    "surcharge": li.surcharge_amount,
                    "detention_hours": li.detention_hours,
                    "detention_charge": li.detention_charge,
                    "total": li.total,
                    "direction": li.direction,
                    "min_charge_applied": li.min_charge_applied,
                    "confidence": li.confidence,
                }
                for li in self.line_items
            ],
            "subtotal_inbound": self.subtotal_inbound,
            "subtotal_outbound": self.subtotal_outbound,
            "pilotage_total": self.pilotage_total,
            "overall_confidence": self.overall_confidence,
            "warnings": self.warnings,
            "source_catalog": self.source_catalog,
        }

    def print_summary(self) -> None:
        """PDA-style one-page summary."""
        print(f"\n{'='*67}")
        print(f"  PILOTAGE ESTIMATE")
        if self.port:
            print(f"  Port        : {self.port}")
        if self.route:
            print(f"  Route       : {self.route}")
        if self.vessel_name:
            print(f"  Vessel      : {self.vessel_name}")
        print(f"  GRT         : {self.vessel_grt:,}" if self.vessel_grt else "  GRT         : n/a")
        if self.vessel_draft_ft:
            dep_str = f" (dep: {self.departure_draft_ft:.1f} ft)" if self.departure_draft_ft else ""
            print(f"  Draft       : {self.vessel_draft_ft:.1f} ft (arrival){dep_str}")
        if self.arrival_datetime:
            tags = []
            if _is_night(self.arrival_datetime):
                tags.append("NIGHT")
            if _is_weekend(self.arrival_datetime):
                tags.append("WEEKEND")
            tag_str = "  [" + ", ".join(tags) + "]" if tags else ""
            print(f"  Arrival     : {self.arrival_datetime.strftime('%A %Y-%m-%d %H:%M')}{tag_str}")
        if self.departure_datetime:
            tags = []
            if _is_night(self.departure_datetime):
                tags.append("NIGHT")
            if _is_weekend(self.departure_datetime):
                tags.append("WEEKEND")
            tag_str = "  [" + ", ".join(tags) + "]" if tags else ""
            print(f"  Departure   : {self.departure_datetime.strftime('%A %Y-%m-%d %H:%M')}{tag_str}")
        print(f"{'='*67}")
        print(f"  {'Line Item':<40} {'Dir':>8} {'Amount':>14}")
        print(f"  {'-'*62}")
        base_items = [li for li in self.line_items if li.rate_type != "surcharge"]
        surchg_items = [li for li in self.line_items if li.rate_type == "surcharge"]
        for li in base_items:
            min_flag = " ⚑MIN" if li.min_charge_applied else ""
            label = f"{li.association}{min_flag}"
            print(f"  {label:<40} {li.direction:>8} ${li.total:>13,.2f}")
        if surchg_items:
            print(f"  {'-'*62}")
            print(f"  SURCHARGES:")
            for li in surchg_items:
                print(f"    {li.zone_name:<38} {li.direction:>8} ${li.total:>13,.2f}")
        print(f"  {'-'*62}")
        if surchg_items:
            base_total = sum(li.total for li in base_items)
            surchg_total = sum(li.total for li in surchg_items)
            print(f"  {'Base pilotage':<49} ${base_total:>13,.2f}")
            print(f"  {'Surcharges':<49} ${surchg_total:>13,.2f}")
        print(f"  {'TOTAL PILOTAGE':<49} ${self.pilotage_total:>13,.2f}")
        print(f"{'='*67}")
        if self.warnings:
            print("  WARNINGS:")
            for w in self.warnings:
                print(f"    * {w}")
        print(f"  Confidence: {self.overall_confidence}  |  Source: {self.source_catalog}\n")

    def print_math_check(self) -> None:
        """
        Full auditable arithmetic trail — every step shown for hand-verification.
        Designed for ship owner / charterer review of a Proforma Disbursement Account.
        """
        W = 73  # output width
        print(f"\n{'═'*W}")
        print(f"  PILOTAGE CALCULATION — AUDIT TRAIL")
        print(f"  Every arithmetic step shown for hand-verification and compliance review.")
        print(f"{'═'*W}")

        # ----- INPUTS --------------------------------------------------------
        print(f"\n  INPUTS USED IN CALCULATION")
        print(f"  {'─'*60}")
        if self.vessel_name:
            print(f"  {'Vessel':<26}: {self.vessel_name}")
        if self.vessel_grt:
            print(f"  {'Vessel GRT':<26}: {self.vessel_grt:,} GT")
        if self.vessel_draft_ft:
            dep_d = (f" | Departure draft: {self.departure_draft_ft:.2f} ft"
                     if self.departure_draft_ft else
                     " | Departure draft: not provided (using arrival draft for both directions)")
            print(f"  {'Vessel draft (arrival)':<26}: {self.vessel_draft_ft:.2f} ft "
                  f"({self.vessel_draft_ft / 3.28084:.2f} m){dep_d}")
        if self.port:
            print(f"  {'Port':<26}: {self.port}")
        if self.route:
            print(f"  {'Route':<26}: {self.route}")
        print(f"  {'Movements':<26}: {self.direction} "
              f"({'inbound + outbound, each zone billed twice' if self.direction == 'both' else self.direction})")
        if self.arrival_datetime:
            tags = []
            if _is_night(self.arrival_datetime):
                tags.append("NIGHT — after 22:00")
            if _is_weekend(self.arrival_datetime):
                tags.append("WEEKEND")
            tag_str = "  [" + ", ".join(tags) + "]" if tags else ""
            print(f"  {'Arrival datetime':<26}: {self.arrival_datetime.strftime('%A %Y-%m-%d %H:%M')}{tag_str}")
        else:
            print(f"  {'Arrival datetime':<26}: not provided")
        if self.departure_datetime:
            tags = []
            if _is_night(self.departure_datetime):
                tags.append("NIGHT — after 22:00")
            if _is_weekend(self.departure_datetime):
                tags.append("WEEKEND")
            tag_str = "  [" + ", ".join(tags) + "]" if tags else ""
            print(f"  {'Departure datetime':<26}: {self.departure_datetime.strftime('%A %Y-%m-%d %H:%M')}{tag_str}")
        else:
            print(f"  {'Departure datetime':<26}: not provided")
        print(f"  {'Tariff version':<26}: {self.source_catalog}")
        print(f"  {'⚠ DRAFT RATES':<26}: Verify all rates against current published tariffs before use")

        # ----- LINE ITEMS ----------------------------------------------------
        total_items = len(self.line_items)
        for idx, li in enumerate(self.line_items, 1):
            print(f"\n  {'─'*(W-2)}")
            type_label = {
                GRT_TIER:      "GRT-Tier (flat per movement)",
                DRAFT_PER_FOOT:"Draft per foot",
                HOURLY:        "Hourly",
                "surcharge":   "Surcharge",
            }.get(li.rate_type, li.rate_type)

            print(f"  LINE ITEM {idx} of {total_items} — {li.direction.upper()}")
            print(f"    Association : {li.association}")
            print(f"    Zone        : {li.zone_name}")
            print(f"    Rate type   : {type_label}")
            print(f"    Confidence  : {li.confidence}  |  Source: {li.source}")

            if li.calc_steps:
                print(f"")
                col1 = 32
                for label, formula in li.calc_steps:
                    # Highlight the total step
                    if label.lower().startswith(("total", "zone total", "movement total")):
                        print(f"    {'─'*55}")
                        print(f"    {label:<{col1}}  {formula}")
                    elif "→" in formula or "=" in formula:
                        print(f"    {label:<{col1}}  {formula}")
                    else:
                        print(f"    {label:<{col1}}  {formula}")

            print(f"    {'─'*55}")
            print(f"    {'LINE ITEM ' + str(idx) + ' TOTAL':<{32}}  ${li.total:>12,.2f}")

        # ----- ROLL-UP -------------------------------------------------------
        print(f"\n  {'═'*(W-2)}")
        print(f"  ROLL-UP")
        print(f"  {'─'*60}")

        inbound_items  = [li for li in self.line_items if li.direction == "inbound"]
        outbound_items = [li for li in self.line_items if li.direction == "outbound"]

        if inbound_items:
            parts = " + ".join(f"${li.total:,.2f}" for li in inbound_items)
            print(f"  Inbound total   :  {parts}  =  ${self.subtotal_inbound:,.2f}")
        if outbound_items:
            parts = " + ".join(f"${li.total:,.2f}" for li in outbound_items)
            print(f"  Outbound total  :  {parts}  =  ${self.subtotal_outbound:,.2f}")
        print(f"  {'─'*60}")
        print(f"  {'TOTAL PILOTAGE':<20}  ${self.subtotal_inbound:,.2f}  +  ${self.subtotal_outbound:,.2f}  =  ${self.pilotage_total:,.2f}")

        # ----- VERIFICATION NOTES -------------------------------------------
        print(f"\n  {'═'*(W-2)}")
        print(f"  TARIFF VERIFICATION — Confirm current rates before finalising PDA")
        print(f"  {'─'*60}")

        seen_assocs = []
        for li in self.line_items:
            if li.association not in seen_assocs:
                seen_assocs.append(li.association)
                # Try to find tariff URL
                zone_obj = next((z for z in MISS_ZONES.values() if z.association == li.association), None)
                url = zone_obj.tariff_url if zone_obj and zone_obj.tariff_url else "— see association website"
                print(f"    • {li.association:<42}  {url}")

        # ----- HUMAN LOGIC CHECKLIST ----------------------------------------
        print(f"\n  {'─'*60}")
        print(f"  HUMAN LOGIC CHECKLIST — Verify these assumptions before finalising")
        print(f"  {'─'*60}")

        is_miss = self.route is not None

        if is_miss:
            # Mississippi-specific checklist
            draft_str = f"{self.vessel_draft_ft:.2f} ft" if self.vessel_draft_ft else "unknown"
            dep_draft_str = f"{self.departure_draft_ft:.2f} ft" if self.departure_draft_ft else "same as arrival (not provided)"

            zones_used = MISS_ROUTE_TEMPLATES.get(self.route or "", [])
            zone_names = " → ".join(MISS_ZONES[z].name for z in zones_used)

            print(f"  □ DRAFT USED : Arrival (inbound) draft = {draft_str}")
            print(f"                 Departure (outbound) draft = {dep_draft_str}")
            print(f"                 Rule: Use the MAXIMUM (deepest) draft for each direction.")
            print(f"                 Loading port → departure draft is highest (outbound).")
            print(f"                 Discharging port → arrival draft is highest (inbound).")
            print()
            print(f"  □ ROUTE      : {self.route} — zones: {zone_names}")
            print(f"                 Confirm final berth location. If above NOLA bridge,")
            print(f"                 add nola_to_br zone (NOBRA Steamship, ${MISS_ZONES['nola_to_br'].rate_per_foot:.0f}/ft + {MISS_ZONES['nola_to_br'].surcharge_pct:.0f}%).")
            print()
            print(f"  □ SURCHARGE  : The % surcharges ({', '.join(str(int(MISS_ZONES[z].surcharge_pct))+'%' for z in zones_used)})")
            print(f"                 are STANDING TARIFF SURCHARGES — always applied, not conditional")
            print(f"                 on time of day or vessel size.")
            print()
            print(f"  □ DETENTION  : No detention applied in this estimate.")
            print(f"                 Detention starts when pilot BOARDS the vessel.")
            print(f"                 Rates by zone ($/hr):")
            for zid in zones_used:
                z = MISS_ZONES[zid]
                print(f"                   {z.association:<42} ${z.detention_per_hour:,.0f}/hr")
            print(f"                 Common triggers: night arrival at bar (wait for daylight),")
            print(f"                 berth not ready (anchorage wait), tide restriction.")
            print()
            print(f"  □ MINIMUM    : Min charge floors by zone:")
            for zid in zones_used:
                z = MISS_ZONES[zid]
                # Calculate breakeven draft
                breakeven = z.min_charge / z.rate_per_foot
                li_matching = [li for li in self.line_items
                               if li.association == z.association and li.direction == "inbound"]
                min_flag = " ← TRIGGERED" if li_matching and li_matching[0].min_charge_applied else ""
                print(f"                   {z.association:<42} ${z.min_charge:,.0f}  (applies if draft < {breakeven:.1f} ft){min_flag}")
            print()
            print(f"  □ CANCELLATION : If vessel cancels after pilot boards:")
            for zid in zones_used:
                z = MISS_ZONES[zid]
                print(f"                   {z.association:<42} ${z.cancellation_fee:,.0f}")
        else:
            # GRT-tier checklist
            grt_str = f"{self.vessel_grt:,} GT" if self.vessel_grt else "unknown"
            arr_str = self.arrival_datetime.strftime("%H:%M") if self.arrival_datetime else "not provided"
            dep_str = self.departure_datetime.strftime("%H:%M") if self.departure_datetime else "not provided"

            print(f"  □ GRT USED   : {grt_str} — must be Registered Gross Tonnage from")
            print(f"                 Certificate of Registry, NOT deadweight (DWT).")
            print()
            print(f"  □ TIMING     : Night surcharge window: 22:00 – 06:00 local time")
            print(f"                 Arrival time  = {arr_str}  → inbound movement")
            print(f"                 Departure time = {dep_str} → outbound movement")
            print(f"                 Each movement evaluated independently for night/weekend.")
            if not self.departure_datetime:
                print(f"                 ⚠ Departure time not provided — outbound night surcharge")
                print(f"                   NOT applied. Provide departure_datetime= to correct.")
            print()
            if self.vessel_draft_ft:
                dep_d = self.departure_draft_ft or self.vessel_draft_ft
                print(f"  □ DEEP DRAFT : Inbound draft  = {self.vessel_draft_ft:.1f} ft  → applied to inbound movement")
                print(f"                 Outbound draft = {dep_d:.1f} ft → applied to outbound movement")
                print(f"                 If discharging at this port, outbound draft will be LOWER")
                print(f"                 (in ballast). Provide departure_draft_ft= if different.")
            print()
            print(f"  □ SHIFTING   : Standard estimate = {self.movements} movements (inbound + outbound).")
            print(f"                 Each shift within port = 1 additional movement (additional charge).")
            print(f"                 Dry-docking moves, anchor-to-berth, etc. also add movements.")
            print()
            print(f"  □ GRT BELOW COMPULSORY THRESHOLD:")
            print(f"                 Most US ports: compulsory pilotage above 300 GT (federal waters)")
            print(f"                 or 1,600 GRT (Mississippi River). Below threshold = voluntary,")
            print(f"                 may be cheaper. Confirm with port agent.")

        print(f"\n{'═'*W}")
        if self.warnings:
            print("  WARNINGS:")
            for w in self.warnings:
                print(f"    * {w}")
            print(f"{'═'*W}")
        print()

    # ------------------------------------------------------------------
    def to_markdown(self) -> str:
        """
        Generate a full printable markdown audit document.

        Shows:
          • All voyage/vessel inputs and where each came from
          • The complete tariff schedule table for the applicable association,
            with the selected row/zone clearly marked and the selection reason
          • For every line item: the formula, the arithmetic step-by-step,
            and why the charge was applied
          • Roll-up table with inbound/outbound subtotals
          • Assumptions checklist for human review

        Usage:
            md = result.to_markdown()
            Path("pilotage_audit.md").write_text(md)
        """
        L: list[str] = []

        def h(n: int, text: str) -> None:
            L.append(f"{'#' * n} {text}\n")

        def p(text: str = "") -> None:
            L.append(text + "\n")

        def hr() -> None:
            L.append("---\n")

        def tbl(headers: list, rows: list) -> None:
            widths = [
                max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
                for i, h in enumerate(headers)
            ]
            def fmt_row(cells):
                return "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells)) + " |"
            sep = "| " + " | ".join("-" * w for w in widths) + " |"
            L.append(fmt_row(headers))
            L.append(sep)
            for row in rows:
                L.append(fmt_row(row))
            L.append("")

        import datetime as _dt
        now_str = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # ── Title page ────────────────────────────────────────────────────────
        h(1, "PILOTAGE COST CALCULATION — AUDIT DOCUMENT")
        p(f"**Document type:** Proforma Disbursement Account — Pilotage Section  ")
        p(f"**Generated:** {now_str}  ")
        p(f"**Status:** ⚠ DRAFT — All rates require verification against current published tariffs before use  ")
        p(f"**Tariff source:** {self.source_catalog}  ")
        hr()

        # ── Section 1: Inputs ─────────────────────────────────────────────────
        h(2, "Section 1 — Voyage & Vessel Inputs")
        p("These are the parameters fed into the calculation. Each must be confirmed "
          "from official vessel documents or voyage instructions before finalising the PDA.")
        p()

        input_rows = []
        if self.vessel_name:
            input_rows.append(["Vessel Name", self.vessel_name, "Provided"])
        if self.vessel_imo:
            input_rows.append(["IMO Number", self.vessel_imo, "Provided"])
        if self.vessel_grt:
            input_rows.append(["Vessel GRT", f"{self.vessel_grt:,} GT",
                                "Registered Gross Tonnage — from Certificate of Registry. NOT DWT."])
        else:
            input_rows.append(["Vessel GRT", "Not provided", "⚠ Required for GRT-tier ports"])

        if self.vessel_draft_ft:
            input_rows.append(["Arrival Draft (inbound)",
                                f"{self.vessel_draft_ft:.2f} ft  ({self.vessel_draft_ft / 3.28084:.2f} m)",
                                "Draft at time of inbound movement"])
        else:
            input_rows.append(["Arrival Draft", "Not provided", "⚠ Required for Mississippi River"])

        if self.departure_draft_ft:
            input_rows.append(["Departure Draft (outbound)",
                                f"{self.departure_draft_ft:.2f} ft  ({self.departure_draft_ft / 3.28084:.2f} m)",
                                "Draft at time of outbound movement — may differ from arrival"])
        else:
            input_rows.append(["Departure Draft (outbound)", "Not provided — arrival draft used",
                                "⚠ Provide departure_draft_ft= if vessel will be lighter on departure"])

        if self.port:
            input_rows.append(["Port", self.port, "Provided"])
        if self.route:
            reason = f"Auto-inferred from port '{self.port}'" if self.port else "Provided explicitly"
            input_rows.append(["River Route", self.route, reason])

        dir_desc = "Inbound + Outbound — each zone/movement billed twice" if self.direction == "both" else self.direction
        input_rows.append(["Direction", self.direction, dir_desc])

        def dt_row(label, dt_val, use_label):
            if dt_val:
                tags = []
                if _is_night(dt_val):    tags.append("NIGHT (after 22:00)")
                if _is_weekend(dt_val):  tags.append("WEEKEND")
                tag_str = "  [" + " + ".join(tags) + "]" if tags else "  [daytime weekday]"
                return [label, dt_val.strftime("%Y-%m-%d %H:%M") + tag_str, use_label]
            return [label, "Not provided", f"Night/weekend surcharge NOT evaluated for {use_label.lower()}"]

        input_rows.append(dt_row("Arrival datetime",   self.arrival_datetime,   "Inbound movement"))
        input_rows.append(dt_row("Departure datetime", self.departure_datetime, "Outbound movement"))

        tbl(["Parameter", "Value", "Notes / Source"], input_rows)
        hr()

        # ── Section 2: Tariff Schedule Selection ─────────────────────────────
        h(2, "Section 2 — Tariff Schedule & Rate Selection")

        is_miss = self.route is not None

        if is_miss:
            zone_ids = MISS_ROUTE_TEMPLATES.get(self.route, [])
            p(f"**Applicable rate basis:** Draft per foot (sliding scale with minimum charge floor)  ")
            p(f"**Route:** `{self.route}` — {len(zone_ids)} zone(s), each billed by a separate licensed association  ")
            p()

            for zid in zone_ids:
                z = MISS_ZONES[zid]
                h(3, f"Zone: {z.name}")
                p(f"**Association:** {z.association}  ")
                if z.tariff_url:
                    p(f"**Tariff URL:** {z.tariff_url}  ")
                p(f"**River miles:** {z.mile_from} to {z.mile_to} (AHP miles from Head of Passes)  ")
                p()

                # Rate table — Mississippi has a single rate per foot, not tiered
                p("**Rate Schedule:**")
                tbl(
                    ["Component", "Value", "Explanation"],
                    [
                        ["Rate per foot of draft", f"${z.rate_per_foot:.2f}/ft",
                         "Applied to actual vessel draft at time of transit"],
                        ["Minimum charge", f"${z.min_charge:,.2f}",
                         f"Floor — applies if vessel draft × ${z.rate_per_foot:.2f} < ${z.min_charge:,.2f}  "
                         f"(i.e., draft below {z.min_charge / z.rate_per_foot:.1f} ft)"],
                        ["Standing surcharge", f"{z.surcharge_pct:.0f}%",
                         "ALWAYS APPLIED — general/fuel surcharge built into published tariff. Not conditional on time of day."],
                        ["Detention rate", f"${z.detention_per_hour:,.0f}/hr",
                         "Applies when pilot is waiting (berth not ready, tide, anchorage, etc.)"],
                        ["Cancellation fee", f"${z.cancellation_fee:,.0f}",
                         "Applies if vessel cancels after pilot has boarded"],
                    ]
                )

                p("**Calculation formula:**")
                L.append("```")
                L.append(f"  Step 1  Raw charge     =  Draft (ft)  ×  ${z.rate_per_foot:.2f} per foot")
                L.append(f"  Step 2  Applied charge  =  max( Raw charge,  ${z.min_charge:,.2f} minimum )")
                L.append(f"  Step 3  Surcharge       =  Applied charge  ×  {z.surcharge_pct:.1f}%   (standing — always)")
                L.append(f"  Step 4  Detention       =  Hours waiting   ×  ${z.detention_per_hour:,.0f}/hr")
                L.append(f"  Step 5  Zone total      =  Applied charge  +  Surcharge  +  Detention")
                L.append("```")
                L.append("")

        else:
            # GRT-tier — show full bracket table with selected row flagged
            p("**Applicable rate basis:** GRT-tier — flat rate per pilotage movement  ")
            p("The vessel's Registered Gross Tonnage is looked up in the published tariff "
              "schedule. The rate for that GRT bracket is a flat fee per movement. "
              "Inbound = 1 movement, Outbound = 1 movement.  ")
            p()

            # Attempt to fetch the full tier table
            try:
                catalog = _load_catalog()
                assoc_data = None
                if self.port:
                    p_lower = self.port.lower().strip()
                    for a in catalog.get("associations", []):
                        for ap in a.get("ports", []):
                            if ap.lower() == p_lower or p_lower in ap.lower():
                                assoc_data = a
                                break
                        if assoc_data:
                            break
            except Exception:
                assoc_data = None

            if assoc_data:
                h(3, f"Association: {assoc_data['name']}")
                if assoc_data.get("notes"):
                    p(f"*{assoc_data['notes']}*  ")
                if assoc_data.get("website"):
                    p(f"**Website:** {assoc_data['website']}  ")
                if assoc_data.get("tariff_url"):
                    p(f"**Tariff URL:** {assoc_data['tariff_url']}  ")
                p()

                tiers = assoc_data.get("grt_tiers", [])
                if tiers:
                    p("**Full Published GRT Rate Schedule** (rate per pilotage movement):")
                    tier_rows = []
                    for tier in tiers:
                        max_str = f"{tier['grt_max']:,}" if tier["grt_max"] < 999999 else "and above"
                        if self.vessel_grt and tier["grt_min"] <= self.vessel_grt <= tier["grt_max"]:
                            sel = f"← **VESSEL FALLS HERE** (GRT {self.vessel_grt:,})"
                            from_str = f"**{tier['grt_min']:,}**"
                            to_str   = f"**{max_str}**"
                            rate_str = f"**${tier['rate_usd']:,.2f}**"
                        elif self.vessel_grt and self.vessel_grt > 999999 and tier == tiers[-1]:
                            sel = f"← **VESSEL FALLS HERE** (GRT {self.vessel_grt:,} — above all tiers, highest rate applies)"
                            from_str = f"**{tier['grt_min']:,}**"
                            to_str   = f"**{max_str}**"
                            rate_str = f"**${tier['rate_usd']:,.2f}**"
                        else:
                            sel = ""
                            from_str = f"{tier['grt_min']:,}"
                            to_str   = max_str
                            rate_str = f"${tier['rate_usd']:,.2f}"
                        tier_rows.append([from_str, to_str, rate_str, sel])
                    tbl(["GRT From", "GRT To", "Rate per Movement (USD)", "Selection"], tier_rows)

                    # Find selected
                    sel_tier = next((t for t in tiers if self.vessel_grt and t["grt_min"] <= self.vessel_grt <= t["grt_max"]), tiers[-1])
                    p(f"**→ Vessel GRT:** {self.vessel_grt:,} GT  ")
                    max_grt_str = "and above" if sel_tier['grt_max'] >= 999999 else f"{sel_tier['grt_max']:,}"
                    p(f"**→ Selected bracket:** {sel_tier['grt_min']:,} – {max_grt_str} GT  ")
                    p(f"**→ Rate applied:** ${sel_tier['rate_usd']:,.2f} per movement  ")
                    p()

                p("**Calculation formula:**")
                L.append("```")
                L.append("  Step 1  Look up GRT in tariff schedule → identify bracket → read flat rate")
                L.append("  Step 2  Movement charge  =  Flat rate (no further scaling)")
                L.append("  Step 3  Detention        =  Hours waiting  ×  detention rate/hr")
                L.append("  Step 4  Movement total   =  Flat rate  +  Detention")
                L.append("  Note:   Surcharges (night, deep draft, etc.) are separate line items below")
                L.append("```")
                L.append("")

                if assoc_data.get("surcharges"):
                    p("**Applicable Surcharges from Published Tariff:**")
                    sr = assoc_data["surcharges"]
                    sur_rows = []
                    for s in sr:
                        amt = f"${s['amount_usd']:,.2f}" if s.get("amount_usd") else "— (verify)"
                        sur_rows.append([s.get("type", ""), amt,
                                         s.get("notes", ""),
                                         "Per movement direction — evaluated separately for inbound and outbound"])
                    tbl(["Surcharge Type", "Rate", "Condition / Notes", "How Applied"], sur_rows)

        hr()

        # ── Section 3: Line-by-line calculations ──────────────────────────────
        h(2, "Section 3 — Line Item Calculations")
        p("Every arithmetic step is shown. Each figure can be verified independently with a hand calculator.")
        p()

        for idx, li in enumerate(self.line_items, 1):
            type_labels = {
                DRAFT_PER_FOOT: "Draft per foot (sliding scale)",
                GRT_TIER:       "GRT-tier (flat rate per movement)",
                HOURLY:         "Hourly rate",
                "surcharge":    "Surcharge",
            }
            h(3, f"Line Item {idx} — {li.direction.upper()}:  {li.association}")
            p(f"| | |")
            p(f"|---|---|")
            p(f"| **Zone / Service** | {li.zone_name} |")
            p(f"| **Rate type** | {type_labels.get(li.rate_type, li.rate_type)} |")
            p(f"| **Direction** | {li.direction.capitalize()} |")
            p(f"| **Confidence** | {li.confidence} |")
            p(f"| **Tariff source** | {li.source} |")
            p()

            if li.calc_steps:
                p("**Step-by-step arithmetic:**")
                step_rows = []
                for step_label, formula in li.calc_steps:
                    is_total = any(step_label.lower().startswith(k)
                                   for k in ("zone total", "movement total", "total"))
                    if is_total:
                        step_rows.append([f"**{step_label}**", f"**{formula}**"])
                    else:
                        step_rows.append([step_label, formula])
                tbl(["Step", "Calculation"], step_rows)

            if li.min_charge_applied:
                p(f"> **⚑ Minimum charge applied.**  The calculated rate "
                  f"(draft × rate/ft) fell below the minimum charge floor.  "
                  f"This occurs when the vessel is in ballast or lightly loaded.  "
                  f"Minimum charge of **${li.gross_charge:,.2f}** applied instead.")
                p()

            p(f"**Line Item {idx} Total:  ${li.total:,.2f}**")
            hr()

        # ── Section 4: Roll-up ────────────────────────────────────────────────
        h(2, "Section 4 — Summary & Total")

        inbound_items  = [li for li in self.line_items if li.direction == "inbound"]
        outbound_items = [li for li in self.line_items if li.direction == "outbound"]

        sum_rows = []
        for li in inbound_items:
            sum_rows.append([li.association, li.zone_name, "Inbound", f"${li.total:,.2f}"])
        sum_rows.append(["", "", "*Inbound subtotal*", f"*${self.subtotal_inbound:,.2f}*"])
        sum_rows.append(["", "", "", ""])
        for li in outbound_items:
            sum_rows.append([li.association, li.zone_name, "Outbound", f"${li.total:,.2f}"])
        sum_rows.append(["", "", "*Outbound subtotal*", f"*${self.subtotal_outbound:,.2f}*"])
        sum_rows.append(["", "", "", ""])
        sum_rows.append(["", "", "**TOTAL PILOTAGE**", f"**${self.pilotage_total:,.2f}**"])

        tbl(["Association", "Zone / Service", "Direction", "Amount (USD)"], sum_rows)
        p(f"Inbound subtotal:   **${self.subtotal_inbound:,.2f}**  ")
        p(f"Outbound subtotal:  **${self.subtotal_outbound:,.2f}**  ")
        p(f"  ")
        p(f"## TOTAL PILOTAGE:  ${self.pilotage_total:,.2f}")
        hr()

        # ── Section 5: Human logic checklist ─────────────────────────────────
        h(2, "Section 5 — Assumptions & Human Logic Checklist")
        p("The following must be confirmed before this estimate is used in a final PDA or presented to a ship owner:")
        p()

        if is_miss:
            zone_ids_used = MISS_ROUTE_TEMPLATES.get(self.route or "", [])
            draft_str    = f"{self.vessel_draft_ft:.2f} ft" if self.vessel_draft_ft else "unknown"
            dep_draft_str = f"{self.departure_draft_ft:.2f} ft" if self.departure_draft_ft else f"not provided — arrival draft used ({draft_str})"

            p(f"- [ ] **Draft used — INBOUND:** {draft_str}.  "
              f"Rule: use the MAXIMUM draft for each direction.  "
              f"Discharging port → arrival draft is heaviest.  "
              f"Loading port → departure draft is heaviest.  ")
            p(f"- [ ] **Draft used — OUTBOUND:** {dep_draft_str}.  ")
            p(f"- [ ] **Route correct:** `{self.route}` — zones: "
              f"{' → '.join(MISS_ZONES[z].name for z in zone_ids_used)}.  "
              f"Confirm final berth. If berth is above NOLA bridge, add `nola_to_br` zone.  ")
            p(f"- [ ] **Standing surcharges** ({', '.join(str(int(MISS_ZONES[z].surcharge_pct))+'%' for z in zone_ids_used)}) "
              f"are ALWAYS applied — they are built-in tariff surcharges, not night/weekend charges.  ")
            p(f"- [ ] **Detention:** Not applied in this estimate. "
              f"Add if pilot was detained waiting (berth, tide, anchorage, night-at-bar).  ")
            p("  | Association | Detention rate |")
            p("  |---|---|")
            for zid in zone_ids_used:
                z = MISS_ZONES[zid]
                p(f"  | {z.association} | ${z.detention_per_hour:,.0f}/hr |")
            p()
            p(f"- [ ] **Minimum charge floors:**  ")
            for zid in zone_ids_used:
                z = MISS_ZONES[zid]
                breakeven = z.min_charge / z.rate_per_foot
                li_match = [li for li in self.line_items if li.association == z.association and li.direction == "inbound"]
                triggered = " ← **TRIGGERED IN THIS ESTIMATE**" if li_match and li_match[0].min_charge_applied else ""
                p(f"  - {z.association}: ${z.min_charge:,.2f} (applies if draft < {breakeven:.1f} ft){triggered}  ")
            p(f"- [ ] **Cancellation fees** (if vessel cancels after pilot boards):  ")
            for zid in zone_ids_used:
                z = MISS_ZONES[zid]
                p(f"  - {z.association}: ${z.cancellation_fee:,.0f}  ")
        else:
            grt_str = f"{self.vessel_grt:,} GT" if self.vessel_grt else "unknown"
            arr_t = self.arrival_datetime.strftime("%H:%M") if self.arrival_datetime else "not provided"
            dep_t = self.departure_datetime.strftime("%H:%M") if self.departure_datetime else "not provided"

            p(f"- [ ] **GRT confirmed:** {grt_str}.  "
              f"Must be Registered Gross Tonnage from Certificate of Registry — NOT DWT.  ")
            p(f"- [ ] **Night surcharge window:** 22:00–06:00 local time.  "
              f"Arrival = {arr_t} (inbound).  Departure = {dep_t} (outbound).  "
              f"Each movement evaluated **independently**.  ")
            if not self.departure_datetime:
                p(f"  > ⚠ Departure time not provided — outbound night surcharge NOT applied. "
                  f"Provide `departure_datetime=` to evaluate.")
            if self.vessel_draft_ft:
                dep_d = self.departure_draft_ft or self.vessel_draft_ft
                p(f"- [ ] **Deep draft:**  "
                  f"Inbound = {self.vessel_draft_ft:.1f} ft.  Outbound = {dep_d:.1f} ft.  "
                  f"Surcharge applies only to the direction where draft exceeds the threshold.  ")
            p(f"- [ ] **Shifting:** Standard = 2 movements (in + out).  "
              f"Each shift within port = 1 additional movement.  ")
            p(f"- [ ] **GRT below compulsory threshold:** Most US ports compulsory above 300 GT.  "
              f"Below threshold = voluntary — confirm with port agent.  ")

        if self.warnings:
            hr()
            h(2, "Warnings")
            for w in self.warnings:
                p(f"- ⚠ {w}")

        hr()
        p(f"*End of document — {self.source_catalog}*")

        return "\n".join(L)

    def save_markdown(self, path: str) -> None:
        """Write the audit document to a markdown file."""
        from pathlib import Path as _Path
        _Path(path).write_text(self.to_markdown(), encoding="utf-8")
        print(f"Audit document written to: {path}")


# ---------------------------------------------------------------------------
# Catalog loader
# ---------------------------------------------------------------------------

_catalog_cache: Optional[dict] = None


def _load_catalog() -> dict:
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    if not _CATALOG_FILE.exists():
        raise FileNotFoundError(
            f"Pilot associations catalog not found: {_CATALOG_FILE}\n"
            "Run the data collection phase first."
        )
    _catalog_cache = json.loads(_CATALOG_FILE.read_text(encoding="utf-8"))
    return _catalog_cache


def _get_association(port_key: str) -> Optional[dict]:
    catalog = _load_catalog()
    port_lower = port_key.lower().strip()
    for assoc in catalog.get("associations", []):
        for p in assoc.get("ports", []):
            if p.lower() == port_lower:
                return assoc
    return None


def _resolve_port_to_assoc(port: str) -> Optional[dict]:
    assoc = _get_association(port)
    if assoc:
        return assoc
    catalog = _load_catalog()
    port_lower = port.lower().strip()
    for assoc in catalog.get("associations", []):
        for p in assoc.get("ports", []):
            if port_lower in p.lower() or p.lower() in port_lower:
                return assoc
    return None


# ---------------------------------------------------------------------------
# Rate calculation helpers
# ---------------------------------------------------------------------------

def _calc_grt_tier(
    assoc: dict,
    grt: int,
    movements: int,
    direction: str,
    detention_hours: float = 0.0,
) -> list[PilotageLineItem]:
    """Calculate pilotage for a GRT-tier association.
    Note: surcharges (night, deep draft) are applied separately by _apply_surcharges().
    """
    tiers = assoc.get("grt_tiers", [])
    if not tiers:
        return []

    matched_tier = None
    for tier in tiers:
        if tier["grt_min"] <= grt <= tier["grt_max"]:
            matched_tier = tier
            break
    if matched_tier is None:
        matched_tier = tiers[-1]  # Vessel above all tiers — use highest

    rate_usd = matched_tier["rate_usd"]
    tier_max_str = (f"{matched_tier['grt_max']:,}"
                    if matched_tier["grt_max"] < 999999 else "and above")
    bracket_label = f"{matched_tier['grt_min']:,} – {tier_max_str} GT"

    det_rate = assoc.get("detention_per_hour", 0.0)
    det_charge = round(detention_hours * det_rate, 2)

    items = []
    dirs = ["inbound", "outbound"] if direction == "both" else [direction]

    for d in dirs:
        total = round(rate_usd + det_charge, 2)
        calc_steps: list[tuple[str, str]] = [
            ("Vessel GRT",       f"{grt:,} GT"),
            ("GRT bracket",      bracket_label),
            ("Tariff rate",      f"${rate_usd:,.2f} per movement (flat — GRT tier)"),
            ("Direction",        d),
        ]
        if detention_hours > 0:
            calc_steps.append((
                f"Detention ({detention_hours:.1f} hrs)",
                f"{detention_hours:.1f} hrs × ${det_rate:,.0f}/hr = ${det_charge:,.2f}"
            ))
        if detention_hours > 0:
            calc_steps.append((
                "Movement total",
                f"${rate_usd:,.2f} + ${det_charge:,.2f} detention = ${total:,.2f}"
            ))
        else:
            calc_steps.append((
                "Movement total",
                f"${rate_usd:,.2f} (flat rate — no detention)"
            ))

        items.append(PilotageLineItem(
            association=assoc["name"],
            zone_name=f"{assoc['name']} — Port Call",
            rate_type=GRT_TIER,
            rate_basis_description=f"GRT {grt:,} → ${rate_usd:,.0f}/movement",
            gross_charge=round(rate_usd, 2),
            surcharge_pct=0.0,
            surcharge_amount=0.0,
            detention_hours=detention_hours,
            detention_charge=det_charge,
            total=total,
            direction=d,
            confidence=assoc.get("confidence", "medium"),
            source=assoc.get("verification_url") or assoc.get("tariff_url") or "catalog",
            min_charge_applied=False,
            calc_steps=calc_steps,
        ))
    return items


def _calc_draft_per_foot(
    zone: MissZone,
    draft_ft: float,
    direction: str,
    detention_hours: float = 0.0,
) -> list[PilotageLineItem]:
    """
    Calculate pilotage for a single Mississippi River draft-per-foot zone.

    Formula:
        raw_calc = rate_per_foot × draft_ft
        gross    = max(raw_calc, min_charge)        ← minimum floor
        surcharge = gross × (surcharge_pct / 100)   ← ALWAYS applied (standing surcharge)
        detention = detention_hours × detention_per_hour
        total    = gross + surcharge + detention
    """
    items = []
    dirs = ["inbound", "outbound"] if direction == "both" else [direction]

    raw_calc = round(zone.rate_per_foot * draft_ft, 2)
    min_applied = raw_calc < zone.min_charge
    gross = round(max(raw_calc, zone.min_charge), 2)
    surcharge = round(gross * zone.surcharge_pct / 100.0, 2)
    det_charge = round(detention_hours * zone.detention_per_hour, 2)
    total = round(gross + surcharge + det_charge, 2)

    for d in dirs:
        calc_steps: list[tuple[str, str]] = [
            ("Draft (ft)",            f"{draft_ft:.2f} ft"),
            ("Rate per foot",         f"${zone.rate_per_foot:.2f}/ft"),
            ("Raw calculation",       f"{draft_ft:.2f} ft × ${zone.rate_per_foot:.2f}/ft = ${raw_calc:,.2f}"),
            ("Minimum charge floor",  f"${zone.min_charge:,.2f}"),
        ]
        if min_applied:
            calc_steps.append((
                "Min charge applied?",
                f"YES — ${raw_calc:,.2f} < ${zone.min_charge:,.2f} floor → use ${gross:,.2f}"
            ))
        else:
            calc_steps.append((
                "Min charge applied?",
                f"NO — ${raw_calc:,.2f} > ${zone.min_charge:,.2f} floor → gross applies"
            ))
        calc_steps.append(("Charge before surcharge", f"${gross:,.2f}"))
        calc_steps.append((
            f"Surcharge ({zone.surcharge_pct:.0f}%) — standing",
            f"${gross:,.2f} × {zone.surcharge_pct:.1f}% = ${surcharge:,.2f}"
            "  ← always applied (tariff standing surcharge)"
        ))
        if detention_hours > 0:
            calc_steps.append((
                f"Detention ({detention_hours:.1f} hrs)",
                f"{detention_hours:.1f} hrs × ${zone.detention_per_hour:,.0f}/hr = ${det_charge:,.2f}"
            ))
        if detention_hours > 0:
            calc_steps.append((
                "Zone total",
                f"${gross:,.2f} + ${surcharge:,.2f} surcharge + ${det_charge:,.2f} detention = ${total:,.2f}"
            ))
        else:
            calc_steps.append((
                "Zone total",
                f"${gross:,.2f} + ${surcharge:,.2f} surcharge = ${total:,.2f}"
            ))

        items.append(PilotageLineItem(
            association=zone.association,
            zone_name=zone.name,
            rate_type=DRAFT_PER_FOOT,
            rate_basis_description=(
                f"${zone.rate_per_foot:.2f}/ft × {draft_ft:.1f} ft draft "
                f"(min ${zone.min_charge:,.0f}) + {zone.surcharge_pct:.0f}% standing surcharge"
            ),
            gross_charge=gross,
            surcharge_pct=zone.surcharge_pct,
            surcharge_amount=surcharge,
            detention_hours=detention_hours,
            detention_charge=det_charge,
            total=total,
            direction=d,
            confidence="medium",
            source=f"2024/2025 tariff card — verify at {zone.tariff_url}",
            min_charge_applied=min_applied,
            calc_steps=calc_steps,
        ))

    return items


# ---------------------------------------------------------------------------
# Surcharge helpers
# ---------------------------------------------------------------------------

def _is_night(t: dt.datetime) -> bool:
    """True if time is between 22:00 and 06:00 (standard US pilot night window)."""
    return t.hour >= 22 or t.hour < 6


def _is_weekend(t: dt.datetime) -> bool:
    """True if Saturday (5) or Sunday (6)."""
    return t.weekday() >= 5


def _parse_draft_threshold_ft(notes: str) -> Optional[float]:
    """Extract draft threshold in feet from surcharge notes string."""
    m = re.search(r"over\s+(\d+(?:\.\d+)?)\s*f(?:ee)?t", notes, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"over\s+(\d+(?:\.\d+)?)\s*m", notes, re.I)
    if m:
        return float(m.group(1)) * 3.28084
    return None


def _apply_surcharges(
    assoc: dict,
    direction: str,
    arrival: Optional[dt.datetime],
    departure: Optional[dt.datetime],
    arrival_draft_ft: Optional[float],
    departure_draft_ft: Optional[float],
    port: Optional[str],
) -> list[PilotageLineItem]:
    """
    Evaluate catalog surcharges for a GRT-tier association.

    KEY LOGIC — each surcharge is evaluated per direction:
      • Night/weekend: applied to INBOUND if arrival is night; OUTBOUND if departure is night.
        If departure_datetime not provided, outbound night surcharge is NOT applied (warn).
      • Deep draft: applied to INBOUND if arrival_draft_ft > threshold;
                    OUTBOUND if departure_draft_ft > threshold.
                    If departure_draft_ft not provided, use arrival_draft_ft for outbound too
                    (conservative — same draft assumption), with a warning.
      • Chesapeake Bay Transit: outbound only.
      • James River segment: both directions, named ports only.
      • Shifting/maneuvering: NOT auto-applied — requires explicit user input.
    """
    items: list[PilotageLineItem] = []

    # Determine which directions we're handling
    all_dirs = ["inbound", "outbound"] if direction == "both" else [direction]

    for surchg in assoc.get("surcharges", []):
        stype = surchg.get("type", "").lower()
        amount = surchg.get("amount_usd")
        notes = surchg.get("notes", "")

        if amount is None:
            continue

        # ── Night / Weekend ───────────────────────────────────────────────────
        if any(kw in stype for kw in ("night", "weekend", "after hours", "off hours")):
            for d in all_dirs:
                if d == "inbound":
                    event_dt = arrival
                    label_when = f"arrival {arrival.strftime('%H:%M')}" if arrival else "n/a"
                else:
                    event_dt = departure
                    label_when = f"departure {departure.strftime('%H:%M')}" if departure else "n/a"

                if event_dt is None:
                    # Can't evaluate without the datetime for this direction
                    continue

                is_nt = _is_night(event_dt)
                is_we = _is_weekend(event_dt)
                if not (is_nt or is_we):
                    continue  # Not applicable — daytime weekday

                reasons = []
                if is_nt:
                    reasons.append(f"night ({event_dt.strftime('%H:%M')} is after 22:00)")
                if is_we:
                    reasons.append(f"weekend ({event_dt.strftime('%A')})")
                reason_str = " + ".join(reasons)
                label = surchg.get("type", "Night/Weekend Surcharge")

                calc_steps: list[tuple[str, str]] = [
                    ("Condition",  f"{label} — triggers when movement is night or weekend"),
                    ("Movement",   f"{d.upper()} — {label_when}"),
                    ("Triggered?", f"YES — {reason_str}"),
                    ("Rate",       f"${amount:,.2f} flat per movement"),
                    ("Total",      f"${amount:,.2f}"),
                ]

                items.append(PilotageLineItem(
                    association=assoc["name"],
                    zone_name=label,
                    rate_type="surcharge",
                    rate_basis_description=f"${amount:,.0f} flat — {notes}",
                    gross_charge=amount,
                    surcharge_pct=0.0,
                    surcharge_amount=0.0,
                    detention_hours=0.0,
                    detention_charge=0.0,
                    total=amount,
                    direction=d,
                    confidence=assoc.get("confidence", "medium"),
                    source="catalog",
                    calc_steps=calc_steps,
                ))

        # ── Deep Draft ────────────────────────────────────────────────────────
        elif any(kw in stype for kw in ("deep draft", "draft surcharge", "deep")):
            threshold = _parse_draft_threshold_ft(notes)
            if threshold is None:
                continue

            for d in all_dirs:
                if d == "inbound":
                    draft_for_dir = arrival_draft_ft
                else:
                    # Use departure_draft_ft if given, else fall back to arrival_draft_ft
                    draft_for_dir = departure_draft_ft if departure_draft_ft is not None else arrival_draft_ft

                if draft_for_dir is None or draft_for_dir <= threshold:
                    continue

                label = surchg.get("type", "Deep Draft Surcharge")
                note_str = (
                    f"Draft {draft_for_dir:.1f} ft > {threshold:.0f} ft threshold — ${amount:,.0f} flat"
                )
                calc_steps = [
                    ("Threshold",    f"{threshold:.0f} ft (per tariff schedule)"),
                    (f"Vessel draft ({d})", f"{draft_for_dir:.1f} ft"),
                    ("Triggered?",   f"YES — {draft_for_dir:.1f} ft > {threshold:.0f} ft threshold"),
                    ("Rate",         f"${amount:,.2f} flat per movement"),
                    ("Total",        f"${amount:,.2f}"),
                ]

                if departure_draft_ft is None and d == "outbound":
                    calc_steps.append((
                        "Note",
                        "departure_draft_ft not provided — using arrival draft for outbound. "
                        "Provide departure_draft_ft= if vessel is lighter on departure."
                    ))

                items.append(PilotageLineItem(
                    association=assoc["name"],
                    zone_name=f"{label} (>{threshold:.0f} ft)",
                    rate_type="surcharge",
                    rate_basis_description=note_str,
                    gross_charge=amount,
                    surcharge_pct=0.0,
                    surcharge_amount=0.0,
                    detention_hours=0.0,
                    detention_charge=0.0,
                    total=amount,
                    direction=d,
                    confidence=assoc.get("confidence", "medium"),
                    source="catalog",
                    calc_steps=calc_steps,
                ))

        # ── Chesapeake Bay Transit (Virginia Pilots — outbound only) ──────────
        elif "chesapeake" in stype or "bay transit" in stype:
            out_dirs = [d for d in all_dirs if d == "outbound"]
            if not out_dirs:
                continue
            label = surchg.get("type", "Chesapeake Bay Transit")
            for d in out_dirs:
                items.append(PilotageLineItem(
                    association=assoc["name"],
                    zone_name=label,
                    rate_type="surcharge",
                    rate_basis_description=f"${amount:,.0f} — {notes}",
                    gross_charge=amount,
                    surcharge_pct=0.0,
                    surcharge_amount=0.0,
                    detention_hours=0.0,
                    detention_charge=0.0,
                    total=amount,
                    direction=d,
                    confidence=assoc.get("confidence", "medium"),
                    source="catalog",
                    calc_steps=[
                        ("Condition", "Chesapeake Bay Transit — outbound only"),
                        ("Applied?",  "YES — outbound movement from Hampton Roads to sea"),
                        ("Rate",      f"${amount:,.2f} flat"),
                    ],
                ))

        # ── James River / Named Segment ────────────────────────────────────────
        elif "james river" in stype or "segment" in stype:
            james_river_ports = {"richmond", "hopewell", "chester", "bermuda hundred"}
            if not port or port.lower().strip() not in james_river_ports:
                continue
            label = surchg.get("type", "James River Segment")
            for d in all_dirs:
                items.append(PilotageLineItem(
                    association=assoc["name"],
                    zone_name=label,
                    rate_type="surcharge",
                    rate_basis_description=f"${amount:,.0f} — {notes}",
                    gross_charge=amount,
                    surcharge_pct=0.0,
                    surcharge_amount=0.0,
                    detention_hours=0.0,
                    detention_charge=0.0,
                    total=amount,
                    direction=d,
                    confidence=assoc.get("confidence", "medium"),
                    source="catalog",
                    calc_steps=[
                        ("Condition", f"James River segment — port: {port}"),
                        ("Applied?",  "YES — berth is on James River above Hampton Roads"),
                        ("Rate",      f"${amount:,.2f} flat per direction"),
                    ],
                ))

        # ── Shifting / Maneuvering — NOT auto-applied ─────────────────────────
        elif any(kw in stype for kw in ("shifting", "maneuvering", "manoeuvring")):
            continue  # User must request shifting explicitly as additional movements

    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_pilotage(
    port: Optional[str] = None,
    route: Optional[str] = None,
    vessel_imo: Optional[str] = None,
    vessel_grt: Optional[int] = None,
    vessel_loa: Optional[float] = None,
    vessel_draft_ft: Optional[float] = None,    # Arrival (inbound) draft
    departure_draft_ft: Optional[float] = None, # Departure (outbound) draft — may differ
    vessel_draft_m: Optional[float] = None,     # Auto-converted to ft
    movements: int = 2,
    direction: str = "both",
    detention_hours: float = 0.0,
    arrival_datetime: Optional[dt.datetime] = None,
    departure_datetime: Optional[dt.datetime] = None,
    force_web_lookup: bool = False,
) -> PilotageResult:
    """Calculate compulsory pilotage cost for a port call or river transit.

    Parameters
    ----------
    port : str, optional
        Port name — e.g. "New Orleans", "Houston", "Savannah".
        If a Mississippi River port, route is inferred automatically.
    route : str, optional
        Explicit Mississippi River route key: "sea_to_nola" | "sea_to_br" | etc.
        Overrides port-based route inference.
    vessel_imo : str, optional
        IMO number — triggers automatic vessel parameter lookup.
    vessel_grt : int, optional
        Registered Gross Tonnage. Required for GRT-tier ports.
    vessel_draft_ft : float, optional
        ARRIVAL (inbound) draft in feet. Required for Mississippi River.
    departure_draft_ft : float, optional
        DEPARTURE (outbound) draft in feet. Often different from arrival.
        If not provided, arrival draft is used for outbound (conservative).
    vessel_draft_m : float, optional
        Draft in metres — auto-converted to feet.
    movements : int
        Total pilotage movements. Default 2 (inbound + outbound).
    direction : str
        "both" | "inbound" | "outbound"
    detention_hours : float
        Pilot waiting-time per zone (hours). Default 0.
    arrival_datetime : datetime, optional
        Vessel arrival — evaluated for night/weekend surcharge on INBOUND move.
    departure_datetime : datetime, optional
        Vessel departure — evaluated for night/weekend surcharge on OUTBOUND move.
        If not provided, outbound night surcharge is NOT applied (with warning).
    force_web_lookup : bool
        Force web lookup for vessel data.

    Returns
    -------
    PilotageResult
    """
    warnings: list[str] = []

    # ── Step 1: Resolve vessel parameters ─────────────────────────────────────
    vessel_params: Optional[VesselParams] = None

    if vessel_draft_m and not vessel_draft_ft:
        vessel_draft_ft = round(vessel_draft_m * 3.28084, 2)

    if vessel_imo:
        try:
            vessel_params = resolve_vessel(
                imo=vessel_imo,
                grt=vessel_grt,
                draft_m=(vessel_draft_ft / 3.28084) if vessel_draft_ft else vessel_draft_m,
                loa_m=vessel_loa,
                force_web=force_web_lookup,
            )
            if vessel_grt is None and vessel_params.grt:
                vessel_grt = vessel_params.grt
            if vessel_draft_ft is None and vessel_params.draft_ft:
                vessel_draft_ft = vessel_params.draft_ft
            warnings.extend(vessel_params.warnings)
        except VesselNotFoundError as e:
            warnings.append(str(e))

    vessel_name = vessel_params.name if vessel_params else None

    # Warning when departure_datetime not provided for "both" direction
    if direction == "both" and departure_datetime is None:
        warnings.append(
            "departure_datetime not provided — outbound night/weekend surcharges NOT applied. "
            "Provide departure_datetime= for a complete and accurate estimate."
        )

    # ── Step 2: Determine if Mississippi River route applies ───────────────────
    effective_route: Optional[str] = route

    if effective_route is None and port:
        effective_route = MISS_PORT_ROUTES.get(port.lower().strip())

    is_miss_river = effective_route is not None
    assoc: Optional[dict] = None

    # ── Step 3: Build result skeleton ─────────────────────────────────────────
    result = PilotageResult(
        port=port,
        route=effective_route,
        vessel_imo=vessel_imo,
        vessel_name=vessel_name,
        vessel_grt=vessel_grt,
        vessel_draft_ft=vessel_draft_ft,
        departure_draft_ft=departure_draft_ft,
        movements=movements,
        direction=direction,
        arrival_datetime=arrival_datetime,
        departure_datetime=departure_datetime,
        warnings=warnings,
    )

    # ── Step 4a: Mississippi River — draft-per-foot, zone-by-zone ─────────────
    if is_miss_river:
        if vessel_draft_ft is None:
            result.warnings.append(
                "Vessel draft (feet) required for Mississippi River pilotage. "
                "Provide vessel_draft_ft= or vessel_imo= to auto-resolve."
            )
            result.overall_confidence = "low"
            return result

        zone_ids = MISS_ROUTE_TEMPLATES.get(effective_route, [])
        if not zone_ids:
            result.warnings.append(
                f"Unknown Mississippi route '{effective_route}'. "
                f"Valid: {', '.join(MISS_ROUTE_TEMPLATES.keys())}"
            )
            result.overall_confidence = "low"
            return result

        # For Mississippi outbound, use departure_draft_ft if provided, else arrival_draft_ft
        inb_draft = vessel_draft_ft
        out_draft = departure_draft_ft if departure_draft_ft is not None else vessel_draft_ft
        if departure_draft_ft is None and direction == "both":
            result.warnings.append(
                f"departure_draft_ft not provided — using arrival draft ({vessel_draft_ft:.2f} ft) "
                "for outbound Mississippi River legs. "
                "Provide departure_draft_ft= if vessel will be lighter on departure."
            )

        for zone_id in zone_ids:
            zone = MISS_ZONES[zone_id]
            # Inbound items
            if direction in ("both", "inbound"):
                items_in = _calc_draft_per_foot(zone, inb_draft, "inbound", detention_hours)
                result.line_items.extend(items_in)
            # Outbound items (may use different draft)
            if direction in ("both", "outbound"):
                items_out = _calc_draft_per_foot(zone, out_draft, "outbound", detention_hours)
                result.line_items.extend(items_out)

        if vessel_grt and vessel_grt > 50000:
            result.warnings.append(
                f"Vessel GRT {vessel_grt:,} — very large for Mississippi River. "
                "Verify with pilot associations for any large-vessel surcharges."
            )

    # ── Step 4b: Standard port call — GRT-tier ────────────────────────────────
    else:
        if vessel_grt is None:
            result.warnings.append(
                "Vessel GRT required for port pilotage. "
                "Provide vessel_grt= or vessel_imo= to auto-resolve."
            )
            result.overall_confidence = "low"
            return result

        if port is None:
            result.warnings.append("Port name required for GRT-tier pilotage lookup.")
            result.overall_confidence = "low"
            return result

        assoc = _resolve_port_to_assoc(port)
        if assoc is None:
            result.warnings.append(
                f"Port '{port}' not found in pilot associations catalog. "
                "Check spelling or add the association to pilot_associations_catalog.json."
            )
            result.overall_confidence = "low"
            return result

        if not assoc.get("grt_tiers"):
            result.warnings.append(
                f"No GRT tier data for {assoc['name']} — confidence: low. "
                "Pull current tariff from association website."
            )
            result.overall_confidence = "low"
            result.line_items = []
            return result

        items = _calc_grt_tier(assoc, vessel_grt, movements, direction, detention_hours)
        result.line_items.extend(items)

    # ── Step 5: Surcharges (GRT-tier ports only — Miss River handles own %) ────
    if not is_miss_river and assoc:
        surchg_items = _apply_surcharges(
            assoc=assoc,
            direction=direction,
            arrival=arrival_datetime,
            departure=departure_datetime,
            arrival_draft_ft=vessel_draft_ft,
            departure_draft_ft=departure_draft_ft,
            port=port,
        )
        result.line_items.extend(surchg_items)

    # ── Step 6: Roll-up totals ─────────────────────────────────────────────────
    result.subtotal_inbound = round(
        sum(li.total for li in result.line_items if li.direction == "inbound"), 2
    )
    result.subtotal_outbound = round(
        sum(li.total for li in result.line_items if li.direction == "outbound"), 2
    )
    result.pilotage_total = round(result.subtotal_inbound + result.subtotal_outbound, 2)

    # ── Step 7: Overall confidence ─────────────────────────────────────────────
    confidences = [li.confidence for li in result.line_items]
    if all(c == "high" for c in confidences):
        result.overall_confidence = "high"
    elif any(c == "low" for c in confidences) or result.warnings:
        result.overall_confidence = "medium"
    else:
        result.overall_confidence = "medium"

    return result


# ---------------------------------------------------------------------------
# Utility / introspection
# ---------------------------------------------------------------------------

def list_associations() -> list[dict]:
    """Return all pilot associations from catalog (summary view)."""
    catalog = _load_catalog()
    return [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "ports": a.get("ports", []),
            "state": a.get("state"),
            "coast": a.get("coast"),
            "rate_basis": a.get("rate_basis"),
            "confidence": a.get("confidence"),
            "tariff_found": bool(a.get("grt_tiers")),
            "website": a.get("website"),
        }
        for a in catalog.get("associations", [])
    ]


def list_routes() -> list[dict]:
    """Return all Mississippi River route templates with zone detail."""
    return [
        {
            "route": name,
            "zones": [
                {
                    "zone_id": zid,
                    "association": MISS_ZONES[zid].association,
                    "name": MISS_ZONES[zid].name,
                    "rate_per_foot": MISS_ZONES[zid].rate_per_foot,
                    "min_charge": MISS_ZONES[zid].min_charge,
                    "surcharge_pct": MISS_ZONES[zid].surcharge_pct,
                    "detention_per_hour": MISS_ZONES[zid].detention_per_hour,
                    "cancellation_fee": MISS_ZONES[zid].cancellation_fee,
                }
                for zid in zone_ids
            ],
        }
        for name, zone_ids in MISS_ROUTE_TEMPLATES.items()
    ]


def estimate_from_dwt(dwt: int, vessel_type: str = "bulk_carrier") -> dict:
    """Estimate GRT and draft from DWT. Use only when actual data unavailable."""
    ratios = {
        "bulk_carrier":  {"grt_per_dwt": 0.62, "draft_m_per_10k_dwt": 1.35, "base_draft_m": 5.0},
        "tanker":        {"grt_per_dwt": 0.58, "draft_m_per_10k_dwt": 1.40, "base_draft_m": 5.5},
        "containership": {"grt_per_dwt": 1.10, "draft_m_per_10k_dwt": 1.25, "base_draft_m": 6.0},
        "general_cargo": {"grt_per_dwt": 0.75, "draft_m_per_10k_dwt": 1.20, "base_draft_m": 4.5},
    }
    r = ratios.get(vessel_type, ratios["bulk_carrier"])
    est_grt = int(dwt * r["grt_per_dwt"])
    est_draft_m = round(r["base_draft_m"] + (dwt / 10_000) * r["draft_m_per_10k_dwt"], 1)
    return {
        "input_dwt": dwt,
        "vessel_type": vessel_type,
        "estimated_grt": est_grt,
        "estimated_draft_m": est_draft_m,
        "estimated_draft_ft": round(est_draft_m * 3.28084, 1),
        "confidence": "low",
        "warning": "Estimated from DWT ratio — use actual vessel data for accurate pilotage calc",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import datetime as dt

    print("\n" + "="*73)
    print("  EXAMPLE 1: New Orleans via sea — 39.4 ft draft — both directions")
    print("="*73)
    r1 = calculate_pilotage(
        port="New Orleans",
        vessel_grt=35_000,
        vessel_draft_ft=39.4,
        departure_draft_ft=24.0,    # ballast after discharging
        direction="both",
    )
    r1.print_math_check()

    print("\n" + "="*73)
    print("  EXAMPLE 2: Houston — night arrival, daytime departure, deep draft")
    print("="*73)
    r2 = calculate_pilotage(
        port="Houston",
        vessel_grt=35_000,
        vessel_draft_ft=41.5,          # loaded inbound — over 40 ft threshold
        departure_draft_ft=22.0,        # ballast outbound — below threshold
        direction="both",
        arrival_datetime=dt.datetime(2025, 3, 8, 23, 0),    # night
        departure_datetime=dt.datetime(2025, 3, 10, 10, 0), # daytime
    )
    r2.print_math_check()
