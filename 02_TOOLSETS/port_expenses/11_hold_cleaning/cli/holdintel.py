#!/usr/bin/env python3
"""
holdintel - OceanDatum Hold Cleaning Intelligence CLI
Ocean-going Dry Bulk Carrier Hold Preparation & Cargo Readiness System

Commands:
  search        Search the knowledge base and web sources
  download      Download source documents (P&I circulars, USCG, IMO)
  lookup        Look up a cargo or cleanliness standard
  checklist     Generate a pre-loading checklist for a specific cargo
  report        Generate a hold cleaning readiness report
  sources       List all authoritative sources
  update        Check for new P&I club circulars / IMO updates
  marpol        MARPOL Annex V compliance check for wash water discharge
  survey        Generate survey preparation guide

Usage:
  holdintel search "grain clean soda ash"
  holdintel lookup --cargo "soda ash"
  holdintel lookup --standard "grain clean"
  holdintel checklist --cargo grain --previous-cargo coal --vessel panamax
  holdintel download --source ukpi --all-hold-cleaning
  holdintel download --url <url>
  holdintel report --cargo grain --previous coal --vessel-type panamax
  holdintel marpol --cargo "soda ash" --position "36N 075W"
  holdintel sources --type pi_club
  holdintel survey --cargo grain --port "Hampton Roads VA"
"""

import argparse
import json
import os
import sys
import textwrap
import re
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
KB_PATH  = BASE_DIR / "knowledge_base" / "hold_cleaning_kb.json"
DATA_DIR = BASE_DIR / "data"
DL_DIR   = DATA_DIR / "downloads"
SRC_DIR  = DATA_DIR / "sources"
CACHE_DIR= DATA_DIR / "cache"

for d in [DL_DIR, SRC_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Utilities ──────────────────────────────────────────────────────────────────

def load_kb() -> dict:
    """Load the knowledge base."""
    if not KB_PATH.exists():
        print(f"[ERROR] Knowledge base not found at: {KB_PATH}")
        sys.exit(1)
    with open(KB_PATH) as f:
        return json.load(f)

def banner(title: str, width: int = 72) -> None:
    print("\n" + "═" * width)
    print(f"  {title}")
    print("═" * width)

def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title.upper()}")
    print(f"{'─' * 60}")

def bullet(text: str, indent: int = 2) -> None:
    lines = textwrap.wrap(text, width=68)
    prefix = " " * indent + "• "
    for i, line in enumerate(lines):
        if i == 0:
            print(prefix + line)
        else:
            print(" " * (indent + 2) + line)

def header_block(lines: list) -> None:
    for line in lines:
        print(f"  {line}")

def fuzzy_match(query: str, text: str) -> bool:
    """Case-insensitive substring match across space-split tokens."""
    q = query.lower().strip()
    t = text.lower()
    # Direct match
    if q in t:
        return True
    # Token match - all words in query must appear somewhere in text
    tokens = q.split()
    return all(tok in t for tok in tokens)


# ── COMMANDS ───────────────────────────────────────────────────────────────────

