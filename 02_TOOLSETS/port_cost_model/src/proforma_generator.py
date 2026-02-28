"""Proforma port cost estimate generator.

Aggregates pilotage, towage, port tariffs (dockage, wharfage, harbour dues),
stevedoring, and ancillary costs into a complete proforma estimate for a
vessel port call. This is the standard format used in ship agency and
chartering to estimate voyage costs.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

from port_cost_model.src.pilotage_calculator import (
    PilotageEstimate,
    calculate_route_pilotage,
)
from port_cost_model.src.port_tariff_engine import (
    PortCharges,
    calculate_port_charges,
)
from port_cost_model.src.stevedoring_model import (
    StevedoringEstimate,
    calculate_stevedoring,
)
from port_cost_model.src.towage_calculator import (
    TowageEstimate,
    calculate_towage,
)


# ---------------------------------------------------------------------------
# Ancillary cost defaults
# ---------------------------------------------------------------------------

@dataclass
class AncillaryCosts:
    """Miscellaneous port call costs."""
    agency_fee: float = 3_500.0
    customs_clearance: float = 750.0
    immigration: float = 250.0
    quarantine: float = 200.0
    surveyor_fees: float = 1_500.0
    communications: float = 300.0
    garbage_removal: float = 400.0
    launch_service: float = 500.0
    canal_transit: float = 0.0
    bunker_delivery: float = 0.0
    misc: float = 500.0

    @property
    def total(self) -> float:
        return (
            self.agency_fee + self.customs_clearance + self.immigration
            + self.quarantine + self.surveyor_fees + self.communications
            + self.garbage_removal + self.launch_service
            + self.canal_transit + self.bunker_delivery + self.misc
        )


# ---------------------------------------------------------------------------
# Proforma dataclass
# ---------------------------------------------------------------------------

@dataclass
class PortProforma:
    """Complete proforma port cost estimate."""
    # Header
    vessel_name: str
    port: str
    cargo_type: str
    cargo_tons: float
    estimated_date: str = ""

    # Vessel particulars
    vessel_loa_feet: float = 0.0
    vessel_beam_feet: float = 0.0
    vessel_draft_feet: float = 0.0
    vessel_gt: int = 0
    vessel_nrt: int = 0
    vessel_dwt: int = 0
    vessel_flag: str = ""
    vessel_type: str = ""

    # Cost components
    pilotage: PilotageEstimate | None = None
    towage: TowageEstimate | None = None
    port_charges: PortCharges | None = None
    stevedoring: StevedoringEstimate | None = None
    ancillary: AncillaryCosts = field(default_factory=AncillaryCosts)

    # Totals
    total_port_cost: float = 0.0
    cost_per_ton: float = 0.0

    # Metadata
    prepared_by: str = "US Bulk Supply Chain Reporting Platform"
    currency: str = "USD"
    notes: list[str] = field(default_factory=list)

    def compute_totals(self) -> None:
        """Recalculate totals from components."""
        self.total_port_cost = (
            (self.pilotage.total_pilotage if self.pilotage else 0.0)
            + (self.towage.total if self.towage else 0.0)
            + (self.port_charges.total if self.port_charges else 0.0)
            + (self.stevedoring.total if self.stevedoring else 0.0)
            + self.ancillary.total
        )
        if self.cargo_tons > 0:
            self.cost_per_ton = round(self.total_port_cost / self.cargo_tons, 2)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a flat dictionary for reporting."""
        d: dict[str, Any] = {
            "vessel_name": self.vessel_name,
            "port": self.port,
            "cargo_type": self.cargo_type,
            "cargo_tons": self.cargo_tons,
            "vessel_loa_feet": self.vessel_loa_feet,
            "vessel_draft_feet": self.vessel_draft_feet,
            "vessel_gt": self.vessel_gt,
            "vessel_dwt": self.vessel_dwt,
            "vessel_flag": self.vessel_flag,
            "pilotage_total": self.pilotage.total_pilotage if self.pilotage else 0,
            "towage_total": self.towage.total if self.towage else 0,
            "port_charges_total": self.port_charges.total if self.port_charges else 0,
            "stevedoring_total": self.stevedoring.total if self.stevedoring else 0,
            "ancillary_total": self.ancillary.total,
            "total_port_cost": self.total_port_cost,
            "cost_per_ton": self.cost_per_ton,
            "currency": self.currency,
        }
        return d


