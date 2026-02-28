#!/usr/bin/env python3
"""
STB Amended Contract Summary (ACS) PDF Parser
==============================================
Parses ACS PDF filings from the Surface Transportation Board into structured
data suitable for database storage.

Usage:
    python parse_acs_pdf.py <pdf_path> [--json] [--csv] [--sql] [--sqlite]

Examples:
    python parse_acs_pdf.py ACS-UP-4Q-11-29-2021.pdf --json --csv
    python parse_acs_pdf.py ACS-UP-4Q-11-29-2021.pdf --sqlite
"""

import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ContractSummary:
    contract_id: str = ""
    railroad: str = ""
    issued_date: str = ""
    effective_date: str = ""
    issuer_name: str = ""
    issuer_title: str = ""
    issuer_address: str = ""
    participating_carriers: list = field(default_factory=list)
    commodities: list = field(default_factory=list)
    shippers: list = field(default_factory=list)
    origins: list = field(default_factory=list)
    destinations: list = field(default_factory=list)
    ports: str = ""
    duration_effective_date: str = ""
    duration_amendment_effective_date: str = ""
    duration_expiration_date: str = ""
    rail_car_data: str = ""
    rates_and_charges: str = ""
    volume: str = ""
    special_features: str = ""
    special_notice: str = ""
    exhibit_definitions: dict = field(default_factory=dict)
    source_file: str = ""
    filing_received_date: str = ""


