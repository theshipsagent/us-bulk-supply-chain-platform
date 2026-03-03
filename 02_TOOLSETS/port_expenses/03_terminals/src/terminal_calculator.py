"""
US Port Terminal Cost Calculator
=================================
Calculates terminal charges for a vessel port call:

  Stevedoring
  -----------
  - Labour:    rate_per_ST × cargo_tonnes × regional_multiplier
  - Equipment: equipment_per_hour × estimated_hours × regional_multiplier
  - Overtime:  +overtime_pct on labour + equipment when night/weekend arrival

  Port Authority Charges
  ----------------------
  - Dockage:        $/LOA-ft/day  × LOA(ft) × days_in_berth
  - Wharfage:       $/ST × cargo_tonnes  (commodity-specific)
  - Harbour dues:   $/GT × vessel_GRT
  - Line handling:  $/operation  (arrival + departure = 2 ops)
  - Security fee:   flat $/call (ISPS)
  - Fresh water:    $/MT × MT delivered (optional)

Data Sources
------------
  data/port_authority_tariffs.json  — 11 US Gulf/Atlantic ports
  data/stevedoring_rates.json       — 13 cargo/method combinations

Usage
-----
    from terminal_calculator import calculate_terminal_costs

    result = calculate_terminal_costs(
        port="New Orleans",
        commodity="grain",
        cargo_tonnes=50000.0,
        vessel_loa=225.0,    # metres
        vessel_grt=35000,
    )
    result.print_summary()

    # Night arrival triggers overtime
    import datetime as dt
    result = calculate_terminal_costs(
        port="Houston",
        commodity="steel coils",
        cargo_tonnes=8000.0,
        vessel_loa=195.0,
        vessel_grt=28000,
        arrival_datetime=dt.datetime(2025, 3, 8, 22, 0),
    )
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
_PORT_TARIFFS_FILE = _DATA_DIR / "port_authority_tariffs.json"
_STEV_RATES_FILE = _DATA_DIR / "stevedoring_rates.json"

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
    logger.warning("vessel_resolver not available — IMO lookup disabled for terminal calculator")


# ---------------------------------------------------------------------------
# Commodity → rate key mapping
# ---------------------------------------------------------------------------

# (stevedoring_rate_key, wharfage_rate_key)
_COMMODITY_MAP: dict[str, tuple[str, str]] = {
    "grain":            ("grain_elevator",   "grain"),
    "wheat":            ("grain_elevator",   "grain"),
    "corn":             ("grain_elevator",   "grain"),
    "soybeans":         ("grain_elevator",   "grain"),
    "sorghum":          ("grain_elevator",   "grain"),
    "barley":           ("grain_elevator",   "grain"),
    "coal":             ("coal_grab",        "coal"),
    "petcoke":          ("coal_grab",        "coal"),
    "coke":             ("coal_grab",        "coal"),
    "cement":           ("cement_pneumatic", "cement"),
    "clinker":          ("cement_grab",      "cement"),
    "fly ash":          ("cement_pneumatic", "cement"),
    "slag":             ("cement_pneumatic", "cement"),
    "fertilizer":       ("fertilizer_grab",  "fertilizer"),
    "urea":             ("fertilizer_grab",  "fertilizer"),
    "dap":              ("fertilizer_grab",  "fertilizer"),
    "map":              ("fertilizer_grab",  "fertilizer"),
    "potash":           ("fertilizer_grab",  "fertilizer"),
    "ammonium":         ("fertilizer_grab",  "fertilizer"),
    "phosphate":        ("phosphate_grab",   "phosphate"),
    "phosphate rock":   ("phosphate_grab",   "phosphate"),
    "salt":             ("bulk_dry_general", "bulk_dry"),
    "sand":             ("bulk_dry_general", "bulk_dry"),
    "gravel":           ("bulk_dry_general", "bulk_dry"),
    "sulphur":          ("bulk_dry_general", "bulk_dry"),
    "rock":             ("bulk_dry_general", "bulk_dry"),
    "bulk_dry":         ("bulk_dry_general", "bulk_dry"),
    "steel coils":      ("steel_coils",      "steel"),
    "coils":            ("steel_coils",      "steel"),
    "steel_coils":      ("steel_coils",      "steel"),
    "hot rolled":       ("steel_coils",      "steel"),
    "cold rolled":      ("steel_coils",      "steel"),
    "steel plate":      ("steel_plate",      "steel"),
    "plate":            ("steel_plate",      "steel"),
    "steel_plate":      ("steel_plate",      "steel"),
    "rebar":            ("steel_rebar",      "steel"),
    "wire rod":         ("steel_rebar",      "steel"),
    "steel_rebar":      ("steel_rebar",      "steel"),
    "steel":            ("steel_coils",      "steel"),    # default steel → coils
    "breakbulk":        ("breakbulk_general","breakbulk"),
    "bagged":           ("breakbulk_general","breakbulk"),
    "project":          ("project_cargo",    "breakbulk"),
    "heavy lift":       ("project_cargo",    "breakbulk"),
    "oog":              ("project_cargo",    "breakbulk"),
    "liquid":           ("liquid_bulk",      "bulk_liquid"),
    "petroleum":        ("liquid_bulk",      "bulk_liquid"),
    "chemicals":        ("liquid_bulk",      "bulk_liquid"),
    "vegetable oil":    ("liquid_bulk",      "bulk_liquid"),
    "molasses":         ("liquid_bulk",      "bulk_liquid"),
    "liquid_bulk":      ("liquid_bulk",      "bulk_liquid"),
    "containers":       ("containers",       "containers"),
    "teu":              ("containers",       "containers"),
    "container":        ("containers",       "containers"),
}

# Port coast string → stevedoring regional_adjustments key
_COAST_TO_REGION: dict[str, str] = {
    "gulf":             "gulf_coast",
    "gulf coast":       "gulf_coast",
    "east coast south": "east_coast_south",
    "se":               "east_coast_south",
    "southeast":        "east_coast_south",
    "east coast mid":   "east_coast_mid",
    "mid atlantic":     "east_coast_mid",
    "mid-atlantic":     "east_coast_mid",
    "northeast":        "northeast",
    "ne":               "northeast",
    "pacific":          "pacific_coast",
    "pacific coast":    "pacific_coast",
    "west coast":       "pacific_coast",
    "great lakes":      "great_lakes",
    # Specific values used in port_authority_tariffs.json
    "southeast":        "east_coast_south",
    "mid-atlantic":     "east_coast_mid",
    "northeast":        "northeast",
    "pacific northwest":"pacific_coast",
    "east":             "east_coast_mid",  # fallback for generic "East"
}


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

@dataclass
class TerminalLineItem:
    description: str
    category: str          # "stevedoring" | "stevedoring_equipment" | "overtime" | "port_authority"
    rate: float
    rate_basis: str        # "$X/ST", "$X/LOA-ft/day", etc.
    quantity: float
    quantity_unit: str
    total: float


@dataclass
class TerminalResult:
    port: str
    commodity: str
    cargo_tonnes: float
    days_in_berth: float
    vessel_loa_m: Optional[float]
    vessel_grt: Optional[int]
    vessel_imo: Optional[str]
    vessel_name: Optional[str]
    arrival_datetime: Optional[dt.datetime]

    stevedoring_key: str = ""
    wharfage_key: str = ""
    regional_multiplier: float = 1.0
    overtime_applied: bool = False
    overtime_reason: str = ""

    line_items: list[TerminalLineItem] = field(default_factory=list)

    stevedoring_total: float = 0.0
    port_authority_total: float = 0.0
    terminal_total: float = 0.0

    confidence: str = "medium"
    source: str = "port_authority_tariffs.json + stevedoring_rates.json v0.2.0-draft"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "commodity": self.commodity,
            "cargo_tonnes": self.cargo_tonnes,
            "days_in_berth": self.days_in_berth,
            "vessel_loa_m": self.vessel_loa_m,
            "vessel_grt": self.vessel_grt,
            "vessel_imo": self.vessel_imo,
            "vessel_name": self.vessel_name,
            "stevedoring_key": self.stevedoring_key,
            "wharfage_key": self.wharfage_key,
            "regional_multiplier": self.regional_multiplier,
            "overtime_applied": self.overtime_applied,
            "overtime_reason": self.overtime_reason,
            "line_items": [
                {
                    "description": li.description,
                    "category": li.category,
                    "rate": li.rate,
                    "rate_basis": li.rate_basis,
                    "quantity": li.quantity,
                    "quantity_unit": li.quantity_unit,
                    "total": li.total,
                }
                for li in self.line_items
            ],
            "stevedoring_total": self.stevedoring_total,
            "port_authority_total": self.port_authority_total,
            "terminal_total": self.terminal_total,
            "confidence": self.confidence,
            "source": self.source,
            "warnings": self.warnings,
        }

    def print_summary(self) -> None:
        loa_str = (
            f"{self.vessel_loa_m:.1f} m ({self.vessel_loa_m / 0.3048:.0f} ft)"
            if self.vessel_loa_m else "n/a"
        )
        grt_str = f"{self.vessel_grt:,}" if self.vessel_grt else "n/a"
        print(f"\n{'='*72}")
        print(f"  TERMINAL COST ESTIMATE")
        print(f"  Port      : {self.port}")
        if self.vessel_name:
            print(f"  Vessel    : {self.vessel_name}")
        print(f"  LOA       : {loa_str}   GRT: {grt_str}")
        print(f"  Commodity : {self.commodity}  ({self.stevedoring_key})")
        print(f"  Cargo     : {self.cargo_tonnes:,.0f} ST   Days in berth: {self.days_in_berth:.1f}")
        if self.regional_multiplier != 1.0:
            print(f"  Region adj: ×{self.regional_multiplier:.2f}")
        if self.overtime_applied:
            print(f"  Overtime  : YES — {self.overtime_reason}")
        if self.arrival_datetime:
            print(f"  Arrival   : {self.arrival_datetime.strftime('%A %Y-%m-%d %H:%M')}")
        print(f"{'='*72}")
        print(f"  {'Description':<47} {'Qty':>8} {'Rate':>10} {'Total':>12}")
        print(f"  {'-'*77}")

        stev_items = [li for li in self.line_items
                      if li.category in ("stevedoring", "stevedoring_equipment", "overtime")]
        pa_items   = [li for li in self.line_items if li.category == "port_authority"]

        if stev_items:
            print(f"  --- STEVEDORING ---")
        for li in stev_items:
            print(f"  {li.description:<47} {li.quantity:>8,.1f} {li.rate_basis:>10}  ${li.total:>10,.2f}")

        if pa_items:
            print(f"  --- PORT AUTHORITY CHARGES ---")
        for li in pa_items:
            print(f"  {li.description:<47} {li.quantity:>8,.1f} {li.rate_basis:>10}  ${li.total:>10,.2f}")

        print(f"  {'-'*77}")
        print(f"  {'Stevedoring subtotal':<57}  ${self.stevedoring_total:>10,.2f}")
        print(f"  {'Port authority charges subtotal':<57}  ${self.port_authority_total:>10,.2f}")
        print(f"  {'TOTAL TERMINAL':<57}  ${self.terminal_total:>10,.2f}")
        print(f"{'='*72}")
        if self.warnings:
            print("  WARNINGS:")
            for w in self.warnings:
                print(f"    * {w}")
        print(f"  Confidence: {self.confidence}  |  Source: {self.source}\n")


# ---------------------------------------------------------------------------
# Loaders (module-level cache)
# ---------------------------------------------------------------------------

_port_tariffs_cache: Optional[dict] = None
_stev_rates_cache: Optional[dict] = None


def _load_port_tariffs() -> dict:
    global _port_tariffs_cache
    if _port_tariffs_cache is None:
        if not _PORT_TARIFFS_FILE.exists():
            raise FileNotFoundError(f"Port tariffs file not found: {_PORT_TARIFFS_FILE}")
        _port_tariffs_cache = json.loads(_PORT_TARIFFS_FILE.read_text(encoding="utf-8"))
    return _port_tariffs_cache


def _load_stev_rates() -> dict:
    global _stev_rates_cache
    if _stev_rates_cache is None:
        if not _STEV_RATES_FILE.exists():
            raise FileNotFoundError(f"Stevedoring rates file not found: {_STEV_RATES_FILE}")
        _stev_rates_cache = json.loads(_STEV_RATES_FILE.read_text(encoding="utf-8"))
    return _stev_rates_cache


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_port(port: str) -> Optional[dict]:
    tariffs = _load_port_tariffs()
    port_lower = port.lower().strip()
    for _key, pdata in tariffs.get("ports", {}).items():
        if port_lower == _key or port_lower == pdata.get("display_name", "").lower():
            return pdata
        if port_lower in [a.lower() for a in pdata.get("aliases", [])]:
            return pdata
        if any(port_lower in a.lower() or a.lower() in port_lower
               for a in pdata.get("aliases", [])):
            return pdata
    return None


def _map_commodity(commodity: str) -> tuple[str, str]:
    """Return (stevedoring_key, wharfage_key). Falls back to bulk_dry_general."""
    c = commodity.lower().strip()
    if c in _COMMODITY_MAP:
        return _COMMODITY_MAP[c]
    for key, val in _COMMODITY_MAP.items():
        if key in c or c in key:
            return val
    return ("bulk_dry_general", "bulk_dry")


def _get_regional_multiplier(port_data: dict) -> tuple[float, str]:
    stev = _load_stev_rates()
    adj = stev.get("regional_adjustments", {})
    coast = port_data.get("coast", "gulf").lower()
    region_key = _COAST_TO_REGION.get(coast, "gulf_coast")
    mult = adj.get(region_key, {}).get("multiplier", 1.0)
    return mult, region_key


def _is_overtime(arrival: Optional[dt.datetime]) -> tuple[bool, str]:
    if arrival is None:
        return False, ""
    reasons = []
    if arrival.hour >= 18 or arrival.hour < 6:
        reasons.append("night (18:00–06:00)")
    if arrival.weekday() >= 5:
        reasons.append("weekend")
    return bool(reasons), " + ".join(reasons)


def _estimate_days_from_throughput(cargo_tonnes: float, stev_data: dict) -> float:
    """cargo_tonnes ÷ throughput_tph ÷ 24 hrs, +10% factor, min 0.5 day."""
    tph = stev_data.get("throughput_tph", 400)
    if tph <= 0:
        return 2.0
    hours = cargo_tonnes / tph
    return max(0.5, round((hours / 24) * 1.10, 2))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_terminal_costs(
    port: str,
    commodity: str,
    cargo_tonnes: float,
    days_in_berth: Optional[float] = None,
    vessel_loa: Optional[float] = None,          # metres
    vessel_grt: Optional[int] = None,
    vessel_imo: Optional[str] = None,
    terminal_name: Optional[str] = None,         # reserved for future terminal-specific lookup
    arrival_datetime: Optional[dt.datetime] = None,
    include_fresh_water: bool = False,
    fresh_water_mt: float = 100.0,
    force_web_lookup: bool = False,
) -> TerminalResult:
    """Calculate terminal costs for a port call.

    Parameters
    ----------
    port : str
        US port name, alias, or UNLOCODE.
    commodity : str
        Cargo type — e.g. "grain", "coal", "cement", "steel coils", "rebar".
    cargo_tonnes : float
        Cargo weight in short tons.
    days_in_berth : float, optional
        Days vessel occupies the berth. Auto-estimated from throughput if None.
    vessel_loa : float, optional
        Length Over All in metres. Required for dockage charge.
    vessel_grt : int, optional
        Gross Registered Tons. Required for harbour dues.
    vessel_imo : str, optional
        IMO number — auto-resolves vessel_loa and vessel_grt from ships register.
    terminal_name : str, optional
        Specific terminal name (future: terminal-specific rate lookup).
    arrival_datetime : datetime, optional
        Vessel arrival — triggers overtime assessment on stevedoring.
    include_fresh_water : bool
        Include fresh water delivery as a line item.
    fresh_water_mt : float
        Metric tons of fresh water (default 100 MT).
    force_web_lookup : bool
        Force web lookup for vessel data even if found in local register.

    Returns
    -------
    TerminalResult
    """
    warnings: list[str] = []
    vessel_name: Optional[str] = None

    # -------------------------------------------------------------------------
    # Step 1: Resolve vessel parameters from IMO if dimensions missing
    # -------------------------------------------------------------------------
    if vessel_imo and (vessel_loa is None or vessel_grt is None):
        if _VESSEL_RESOLVER_AVAILABLE:
            try:
                params = resolve_vessel(imo=vessel_imo, force_web=force_web_lookup)
                vessel_name = params.name
                if vessel_loa is None and params.loa_m:
                    vessel_loa = params.loa_m
                if vessel_grt is None and params.grt:
                    vessel_grt = params.grt
                warnings.extend(params.warnings)
            except VesselNotFoundError as e:
                warnings.append(str(e))
        else:
            warnings.append(
                "Vessel resolver not available — provide vessel_loa= and vessel_grt= manually."
            )

    # -------------------------------------------------------------------------
    # Step 2: Resolve port
    # -------------------------------------------------------------------------
    port_data = _resolve_port(port)
    if port_data is None:
        result = TerminalResult(
            port=port, commodity=commodity, cargo_tonnes=cargo_tonnes,
            days_in_berth=days_in_berth or 2.0,
            vessel_loa_m=vessel_loa, vessel_grt=vessel_grt,
            vessel_imo=vessel_imo, vessel_name=vessel_name,
            arrival_datetime=arrival_datetime,
            confidence="low", warnings=warnings,
        )
        result.warnings.append(
            f"Port '{port}' not found in terminal tariffs catalog. "
            "Add it to port_authority_tariffs.json or supply rates manually."
        )
        return result

    # -------------------------------------------------------------------------
    # Step 3: Map commodity to rate keys
    # -------------------------------------------------------------------------
    stev_key, wharf_key = _map_commodity(commodity)
    stev_data = _load_stev_rates().get("rates", {}).get(stev_key, {})
    if not stev_data:
        warnings.append(
            f"Stevedoring rate key '{stev_key}' not found — falling back to bulk_dry_general."
        )
        stev_key = "bulk_dry_general"
        stev_data = _load_stev_rates().get("rates", {}).get(stev_key, {})

    # -------------------------------------------------------------------------
    # Step 4: Regional multiplier
    # -------------------------------------------------------------------------
    reg_mult, reg_key = _get_regional_multiplier(port_data)

    # -------------------------------------------------------------------------
    # Step 5: Days in berth
    # -------------------------------------------------------------------------
    if days_in_berth is None:
        days_in_berth = _estimate_days_from_throughput(cargo_tonnes, stev_data)
        tph = stev_data.get("throughput_tph", 400)
        warnings.append(
            f"days_in_berth auto-estimated: {days_in_berth:.1f} days "
            f"({cargo_tonnes:,.0f} ST ÷ {tph} TPH × 1.1). "
            "Override with days_in_berth= for accuracy."
        )

    # -------------------------------------------------------------------------
    # Step 6: Overtime check
    # -------------------------------------------------------------------------
    overtime_applies, overtime_reason = _is_overtime(arrival_datetime)
    overtime_pct = stev_data.get("overtime_pct", 50.0) if overtime_applies else 0.0

    line_items: list[TerminalLineItem] = []

    # =========================================================================
    # STEVEDORING
    # =========================================================================

    # Labour
    stev_rate = stev_data.get("rate_per_st_usd", 4.00)
    effective_rate = round(stev_rate * reg_mult, 4)
    stev_labour_total = round(cargo_tonnes * effective_rate, 2)

    line_items.append(TerminalLineItem(
        description=f"Stevedoring — {commodity} ({stev_data.get('handling_method', 'grab_crane')})",
        category="stevedoring",
        rate=effective_rate,
        rate_basis=f"${effective_rate:.2f}/ST",
        quantity=cargo_tonnes,
        quantity_unit="ST",
        total=stev_labour_total,
    ))

    # Equipment
    equip_rate_hr = stev_data.get("equipment_per_hour_usd", 0.0)
    tph = stev_data.get("throughput_tph", 400)
    estimated_hours = round(cargo_tonnes / tph, 1) if tph > 0 else 0.0
    equip_total = 0.0

    if equip_rate_hr > 0 and estimated_hours > 0:
        effective_equip_rate = round(equip_rate_hr * reg_mult, 2)
        equip_total = round(effective_equip_rate * estimated_hours, 2)
        line_items.append(TerminalLineItem(
            description=f"Equipment — {stev_data.get('handling_method', '')}",
            category="stevedoring_equipment",
            rate=effective_equip_rate,
            rate_basis=f"${effective_equip_rate:,.0f}/hr",
            quantity=estimated_hours,
            quantity_unit="hrs",
            total=equip_total,
        ))

    # Overtime surcharge on labour + equipment
    total_overtime = 0.0
    if overtime_applies and overtime_pct > 0:
        overtime_base = stev_labour_total + equip_total
        total_overtime = round(overtime_base * overtime_pct / 100, 2)
        line_items.append(TerminalLineItem(
            description=f"Overtime surcharge ({overtime_reason}) — {overtime_pct:.0f}%",
            category="overtime",
            rate=overtime_pct / 100,
            rate_basis=f"+{overtime_pct:.0f}%",
            quantity=overtime_base,
            quantity_unit="base",
            total=total_overtime,
        ))

    stevedoring_total = round(stev_labour_total + equip_total + total_overtime, 2)

    # =========================================================================
    # PORT AUTHORITY CHARGES
    # =========================================================================

    # Dockage: $/LOA-ft/day
    dockage_total = 0.0
    if vessel_loa is not None:
        loa_ft = vessel_loa / 0.3048
        dock_rate = port_data.get("dockage_rate_per_loa_ft_per_day", 9.50)
        dock_min = port_data.get("dockage_min_usd", 0.0)
        dockage_calc = loa_ft * dock_rate * days_in_berth
        dockage_total = round(max(dockage_calc, dock_min), 2)
        line_items.append(TerminalLineItem(
            description=f"Dockage — {days_in_berth:.1f} days × {loa_ft:.0f} LOA-ft",
            category="port_authority",
            rate=dock_rate,
            rate_basis=f"${dock_rate}/LOA-ft/day",
            quantity=round(loa_ft * days_in_berth, 1),
            quantity_unit="LOA-ft·days",
            total=dockage_total,
        ))
    else:
        warnings.append(
            "vessel_loa not provided — dockage excluded from estimate. "
            "Provide vessel_loa= or vessel_imo= for a complete PDA."
        )

    # Wharfage: $/ST by commodity
    wharf_rates = port_data.get("wharfage_rates_per_st", {})
    wharf_rate = wharf_rates.get(wharf_key, port_data.get("wharfage_default_per_st", 1.85))
    wharfage_total = round(cargo_tonnes * wharf_rate, 2)
    line_items.append(TerminalLineItem(
        description=f"Wharfage — {commodity}",
        category="port_authority",
        rate=wharf_rate,
        rate_basis=f"${wharf_rate}/ST",
        quantity=cargo_tonnes,
        quantity_unit="ST",
        total=wharfage_total,
    ))

    # Harbour dues: $/GT
    harbour_total = 0.0
    if vessel_grt is not None:
        hd_rate = port_data.get("harbour_dues_per_gt", 0.065)
        hd_min = port_data.get("harbour_dues_min_usd", 0.0)
        harbour_total = round(max(vessel_grt * hd_rate, hd_min), 2)
        line_items.append(TerminalLineItem(
            description=f"Harbour dues — {vessel_grt:,} GT",
            category="port_authority",
            rate=hd_rate,
            rate_basis=f"${hd_rate}/GT",
            quantity=vessel_grt,
            quantity_unit="GT",
            total=harbour_total,
        ))
    else:
        warnings.append(
            "vessel_grt not provided — harbour dues excluded from estimate. "
            "Provide vessel_grt= or vessel_imo= for a complete PDA."
        )

    # Line handling: $/op (arrival + departure = 2 ops default)
    lh_rate = port_data.get("line_handling_per_op_usd", 2500.0)
    lh_total = round(lh_rate * 2, 2)
    line_items.append(TerminalLineItem(
        description="Line handling (arrival + departure)",
        category="port_authority",
        rate=lh_rate,
        rate_basis=f"${lh_rate:,.0f}/op",
        quantity=2,
        quantity_unit="ops",
        total=lh_total,
    ))

    # Security fee: flat per call
    sec_fee = port_data.get("security_fee_usd", 0.0)
    if sec_fee > 0:
        line_items.append(TerminalLineItem(
            description="ISPS / Terminal security fee",
            category="port_authority",
            rate=sec_fee,
            rate_basis="flat/call",
            quantity=1,
            quantity_unit="call",
            total=round(sec_fee, 2),
        ))

    # Fresh water (optional)
    if include_fresh_water:
        fw_rate = port_data.get("fresh_water_per_mt_usd", 18.0)
        fw_total = round(fw_rate * fresh_water_mt, 2)
        line_items.append(TerminalLineItem(
            description=f"Fresh water supply",
            category="port_authority",
            rate=fw_rate,
            rate_basis=f"${fw_rate}/MT",
            quantity=fresh_water_mt,
            quantity_unit="MT",
            total=fw_total,
        ))

    # =========================================================================
    # Totals + confidence
    # =========================================================================
    pa_items = [li for li in line_items if li.category == "port_authority"]
    port_authority_total = round(sum(li.total for li in pa_items), 2)
    terminal_total = round(stevedoring_total + port_authority_total, 2)

    conf_rank = {"high": 3, "medium": 2, "low": 1}
    port_conf = port_data.get("confidence", "medium")
    stev_conf = stev_data.get("confidence", "medium")
    min_rank = min(conf_rank.get(port_conf, 2), conf_rank.get(stev_conf, 2))
    overall_conf = {3: "high", 2: "medium", 1: "low"}.get(min_rank, "medium")

    # Rate range advisory
    rng = stev_data.get("rate_range", {})
    if rng:
        low_est = round(cargo_tonnes * rng.get("low", stev_rate) * reg_mult + port_authority_total, 2)
        high_est = round(cargo_tonnes * rng.get("high", stev_rate) * reg_mult + port_authority_total, 2)
        warnings.append(
            f"Stevedoring rate range: ${rng.get('low', stev_rate):.2f}–${rng.get('high', stev_rate):.2f}/ST. "
            f"Estimated terminal total range: ${low_est:,.0f}–${high_est:,.0f}"
        )

    if terminal_name:
        warnings.append(
            f"Terminal-specific rates for '{terminal_name}' not yet implemented — "
            "using port-level benchmarks. Verify against terminal tariff directly."
        )

    return TerminalResult(
        port=port_data.get("display_name", port),
        commodity=commodity,
        cargo_tonnes=cargo_tonnes,
        days_in_berth=days_in_berth,
        vessel_loa_m=vessel_loa,
        vessel_grt=vessel_grt,
        vessel_imo=vessel_imo,
        vessel_name=vessel_name,
        arrival_datetime=arrival_datetime,
        stevedoring_key=stev_key,
        wharfage_key=wharf_key,
        regional_multiplier=reg_mult,
        overtime_applied=overtime_applies,
        overtime_reason=overtime_reason,
        line_items=line_items,
        stevedoring_total=stevedoring_total,
        port_authority_total=port_authority_total,
        terminal_total=terminal_total,
        confidence=overall_conf,
        source=(
            f"port_authority_tariffs.json + stevedoring_rates.json v0.2.0-draft "
            f"| {port_data.get('display_name', port)} | region: {reg_key}"
        ),
        warnings=warnings,
    )