# ---------------------------------------------------------------------------
# Proforma generation
# ---------------------------------------------------------------------------

# Map port keys to default pilotage routes
_PORT_PILOTAGE_MAP: dict[str, str] = {
    "new_orleans": "sea_to_nola",
    "baton_rouge": "sea_to_br",
    "houston": "sea_to_houston",
    "lake_charles": "sea_to_lake_charles",
    "mobile": "sea_to_mobile",
    "tampa": "sea_to_tampa",
    "norfolk": "sea_to_norfolk",
}


def generate_proforma(
    vessel_name: str,
    port: str,
    cargo_type: str,
    cargo_tons: float,
    vessel_loa_feet: float,
    vessel_draft_feet: float,
    vessel_gt: int,
    vessel_dwt: int = 0,
    vessel_flag: str = "Foreign",
    vessel_type: str = "bulk_carrier",
    days_alongside: float = 3.0,
    pilotage_route: str | None = None,
    pilotage_direction: str = "both",
    num_tugs: int | None = None,
    handling_method: str | None = None,
    overtime_hours: float = 0.0,
    fresh_water_tons: float = 0.0,
    custom_ancillary: AncillaryCosts | None = None,
) -> PortProforma:
    """Generate a complete proforma port cost estimate.

    Parameters
    ----------
    vessel_name : str
        Name of the vessel.
    port : str
        Port key (e.g. ``"new_orleans"``, ``"houston"``).
    cargo_type : str
        Cargo type for wharfage and stevedoring (e.g. ``"cement"``).
    cargo_tons : float
        Cargo quantity in short tons.
    vessel_loa_feet, vessel_draft_feet, vessel_gt, vessel_dwt : numeric
        Vessel particulars.
    vessel_flag : str
        Flag state (pilotage is compulsory for foreign flag).
    days_alongside : float
        Expected berth occupancy in days.
    pilotage_route : str, optional
        Override pilotage route. If None, auto-selected from port.
    pilotage_direction : str
        ``"inbound"``, ``"outbound"``, or ``"both"``.
    num_tugs : int, optional
        Override number of tugs.
    handling_method : str, optional
        Stevedoring handling method override.
    overtime_hours : float
        Overtime labour hours for stevedoring.
    fresh_water_tons : float
        Fresh water delivered.
    custom_ancillary : AncillaryCosts, optional
        Override default ancillary costs.
    """
    port_key = port.lower().replace(" ", "_")

    # 1. Pilotage
    route = pilotage_route or _PORT_PILOTAGE_MAP.get(port_key, port_key)
    try:
        pilotage = calculate_route_pilotage(
            route, vessel_draft_feet, pilotage_direction
        )
    except Exception:
        pilotage = None

    # 2. Towage
    try:
        towage = calculate_towage(
            port, vessel_gt, num_tugs=num_tugs, movements=2
        )
    except Exception:
        towage = None

    # 3. Port charges
    try:
        port_charges = calculate_port_charges(
            port=port,
            vessel_loa_feet=vessel_loa_feet,
            vessel_gt=vessel_gt,
            cargo_type=cargo_type,
            cargo_tons=cargo_tons,
            days_alongside=days_alongside,
            fresh_water_tons=fresh_water_tons,
        )
    except Exception:
        port_charges = None

    # 4. Stevedoring
    try:
        stevedoring = calculate_stevedoring(
            cargo_type=cargo_type,
            cargo_tons=cargo_tons,
            handling_method=handling_method,
            overtime_hours=overtime_hours,
        )
    except Exception:
        stevedoring = None

    # 5. Ancillary
    ancillary = custom_ancillary or AncillaryCosts()

    # Assemble proforma
    pf = PortProforma(
        vessel_name=vessel_name,
        port=port,
        cargo_type=cargo_type,
        cargo_tons=cargo_tons,
        estimated_date=dt.date.today().isoformat(),
        vessel_loa_feet=vessel_loa_feet,
        vessel_draft_feet=vessel_draft_feet,
        vessel_gt=vessel_gt,
        vessel_dwt=vessel_dwt,
        vessel_flag=vessel_flag,
        vessel_type=vessel_type,
        pilotage=pilotage,
        towage=towage,
        port_charges=port_charges,
        stevedoring=stevedoring,
        ancillary=ancillary,
    )
    pf.compute_totals()

    return pf


