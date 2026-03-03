#!/usr/bin/env python3
"""
extract_coal_reports.py
Coal Module — Export Report PDF Extractor

Processes 58 monthly "Coal Export Report — U.S. Atlantic & Gulf Coast" PDFs
(Oct 2021 → Jan 2026) into structured analytics data in DuckDB + CSV.

Three tables extracted:
  - coal_vessel_calls       ~8,000–11,000 individual shipment records
  - coal_monthly_summary    port-level Met/Thermal summaries (best effort)
  - coal_destination_flows  Africa/Americas/Far East/Med/N.Europe flows

Usage:
    python src/extract_coal_reports.py                  # full run
    python src/extract_coal_reports.py --sample 3       # test 3 PDFs
    python src/extract_coal_reports.py --csv-only       # skip DuckDB
    python src/extract_coal_reports.py --vessel-only    # vessel calls only
"""

import re
import sys
import json
import warnings
from datetime import date
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

try:
    import pdfplumber
    import duckdb
    import pandas as pd
    import click
except ImportError:
    print("Install: pip install pdfplumber duckdb pandas click")
    sys.exit(1)

# ─── Paths ───────────────────────────────────────────────────────────────────
MODULE_DIR   = Path(__file__).parent.parent
REPORTS_DIR  = MODULE_DIR / "data" / "raw" / "export_reports"
DB_PATH      = MODULE_DIR / "data" / "coal_analytics.duckdb"
PROCESSED    = MODULE_DIR / "data" / "processed"

# ─── Constants ───────────────────────────────────────────────────────────────
MONTH_MAP = {
    "january":1, "february":2, "march":3, "april":4,
    "may":5, "june":6, "july":7, "august":8,
    "september":9, "october":10, "november":11, "december":12,
    "jan":1, "feb":2, "mar":3, "apr":4,
    "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12,
}

# Files with suffixes to deprioritize when date-deduplicating
LOW_PRIORITY_TOKENS = {"downsize", "tester", "copy"}

# Known coal type values in vessel tables
COAL_TYPES = {"MET", "THERMAL", "MIDSTREAM"}

# Known terminal operators — used to disambiguate country vs shipper in old MOBILE format
KNOWN_TERMINALS = {
    "CNX", "CONSOL", "CSX", "NS", "DTA", "PIER IX", "MCDUFFIE",
    "CMT", "UBT", "CHIPCO", "PASCAGOULA", "ASCENSION",
    "MIDSTREAM BUOYS", "DEEPWATER", "BURNSIDE", "CORE",
}

# Common destination countries — helps correct old-format MOBILE rows where
# shipper was blank and the country ended up in the shipper column position
KNOWN_DEST_COUNTRIES = {
    "ARGENTINA", "AUSTRALIA", "BELGIUM", "BRAZIL", "CANADA", "CHILE",
    "CHINA", "COLOMBIA", "CROATIA", "DENMARK", "DOM REP", "EGYPT",
    "FINLAND", "FRANCE", "GERMANY", "INDIA", "INDONESIA", "ISRAEL",
    "ITALY", "JAPAN", "JORDAN", "MEXICO", "MOROCCO", "NETHERLANDS",
    "PAKISTAN", "POLAND", "PORTUGAL", "S AFRICA", "S KOREA", "SOUTH AFRICA",
    "SOUTH KOREA", "SPAIN", "SRI LANKA", "SWEDEN", "THAILAND", "TOGO",
    "TRINIDAD", "TURKEY", "UKRAINE", "UNITED KINGDOM", "VIETNAM",
}

# Known ports (normalized). Both long and short forms.
KNOWN_PORTS = {
    "BALTIMORE", "H ROADS", "HAMPTON ROADS", "MOBILE", "HOUSTON",
    "NEW ORLEANS", "NOLA", "N ORLEANS", "PASCAGOULA", "N.O.", "SAVANNAH",
}

# Destination regions (for destination flow extraction)
DEST_REGIONS = ["Africa", "Americas", "Far East", "Mediterranean", "Northern Europe"]