def cmd_lookup(args):
    kb = load_kb()

    if args.cargo:
        cargo_name = args.cargo.lower().strip()
        banner(f"CARGO LOOKUP: {args.cargo.upper()}")

        # Search cargo-specific guidance
        cargo_found = False
        for key, data in kb.get("cargo_specific_guidance", {}).items():
            if fuzzy_match(cargo_name, key) or fuzzy_match(cargo_name, key.replace("_", " ")):
                cargo_found = True
                print(f"\n  Cargo: {key.replace('_',' ').title()}")
                print(f"  Cleanliness Required: {data.get('cleanliness_required','—')}")

                if "hold_requirements" in data:
                    section("Hold Requirements")
                    for req in data["hold_requirements"]:
                        bullet(req)

                if "regulatory_framework" in data:
                    section("Regulatory Framework")
                    for reg in data["regulatory_framework"]:
                        bullet(reg)

                if "pre_loading_requirements" in data:
                    section("Pre-Loading Requirements")
                    for req in data["pre_loading_requirements"]:
                        bullet(req)

                if "cargo_properties" in data:
                    section("Cargo Properties / Hazards")
                    for prop in data["cargo_properties"]:
                        bullet(prop)

                if "critical_restrictions" in data:
                    section("⚠  CRITICAL RESTRICTIONS")
                    for r in data["critical_restrictions"]:
                        bullet(r)

        if not cargo_found:
            print(f"\n  [!] No specific entry found for '{args.cargo}'.")
            print("  Run: holdintel sources  for a list of references to check manually.")

            # Try to find in cleanliness standards
            for std in kb.get("cleanliness_standards", {}).get("hierarchy", []):
                cargo_list = std.get("required_cargoes", [])
                if any(fuzzy_match(cargo_name, c) for c in cargo_list):
                    print(f"\n  Found reference in Cleanliness Standards:")
                    print(f"  Required standard: {std['name']}")
                    print(f"  Description: {std['description']}")

    elif args.standard:
        std_name = args.standard.lower().strip()
        banner(f"CLEANLINESS STANDARD LOOKUP: {args.standard.upper()}")

        for std in kb.get("cleanliness_standards", {}).get("hierarchy", []):
            aliases = [std["name"].lower()] + [a.lower() for a in std.get("aliases", [])]
            if any(fuzzy_match(std_name, a) for a in aliases):
                section(f"Standard #{std['rank']}: {std['name']}")
                print(f"\n  Description:\n")
                for line in textwrap.wrap(std["description"], 66):
                    print(f"    {line}")

                print(f"\n  Rust Tolerance:   {std.get('rust_tolerance','—')}")
                print(f"  Scale Tolerance:  {std.get('scale_tolerance','—')}")

                if "required_cargoes" in std:
                    print(f"\n  Typical Cargoes Requiring This Standard:")
                    for c in std["required_cargoes"]:
                        print(f"    • {c}")

                if "jurisdiction_variations" in std:
                    section("Jurisdiction Variations")
                    for jur, note in std["jurisdiction_variations"].items():
                        print(f"  {jur}:")
                        for line in textwrap.wrap(note, 60):
                            print(f"    {line}")

                if "practical_note" in std:
                    print(f"\n  Practical Note: {std['practical_note']}")
                return

        print(f"\n  [!] Standard '{args.standard}' not found.")
        print("  Available: hospital clean, grain clean, normal clean, shovel clean, load on top")

    else:
        print("Usage: holdintel lookup --cargo <cargo> OR --standard <standard>")


