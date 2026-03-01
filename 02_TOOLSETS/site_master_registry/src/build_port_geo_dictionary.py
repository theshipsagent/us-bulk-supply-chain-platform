"""Build a unified port geo-dictionary from multiple source files.

Merges four upstream sources into a single JSON keyed by Census 4-digit
port_code.  Every entry carries the full classification chain plus
cross-references to USACE and Panjiva identifiers.

Source files:
  1. census_trade/.../port_reference.csv       (549 rows, canonical)
  2. policy_analysis/.../us_port_dictionary.csv (777 rows, USACE codes)
  3. policy_analysis/.../usace_to_census_port_mapping.csv (273 rows)
  4. vessel_intelligence/data/ports_master.csv  (160 rows, Panjiva names)

Output:
  site_master_registry/data/reference/port_geo_dictionary.json
"""

from __future__ import annotations

import csv
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------

def _normalize_coast(val: str) -> str:
    """Fix known inconsistencies in coast values.

    "Land  Ports" (double space) -> "Land Ports"
    "Alaska, US Islands"         -> "Alaska/US Islands"
    Trailing/leading whitespace  -> stripped
    """
    if not val:
        return val
    val = " ".join(val.split())  # collapse any multi-space
    val = val.strip()
    if val.lower().startswith("alaska") and "island" in val.lower():
        val = "Alaska/US Islands"
    return val


def _normalize_consolidated(val: str) -> str:
    """Strip trailing whitespace from consolidated names."""
    return val.strip() if val else val


def _zero_pad_port_code(code: Any) -> str:
    """Ensure port_code is a 4-digit zero-padded string."""
    return str(code).strip().zfill(4)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_census_ports(path: Path) -> dict[str, dict]:
    """Load port_reference.csv — the canonical 549-row census reference.

    Returns dict keyed by 4-digit port_code.
    """
    ports: dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = _zero_pad_port_code(row["port_code"])
            ports[code] = {
                "port_code": code,
                "sked_d_name": row.get("sked_d_name", "").strip(),
                "cbp_name": row.get("cbp_appendix_e_name", "").strip(),
                "state": row.get("state", "").strip(),
                "district_code": row.get("district_code", "").strip(),
                "district_name": row.get("district_name", "").strip(),
                "port_type": row.get("port_type", "").strip(),
                "port_consolidated": _normalize_consolidated(
                    row.get("port_consolidated", "")
                ),
                "port_coast": _normalize_coast(row.get("port_coast", "")),
                "port_region": row.get("port_region", "").strip(),
            }
    logger.info(f"Loaded {len(ports)} census ports from {path.name}")
    return ports


def _load_usace_dictionary(path: Path) -> dict[str, dict]:
    """Load us_port_dictionary.csv — 777 USACE-coded entries.

    Returns dict keyed by USACE 4-digit code.
    """
    entries: dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = _zero_pad_port_code(row.get("Code", ""))
            entries[code] = {
                "usace_code": code,
                "sked_d_e": row.get("Sked_D_E", "").strip(),
                "port_consolidated": _normalize_consolidated(
                    row.get("Port_Consolidated", "")
                ),
                "port_coast": _normalize_coast(row.get("Port_Coast", "")),
                "port_region": row.get("Port_Region", "").strip(),
                "sked_d": row.get("Sked_D", "").strip(),
            }
    logger.info(f"Loaded {len(entries)} USACE port entries from {path.name}")
    return entries


def _load_usace_crosswalk(path: Path) -> list[dict]:
    """Load usace_to_census_port_mapping.csv — 273 crosswalk rows.

    Returns list of dicts with USACE_PORT, Census_Code, Match_Type, etc.
    """
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            usace_port = str(row.get("USACE_PORT", "")).strip()
            census_code = _zero_pad_port_code(row.get("Census_Code", ""))
            if not row.get("Census_Code", "").strip():
                census_code = ""
            rows.append({
                "usace_port": usace_port,
                "usace_port_name": row.get("USACE_PORT_NAME", "").strip(),
                "census_code": census_code,
                "match_type": row.get("Match_Type", "").strip(),
                "port_consolidated": _normalize_consolidated(
                    row.get("Port_Consolidated", "")
                ),
                "port_coast": _normalize_coast(row.get("Port_Coast", "")),
                "port_region": row.get("Port_Region", "").strip(),
            })
    logger.info(f"Loaded {len(rows)} USACE->Census crosswalk rows from {path.name}")
    return rows


