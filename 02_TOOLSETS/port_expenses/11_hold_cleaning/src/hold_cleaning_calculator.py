"""
Hold Cleaning Cost Calculator
02_TOOLSETS/port_expenses/11_hold_cleaning/src/hold_cleaning_calculator.py

Estimates hold cleaning costs for a vessel port call based on:
  - Next cargo (commodity being loaded)
  - Previous cargo (what the vessel last carried)
  - Port (for rate lookup)
  - Hold count and vessel parameters

Integrates:
  - data/hold_cleaning_rates.csv — operation × port rate table
  - data/cargo_compatibility_matrix.csv — previous → next cargo cleaning requirements
  - data/fgis_inspection_fees.csv — USDA FGIS / NCB regulated inspection fees
  - knowledge_base/hold_cleaning_kb.json — cleaning protocols and risk intelligence

Output fields match PDA line item schema:
  hold_cleaning_sweep
  hold_cleaning_wash
  hold_cleaning_fumigation
  hold_cleaning_fgis_inspection
  hold_cleaning_days_lost
  hold_cleaning_total
  hold_cleaning_previous_cargo
  hold_cleaning_risk_level
  hold_cleaning_basis
  hold_cleaning_source
  hold_cleaning_confidence
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
_MODULE_DIR = Path(__file__).parent.parent
_RATES_CSV   = _MODULE_DIR / "data" / "hold_cleaning_rates.csv"
_MATRIX_CSV  = _MODULE_DIR / "data" / "cargo_compatibility_matrix.csv"
_FGIS_CSV    = _MODULE_DIR / "data" / "fgis_inspection_fees.csv"
_KB_JSON     = _MODULE_DIR / "knowledge_base" / "hold_cleaning_kb.json"

# Grain commodities that trigger FGIS inspection
_GRAIN_COMMODITIES = {
    "grain", "wheat", "corn", "maize", "barley", "oats", "rye",
    "soybeans", "soya", "soybean", "rapeseed", "canola", "milo",
    "sorghum", "sunflower seed",
}

# Cleaning operation → rate CSV column names
_CREW_CLEANING = "crew"
_SHORE_CLEANING = "shore_gang"


def _load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _normalize(text: str) -> str:
    return text.lower().strip().replace("-", "_").replace(" ", "_")


def _is_grain(commodity: str) -> bool:
    nc = _normalize(commodity)
    return any(g in nc for g in _grain_commodities_normalized())


def _grain_commodities_normalized() -> set[str]:
    return {_normalize(c) for c in _GRAIN_COMMODITIES}


def _get_matrix_row(
    matrix: list[dict], previous_cargo: str, next_cargo: str
) -> Optional[dict]:
    """Find best match in cargo compatibility matrix."""
    nc_prev = _normalize(previous_cargo)
    nc_next = _normalize(next_cargo)

    # Exact match
    for row in matrix:
        if _normalize(row["previous_cargo"]) == nc_prev and _normalize(row["next_cargo"]) == nc_next:
            return row

    # Partial match — previous cargo only (next cargo defaults)
    for row in matrix:
        rp = _normalize(row["previous_cargo"])
        if rp == nc_prev or rp in nc_prev or nc_prev in rp:
            # And next cargo is a grain match
            rn = _normalize(row["next_cargo"])
            if _is_grain(next_cargo) and _is_grain(rn):
                return row

    # Wildcard — just match previous cargo to any grain row
    for row in matrix:
        rp = _normalize(row["previous_cargo"])
        if rp == nc_prev or rp in nc_prev or nc_prev in rp:
            return row

    return None


def _get_rate(
    rates: list[dict],
    port: str,
    operation: str,
    cleaning_type: str = _CREW_CLEANING,
) -> Optional[float]:
    """Return midpoint rate for port + operation + cleaning type. Falls back to DEFAULT."""
    nc_port = _normalize(port)
    nc_op = _normalize(operation)
    nc_type = _normalize(cleaning_type)

    # Try specific port first
    for row in rates:
        if (
            _normalize(row["port"]) == nc_port
            and _normalize(row["operation"]) == nc_op
            and _normalize(row["cleaning_type"]) == nc_type
        ):
            return float(row["rate_usd_mid"])

    # Partial port match
    for row in rates:
        rp = _normalize(row["port"])
        if (
            (rp in nc_port or nc_port in rp)
            and _normalize(row["operation"]) == nc_op
            and _normalize(row["cleaning_type"]) == nc_type
        ):
            return float(row["rate_usd_mid"])

    # DEFAULT fallback
    for row in rates:
        if (
            row["port"].upper() == "DEFAULT"
            and _normalize(row["operation"]) == nc_op
            and _normalize(row["cleaning_type"]) == nc_type
        ):
            return float(row["rate_usd_mid"])

    return None


def _get_fgis_fee(
    fgis_rows: list[dict], service: str, vessel_dwt: Optional[int]
) -> float:
    """Return FGIS fee for given service and vessel DWT."""
    nc_service = _normalize(service)
    for row in fgis_rows:
        if _normalize(row["service"]) != nc_service:
            continue
        dwt_min = int(row["vessel_size_dwt_min"])
        dwt_max = int(row["vessel_size_dwt_max"])
        if vessel_dwt is None:
            return float(row["fee_usd"])
        if dwt_min <= vessel_dwt <= dwt_max:
            return float(row["fee_usd"])
    # Fallback: largest bracket
    for row in reversed(fgis_rows):
        if _normalize(row["service"]) == nc_service:
            return float(row["fee_usd"])
    return 0.0


def calculate_hold_cleaning(
    port: str,
    hold_count: int,
    commodity_loading: str,
    previous_cargo: Optional[str] = None,
    vessel_grt: Optional[int] = None,
    vessel_dwt: Optional[int] = None,
    include_fgis_inspection: Optional[bool] = None,
    use_shore_gang: bool = False,
    include_fumigation: bool = False,
) -> dict:
    """
    Calculate hold cleaning cost estimate for a vessel port call.

    Parameters
    ----------
    port : str
        US port name (e.g., "New Orleans", "Hampton Roads")
    hold_count : int
        Number of cargo holds to clean
    commodity_loading : str
        Cargo being loaded (drives cleanliness standard and FGIS trigger)
    previous_cargo : str, optional
        Cargo vessel previously carried. If None, assumes same commodity (minimum cleaning).
    vessel_grt : int, optional
        Gross registered tons (informational)
    vessel_dwt : int, optional
        Deadweight tons (used for FGIS fee tier lookup)
    include_fgis_inspection : bool, optional
        Force include/exclude FGIS inspection. If None, auto-detected from commodity.
    use_shore_gang : bool
        Use shore gang rates instead of crew cleaning rates.
    include_fumigation : bool
        Include fumigation cost (default False — only when infestation present).

    Returns
    -------
    dict with keys:
        hold_cleaning_sweep           float (USD)
        hold_cleaning_wash            float (USD)
        hold_cleaning_fumigation      float (USD)
        hold_cleaning_fgis_inspection float (USD)
        hold_cleaning_days_lost       float (days)
        hold_cleaning_total           float (USD)
        hold_cleaning_previous_cargo  str
        hold_cleaning_risk_level      str
        hold_cleaning_basis           str
        hold_cleaning_source          str
        hold_cleaning_confidence      str
        hold_cleaning_warnings        list[str]
        hold_cleaning_operations      list[str]
        hold_cleaning_regulatory_flags list[str]
    """
    # Load data
    rates  = _load_csv(_RATES_CSV)
    matrix = _load_csv(_MATRIX_CSV)
    fgis   = _load_csv(_FGIS_CSV)

    cleaning_type = _SHORE_CLEANING if use_shore_gang else _CREW_CLEANING
    warnings: list[str] = []
    regulatory_flags: list[str] = []
    operations_applied: list[str] = []

    # ── Previous cargo defaults ─────────────────────────────────────────────
    if previous_cargo is None:
        previous_cargo = commodity_loading
        warnings.append("Previous cargo not specified — assumed same commodity (minimum cleaning).")

    # ── FGIS auto-detection ─────────────────────────────────────────────────
    is_grain_cargo = _is_grain(commodity_loading)
    if include_fgis_inspection is None:
        include_fgis_inspection = is_grain_cargo

    if is_grain_cargo:
        regulatory_flags.append("FGIS stowage examination required (US grain export).")
        regulatory_flags.append("NCB Grain Certificate of Readiness required (all US grain export ports).")
        regulatory_flags.append("Document of Authorization (Grain Code) must be onboard and valid.")

    # ── Cargo compatibility matrix lookup ───────────────────────────────────
    matrix_row = _get_matrix_row(matrix, previous_cargo, commodity_loading)

    if matrix_row:
        risk_level         = matrix_row.get("risk_level", "medium")
        cleaning_req       = matrix_row.get("cleaning_requirement", "seawater_freshwater_rinse")
        fgis_concern       = matrix_row.get("fgis_concern", "no").lower() == "yes"
        chemical_required  = matrix_row.get("chemical_wash_required", "no").lower() == "yes"
        days_lost_estimate = float(matrix_row.get("days_lost_estimate", 1.0))
        matrix_notes       = matrix_row.get("notes", "")
    else:
        # No matrix match — apply conservative default
        risk_level = "medium"
        cleaning_req = "seawater_freshwater_rinse"
        fgis_concern = is_grain_cargo
        chemical_required = False
        days_lost_estimate = 1.0
        matrix_notes = f"No specific protocol for {previous_cargo} → {commodity_loading}. Conservative defaults applied."
        warnings.append(f"Cargo transition '{previous_cargo}' → '{commodity_loading}' not in compatibility matrix. Defaults used.")

    if matrix_notes:
        warnings.append(matrix_notes)

    # Escalate FGIS concern from matrix
    if fgis_concern and is_grain_cargo:
        regulatory_flags.append(
            f"Previous cargo '{previous_cargo}' flagged as FGIS concern — surveyor may require additional cleaning documentation."
        )

    # ── SWEEP cost ──────────────────────────────────────────────────────────
    sweep_rate = _get_rate(rates, port, "sweep_per_hold", _CREW_CLEANING)
    if sweep_rate is None:
        sweep_rate = 350.0
        warnings.append("Sweep rate not found for port — using $350/hold default.")
    sweep_cost = sweep_rate * hold_count
    operations_applied.append(f"Sweep: {hold_count} holds × ${sweep_rate:.0f} = ${sweep_cost:,.0f}")

    # ── WASH cost ───────────────────────────────────────────────────────────
    wash_cost = 0.0

    # Seawater wash — always
    sw_rate = _get_rate(rates, port, "wash_saltwater_per_hold", cleaning_type)
    if sw_rate is None:
        sw_rate = 450.0 if cleaning_type == _CREW_CLEANING else 1250.0
        warnings.append(f"Saltwater wash rate not found for port/type — using ${sw_rate:.0f}/hold default.")
    sw_cost = sw_rate * hold_count
    wash_cost += sw_cost
    operations_applied.append(f"Seawater wash ({cleaning_type}): {hold_count} holds × ${sw_rate:.0f} = ${sw_cost:,.0f}")

    # Fresh water rinse — required for grain clean and above
    fw_rate = _get_rate(rates, port, "wash_freshwater_per_hold", cleaning_type)
    if fw_rate is None:
        fw_rate = 600.0 if cleaning_type == _CREW_CLEANING else 1500.0
        warnings.append(f"Fresh water wash rate not found — using ${fw_rate:.0f}/hold default.")
    fw_cost = fw_rate * hold_count
    wash_cost += fw_cost
    operations_applied.append(f"Fresh water rinse ({cleaning_type}): {hold_count} holds × ${fw_rate:.0f} = ${fw_cost:,.0f}")

    # Chemical wash if required
    if chemical_required:
        chem_rate = _get_rate(rates, port, "chemical_wash_per_hold", cleaning_type)
        if chem_rate is None:
            chem_rate = 950.0 if cleaning_type == _CREW_CLEANING else 1850.0
            warnings.append(f"Chemical wash rate not found — using ${chem_rate:.0f}/hold default.")
        chem_cost = chem_rate * hold_count
        wash_cost += chem_cost
        operations_applied.append(f"Chemical wash ({cleaning_type}): {hold_count} holds × ${chem_rate:.0f} = ${chem_cost:,.0f}")
        regulatory_flags.append(
            "Chemical cleaning agents used — confirm MARPOL Annex V HME status of cleaning product before any sea discharge."
        )

    # ── FUMIGATION cost ─────────────────────────────────────────────────────
    fumigation_cost = 0.0
    if include_fumigation:
        fum_rate = _get_rate(rates, port, "fumigation_per_hold", "certified_fumigator")
        if fum_rate is None:
            fum_rate = 1200.0
            warnings.append("Fumigation rate not found — using $1,200/hold default.")
        fumigation_cost = fum_rate * hold_count
        operations_applied.append(f"Fumigation (certified): {hold_count} holds × ${fum_rate:.0f} = ${fumigation_cost:,.0f}")
        regulatory_flags.append("Fumigation certificate required — certified fumigator must be engaged.")
        regulatory_flags.append("Vessel must not depart before minimum fumigation period expires.")

    # ── FGIS / NCB INSPECTION fees ──────────────────────────────────────────
    fgis_total = 0.0
    if include_fgis_inspection:
        # FGIS stowage examination
        fgis_exam = _get_fgis_fee(fgis, "stowage_examination_basic", vessel_dwt)
        fgis_total += fgis_exam
        operations_applied.append(f"FGIS stowage examination: ${fgis_exam:,.0f}")

        # NCB Grain Certificate of Readiness
        ncb_cert = _get_fgis_fee(fgis, "ncb_grain_certificate", vessel_dwt)
        fgis_total += ncb_cert
        operations_applied.append(f"NCB Grain Certificate of Readiness: ${ncb_cert:,.0f}")

        # NCB stability review — include when previous cargo was problematic
        if risk_level in ("high", "very_high"):
            ncb_stab = _get_fgis_fee(fgis, "ncb_stability_review", vessel_dwt)
            fgis_total += ncb_stab
            operations_applied.append(f"NCB stability review (high-risk transition): ${ncb_stab:,.0f}")

        # USDA per-hold cleanliness certificates (typically required at major terminals)
        usda_per_hold = _get_fgis_fee(fgis, "usda_cleanliness_certificate", vessel_dwt)
        usda_total = usda_per_hold * hold_count
        fgis_total += usda_total
        operations_applied.append(f"USDA cleanliness certificates: {hold_count} holds × ${usda_per_hold:.0f} = ${usda_total:,.0f}")

        # Re-inspection reserve if high risk
        if risk_level in ("high", "very_high"):
            reinspect = _get_fgis_fee(fgis, "reinspection_surcharge", vessel_dwt)
            fgis_total += reinspect
            operations_applied.append(
                f"Reinspection reserve (high-risk previous cargo): ${reinspect:,.0f}"
            )
            warnings.append(
                f"High-risk previous cargo ('{previous_cargo}'): reinspection fee included as reserve. "
                "Risk of survey failure is elevated — allocate additional cleaning time."
            )

    # ── TOTAL ───────────────────────────────────────────────────────────────
    total = sweep_cost + wash_cost + fumigation_cost + fgis_total

    # ── Confidence and basis ─────────────────────────────────────────────────
    if port.upper() == "DEFAULT":
        confidence = "indicative"
    else:
        # Check if port was found in rates table
        port_found = any(_normalize(r["port"]) == _normalize(port) for r in rates)
        confidence = "estimated" if port_found else "indicative"

    basis = (
        f"Hold count: {hold_count} | "
        f"Previous cargo: {previous_cargo} | "
        f"Cleanliness req: {cleaning_req} | "
        f"Cleaning type: {cleaning_type} | "
        f"Risk level: {risk_level}"
    )

    return {
        # PDA line items
        "hold_cleaning_sweep":             round(sweep_cost, 2),
        "hold_cleaning_wash":              round(wash_cost, 2),
        "hold_cleaning_fumigation":        round(fumigation_cost, 2),
        "hold_cleaning_fgis_inspection":   round(fgis_total, 2),
        "hold_cleaning_days_lost":         days_lost_estimate,
        "hold_cleaning_total":             round(total, 2),
        # Metadata
        "hold_cleaning_previous_cargo":    previous_cargo,
        "hold_cleaning_risk_level":        risk_level,
        "hold_cleaning_basis":             basis,
        "hold_cleaning_source":            "hold_cleaning_rates.csv | cargo_compatibility_matrix.csv | fgis_inspection_fees.csv",
        "hold_cleaning_confidence":        confidence,
        # Intelligence output
        "hold_cleaning_warnings":          warnings,
        "hold_cleaning_operations":        operations_applied,
        "hold_cleaning_regulatory_flags":  regulatory_flags,
    }


def format_pda_summary(result: dict) -> str:
    """Return a formatted text PDA line-item summary for hold cleaning."""
    lines = []
    lines.append("  HOLD CLEANING")
    lines.append(f"    Previous cargo:   {result['hold_cleaning_previous_cargo']}")
    lines.append(f"    Risk level:       {result['hold_cleaning_risk_level'].upper()}")
    lines.append(f"    Days lost est.:   {result['hold_cleaning_days_lost']}")
    lines.append("")
    lines.append(f"    Sweep:            ${result['hold_cleaning_sweep']:>10,.2f}")
    lines.append(f"    Washing:          ${result['hold_cleaning_wash']:>10,.2f}")
    if result["hold_cleaning_fumigation"] > 0:
        lines.append(f"    Fumigation:       ${result['hold_cleaning_fumigation']:>10,.2f}")
    if result["hold_cleaning_fgis_inspection"] > 0:
        lines.append(f"    FGIS / NCB:       ${result['hold_cleaning_fgis_inspection']:>10,.2f}")
    lines.append(f"    ─────────────────────────────────")
    lines.append(f"    TOTAL:            ${result['hold_cleaning_total']:>10,.2f}")
    if result["hold_cleaning_warnings"]:
        lines.append("")
        lines.append("    Warnings / Notes:")
        for w in result["hold_cleaning_warnings"]:
            lines.append(f"      ⚠  {w}")
    if result["hold_cleaning_regulatory_flags"]:
        lines.append("")
        lines.append("    Regulatory:")
        for f in result["hold_cleaning_regulatory_flags"]:
            lines.append(f"      [ ] {f}")
    return "\n".join(lines)


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("  Hold Cleaning Calculator — Demo")
    print("="*70)

    # Demo 1: Coal to grain, Panamax, Hampton Roads
    print("\n[1] Coal → Grain | Panamax (75,000 DWT) | 7 holds | Hampton Roads VA")
    r = calculate_hold_cleaning(
        port="Hampton Roads",
        hold_count=7,
        commodity_loading="grain",
        previous_cargo="coal",
        vessel_dwt=75000,
    )
    print(format_pda_summary(r))
    print(f"\n  Operations breakdown:")
    for op in r["hold_cleaning_operations"]:
        print(f"    • {op}")

    # Demo 2: Grain to grain, same cargo, New Orleans
    print("\n[2] Grain → Grain | Supramax (58,000 DWT) | 5 holds | New Orleans")
    r2 = calculate_hold_cleaning(
        port="New Orleans",
        hold_count=5,
        commodity_loading="grain",
        previous_cargo="grain",
        vessel_dwt=58000,
    )
    print(format_pda_summary(r2))

    # Demo 3: Cement to grain, shore gang
    print("\n[3] Cement → Grain | Post-Panamax (110,000 DWT) | 9 holds | New Orleans | Shore gang")
    r3 = calculate_hold_cleaning(
        port="New Orleans",
        hold_count=9,
        commodity_loading="grain",
        previous_cargo="cement",
        vessel_dwt=110000,
        use_shore_gang=True,
    )
    print(format_pda_summary(r3))

    print("\n" + "="*70)
    print("  Demo complete.")
    print("="*70 + "\n")