def cmd_checklist(args):
    kb = load_kb()
    cargo     = args.cargo.lower().strip() if args.cargo else "grain"
    prev_cargo = args.previous_cargo.lower().strip() if args.previous_cargo else "coal"
    vessel_type = args.vessel_type.upper() if args.vessel_type else "PANAMAX"

    banner(f"HOLD CLEANING CHECKLIST — {cargo.upper()} LOADING / POST-{prev_cargo.upper()} / {vessel_type}")
    header_block([
        f"Generated:    {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Previous Cargo: {prev_cargo.title()}",
        f"Next Cargo:     {cargo.title()}",
        f"Vessel Type:    {vessel_type}",
        ""
    ])

    # Determine cleanliness required
    cg = kb.get("cargo_specific_guidance", {})
    clean_req = "Grain Clean"  # default
    for key, data in cg.items():
        if fuzzy_match(cargo, key):
            clean_req = data.get("cleanliness_required", "Grain Clean")

    print(f"\n  ⚑  TARGET STANDARD: {clean_req.upper()}")

    proc = kb.get("cleaning_procedure", {})

    section("PHASE 1 — IMMEDIATE POST-DISCHARGE")
    phase1 = proc.get("phase_1_immediate_post_discharge", {})
    for i, step in enumerate(phase1.get("steps", []), 1):
        bullet(f"[{i}] {step}")

    section("PHASE 2 — DRY CLEANING")
    phase2 = proc.get("phase_2_dry_cleaning", {})
    for i, step in enumerate(phase2.get("steps", []), 1):
        bullet(f"[{i}] {step}")

    print(f"\n  ⚠  CRITICAL AREAS TO VERIFY:")
    for area in phase2.get("critical_areas", []):
        bullet(area)

    section("PHASE 3 — CHEMICAL WASH")
    chem = proc.get("phase_3_chemical_washing", {})
    chem_by_cargo = chem.get("chemistry_by_previous_cargo", {})
    matched_chem = None
    for key, data in chem_by_cargo.items():
        if fuzzy_match(prev_cargo, key):
            matched_chem = data
            break

    if matched_chem:
        print(f"\n  Challenge:   {matched_chem.get('challenge','')}")
        print(f"  Recommended: {matched_chem.get('recommended','')}")
        if "marpol_status" in matched_chem:
            print(f"  MARPOL:      {matched_chem['marpol_status']}")
        if "warning" in matched_chem:
            print(f"\n  ⛔ WARNING: {matched_chem['warning']}")
    else:
        print(f"\n  No specific chemical protocol for '{prev_cargo}'.")
        print("  Apply standard alkaline wash where appropriate.")

    section("PHASE 4 — SEAWATER WASH")
    phase4 = proc.get("phase_4_seawater_wash", {})
    for i, step in enumerate(phase4.get("steps", []), 1):
        bullet(f"[{i}] {step}")

    section("PHASE 5 — FRESH WATER RINSE  ⚑ CRITICAL")
    phase5 = proc.get("phase_5_freshwater_rinse", {})
    print(f"\n  WHY CRITICAL: {phase5.get('critical_importance','')}")
    print(f"\n  Timing: {phase5.get('timing','')}")
    print(f"  Quantity: {phase5.get('quantity_guide','')}")
    print(f"  Procedure: {phase5.get('procedure','')}")

    section("PHASE 6 — DRYING AND VENTILATION")
    phase6 = proc.get("phase_6_drying_ventilation", {})
    for i, step in enumerate(phase6.get("steps", []), 1):
        bullet(f"[{i}] {step}")

    section("PHASE 7 — PRE-SURVEY CLOSE-OUT CHECKS")
    close_outs = [
        "Inspect ALL bilge wells — open, clean, dry, covers grain-tight",
        "Bilge suction test — dry suck ONLY before survey (do NOT introduce water)",
        "Hatch cover inspection — rubbers, drain channels, seals, compression",
        "Check ALL underdeck frames and coaming frames with torch",
        "White glove / cloth test across representative surfaces",
        "Silver nitrate test — no chloride residue",
        "Check for insect infestation, larvae, eggs in all areas",
        "Confirm hold completely dry — zero standing water",
        "Verify hold is odour-free — especially if post-fishmeal or fertilizer",
        "Photograph: all holds from hatch opening before survey, note any issues",
        "Brief Mate and crew on EXACT deficiency locations and correction status",
        "Have cleaning crew standing by at survey to rectify any noted deficiencies immediately",
    ]
    for i, item in enumerate(close_outs, 1):
        bullet(f"[{i}] {item}")

    section("DOCUMENTATION REQUIRED")
    if "grain" in cargo:
        docs = kb.get("cargo_specific_guidance", {}).get("grain", {}).get("pre_loading_requirements", [])
        for doc in docs:
            bullet(doc)
    else:
        for d in ["Previous cargo records (minimum last 3 cargoes)", "Hold cleaning log with dates, methods, chemicals used", "Photographs of cleaned holds", "Charter party cleanliness clause review", "MARPOL Garbage Record Book entries for all wash water disposed"]:
            bullet(d)

    section("COMMON REASONS FOR SURVEY FAILURE — WATCH FOR")
    failures = kb.get("common_failure_reasons", {}).get("survey_failures", [])
    for f in failures:
        bullet(f"⚠  {f}")

    print(f"\n  {'═'*70}")
    print(f"  Checklist complete. Hold cleaning target: {clean_req.upper()}")
    print(f"  Sources: UK P&I, Skuld P&I, West of England, Swedish Club, NCB, USCG")
    print(f"  {'═'*70}\n")