# Shipper normalization: map long/variant forms to canonical short form
SHIPPER_NORM = {
    # Core Natural Resources (Arch + Alpha merger, Dec 2024)
    "CORE NATURAL RESOURCES": "CORE",
    # Arch Resources
    "ARCH RESOURCES": "ARCH",
    "ARCH COAL": "ARCH",
    "ARCHCOAL": "ARCH",
    # Alpha Metallurgical Resources
    "ALPHA METALLURGICAL": "ALPHA",
    "ALPHA METALLURGICAL RESOURCES": "ALPHA",
    "ALPHA MET": "ALPHA",
    "ALPHA NATURAL RESOURCES": "ALPHA",
    # Warrior Met Coal
    "WARRIOR MET COAL": "WARRIOR",
    "WARRIOR MET": "WARRIOR",
    # Coronado Global Resources
    "CORONADO COAL": "CORONADO",
    "CORONADO GLOBAL RESOURCES": "CORONADO",
    "CORONADO GLOBAL": "CORONADO",
    # CNX / CONSOL
    "CNX COAL": "CNX",
    "CNX RESOURCES": "CNX",
    "CONSOL ENERGY": "CONSOL",
    # Javelin
    "JAVELIN GLOBAL COMMODITIES": "JAVELIN",
    "JAVELIN GLOBAL": "JAVELIN",
    # Blackhawk Mining
    "BLACKHAWK MINING": "BLACKHAWK",
    # Alliance
    "ALLIANCE COAL": "ALLIANCE",
    "ALLIANCE RESOURCE": "ALLIANCE",
    # Integrity
    "INTEGRITY COAL SALES": "INTEGRITY",
    "INTEGRITY COAL": "INTEGRITY",
    # Xcoal
    "XCOAL ENERGY": "XCOAL",
    "XCOAL ENERGY & RESOURCES": "XCOAL",
    # United
    "UNITED COAL": "UNITED",
    # Pocahontas
    "POCAHONTAS LAND": "POCAHONTAS",
    "POCAHONTAS COAL": "POCAHONTAS",
    # Robindale
    "ROBINDALE ENERGY": "ROBINDALE",
    # Ramaco
    "RAMACO RESOURCES": "RAMACO",
    # CM Energy
    "CM ENERGY TRADING": "CM ENERGY",
    # Keep as-is
    "ION CARBON": "ION CARBON",
    "COKING COAL": "COKING COAL",
}

# ─── Date Parsing ────────────────────────────────────────────────────────────

def parse_report_date(filename: str) -> Optional[date]:
    """
    Parse report month from PDF filename. Handles 4 variants:
      USEC-and-USG-Combined-October-2021.pdf          → 2021-10
      Combined-Report-March-2025.pdf                  → 2025-03
      Coal-Report-January-2026.pdf                    → 2026-01
      USEC-and-USG-Combined-Report-5.25.pdf           → 2025-05
      Combined-Report-2.25-copy.pdf                   → 2025-02
      Combined-Report-January-2025-tester.pdf         → 2025-01
    """
    stem = filename.lower()
    stem = stem.replace(".pdf", "")
    # Strip known suffix noise
    for tok in LOW_PRIORITY_TOKENS:
        stem = stem.replace(f"-{tok}", "")
    stem = stem.strip("-")

    # Pattern 1: full month name + 4-digit year at end
    # e.g., "october-2021", "december-2024"
    m = re.search(r"[_-]([a-z]+)[_-](\d{4})$", stem)
    if m:
        month_str = m.group(1)
        year_str = m.group(2)
        if month_str in MONTH_MAP:
            return date(int(year_str), MONTH_MAP[month_str], 1)

    # Pattern 2: abbreviated M.YY or MM.YY
    # e.g., "-5.25" → May 2025,  "-4.25" → Apr 2025
    m = re.search(r"[_-](\d{1,2})\.(\d{2})$", stem)
    if m:
        month = int(m.group(1))
        year = 2000 + int(m.group(2))
        if 1 <= month <= 12:
            return date(year, month, 1)

    return None


def is_low_priority(filename: str) -> bool:
    """True if filename has a suffix token (downsize, tester, copy, etc.)."""
    stem = filename.lower().replace(".pdf", "")
    return any(f"-{tok}" in stem for tok in LOW_PRIORITY_TOKENS)