def _load_panjiva_crosswalk(path: Path) -> list[dict]:
    """Load ports_master.csv — 160 Panjiva discharge-name-to-code entries.

    Returns list of dicts with panjiva_name, port_code, consolidated, etc.
    """
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = _zero_pad_port_code(row.get("Port_Code", ""))
            rows.append({
                "panjiva_name": row.get("Port of Discharge (D)", "").strip(),
                "port_code": code,
                "port_consolidated": _normalize_consolidated(
                    row.get("Port_Consolidated", "")
                ),
                "port_coast": _normalize_coast(row.get("Port_Coast", "")),
                "port_region": row.get("Port_Region", "").strip(),
            })
    logger.info(f"Loaded {len(rows)} Panjiva crosswalk rows from {path.name}")
    return rows


# ---------------------------------------------------------------------------
# Hierarchy builder
# ---------------------------------------------------------------------------

def _build_hierarchy(
    ports: dict[str, dict],
) -> dict[str, dict[str, list[str]]]:
    """Build coast -> region -> [consolidated] hierarchy from port entries.

    Only includes non-empty coasts/regions.
    """
    tree: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for entry in ports.values():
        coast = entry.get("port_coast", "")
        region = entry.get("port_region", "")
        consolidated = entry.get("port_consolidated", "")
        if coast and region and consolidated:
            tree[coast][region].add(consolidated)

    # Convert sets to sorted lists for JSON serialization
    return {
        coast: {
            region: sorted(cons_set)
            for region, cons_set in sorted(regions.items())
        }
        for coast, regions in sorted(tree.items())
    }


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def build_port_geo_dictionary(project_root: str | Path) -> Path:
    """Build the unified port geo-dictionary JSON.

    Merges 4 source files, normalizes names, writes:
        site_master_registry/data/reference/port_geo_dictionary.json

    Returns the path to the written JSON file.
    """
    root = Path(project_root)

    # --- Locate source files ---
    census_port_ref = (
        root / "02_TOOLSETS" / "census_trade" / "data" / "reference"
        / "port_reference.csv"
    )
    usace_dict_path = (
        root / "02_TOOLSETS" / "policy_analysis" / "usace_entrance_clearance"
        / "01_DICTIONARIES" / "us_port_dictionary.csv"
    )
    usace_crosswalk_path = (
        root / "02_TOOLSETS" / "policy_analysis" / "usace_entrance_clearance"
        / "01_DICTIONARIES" / "usace_to_census_port_mapping.csv"
    )
    panjiva_crosswalk_path = (
        root / "02_TOOLSETS" / "vessel_intelligence" / "data"
        / "ports_master.csv"
    )

    # Validate all files exist
    for p in [census_port_ref, usace_dict_path, usace_crosswalk_path,
              panjiva_crosswalk_path]:
        if not p.exists():
            raise FileNotFoundError(f"Required source file not found: {p}")

    # --- Load all sources ---
    census_ports = _load_census_ports(census_port_ref)
    _usace_dict = _load_usace_dictionary(usace_dict_path)
    usace_crosswalk = _load_usace_crosswalk(usace_crosswalk_path)
    panjiva_crosswalk = _load_panjiva_crosswalk(panjiva_crosswalk_path)

    # --- Import seaport coordinates from geo_enrichment ---
    from geo_enrichment import build_seaport_coordinates
    seaport_coords = build_seaport_coordinates()

    # --- Build USACE -> Census crosswalk dict ---
    usace_to_census: dict[str, str] = {}
    direct_matches = 0
    fallback_matches = 0
    for row in usace_crosswalk:
        usace_code = row["usace_port"]
        census_code = row["census_code"]
        match_type = row["match_type"]
        if not usace_code or match_type == "NO MATCH":
            continue
        if census_code:
            usace_to_census[usace_code] = census_code
            direct_matches += 1
        else:
            # State fallback: map to the consolidated group's region
            # but no specific census code — store with empty string
            # so we can still count the mapping attempt
            fallback_matches += 1

    logger.info(
        f"USACE crosswalk: {direct_matches} direct, "
        f"{fallback_matches} fallback"
    )

    # --- Build Panjiva -> Census crosswalk dict ---
    panjiva_to_census: dict[str, str] = {}
    for row in panjiva_crosswalk:
        name = row["panjiva_name"]
        code = row["port_code"]
        if name and code:
            panjiva_to_census[name] = code

    logger.info(f"Panjiva crosswalk: {len(panjiva_to_census)} mappings")

    # --- Enrich census ports with cross-references ---
    # Build reverse lookup: census_code -> [usace_codes]
    census_to_usace: dict[str, list[str]] = defaultdict(list)
    for usace_code, census_code in usace_to_census.items():
        census_to_usace[census_code].append(usace_code)

    # Build reverse lookup: census_code -> [panjiva_names]
    census_to_panjiva: dict[str, list[str]] = defaultdict(list)
    for pname, census_code in panjiva_to_census.items():
        census_to_panjiva[census_code].append(pname)

    # Build consolidated -> [port_codes] lookup
    consolidated_to_ports: dict[str, list[str]] = defaultdict(list)

    # Assemble final port entries
    ports_out: dict[str, dict] = {}
    seaport_count = 0

    for code, entry in census_ports.items():
        port_entry = {
            "port_code": code,
            "sked_d_name": entry["sked_d_name"],
            "cbp_name": entry["cbp_name"],
            "state": entry["state"],
            "district_code": entry["district_code"],
            "district_name": entry["district_name"],
            "port_type": entry["port_type"],
            "port_consolidated": entry["port_consolidated"],
            "port_coast": entry["port_coast"],
            "port_region": entry["port_region"],
        }

        # Add coordinates if available
        if code in seaport_coords:
            lat, lon = seaport_coords[code]
            port_entry["latitude"] = lat
            port_entry["longitude"] = lon

        # Add cross-references
        usace_codes = sorted(census_to_usace.get(code, []),
                             key=lambda x: int(x) if x.isdigit() else 0)
        if usace_codes:
            port_entry["usace_codes"] = usace_codes

        panjiva_names = sorted(census_to_panjiva.get(code, []))
        if panjiva_names:
            port_entry["panjiva_names"] = panjiva_names

        ports_out[code] = port_entry

        # Track consolidated groupings
        consolidated = entry["port_consolidated"]
        if consolidated:
            consolidated_to_ports[consolidated].append(code)

        if entry["port_type"] == "seaport":
            seaport_count += 1

    # --- Fill seaport coordinate codes not in census reference ---
    # build_seaport_coordinates() has ~120 codes; some use legacy numbering
    # that doesn't match Census Schedule D.  For any code in seaport_coords
    # but NOT in ports_out, find the nearest Census seaport and create an
    # alias entry so every nearest_port_code gets a dictionary hit.
    from geo_enrichment import _haversine_km

    # Build coordinate index of Census seaports for nearest-neighbor lookup
    census_seaport_coords: dict[str, tuple[float, float]] = {}
    for ccode, centry in census_ports.items():
        if ccode in seaport_coords:
            census_seaport_coords[ccode] = seaport_coords[ccode]

    coord_aliases = 0
    for coord_code, (clat, clon) in seaport_coords.items():
        if coord_code in ports_out:
            continue  # already covered by census reference

        # Find nearest Census seaport by coordinates
        best_census_code = None
        best_dist = float("inf")
        for ref_code, (rlat, rlon) in census_seaport_coords.items():
            d = _haversine_km(clat, clon, rlat, rlon)
            if d < best_dist:
                best_dist = d
                best_census_code = ref_code

        if best_census_code and best_census_code in ports_out:
            ref = ports_out[best_census_code]
            alias_entry = {
                "port_code": coord_code,
                "sked_d_name": ref["sked_d_name"],
                "cbp_name": ref["cbp_name"],
                "state": ref["state"],
                "district_code": ref.get("district_code", ""),
                "district_name": ref.get("district_name", ""),
                "port_type": ref["port_type"],
                "port_consolidated": ref["port_consolidated"],
                "port_coast": ref["port_coast"],
                "port_region": ref["port_region"],
                "latitude": clat,
                "longitude": clon,
                "census_alias_of": best_census_code,
            }
            ports_out[coord_code] = alias_entry
            coord_aliases += 1

            # Add to consolidated grouping
            consolidated = ref["port_consolidated"]
            if consolidated:
                consolidated_to_ports[consolidated].append(coord_code)

    if coord_aliases:
        logger.info(
            f"Added {coord_aliases} seaport coordinate aliases "
            f"(legacy codes mapped to Census ports)"
        )

    # Sort consolidated port lists
    consolidated_sorted = {
        k: sorted(v) for k, v in sorted(consolidated_to_ports.items())
    }

    # --- Build hierarchy ---
    hierarchy = _build_hierarchy(census_ports)

    # --- Assemble output ---
    output = {
        "_metadata": {
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_ports": len(ports_out),
            "seaports": seaport_count,
            "ports_with_coordinates": sum(
                1 for p in ports_out.values() if "latitude" in p
            ),
            "usace_crosswalk_entries": len(usace_to_census),
            "panjiva_crosswalk_entries": len(panjiva_to_census),
            "sources": {
                "census_port_reference": str(census_port_ref),
                "usace_port_dictionary": str(usace_dict_path),
                "usace_census_crosswalk": str(usace_crosswalk_path),
                "panjiva_ports_master": str(panjiva_crosswalk_path),
            },
        },
        "ports": ports_out,
        "crosswalks": {
            "usace_to_census": dict(sorted(
                usace_to_census.items(),
                key=lambda x: int(x[0]) if x[0].isdigit() else 0,
            )),
            "panjiva_to_census": dict(sorted(panjiva_to_census.items())),
            "consolidated_to_ports": consolidated_sorted,
        },
        "hierarchy": hierarchy,
    }

    # --- Write output ---
    out_dir = (
        root / "02_TOOLSETS" / "site_master_registry" / "data" / "reference"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "port_geo_dictionary.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"  Port Geo-Dictionary Built")
    print(f"{'=' * 60}")
    print(f"  Census ports:             {len(census_ports)}")
    print(f"  Coordinate aliases:       {coord_aliases}")
    print(f"  Total ports (dict keys):  {len(ports_out)}")
    print(f"  Seaports:                 {seaport_count}")
    print(f"  Ports with coordinates:   "
          f"{output['_metadata']['ports_with_coordinates']}")
    print(f"  USACE crosswalk entries:  {len(usace_to_census)}")
    print(f"  Panjiva crosswalk entries: {len(panjiva_to_census)}")
    print(f"  Consolidated groups:      {len(consolidated_sorted)}")
    print(f"  Coast/Region hierarchy:   "
          f"{len(hierarchy)} coasts, "
          f"{sum(len(r) for r in hierarchy.values())} regions")
    print(f"  Output: {out_path}")
    print(f"{'=' * 60}\n")

    return out_path


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="  %(message)s")

    # Determine project root
    this_dir = Path(__file__).resolve().parent
    # src/ -> site_master_registry/ -> 02_TOOLSETS/ -> project_root/
    project_root = this_dir.parent.parent.parent

    # Ensure geo_enrichment is importable
    if str(this_dir) not in sys.path:
        sys.path.insert(0, str(this_dir))

    build_port_geo_dictionary(project_root)