# Section labels that delimit fields in the contract text
SECTION_LABELS = [
    "PARTICIPATING CARRIERS:",
    "COMMODITY:",
    "SHIPPER:",
    "ORIGIN(S):",
    "DESTINATION(S):",
    "PORT(S):",
    "DURATION:",
    "RAIL CAR DATA:",
    "RATES & CHARGES:",
    "VOLUME:",
    "SPECIAL FEATURES:",
    "SPECIAL NOTICE:",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def strip_amendment_marker(text):
    """Strip ADDITION/DELETION/EXTENSION markers and return (cleaned, marker)."""
    for marker in ["ADDITION", "DELETION", "EXTENSION"]:
        if text.rstrip().endswith(marker):
            return text.rstrip()[: -len(marker)].rstrip(), marker
    return text.rstrip(), None


def parse_location(line):
    """Parse a location line like 'MILWAUKEE, WI ADDITION' into a dict."""
    cleaned, marker = strip_amendment_marker(line.strip())
    is_ags = bool(re.search(r'\bAGS\b', cleaned))
    city, state = "", ""
    loc_match = re.match(r'^(.+?),\s*([A-Z]{2})$', cleaned)
    if loc_match:
        city = loc_match.group(1).strip()
        state = loc_match.group(2).strip()
    return {
        "location": cleaned,
        "city": city,
        "state": state,
        "amendment_action": marker,
        "is_ags_reference": is_ags,
    }


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------
def extract_pdf_text(pdf_path):
    """Extract all text from a PDF using pdfplumber."""
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text


# ---------------------------------------------------------------------------
# Split full text into individual contract blocks
# ---------------------------------------------------------------------------
def split_into_contract_blocks(full_text):
    """
    Split the full PDF text into individual contract blocks.
    Each contract starts with a line like 'STB-UPOTMQ 150381-F' followed by
    a railroad name and 'AMENDED CONTRACT SUMMARY'.
    """
    # Pattern: contract ID line (STB-XXXXX NNNNN-X)
    contract_pattern = re.compile(
        r'^(STB-[A-Z]{2,}[A-Z0-9]*\s+\d+[-A-Z0-9]+)\s*$', re.MULTILINE
    )

    # Find all contract ID occurrences
    matches = list(contract_pattern.finditer(full_text))

    # Contract IDs appear at start AND end of each contract block.
    # Group by unique ID: first occurrence = start, last = end marker.
    id_positions = {}
    for m in matches:
        cid = m.group(1).strip()
        if cid not in id_positions:
            id_positions[cid] = {"first": m.start(), "positions": []}
        id_positions[cid]["positions"].append(m.start())

    # Build blocks: from first occurrence of ID to first occurrence of next ID
    blocks = []
    sorted_ids = sorted(id_positions.items(), key=lambda x: x[1]["first"])

    for i, (cid, info) in enumerate(sorted_ids):
        start = info["first"]
        if i + 1 < len(sorted_ids):
            end = sorted_ids[i + 1][1]["first"]
        else:
            end = len(full_text)
        block_text = full_text[start:end]

        # Verify it contains AMENDED CONTRACT SUMMARY
        if "AMENDED CONTRACT SUMMARY" in block_text or "CONTRACT SUMMARY" in block_text:
            blocks.append((cid, block_text))

    return blocks


# ---------------------------------------------------------------------------
# Extract sections from a contract block
# ---------------------------------------------------------------------------
def extract_sections(block_text):
    """Split a contract block into named sections."""
    lines = block_text.split("\n")
    sections = {}
    current_section = "_HEADER"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        if stripped in SECTION_LABELS:
            current_section = stripped
            sections[current_section] = []
            continue
        if stripped == "EXHIBIT DEFINITIONS:":
            current_section = "EXHIBIT DEFINITIONS:"
            sections[current_section] = []
            continue
        sections.setdefault(current_section, [])
        sections[current_section].append(stripped)

    return sections


# ---------------------------------------------------------------------------
# Parse a single contract block
# ---------------------------------------------------------------------------
def parse_contract(contract_id, block_text, source_file="",
                   filing_received_date=""):
    """Parse a single contract block into a ContractSummary."""
    cs = ContractSummary()
    cs.contract_id = contract_id
    cs.source_file = source_file
    cs.filing_received_date = filing_received_date

    sections = extract_sections(block_text)

    # --- Header (dates, issuer, railroad) ---
    header_lines = [l for l in sections.get("_HEADER", []) if l]
    for line in header_lines:
        date_match = re.findall(r'([A-Z][a-z]+ \d{1,2}, \d{4})', line)
        if len(date_match) == 2 and not cs.issued_date:
            cs.issued_date = date_match[0]
            cs.effective_date = date_match[1]
        elif len(date_match) == 1 and not cs.issued_date:
            cs.issued_date = date_match[0]

    # Railroad name (line after contract ID, before AMENDED CONTRACT SUMMARY)
    for line in header_lines:
        if "RAILROAD" in line or "RAILWAY" in line:
            cs.railroad = line.strip()
            break

    # Issuer info
    issuer_lines = []
    in_issuer = False
    for line in header_lines:
        if line == "Issued by:":
            in_issuer = True
            continue
        if in_issuer:
            issuer_lines.append(line)
    if issuer_lines:
        cs.issuer_name = issuer_lines[0] if len(issuer_lines) > 0 else ""
        cs.issuer_title = issuer_lines[1] if len(issuer_lines) > 1 else ""
        cs.issuer_address = "; ".join(issuer_lines[2:]) if len(issuer_lines) > 2 else ""

    # --- Participating Carriers ---
    carrier_lines = [l for l in sections.get("PARTICIPATING CARRIERS:", []) if l]
    carriers = []
    current_carrier = None
    current_address = []
    current_marker = None

    for line in carrier_lines:
        if line.startswith("STB-"):
            continue
        cleaned, marker = strip_amendment_marker(line)
        is_address = (
            bool(re.match(r'^\d+\s', cleaned)) or
            bool(re.match(r'^P\.?O\.?\s', cleaned, re.IGNORECASE)) or
            bool(re.match(r'^Col\.\s', cleaned)) or
            bool(re.search(r',\s*[A-Z]{2}\s+\d{4,5}', cleaned)) or
            bool(re.search(r',\s*[A-Z]{2}\s+[A-Z]\d[A-Z]', cleaned)) or
            bool(re.search(r'City,\s*\w+\s+\d{5}', cleaned)) or
            bool(re.match(r'^Mail Stop', cleaned))
        )
        if is_address and current_carrier:
            current_address.append(cleaned)
        else:
            if current_carrier:
                carriers.append({
                    "name": current_carrier,
                    "address": "; ".join(current_address) if current_address else "",
                    "amendment_action": current_marker,
                })
            current_carrier = cleaned
            current_marker = marker
            current_address = []

    if current_carrier:
        carriers.append({
            "name": current_carrier,
            "address": "; ".join(current_address) if current_address else "",
            "amendment_action": current_marker,
        })
    cs.participating_carriers = carriers

    # --- Commodities ---
    commodity_lines = [l for l in sections.get("COMMODITY:", []) if l]
    commodities = []
    buffer = ""
    for line in commodity_lines:
        if line.startswith("STB-"):
            continue
        # Continuation lines start lowercase or digit (STCC codes)
        if buffer and len(line) > 0 and (line[0].islower() or line[0].isdigit()):
            buffer += " " + line
        else:
            if buffer:
                cleaned, marker = strip_amendment_marker(buffer)
                commodities.append({"description": cleaned, "amendment_action": marker})
            buffer = line
    if buffer:
        cleaned, marker = strip_amendment_marker(buffer)
        commodities.append({"description": cleaned, "amendment_action": marker})
    cs.commodities = commodities

    # --- Shippers ---
    shipper_lines = [l for l in sections.get("SHIPPER:", []) if l]
    cs.shippers = [l.strip() for l in shipper_lines if not l.startswith("STB-")]

    # --- Origins ---
    origin_lines = [l for l in sections.get("ORIGIN(S):", []) if l]
    cs.origins = [parse_location(l) for l in origin_lines if not l.startswith("STB-")]

    # --- Destinations ---
    dest_lines = [l for l in sections.get("DESTINATION(S):", []) if l]
    cs.destinations = [parse_location(l) for l in dest_lines if not l.startswith("STB-")]

    # --- Ports ---
    port_lines = [l for l in sections.get("PORT(S):", []) if l]
    cs.ports = "; ".join(l for l in port_lines if not l.startswith("STB-"))

    # --- Duration ---
    duration_lines = [l for l in sections.get("DURATION:", []) if l]
    for line in duration_lines:
        if line.startswith("STB-"):
            continue
        cleaned, _ = strip_amendment_marker(line)
        if "Effective Date:" in cleaned and "Amendment" not in cleaned:
            cs.duration_effective_date = cleaned.replace("Effective Date:", "").strip()
        elif "Amendment Effective Date:" in cleaned:
            cs.duration_amendment_effective_date = cleaned.replace(
                "Amendment Effective Date:", ""
            ).strip()
        elif "Expiration Date:" in cleaned:
            cs.duration_expiration_date = cleaned.replace("Expiration Date:", "").strip()

    # --- Simple text fields ---
    for section_key, attr in [
        ("RAIL CAR DATA:", "rail_car_data"),
        ("RATES & CHARGES:", "rates_and_charges"),
        ("VOLUME:", "volume"),
        ("SPECIAL FEATURES:", "special_features"),
        ("SPECIAL NOTICE:", "special_notice"),
    ]:
        lines_list = [l for l in sections.get(section_key, []) if l]
        setattr(cs, attr, "; ".join(l for l in lines_list if not l.startswith("STB-")))

    # --- Exhibit Definitions ---
    exhibit_lines = [l for l in sections.get("EXHIBIT DEFINITIONS:", []) if l]
    exhibits = {}
    current_exhibit = None
    for line in exhibit_lines:
        if line.startswith("STB-"):
            continue
        exhibit_match = re.match(r'^(.+?)\s+consist[s]?\s+of:', line, re.IGNORECASE)
        if exhibit_match:
            current_exhibit = exhibit_match.group(1).strip()
            exhibits[current_exhibit] = []
        elif current_exhibit:
            cleaned, marker = strip_amendment_marker(line)
            if cleaned:
                exhibits[current_exhibit].append(cleaned)
    cs.exhibit_definitions = exhibits

    return cs


# ---------------------------------------------------------------------------
# Main: parse an entire PDF
# ---------------------------------------------------------------------------
def parse_acs_pdf(pdf_path):
    """Parse an entire ACS PDF file and return a list of ContractSummary objects."""
    full_text = extract_pdf_text(pdf_path)

    # Extract filing received date from cover page
    filing_date = ""
    date_match = re.search(
        r'received.*?on\s+(\w+ \d{1,2}, \d{4})', full_text, re.IGNORECASE
    )
    if date_match:
        filing_date = date_match.group(1)

    blocks = split_into_contract_blocks(full_text)

    contracts = []
    for contract_id, block_text in blocks:
        cs = parse_contract(
            contract_id, block_text,
            source_file=os.path.basename(pdf_path),
            filing_received_date=filing_date,
        )
        contracts.append(cs)

    return contracts


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------
def contracts_to_json(contracts):
    """Serialize contracts to JSON."""
    return json.dumps([asdict(c) for c in contracts], indent=2, default=str)


def contracts_to_csv_rows(contracts):
    """Flatten contracts to one-row-per-contract for CSV export."""
    rows = []
    for c in contracts:
        row = {
            "contract_id": c.contract_id,
            "railroad": c.railroad,
            "issued_date": c.issued_date,
            "effective_date": c.effective_date,
            "issuer_name": c.issuer_name,
            "carriers": "; ".join(ca["name"] for ca in c.participating_carriers),
            "commodities": "; ".join(co["description"] for co in c.commodities),
            "shippers": "; ".join(c.shippers),
            "origins": "; ".join(o["location"] for o in c.origins),
            "destinations": "; ".join(d["location"] for d in c.destinations),
            "ports": c.ports,
            "effective_date_duration": c.duration_effective_date,
            "amendment_effective_date": c.duration_amendment_effective_date,
            "expiration_date": c.duration_expiration_date,
            "rail_car_data": c.rail_car_data,
            "rates_and_charges": c.rates_and_charges,
            "volume": c.volume,
            "special_features": c.special_features,
            "special_notice": c.special_notice,
            "num_origins": len(c.origins),
            "num_destinations": len(c.destinations),
            "num_commodities": len(c.commodities),
            "source_file": c.source_file,
            "filing_received_date": c.filing_received_date,
        }
        rows.append(row)
    return rows


def generate_sql_schema():
    """Generate normalized SQL CREATE TABLE statements."""
    return """\
-- ============================================================================
-- STB Amended Contract Summary (ACS) - Normalized Database Schema
-- ============================================================================

-- Filing-level metadata (one PDF = one filing)
CREATE TABLE IF NOT EXISTS acs_filing (
    filing_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file          TEXT NOT NULL,
    filing_received_date TEXT,
    railroad             TEXT NOT NULL,
    parsed_at            TEXT DEFAULT (datetime('now'))
);

-- Contract-level data (one row per contract summary within a filing)
CREATE TABLE IF NOT EXISTS acs_contract (
    contract_id                  TEXT PRIMARY KEY,
    filing_id                    INTEGER NOT NULL REFERENCES acs_filing(filing_id),
    document_type                TEXT DEFAULT 'AMENDED CONTRACT SUMMARY',
    issued_date                  TEXT,
    effective_date               TEXT,
    issuer_name                  TEXT,
    issuer_title                 TEXT,
    issuer_address               TEXT,
    ports                        TEXT,
    duration_effective_date      TEXT,
    duration_amendment_effective TEXT,
    duration_expiration_date     TEXT,
    rail_car_data                TEXT,
    rates_and_charges            TEXT,
    volume                       TEXT,
    special_features             TEXT,
    special_notice               TEXT
);

-- Participating carriers (many per contract)
CREATE TABLE IF NOT EXISTS acs_carrier (
    carrier_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id      TEXT NOT NULL REFERENCES acs_contract(contract_id),
    carrier_name     TEXT NOT NULL,
    carrier_address  TEXT,
    amendment_action TEXT
);

-- Commodities (many per contract)
CREATE TABLE IF NOT EXISTS acs_commodity (
    commodity_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id      TEXT NOT NULL REFERENCES acs_contract(contract_id),
    description      TEXT NOT NULL,
    amendment_action TEXT
);

-- Shippers (typically 1-2 per contract)
CREATE TABLE IF NOT EXISTS acs_shipper (
    shipper_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id  TEXT NOT NULL REFERENCES acs_contract(contract_id),
    shipper_name TEXT NOT NULL
);

-- Origins (many per contract)
CREATE TABLE IF NOT EXISTS acs_origin (
    origin_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id      TEXT NOT NULL REFERENCES acs_contract(contract_id),
    location         TEXT NOT NULL,
    city             TEXT,
    state            TEXT,
    amendment_action TEXT,
    is_ags_reference BOOLEAN DEFAULT 0
);

-- Destinations (many per contract)
CREATE TABLE IF NOT EXISTS acs_destination (
    destination_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id      TEXT NOT NULL REFERENCES acs_contract(contract_id),
    location         TEXT NOT NULL,
    city             TEXT,
    state            TEXT,
    amendment_action TEXT,
    is_ags_reference BOOLEAN DEFAULT 0
);

-- Exhibit (AGS) definitions with member stations
CREATE TABLE IF NOT EXISTS acs_exhibit (
    exhibit_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id      TEXT NOT NULL REFERENCES acs_contract(contract_id),
    exhibit_name     TEXT NOT NULL,
    station_name     TEXT NOT NULL,
    amendment_action TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_contract_filing      ON acs_contract(filing_id);
CREATE INDEX IF NOT EXISTS idx_carrier_contract     ON acs_carrier(contract_id);
CREATE INDEX IF NOT EXISTS idx_commodity_contract   ON acs_commodity(contract_id);
CREATE INDEX IF NOT EXISTS idx_shipper_contract     ON acs_shipper(contract_id);
CREATE INDEX IF NOT EXISTS idx_origin_contract      ON acs_origin(contract_id);
CREATE INDEX IF NOT EXISTS idx_destination_contract ON acs_destination(contract_id);
CREATE INDEX IF NOT EXISTS idx_exhibit_contract     ON acs_exhibit(contract_id);
CREATE INDEX IF NOT EXISTS idx_origin_state         ON acs_origin(state);
CREATE INDEX IF NOT EXISTS idx_destination_state    ON acs_destination(state);
CREATE INDEX IF NOT EXISTS idx_commodity_desc       ON acs_commodity(description);
CREATE INDEX IF NOT EXISTS idx_shipper_name         ON acs_shipper(shipper_name);
"""


def load_to_sqlite(contracts, db_path="acs_contracts.db"):
    """Load parsed contracts into a SQLite database."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create schema
    for stmt in generate_sql_schema().split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt + ";")

    if not contracts:
        conn.close()
        return db_path

    # Insert filing
    c0 = contracts[0]
    cur.execute(
        "INSERT INTO acs_filing (source_file, filing_received_date, railroad) VALUES (?, ?, ?)",
        (c0.source_file, c0.filing_received_date, c0.railroad),
    )
    filing_id = cur.lastrowid

    for c in contracts:
        # Contract
        cur.execute(
            """INSERT OR REPLACE INTO acs_contract
               (contract_id, filing_id, issued_date, effective_date,
                issuer_name, issuer_title, issuer_address, ports,
                duration_effective_date, duration_amendment_effective,
                duration_expiration_date, rail_car_data, rates_and_charges,
                volume, special_features, special_notice)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                c.contract_id, filing_id, c.issued_date, c.effective_date,
                c.issuer_name, c.issuer_title, c.issuer_address, c.ports,
                c.duration_effective_date, c.duration_amendment_effective_date,
                c.duration_expiration_date, c.rail_car_data, c.rates_and_charges,
                c.volume, c.special_features, c.special_notice,
            ),
        )

        # Carriers
        for ca in c.participating_carriers:
            cur.execute(
                "INSERT INTO acs_carrier (contract_id, carrier_name, carrier_address, amendment_action) VALUES (?,?,?,?)",
                (c.contract_id, ca["name"], ca.get("address", ""), ca.get("amendment_action")),
            )

        # Commodities
        for co in c.commodities:
            cur.execute(
                "INSERT INTO acs_commodity (contract_id, description, amendment_action) VALUES (?,?,?)",
                (c.contract_id, co["description"], co.get("amendment_action")),
            )

        # Shippers
        for sh in c.shippers:
            cur.execute(
                "INSERT INTO acs_shipper (contract_id, shipper_name) VALUES (?,?)",
                (c.contract_id, sh),
            )

        # Origins
        for o in c.origins:
            cur.execute(
                "INSERT INTO acs_origin (contract_id, location, city, state, amendment_action, is_ags_reference) VALUES (?,?,?,?,?,?)",
                (c.contract_id, o["location"], o["city"], o["state"],
                 o.get("amendment_action"), 1 if o.get("is_ags_reference") else 0),
            )

        # Destinations
        for d in c.destinations:
            cur.execute(
                "INSERT INTO acs_destination (contract_id, location, city, state, amendment_action, is_ags_reference) VALUES (?,?,?,?,?,?)",
                (c.contract_id, d["location"], d["city"], d["state"],
                 d.get("amendment_action"), 1 if d.get("is_ags_reference") else 0),
            )

        # Exhibits
        for exhibit_name, stations in c.exhibit_definitions.items():
            for station in stations:
                cur.execute(
                    "INSERT INTO acs_exhibit (contract_id, exhibit_name, station_name) VALUES (?,?,?)",
                    (c.contract_id, exhibit_name, station),
                )

    conn.commit()
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------
def print_summary(contracts):
    """Print a human-readable summary of parsed contracts."""
    print("=" * 80)
    print(f"  ACS PDF PARSER RESULTS")
    print(f"  Contracts parsed: {len(contracts)}")
    if contracts:
        print(f"  Source file: {contracts[0].source_file}")
        print(f"  Filing received: {contracts[0].filing_received_date}")
    print("=" * 80)

    for i, c in enumerate(contracts, 1):
        print(f"\n{'~' * 70}")
        print(f"  CONTRACT {i}: {c.contract_id}")
        print(f"{'~' * 70}")
        print(f"  Railroad:   {c.railroad}")
        print(f"  Issued:     {c.issued_date}")
        print(f"  Effective:  {c.effective_date}")
        print(f"  Issuer:     {c.issuer_name}, {c.issuer_title}")
        print(f"  Carriers:   {len(c.participating_carriers)}")
        for ca in c.participating_carriers:
            action = f" [{ca.get('amendment_action', '')}]" if ca.get('amendment_action') else ""
            print(f"    - {ca['name']}{action}")
        print(f"  Commodities: {len(c.commodities)}")
        for co in c.commodities:
            action = f" [{co.get('amendment_action', '')}]" if co.get('amendment_action') else ""
            print(f"    - {co['description']}{action}")
        print(f"  Shippers:   {', '.join(c.shippers)}")
        print(f"  Origins:    {len(c.origins)}  |  Destinations: {len(c.destinations)}")
        print(f"  Duration:   {c.duration_effective_date} -> {c.duration_expiration_date}")
        print(f"  Rates:      {c.rates_and_charges}")
        print(f"  Volume:     {c.volume}")
        if c.exhibit_definitions:
            for name, stations in c.exhibit_definitions.items():
                print(f"  Exhibit '{name}': {len(stations)} stations")

    # Aggregate stats
    all_shippers = set()
    all_commodities = set()
    all_origins = set()
    all_dests = set()
    all_carriers = set()
    for c in contracts:
        all_shippers.update(c.shippers)
        all_commodities.update(co["description"] for co in c.commodities)
        all_origins.update(o["location"] for o in c.origins)
        all_dests.update(d["location"] for d in c.destinations)
        all_carriers.update(ca["name"] for ca in c.participating_carriers)

    print(f"\n{'=' * 80}")
    print(f"  AGGREGATE: {len(all_shippers)} shippers, {len(all_commodities)} commodities,")
    print(f"    {len(all_origins)} origins, {len(all_dests)} destinations, {len(all_carriers)} carriers")
    print(f"{'=' * 80}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse STB Amended Contract Summary (ACS) PDF filings."
    )
    parser.add_argument("pdf_path", help="Path to the ACS PDF file")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--csv", action="store_true", help="Output flattened CSV")
    parser.add_argument("--sql", action="store_true", help="Output SQL schema + inserts")
    parser.add_argument("--sqlite", action="store_true", help="Load into SQLite DB")

    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    contracts = parse_acs_pdf(args.pdf_path)
    base = os.path.splitext(args.pdf_path)[0]

    if args.json:
        out_path = base + "_parsed.json"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(contracts_to_json(contracts))
        print(f"JSON written to: {out_path}")

    if args.csv:
        out_path = base + "_parsed.csv"
        rows = contracts_to_csv_rows(contracts)
        if rows:
            with open(out_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        print(f"CSV written to: {out_path}")

    if args.sql:
        out_path = base + "_schema.sql"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(generate_sql_schema())
        print(f"SQL schema written to: {out_path}")

    if args.sqlite:
        db_path = base + ".db"
        load_to_sqlite(contracts, db_path)
        print(f"SQLite DB written to: {db_path}")

    print_summary(contracts)


if __name__ == "__main__":
    main()