def deduplicate_files(pdf_files: list[Path]) -> dict[date, Path]:
    """
    For each report date, pick the canonical file.
    Priority: no-suffix > has-suffix, then full-month-name > abbreviated.
    """
    date_to_file: dict[date, list[Path]] = {}
    skipped = []
    for p in pdf_files:
        d = parse_report_date(p.name)
        if d is None:
            print(f"  ⚠ Cannot parse date: {p.name} — skipping")
            continue
        date_to_file.setdefault(d, []).append(p)

    canonical: dict[date, Path] = {}
    for d, files in sorted(date_to_file.items()):
        if len(files) == 1:
            canonical[d] = files[0]
        else:
            # Prefer: no low-priority suffix, then longer name (more descriptive)
            def priority(p: Path):
                low = is_low_priority(p.name)
                has_full_month = any(mon in p.name.lower() for mon in MONTH_MAP)
                return (int(low), -int(has_full_month), p.name)
            best = sorted(files, key=priority)[0]
            others = [f.name for f in files if f != best]
            print(f"  ℹ Duplicate date {d}: using '{best.name}', skipping {others}")
            canonical[d] = best

    return canonical

# ─── Vessel Call Extraction ───────────────────────────────────────────────────

def _has_exact_coal_type(row) -> bool:
    """True if any cell in row is exactly MET, THERMAL, or MIDSTREAM."""
    return any(str(c or "").strip().upper() in COAL_TYPES for c in row)


def _is_vessel_name(s: str) -> bool:
    """
    Vessel names are predominantly uppercase (>=75% of alpha chars).
    Minimum 2 characters. Rejects: percentages, pure numbers, lowercase words.
    """
    s = s.strip()
    if len(s) < 2:
        return False
    if s.startswith("-") or s.startswith("+") or "%" in s:
        return False
    alpha_chars = [c for c in s if c.isalpha()]
    if not alpha_chars:
        return False
    upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
    return upper_ratio >= 0.75


def parse_vessel_row(row) -> Optional[dict]:
    """
    Parse a single row from a vessel call table.

    Works for BOTH old format (9-10 cols, multi-row tables) and
    new format (8 cols, single-row tables per vessel).

    Strategy: squeeze blanks/None, then anchor on coal_type and metric_tons.
    Column order: [vessel, port, terminal, shipper, country, receiver, coal_type, tons]
    """
    # Squeeze: strip None and empty strings
    values = [str(v).strip() for v in row if v is not None and str(v).strip() not in ("", "-")]
    if len(values) < 4:
        return None

    vessel_name = values[0]
    port = values[1] if len(values) > 1 else None

    if not _is_vessel_name(vessel_name):
        return None

    # Find coal_type: scan right to left for exact MET/THERMAL/MIDSTREAM
    coal_type = None
    coal_idx = -1
    for i in range(len(values) - 1, 1, -1):
        v = values[i].upper().strip()
        if v in COAL_TYPES:
            coal_type = "THERMAL" if v in ("THERMAL", "MIDSTREAM") else "MET"
            coal_idx = i
            break

    if coal_idx == -1:
        return None  # No coal type → not a vessel row

    # metric_tons: first numeric-only value after coal_type position
    metric_tons = None
    for i in range(coal_idx + 1, len(values)):
        cleaned = values[i].replace(",", "").strip()
        if cleaned.isdigit() and int(cleaned) > 0:
            metric_tons = int(cleaned)
            break

    # Middle values between port (idx 1) and coal_type (coal_idx)
    middle = values[2:coal_idx]
    terminal = middle[0] if len(middle) > 0 else None
    shipper   = middle[1] if len(middle) > 1 else None
    country   = middle[2] if len(middle) > 2 else None
    receiver  = middle[3] if len(middle) > 3 else None

    # Fix old-format MOBILE/USG rows where shipper column was blank and the
    # destination country ended up in the shipper slot.
    # Heuristic: if only 2 middle values, first is a known terminal, and second
    # looks like a country (in KNOWN_DEST_COUNTRIES), swap shipper → country.
    if (
        len(middle) == 2
        and (terminal or "").upper() in KNOWN_TERMINALS
        and shipper is not None
        and shipper.upper() in KNOWN_DEST_COUNTRIES
    ):
        country = shipper
        shipper = None

    # Normalize port abbreviations
    port_norm = (port or "").upper().strip()
    port_norm = {
        "H ROADS": "H ROADS",
        "HAMPTON ROADS": "H ROADS",
        "H-ROADS": "H ROADS",
        "N ROADS": "H ROADS",   # artifact: "H" absorbed into terminal col in some old reports
        "ROADS": "H ROADS",
        "NEW ORLEANS": "NOLA",
        "NOLA": "NOLA",
        "N ORLEANS": "NOLA",
        "N.O.": "NOLA",
        "BALTIMORE": "BALTIMORE",
        "MOBILE": "MOBILE",
        "HOUSTON": "HOUSTON",
        "PASCAGOULA": "PASCAGOULA",
        "SAVANNAH": "SAVANNAH",
    }.get(port_norm, port_norm)

    # Reject rows where port is clearly not a port (country name, company name, etc.)
    if port_norm not in {
        "BALTIMORE", "H ROADS", "MOBILE", "NOLA", "HOUSTON",
        "PASCAGOULA", "SAVANNAH", "N ROADS",
    }:
        return None  # Not a valid vessel call row

    # Normalize shipper
    shipper_upper = (shipper or "").upper().strip()
    shipper_norm = SHIPPER_NORM.get(shipper_upper, shipper_upper) if shipper_upper else None

    return {
        "vessel_name":         vessel_name,
        "port":                port_norm,
        "terminal":            terminal,
        "shipper":             shipper,
        "shipper_norm":        shipper_norm,
        "destination_country": country,
        "receiver_group":      receiver,
        "coal_type":           coal_type,
        "metric_tons":         metric_tons,
    }