def format_proforma_text(pf: PortProforma) -> str:
    """Format a proforma as human-readable text."""
    lines = [
        "=" * 70,
        "PROFORMA PORT COST ESTIMATE",
        "=" * 70,
        "",
        f"  Port:            {pf.port}",
        f"  Date:            {pf.estimated_date}",
        f"  Currency:        {pf.currency}",
        "",
        "VESSEL PARTICULARS",
        "-" * 40,
        f"  Name:            {pf.vessel_name}",
        f"  Flag:            {pf.vessel_flag}",
        f"  Type:            {pf.vessel_type}",
        f"  LOA:             {pf.vessel_loa_feet:,.0f} ft",
        f"  Draft:           {pf.vessel_draft_feet:,.1f} ft",
        f"  GT:              {pf.vessel_gt:,}",
        f"  DWT:             {pf.vessel_dwt:,}",
        "",
        "CARGO",
        "-" * 40,
        f"  Type:            {pf.cargo_type}",
        f"  Quantity:        {pf.cargo_tons:,.0f} tons",
        "",
        "COST BREAKDOWN",
        "-" * 40,
    ]

    if pf.pilotage:
        lines.append(f"  Pilotage:        ${pf.pilotage.total_pilotage:>12,.2f}")
        for zc in pf.pilotage.zone_charges:
            lines.append(f"    - {zc.zone.name}: ${zc.total:,.2f}")
    else:
        lines.append("  Pilotage:        N/A")

    if pf.towage:
        lines.append(f"  Towage:          ${pf.towage.total:>12,.2f}")
        lines.append(f"    ({pf.towage.num_tugs} tugs x {pf.towage.movements} movements)")
    else:
        lines.append("  Towage:          N/A")

    if pf.port_charges:
        lines.append(f"  Port Charges:    ${pf.port_charges.total:>12,.2f}")
        lines.append(f"    Dockage:       ${pf.port_charges.dockage:>12,.2f}")
        lines.append(f"    Wharfage:      ${pf.port_charges.wharfage:>12,.2f}")
        lines.append(f"    Harbour dues:  ${pf.port_charges.harbour_dues:>12,.2f}")
        lines.append(f"    Line handling: ${pf.port_charges.line_handling:>12,.2f}")
        lines.append(f"    Security:      ${pf.port_charges.security_fee:>12,.2f}")
    else:
        lines.append("  Port Charges:    N/A")

    if pf.stevedoring:
        lines.append(f"  Stevedoring:     ${pf.stevedoring.total:>12,.2f}")
        lines.append(f"    Rate:          ${pf.stevedoring.rate_per_ton}/ton")
        lines.append(f"    Est. hours:    {pf.stevedoring.estimated_hours:.1f}")
    else:
        lines.append("  Stevedoring:     N/A")

    lines.append(f"  Ancillary:       ${pf.ancillary.total:>12,.2f}")
    lines.extend([
        "",
        "=" * 40,
        f"  TOTAL PORT COST: ${pf.total_port_cost:>12,.2f}",
        f"  COST PER TON:    ${pf.cost_per_ton:>12,.2f}",
        "=" * 40,
        "",
        f"  Prepared by: {pf.prepared_by}",
    ])

    return "\n".join(lines)