def cmd_marpol(args):
    kb = load_kb()
    cargo = args.cargo if args.cargo else "unknown"
    position = args.position if args.position else "unknown"

    banner(f"MARPOL ANNEX V COMPLIANCE CHECK — {cargo.upper()}")
    header_block([
        f"Cargo:    {cargo}",
        f"Position: {position}",
        f"Date:     {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ])

    marpol = kb.get("regulatory_framework", {}).get("marpol_annex_v", {})

    section("GENERAL RULE")
    print(f"\n  {marpol.get('key_principle','')}")

    section("STEP 1 — DETERMINE HME STATUS")
    hme = marpol.get("hme_classification", {})
    print(f"\n  Is the cargo/residue classified as Harmful to Marine Environment (HME)?")
    print(f"\n  How to determine:")
    bullet("Check GESAMP Hazard Profiles")
    bullet("Check country UN GHS databases")
    bullet("Check IMSBC Code schedule for the cargo")
    bullet("Check IMDG Code (marine pollutant designation)")
    bullet("If in doubt: ASSUME HME and consult P&I club")
    print(f"\n  ⛔ IF HME: {hme.get('consequence_hme','')}")
    print(f"  ✓ IF NON-HME: {hme.get('consequence_non_hme','')}")

    section("STEP 2 — IDENTIFY SPECIAL AREA STATUS")
    discharge = marpol.get("discharge_rules_non_hme", {})
    special_areas = discharge.get("inside_special_areas", {}).get("areas", [])
    print(f"\n  MARPOL Annex V Special Areas (stricter rules apply):")
    for sa in special_areas:
        print(f"    • {sa}")

    section("STEP 3 — DISCHARGE CONDITIONS (NON-HME RESIDUES)")
    outside = discharge.get("outside_special_areas", {})
    print(f"\n  OUTSIDE Special Areas — ALL conditions must be met:")
    for i in range(1, 6):
        key = f"condition_{i}"
        if key in outside:
            bullet(f"[{i}] {outside[key]}")

    inside = discharge.get("inside_special_areas", {})
    print(f"\n  INSIDE Special Areas:")
    bullet(inside.get("rule", ""))
    print(f"\n  Narrow exception:")
    bullet(inside.get("narrow_exception", ""))

    section("STEP 4 — CLEANING AGENTS / ADDITIVES")
    agents = marpol.get("cleaning_agents_discharge", {})
    print(f"\n  Rule: {agents.get('rule','')}")
    print(f"  Documentation: {agents.get('documentation_required','')}")
    print(f"\n  COMPLIANT example: {agents.get('example_compliant','')}")
    print(f"  NON-COMPLIANT example: {agents.get('example_non_compliant','')}")

    section("STEP 5 — RECORD KEEPING")
    records = marpol.get("record_keeping", {})
    print(f"\n  Required: {records.get('garbage_record_book','')}")
    print(f"  Category: {records.get('cargo_residue_category','')}")
    print(f"  Required entries: {records.get('required_entries','')}")
    print(f"  Retention: {records.get('retention','')}")

    section("⚠  ENFORCEMENT RISK")
    enf = marpol.get("enforcement_risk", {})
    for k, v in enf.items():
        bullet(v)

    print(f"\n  Reference: Japan P&I Club Circular; Skuld Guidance; ITOPF Technical Advisory\n")


def cmd_sources(args):
    kb = load_kb()
    source_type = args.type.lower() if args.type else None

    banner("AUTHORITATIVE SOURCES — HOLD CLEANING / BULK CARRIER CARGO PREP")

    sources = kb.get("authoritative_sources", {})

    if not source_type or source_type in ("pi_club", "pi", "p&i"):
        section("P&I CLUBS")
        for club in sources.get("pi_clubs", []):
            print(f"\n  {club['name']}")
            for pub in club.get("key_publications", []):
                print(f"    ├─ [{pub.get('type','—')}] {pub['title']}")
                if "url" in pub:
                    print(f"    │   URL: {pub['url']}")

    if not source_type or source_type in ("regulatory", "reg", "uscg", "imo"):
        section("REGULATORY BODIES")
        for body in sources.get("regulatory_bodies", []):
            print(f"\n  {body['name']}")
            for ref in body.get("key_references", []):
                print(f"    ├─ [{ref.get('type','—')}] {ref['title']}")
                if "url" in ref:
                    print(f"    │   URL: {ref['url']}")
                if "note" in ref:
                    print(f"    │   Note: {ref['note']}")

    if not source_type or source_type in ("technical", "service", "vendor"):
        section("TECHNICAL SERVICE PROVIDERS & REFERENCE SITES")
        for prov in sources.get("technical_service_providers", []):
            print(f"\n  {prov['name']}")
            print(f"    Specialty: {prov['specialty']}")
            if "main_url" in prov:
                print(f"    URL: {prov['main_url']}")
            elif "url" in prov:
                print(f"    URL: {prov['url']}")
            if "key_products" in prov:
                for p in prov["key_products"][:3]:
                    print(f"    • {p}")

    if not source_type or source_type in ("youtube", "video"):
        section("VIDEO RESOURCES (YOUTUBE)")
        for vid in sources.get("youtube_resources", []):
            if "title" in vid:
                print(f"\n  {vid['title']}")
                print(f"    URL: {vid['url']}")
                if "note" in vid:
                    print(f"    Note: {vid['note']}")
            if "youtube_search_url" in vid:
                print(f"\n  Recommended YouTube Searches:")
                print(f"    Base URL: {vid['youtube_search_url']}")
                for s in vid.get("suggested_searches", []):
                    print(f"    • {s}")


def cmd_download(args):
    """Download source documents from known authoritative URLs."""
    banner("DOCUMENT DOWNLOADER")

    try:
        import urllib.request
        import urllib.error
    except ImportError:
        print("[ERROR] urllib not available")
        sys.exit(1)

    # Map of source shortcodes to download lists
    source_map = {
        "ukpi": [
            ("UK_PI_FAQ_Hold_Preparation_2021.html", "https://www.ukpandi.com/news-and-resources/articles/2021/faq-hold-preparation-and-cleaning/"),
            ("UK_PI_Carefully_to_Carry_2023_Ch17.pdf", "https://www.ukpandi.com/fileadmin/uploads/ukpandi/Documents/uk-p-i-club/carefully-to-carry/2023/UKPI_Carefully_to_Carry_2023_17.pdf"),
            ("UK_PI_Carefully_to_Carry_2023_Ch1.pdf", "https://www.ukpandi.com/fileadmin/uploads/ukpandi/Documents/uk-p-i-club/carefully-to-carry/2023/UKPI_Carefully_to_Carry_2023_1.pdf"),
            ("UK_PI_Bulk_Matters_Grain.pdf", "https://maritimesafetyinnovationlab.org/wp-content/uploads/2021/03/Bulk-Matters-UK-PampI.pdf"),
        ],
        "skuld": [
            ("Skuld_Preparing_Cargo_Holds_Solid_Bulk.pdf", "https://www.skuld.com/contentassets/e2d486e683a84d7582fa1b867d18f8ac/preparing-cargo-holds_-loading-solid-bulk-cargoes.pdf"),
            ("Skuld_MARPOL_Annex_V_Cargo_Residue_Disposal.pdf", "https://www.skuld.com/contentassets/ec787ec7bd6c49d99a5878b1d0769cfd/guidance_on_disposal_of_cargo_residues_in_line_with_marpol_annex_v-version2-2017october.pdf"),
        ],
        "west": [
            ("WestOfEngland_Cargo_Hold_Cleaning_LP_Bulletin.pdf", "https://www.westpandi.com/globalassets/loss-prevention/loss-prevention-bulletins/west-of-england---loss-prevention-bulletin---cargo-hold-cleaning.pdf"),
        ],
        "swedish": [
            ("SwedishClub_Hold_Cleaning_Guide_2023.pdf", "https://www.swedishclub.com/uploads/2023/12/Cargo-Advice-Hold-cleaning-guide.pdf"),
        ],
        "uscg": [
            ("USCG_NVIC_5-94_Grain_Code.pdf", "https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/5ps/NVIC/1994/n5-94.pdf"),
            ("USCG_NVIC_3-97_Grain_ABS.pdf", "https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/5ps/NVIC/1997/n3-97.pdf"),
            ("USCG_FFVE_Manual.pdf", "https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/CG-5PC/CG-CVC/Guidance/CGTTP_3.72%208_Foreign_Freight_Vessel_Exam_FCD.pdf"),
        ],
        "itopf": [
            ("ITOPF_MARPOL_Annex_V_Compliance.pdf", "https://www.itopf.org/fileadmin/uploads/itopf/data/Documents/TIPS%20TAPS/UK_CLUB_PRINT_MARPOL_July_2013_online_version.pdf"),
        ],
        "wilhelmsen": [
            ("Wilhelmsen_NAVADAN_Quick_Guide.html", "https://manuals.plus/m/914c623c1ea411ec320e3d13ee6e489e489075a75381cb7beaa0e6a8e299f520"),
        ]
    }

    # Single URL download
    if args.url:
        filename = args.output or Path(args.url).name or "download.bin"
        outpath = DL_DIR / filename
        print(f"\n  Downloading: {args.url}")
        print(f"  Saving to:   {outpath}")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (OceanDatum HoldIntel Research Tool)"}
            req = urllib.request.Request(args.url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
            with open(outpath, "wb") as f:
                f.write(content)
            print(f"  ✓ Downloaded {len(content):,} bytes → {outpath}")
        except Exception as e:
            print(f"  ✗ Download failed: {e}")
        return

    # Source-based download
    if args.source:
        source = args.source.lower()
        if source not in source_map and source != "all":
            print(f"  [!] Unknown source '{args.source}'. Available:")
            for k in source_map:
                print(f"    • {k}")
            return

        targets = []
        if source == "all":
            for items in source_map.values():
                targets.extend(items)
        else:
            targets = source_map[source]

        print(f"\n  Downloading {len(targets)} document(s)...")
        for filename, url in targets:
            outpath = DL_DIR / filename
            if outpath.exists() and not args.force:
                print(f"  ⊘ Already exists (--force to re-download): {filename}")
                continue
            print(f"  ↓ {filename}")
            try:
                headers = {"User-Agent": "Mozilla/5.0 (OceanDatum HoldIntel Research Tool)"}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=45) as resp:
                    content = resp.read()
                with open(outpath, "wb") as f:
                    f.write(content)
                size_kb = len(content) // 1024
                print(f"    ✓ {size_kb} KB saved")
            except Exception as e:
                print(f"    ✗ Failed: {e}")
                # Log failed URL
                with open(CACHE_DIR / "failed_downloads.log", "a") as log:
                    log.write(f"{datetime.now().isoformat()} | {filename} | {url} | {e}\n")
        print(f"\n  Downloads saved to: {DL_DIR}")
        return

    # If no args, list available downloads
    print("\n  Available source download bundles:")
    for key, items in source_map.items():
        print(f"\n  --source {key}  ({len(items)} files)")
        for fname, url in items:
            print(f"    • {fname}")
    print("\n  Or use --url <direct_url> to download any specific document.")
    print("  Use --all-hold-cleaning to download all known sources.")


def cmd_search(args):
    """Search knowledge base for a query."""
    kb = load_kb()
    query = " ".join(args.query).lower()
    banner(f"KNOWLEDGE BASE SEARCH: '{query}'")

    results = []

    def scan_dict(d, path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                scan_dict(v, path + "/" + k)
        elif isinstance(d, list):
            for i, item in enumerate(d):
                scan_dict(item, path + f"[{i}]")
        elif isinstance(d, str):
            if fuzzy_match(query, d):
                results.append((path, d))

    scan_dict(kb)

    if not results:
        print(f"\n  No results found for '{query}'")
        print("  Try: holdintel lookup --cargo <cargo>  or  holdintel lookup --standard <standard>")
        return

    # Deduplicate and show best results
    seen = set()
    shown = 0
    for path, text in results:
        if text in seen:
            continue
        seen.add(text)
        if shown >= 20:
            break
        # Only show reasonably short results
        if len(text) < 500:
            print(f"\n  [{path}]")
            for line in textwrap.wrap(text, 68):
                print(f"    {line}")
            shown += 1

    if shown == 0:
        print(f"\n  Matches found in large text blocks. Use 'holdintel lookup' for structured results.")

    print(f"\n  Total raw matches: {len(results)}")


def cmd_report(args):
    """Generate a hold cleaning readiness report."""
    kb = load_kb()
    cargo     = args.cargo or "grain"
    prev      = args.previous or "coal"
    vtype     = args.vessel_type or "Panamax"
    port      = args.port or "TBD"
    date_str  = datetime.now().strftime("%Y-%m-%d")

    banner(f"HOLD CLEANING READINESS REPORT — {cargo.upper()} / {vtype.upper()}")
    print(f"""
  REPORT DATE:      {date_str}
  NEXT CARGO:       {cargo.title()}
  PREVIOUS CARGO:   {prev.title()}
  VESSEL TYPE:      {vtype.title()}
  LOADING PORT:     {port}
  PREPARED BY:      OceanDatum HoldIntel CLI v1.0

  NOTE: This report is a decision-support tool. Master and operators
  must verify against applicable charterparty, voyage instructions,
  flag state regulations, and local port requirements.
""")

    # Determine standard required
    cg = kb.get("cargo_specific_guidance", {})
    std_req = "Grain Clean"
    for key, data in cg.items():
        if fuzzy_match(cargo.lower(), key):
            std_req = data.get("cleanliness_required", std_req)
            break

    section("1. CLEANLINESS STANDARD REQUIRED")
    print(f"\n  Target: {std_req.upper()}")

    # Find standard definition
    for std in kb.get("cleanliness_standards", {}).get("hierarchy", []):
        if fuzzy_match(std_req.lower(), std["name"].lower()):
            print(f"\n  Definition: {std['description']}")
            print(f"  Rust Tolerance: {std.get('rust_tolerance','')}")
            print(f"  Scale Tolerance: {std.get('scale_tolerance','')}")
            break

    section("2. CLEANING CHALLENGE ASSESSMENT")
    chem = kb.get("cleaning_procedure", {}).get("phase_3_chemical_washing", {})
    chem_map = chem.get("chemistry_by_previous_cargo", {})
    challenge_found = False
    for key, data in chem_map.items():
        if fuzzy_match(prev.lower(), key):
            print(f"\n  Previous Cargo Type: {key.replace('_',' ').title()}")
            print(f"  Challenge: {data.get('challenge','')}")
            print(f"  Recommended: {data.get('recommended','')}")
            if "warning" in data:
                print(f"  ⛔ WARNING: {data['warning']}")
            if "marpol_status" in data:
                print(f"  MARPOL Status: {data['marpol_status']}")
            challenge_found = True
            break

    if not challenge_found:
        print(f"\n  No specific protocol found for previous cargo '{prev}'.")
        print("  Apply standard cleaning protocol. Verify with technical manager.")

    section("3. REGULATORY COMPLIANCE CHECKLIST")
    if "grain" in cargo.lower():
        grain_data = kb.get("cargo_specific_guidance", {}).get("grain", {})
        for req in grain_data.get("regulatory_framework", []):
            bullet(req)
        print()
        for req in grain_data.get("pre_loading_requirements", []):
            bullet(f"[ ] {req}")
    else:
        print(f"\n  [ ] Review charterparty cleanliness clause")
        print(f"  [ ] Verify IMSBC Code schedule for {cargo}")
        print(f"  [ ] Determine HME status for wash water MARPOL compliance")
        print(f"  [ ] Confirm surveyor requirements at {port}")

    section("4. MARPOL ANNEX V — WASH WATER DISPOSAL")
    marpol = kb.get("regulatory_framework", {}).get("marpol_annex_v", {})
    print(f"\n  Default Rule: {marpol.get('key_principle','')}")
    outside = marpol.get("discharge_rules_non_hme", {}).get("outside_special_areas", {})
    print(f"\n  For discharge outside Special Areas (non-HME cargo):")
    for i in range(1, 4):
        key = f"condition_{i}"
        if key in outside:
            bullet(f"{outside[key]}")

    section("5. SURVEY PREPARATION")
    failures = kb.get("common_failure_reasons", {}).get("survey_failures", [])
    print(f"\n  Top risks for survey failure (verify each cleared):")
    for f in failures[:8]:
        bullet(f"[ ] {f}")

    section("6. KEY REFERENCE SOURCES")
    refs = [
        ("UK P&I Club FAQ", "https://www.ukpandi.com/news-and-resources/articles/2021/faq-hold-preparation-and-cleaning/"),
        ("Skuld Hold Cleaning Guide", "https://www.skuld.com/topics/cargo/solid-bulk/general-advice/guidance-on-preparing-cargo-holds-and-loading-of-solid-bulk-cargoes/"),
        ("Swedish Club Hold Cleaning Guide 2023", "https://www.swedishclub.com/uploads/2023/12/Cargo-Advice-Hold-cleaning-guide.pdf"),
        ("West of England LP Bulletin", "https://www.westpandi.com/news-and-resources/loss-prevention-bulletins/cargo-hold-cleaning/"),
        ("NCB Grain Certificate of Readiness", "https://natcargo.org/service/cgvs-grain-certificate-of-readiness/"),
        ("USCG NVIC 5-94", "https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/5ps/NVIC/1994/n5-94.pdf"),
    ]
    for name, url in refs:
        print(f"\n  {name}")
        print(f"    {url}")

    print(f"\n  {'═'*70}")
    print(f"  Report complete. OceanDatum HoldIntel | {date_str}")
    print(f"  {'═'*70}\n")


def cmd_update(args):
    """Check for new circulars / updates (future web-fetch module)."""
    banner("SOURCE UPDATE CHECK")
    sources_to_check = [
        ("UK P&I Club - News & Publications", "https://www.ukpandi.com/news-and-resources/"),
        ("Skuld - Cargo Topics", "https://www.skuld.com/topics/cargo/"),
        ("West of England P&I - Loss Prevention", "https://www.westpandi.com/news-and-resources/loss-prevention-bulletins/"),
        ("Swedish Club - Cargo Advice", "https://www.swedishclub.com/"),
        ("Gard - Insight", "https://www.gard.no/web/publications"),
        ("Standard Club - Publications", "https://www.standard-club.com/knowledge-hub/"),
        ("North P&I - Loss Prevention", "https://www.nepia.com/"),
        ("Japan P&I Club - Circulars", "https://www.piclub.or.jp/en/"),
        ("Safety4Sea - Bulk Carriers", "https://safety4sea.com/?s=hold+cleaning+bulk+carrier"),
        ("IMO - MEPC Resolutions", "https://www.imo.org/en/KnowledgeCentre/IndexofIMOResolutions/Pages/MEPC.aspx"),
        ("NCB - News", "https://natcargo.org/news/"),
        ("BIMCO - Circulars", "https://www.bimco.org/"),
    ]
    print(f"\n  Monitoring sources for new circulars and publications:\n")
    for name, url in sources_to_check:
        print(f"  ► {name}")
        print(f"    {url}\n")
    print("  [i] Automated web monitoring module: coming in v2.0")
    print("  [i] Use: holdintel download --source <name> to fetch known documents")


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="holdintel",
        description="OceanDatum Hold Cleaning Intelligence CLI — Ocean-going Dry Bulk Carrier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  holdintel lookup --cargo "soda ash"
  holdintel lookup --standard "grain clean"
  holdintel checklist --cargo grain --previous-cargo coal --vessel-type panamax
  holdintel checklist --cargo "soda ash" --previous-cargo "iron ore"
  holdintel marpol --cargo "soda ash" --position "36N 075W"
  holdintel report --cargo grain --previous coal --vessel-type panamax --port "Hampton Roads"
  holdintel sources --type pi_club
  holdintel download --source ukpi
  holdintel download --source all
  holdintel download --url https://example.com/document.pdf --output my_doc.pdf
  holdintel search "loose rust scale grain"
  holdintel update
        """
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- lookup ---
    p_lookup = sub.add_parser("lookup", help="Look up cargo or cleanliness standard")
    p_lookup.add_argument("--cargo", "-c", help="Cargo name (e.g. 'soda ash', 'grain', 'coal')")
    p_lookup.add_argument("--standard", "-s", help="Cleanliness standard (e.g. 'grain clean', 'hospital clean')")

    # --- checklist ---
    p_check = sub.add_parser("checklist", help="Generate pre-loading hold cleaning checklist")
    p_check.add_argument("--cargo", "-c", default="grain", help="Next cargo to load")
    p_check.add_argument("--previous-cargo", "--prev", default="coal", help="Previous cargo carried")
    p_check.add_argument("--vessel-type", "-v", default="Panamax", help="Vessel type (Handysize/Supramax/Panamax/Capesize)")

    # --- marpol ---
    p_marpol = sub.add_parser("marpol", help="MARPOL Annex V wash water discharge compliance check")
    p_marpol.add_argument("--cargo", "-c", help="Cargo/residue type")
    p_marpol.add_argument("--position", "-p", help="Current vessel position (e.g. '36N 075W')")

    # --- report ---
    p_report = sub.add_parser("report", help="Generate hold cleaning readiness report")
    p_report.add_argument("--cargo", "-c", help="Next cargo")
    p_report.add_argument("--previous", "--prev", help="Previous cargo")
    p_report.add_argument("--vessel-type", "-v", help="Vessel type")
    p_report.add_argument("--port", "-p", help="Loading port")

    # --- sources ---
    p_sources = sub.add_parser("sources", help="List authoritative sources")
    p_sources.add_argument("--type", "-t", choices=["pi_club", "pi", "regulatory", "technical", "youtube", "all"],
                           help="Filter by source type")

    # --- download ---
    p_dl = sub.add_parser("download", help="Download source documents")
    p_dl.add_argument("--source", "-s", help="Source shortcode (ukpi, skuld, west, swedish, uscg, itopf, wilhelmsen, all)")
    p_dl.add_argument("--url", "-u", help="Direct URL to download")
    p_dl.add_argument("--output", "-o", help="Output filename (for --url)")
    p_dl.add_argument("--force", "-f", action="store_true", help="Re-download even if file exists")
    p_dl.add_argument("--all-hold-cleaning", action="store_true", help="Download all known hold cleaning documents")

    # --- search ---
    p_search = sub.add_parser("search", help="Search knowledge base")
    p_search.add_argument("query", nargs="+", help="Search terms")

    # --- update ---
    sub.add_parser("update", help="Check for new P&I / regulatory updates")

    args = parser.parse_args()

    dispatch = {
        "lookup":    cmd_lookup,
        "checklist": cmd_checklist,
        "marpol":    cmd_marpol,
        "report":    cmd_report,
        "sources":   cmd_sources,
        "download":  cmd_download,
        "search":    cmd_search,
        "update":    cmd_update,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