def extract_vessel_calls(pdf_path: Path, report_date: date) -> tuple[list[dict], list[str]]:
    """
    Extract all vessel call records from a PDF report.
    Returns (records, warnings).
    Works for both old format (multi-row tables) and new format (1-row tables).
    """
    records = []
    warn_msgs = []
    source_file = pdf_path.name

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    tables = page.extract_tables(
                        {"snap_tolerance": 4, "join_tolerance": 4}
                    )
                except Exception as e:
                    warn_msgs.append(f"p{page_num}: table extraction error: {e}")
                    continue

                for table in (tables or []):
                    if not table:
                        continue
                    for row in table:
                        if not row or not row[0]:
                            continue
                        # Quick pre-filter: must have exact coal type in row
                        if not _has_exact_coal_type(row):
                            continue
                        parsed = parse_vessel_row(row)
                        if parsed is None:
                            continue
                        parsed["report_date"]  = report_date
                        parsed["report_year"]  = report_date.year
                        parsed["report_month"] = report_date.month
                        parsed["source_file"]  = source_file
                        records.append(parsed)

    except Exception as e:
        warn_msgs.append(f"PDF open error: {e}")

    return records, warn_msgs


# ─── Destination Flow Extraction ──────────────────────────────────────────────

# Pattern to match destination flow lines in page text.
# Examples:
#   "Africa -100.00% -3.75% THERMAL Africa 0 409,164"
#   "Americas -0.59% -26.53% Americas 646,304 180,254"
#   "Far East 4.26% 49.12% Far East 1,599,649 897,313"
#   "Northern Europe 116.36% 267.63% Northern Europe 1,325,720 775,589"
_FLOW_PATTERN = re.compile(
    r"(Africa|Americas|Far East|Mediterranean|Northern Europe)"
    r"\s+"
    r"([+-]?\d[\d,.]*%|--?%?|0\.00%)"   # MoM MET
    r"\s+"
    r"([+-]?\d[\d,.]*%|--?%?|0\.00%)"   # MoM THERMAL
    r"(?:\s+\d+%?)?"                      # optional: "100%" noise
    r"(?:\s+(?:THERMAL|MET))?",           # optional: coal type label
    re.IGNORECASE,
)
_TONS_PATTERN = re.compile(
    r"(Africa|Americas|Far East|Mediterranean|Northern Europe)"
    r"\s+([\d,]+|-+)\s+([\d,]+|-+)",
    re.IGNORECASE,
)


def _parse_pct(s: str) -> Optional[float]:
    s = s.strip().replace("%", "").replace(",", "")
    if s in ("-", "--", ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_tons(s: str) -> Optional[int]:
    s = s.strip().replace(",", "")
    if not s or set(s) <= set("-"):
        return None
    try:
        v = int(s)
        return v if v >= 0 else None
    except ValueError:
        return None


def extract_destination_flows(pdf_path: Path, report_date: date) -> tuple[list[dict], list[str]]:
    """
    Extract destination flow data from page text (not table extraction).
    Returns (records, warnings).
    """
    records = []
    warn_msgs = []
    source_file = pdf_path.name
    found = False

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    continue

                # Only scan pages with destination region content
                if "africa" not in text.lower():
                    continue
                if "month over month" not in text.lower() and "coal type by destination" not in text.lower():
                    continue

                # Extract MoM percentage lines
                mom_data: dict[str, dict] = {}
                for m in _FLOW_PATTERN.finditer(text):
                    region = m.group(1).title()
                    if "northern" in region.lower():
                        region = "Northern Europe"
                    if "far" in region.lower():
                        region = "Far East"
                    mom_data[region] = {
                        "mom_met_pct":    _parse_pct(m.group(2)),
                        "mom_thermal_pct": _parse_pct(m.group(3)),
                    }

                # Extract metric tons lines
                tons_data: dict[str, dict] = {}
                for m in _TONS_PATTERN.finditer(text):
                    region = m.group(1).title()
                    if "northern" in region.lower():
                        region = "Northern Europe"
                    if "far" in region.lower():
                        region = "Far East"
                    # Avoid re-capturing MoM pct lines (those have % signs)
                    if "%" in m.group(2) or "%" in m.group(3):
                        continue
                    t_met    = _parse_tons(m.group(2))
                    t_therm  = _parse_tons(m.group(3))
                    if t_met is not None or t_therm is not None:
                        tons_data[region] = {
                            "met_metric_tons":    t_met,
                            "thermal_metric_tons": t_therm,
                        }

                # Merge into records (one row per region × coal_type)
                all_regions = set(list(mom_data.keys()) + list(tons_data.keys()))
                for region in all_regions:
                    mom = mom_data.get(region, {})
                    tons = tons_data.get(region, {})
                    for coal_type, mom_key, tons_key in [
                        ("MET",     "mom_met_pct",    "met_metric_tons"),
                        ("THERMAL", "mom_thermal_pct", "thermal_metric_tons"),
                    ]:
                        records.append({
                            "report_date":         report_date,
                            "destination_region":  region,
                            "coal_type":           coal_type,
                            "metric_tons":         tons.get(tons_key),
                            "mom_pct":             mom.get(mom_key),
                            "source_file":         source_file,
                        })
                found = True
                break  # Only extract from first matching page

    except Exception as e:
        warn_msgs.append(f"Destination flow extraction error: {e}")

    if not found:
        warn_msgs.append("No destination flow page found")

    return records, warn_msgs


# ─── Monthly Summary Extraction ───────────────────────────────────────────────

# Port names that appear in summary tables
_SUMMARY_PORTS = {
    "Baltimore": "BALTIMORE",
    "Hampton Roads": "H ROADS",
    "Mobile": "MOBILE",
    "Houston": "HOUSTON",
    "New Orleans": "NOLA",
    "NOLA": "NOLA",
    "Total": "TOTAL",
}


def extract_monthly_summary(pdf_path: Path, report_date: date) -> tuple[list[dict], list[str]]:
    """
    Extract port-level Met/Thermal monthly summary (best effort).
    Old format: 5-col table with port, month_tons, yoy%, ytd_tons, ytd_yoy%
    Returns (records, warnings).
    """
    records = []
    warn_msgs = []
    source_file = pdf_path.name
    found = False

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    tables = page.extract_tables({"snap_tolerance": 5})
                except Exception:
                    continue

                for table in (tables or []):
                    if not table or len(table) < 3:
                        continue

                    # Detect summary table: first cell is "Met Coal" or "Thermal Coal"
                    # OR contains port names in subsequent rows
                    has_met_header = any(
                        row and row[0] and str(row[0]).strip().lower() in ("met coal", "thermal coal")
                        for row in table[:3]
                    )
                    if not has_met_header:
                        continue

                    current_coal_type = None
                    for row in table:
                        if not row or not row[0]:
                            continue
                        first = str(row[0]).strip()

                        if first.lower() == "met coal":
                            current_coal_type = "MET"
                            continue
                        if first.lower() == "thermal coal":
                            current_coal_type = "THERMAL"
                            continue
                        if current_coal_type is None:
                            continue

                        # Check if first cell is a known port
                        port_norm = _SUMMARY_PORTS.get(first)
                        if not port_norm:
                            continue

                        # Expect at least 3 data columns after port
                        data_cols = [str(c or "").strip() for c in row[1:]]
                        numeric_cols = [c.replace(",", "").replace("-", "").replace("%", "") for c in data_cols]

                        def safe_int(s: str) -> Optional[int]:
                            try:
                                return int(s.replace(",", ""))
                            except (ValueError, AttributeError):
                                return None

                        def safe_pct(s: str) -> Optional[float]:
                            s = s.replace("%", "").replace(",", "")
                            try:
                                v = float(s)
                                # Percentage values should be in [-10000, 10000] range
                                return v if abs(v) <= 10000 else None
                            except (ValueError, AttributeError):
                                return None

                        # old 5-col layout: port | month_tons | yoy% | ytd_tons | ytd_yoy%
                        record = {
                            "report_date":      report_date,
                            "port":             port_norm,
                            "coal_type":        current_coal_type,
                            "metric_tons":      safe_int(data_cols[0]) if data_cols else None,
                            "yoy_pct":          safe_pct(data_cols[1]) if len(data_cols) > 1 else None,
                            "ytd_metric_tons":  safe_int(data_cols[2]) if len(data_cols) > 2 else None,
                            "ytd_yoy_pct":      safe_pct(data_cols[3]) if len(data_cols) > 3 else None,
                            "source_file":      source_file,
                        }
                        records.append(record)
                        found = True

    except Exception as e:
        warn_msgs.append(f"Monthly summary extraction error: {e}")

    if not found:
        warn_msgs.append("No port summary table found (may use graphic format)")

    return records, warn_msgs


# ─── DuckDB Schema & Loading ──────────────────────────────────────────────────

DDL_VESSEL_CALLS = """
CREATE TABLE IF NOT EXISTS coal_vessel_calls (
    id                  INTEGER PRIMARY KEY,
    report_date         DATE    NOT NULL,
    report_year         INTEGER NOT NULL,
    report_month        INTEGER NOT NULL,
    vessel_name         VARCHAR,
    port                VARCHAR,
    terminal            VARCHAR,
    shipper             VARCHAR,
    shipper_norm        VARCHAR,
    destination_country VARCHAR,
    receiver_group      VARCHAR,
    coal_type           VARCHAR,
    metric_tons         INTEGER,
    source_file         VARCHAR
);
"""

DDL_MONTHLY_SUMMARY = """
CREATE TABLE IF NOT EXISTS coal_monthly_summary (
    id              INTEGER PRIMARY KEY,
    report_date     DATE    NOT NULL,
    port            VARCHAR,
    coal_type       VARCHAR,
    metric_tons     BIGINT,
    yoy_pct         DOUBLE,
    ytd_metric_tons BIGINT,
    ytd_yoy_pct     DOUBLE,
    source_file     VARCHAR
);
"""

DDL_DESTINATION_FLOWS = """
CREATE TABLE IF NOT EXISTS coal_destination_flows (
    id                   INTEGER PRIMARY KEY,
    report_date          DATE    NOT NULL,
    destination_region   VARCHAR,
    coal_type            VARCHAR,
    metric_tons          BIGINT,
    mom_pct              DOUBLE,
    source_file          VARCHAR
);
"""

DDL_EXTRACTION_LOG = """
CREATE TABLE IF NOT EXISTS coal_extraction_log (
    source_file      VARCHAR PRIMARY KEY,
    report_date      DATE,
    vessel_calls_n   INTEGER,
    summary_n        INTEGER,
    flows_n          INTEGER,
    extracted_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    warnings         VARCHAR
);
"""


def init_duckdb(db_path: Path) -> duckdb.DuckDBPyConnection:
    """Create or open coal_analytics.duckdb and ensure all tables exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_vessel_id  START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_summary_id START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_flows_id   START 1")
    conn.execute(DDL_VESSEL_CALLS)
    conn.execute(DDL_MONTHLY_SUMMARY)
    conn.execute(DDL_DESTINATION_FLOWS)
    conn.execute(DDL_EXTRACTION_LOG)
    return conn


def _insert_records(conn, table: str, seq: str, records: list[dict]):
    """
    Insert a list of dicts into a DuckDB table with auto-increment ID.
    Uses explicit column names to avoid position-order mismatches.
    """
    if not records:
        return
    df = pd.DataFrame(records)
    conn.register("_insert_df", df)
    # Build explicit column list (DuckDB matches by name, ID filled by sequence)
    col_list = ", ".join(f'"{c}"' for c in df.columns)
    conn.execute(f"""
        INSERT INTO {table} (id, {col_list})
        SELECT nextval('{seq}'), {col_list}
        FROM _insert_df
    """)
    conn.unregister("_insert_df")


def load_to_duckdb(
    vessel_calls:    list[dict],
    summary:         list[dict],
    flows:           list[dict],
    log_entries:     list[dict],
    db_path:         Path,
) -> None:
    """Load all extracted data into coal_analytics.duckdb."""
    print(f"\nLoading to DuckDB: {db_path}")
    conn = init_duckdb(db_path)

    # Clear existing data (full reload)
    conn.execute("DELETE FROM coal_vessel_calls")
    conn.execute("DELETE FROM coal_monthly_summary")
    conn.execute("DELETE FROM coal_destination_flows")
    conn.execute("DELETE FROM coal_extraction_log")

    _insert_records(conn, "coal_vessel_calls",     "seq_vessel_id",  vessel_calls)
    _insert_records(conn, "coal_monthly_summary",  "seq_summary_id", summary)
    _insert_records(conn, "coal_destination_flows","seq_flows_id",   flows)

    # Log entries use source_file as PK
    if log_entries:
        log_df = pd.DataFrame(log_entries)
        conn.register("_log_df", log_df)
        conn.execute("INSERT INTO coal_extraction_log SELECT * FROM _log_df")
        conn.unregister("_log_df")

    print(f"  vessel_calls:      {len(vessel_calls):,}")
    print(f"  monthly_summary:   {len(summary):,}")
    print(f"  destination_flows: {len(flows):,}")

    conn.close()


def export_csvs(
    vessel_calls: list[dict],
    summary:      list[dict],
    flows:        list[dict],
    output_dir:   Path,
) -> None:
    """Export extracted data to CSV files in data/processed/."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if vessel_calls:
        df = pd.DataFrame(vessel_calls)
        path = output_dir / "coal_vessel_calls.csv"
        df.to_csv(path, index=False)
        print(f"  Saved: {path} ({len(df):,} rows)")

    if summary:
        df = pd.DataFrame(summary)
        path = output_dir / "coal_monthly_summary.csv"
        df.to_csv(path, index=False)
        print(f"  Saved: {path} ({len(df):,} rows)")

    if flows:
        df = pd.DataFrame(flows)
        path = output_dir / "coal_destination_flows.csv"
        df.to_csv(path, index=False)
        print(f"  Saved: {path} ({len(df):,} rows)")


# ─── Main Batch Processing ────────────────────────────────────────────────────

def process_all(
    reports_dir:   Path,
    db_path:       Path,
    output_dir:    Path,
    sample:        int,
    csv_only:      bool,
    vessel_only:   bool,
) -> None:
    """Main batch loop: process all PDFs and load into DuckDB + CSVs."""
    # Discover and deduplicate PDF files
    all_pdfs = sorted(reports_dir.glob("*.pdf"))
    if not all_pdfs:
        print(f"ERROR: No PDFs found in {reports_dir}")
        sys.exit(1)

    print(f"\nFound {len(all_pdfs)} PDFs in {reports_dir}")
    canonical = deduplicate_files(all_pdfs)
    print(f"Canonical reports: {len(canonical)} unique months")

    # Sort by date
    sorted_reports = sorted(canonical.items())

    # Apply sample limit
    if sample:
        # Take first, middle, last for good coverage
        total = len(sorted_reports)
        if sample >= total:
            pass
        elif sample == 3:
            sorted_reports = [
                sorted_reports[0],
                sorted_reports[total // 2],
                sorted_reports[-1],
            ]
        else:
            sorted_reports = sorted_reports[:sample]
        print(f"SAMPLE MODE: processing {len(sorted_reports)} PDFs")

    # Collect results
    all_vessel_calls: list[dict] = []
    all_summary:      list[dict] = []
    all_flows:        list[dict] = []
    log_entries:      list[dict] = []

    print(f"\n{'='*60}")
    for report_date, pdf_path in sorted_reports:
        print(f"\n{report_date}  {pdf_path.name}")

        # Vessel calls (always)
        calls, warn1 = extract_vessel_calls(pdf_path, report_date)
        print(f"  vessel calls: {len(calls)}")

        # Optional extras
        summ, warn2 = [], []
        flows, warn3 = [], []
        if not vessel_only:
            summ, warn2 = extract_monthly_summary(pdf_path, report_date)
            flows, warn3 = extract_destination_flows(pdf_path, report_date)
            print(f"  summary rows: {len(summ)}, flow rows: {len(flows)}")

        all_vessel_calls.extend(calls)
        all_summary.extend(summ)
        all_flows.extend(flows)

        # Log entry
        all_warnings = warn1 + warn2 + warn3
        if all_warnings:
            for w in all_warnings:
                print(f"  ⚠ {w}")

        log_entries.append({
            "source_file":    pdf_path.name,
            "report_date":    report_date,
            "vessel_calls_n": len(calls),
            "summary_n":      len(summ),
            "flows_n":        len(flows),
            "extracted_at":   pd.Timestamp.now(),
            "warnings":       json.dumps(all_warnings) if all_warnings else None,
        })

    print(f"\n{'='*60}")
    print(f"TOTAL vessel calls:      {len(all_vessel_calls):,}")
    print(f"TOTAL summary rows:      {len(all_summary):,}")
    print(f"TOTAL destination flows: {len(all_flows):,}")

    # Coverage check
    if all_vessel_calls:
        df = pd.DataFrame(all_vessel_calls)
        print(f"\nCoverage: {df['report_year'].min()} – {df['report_year'].max()}")
        print("\nVessel calls by year:")
        print(df.groupby("report_year").size().to_string())
        if "shipper_norm" in df.columns:
            print("\nTop 10 shippers (by total metric tons):")
            top = (
                df.dropna(subset=["metric_tons"])
                .groupby("shipper_norm")["metric_tons"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            for shipper, tons in top.items():
                print(f"  {shipper:20s}  {tons:>15,.0f} MT")

    # Write outputs
    print("\nExporting CSVs...")
    export_csvs(all_vessel_calls, all_summary, all_flows, output_dir)

    if not csv_only:
        load_to_duckdb(all_vessel_calls, all_summary, all_flows, log_entries, db_path)
    else:
        print("(csv-only mode — DuckDB not written)")


# ─── CLI ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--reports-dir", type=click.Path(exists=True), default=None,
              help="Path to folder with PDF reports (default: data/raw/export_reports/)")
@click.option("--db-path", type=click.Path(), default=None,
              help="Output DuckDB path (default: data/coal_analytics.duckdb)")
@click.option("--sample", type=int, default=0,
              help="Process N PDFs only (0=all; 3=oldest/mid/newest)")
@click.option("--csv-only", is_flag=True,
              help="Write CSVs only, skip DuckDB")
@click.option("--vessel-only", is_flag=True,
              help="Extract vessel calls only (skip summary and flows)")
def main(reports_dir, db_path, sample, csv_only, vessel_only):
    """
    Extract structured data from Coal Export Report PDFs into DuckDB + CSV.

    Run from the coal module directory:
        python src/extract_coal_reports.py
        python src/extract_coal_reports.py --sample 3
        python src/extract_coal_reports.py --csv-only
    """
    rdir = Path(reports_dir) if reports_dir else REPORTS_DIR
    dpath = Path(db_path) if db_path else DB_PATH
    odir = PROCESSED

    print("\nCoal Export Report Extractor")
    print(f"Reports dir: {rdir}")
    print(f"DB path:     {dpath}")

    process_all(
        reports_dir=rdir,
        db_path=dpath,
        output_dir=odir,
        sample=sample,
        csv_only=csv_only,
        vessel_only=vessel_only,
    )
    print("\nDone.")


if __name__ == "__main__":
    main()
