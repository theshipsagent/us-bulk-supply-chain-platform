#!/usr/bin/env python3
"""
STB Union Pacific Agricultural Contract Summary Scraper
=======================================================
Discovers, downloads, and parses all UP ACS filings from STB.gov (2008-2026).

Usage:
    python scrape_stb_up.py discover    # Phase 1: find all PDF URLs
    python scrape_stb_up.py download    # Phase 1 + 2: discover then download
    python scrape_stb_up.py parse       # Phase 3: parse downloaded PDFs into SQLite
    python scrape_stb_up.py all         # Full pipeline (discover + download + parse)
"""

import json
import multiprocessing
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = SCRIPT_DIR / "downloads" / "UP"
DISCOVERED_URLS_PATH = SCRIPT_DIR / "up_urls_discovered.json"
MANIFEST_PATH = DOWNLOAD_DIR / "manifest.json"
DB_PATH = SCRIPT_DIR / "stb_contracts.db"

STB_BASE = "https://www.stb.gov"
ACS_PAGE = f"{STB_BASE}/reports-data/agricultural-contract-summaries/"
OLD_ARCHIVE_BASE = f"{STB_BASE}/wp-content/uploads/econdata/ACS/UP"
UPLOADS_BASE = f"{STB_BASE}/wp-content/uploads"

REQUEST_DELAY = 1.0  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research; academic rail data project)"
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def fetch_url(url, stream=False):
    """Fetch a URL with rate limiting. Returns response or None on error."""
    time.sleep(REQUEST_DELAY)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                            stream=stream, allow_redirects=True)
        return resp
    except requests.RequestException as e:
        log(f"  Error fetching {url}: {e}")
        return None


def head_url(url):
    """HEAD request to check if a URL exists. Returns True/False."""
    time.sleep(REQUEST_DELAY)
    try:
        resp = requests.head(url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                             allow_redirects=True)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def is_up_pdf(url):
    """Check if a URL looks like a Union Pacific ACS PDF."""
    url_lower = url.lower()
    if not url_lower.endswith(".pdf"):
        return False
    # Must contain UP reference
    up_patterns = ["/up-", "/up_", "acs-up", "acs_up", "/up/",
                   "union-pacific", "union_pacific", "uprr"]
    return any(p in url_lower for p in up_patterns)


# ---------------------------------------------------------------------------
# Phase 1: URL Discovery
# ---------------------------------------------------------------------------
def discover_from_stb_page():
    """Scrape the STB ACS landing page for UP PDF links."""
    log("Fetching STB Agricultural Contract Summaries page...")
    resp = fetch_url(ACS_PAGE)
    if not resp or resp.status_code != 200:
        log(f"  Failed to fetch ACS page (status={resp.status_code if resp else 'N/A'})")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    urls = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(STB_BASE, href)
        if is_up_pdf(full_url):
            urls.add(full_url)

    log(f"  Found {len(urls)} UP PDF links on ACS page")
    return sorted(urls)


def probe_old_archive(start_year=2008, end_year=2022):
    """
    Probe the old econdata archive structure for UP ACS PDFs.
    Pattern: /wp-content/uploads/econdata/ACS/UP/{YEAR}/Q{Q}/ACS-UP-{YEAR}-Q{Q}_{DATE}.pdf
    """
    log(f"Probing old archive structure ({start_year}-{end_year})...")
    urls = set()

    # End-of-quarter dates and nearby variants to try
    quarter_end_dates = {
        1: ["03-31", "03-30", "03-29", "03-28", "04-01", "04-02",
            "03-27", "03-26", "04-03", "04-04"],
        2: ["06-30", "06-29", "06-28", "06-27", "07-01", "07-02",
            "06-26", "06-25", "07-03", "07-04"],
        3: ["09-30", "09-29", "09-28", "09-27", "10-01", "10-02",
            "09-26", "09-25", "10-03", "10-04"],
        4: ["12-31", "12-30", "12-29", "12-28", "01-01", "01-02",
            "12-27", "12-26", "01-03", "01-04"],
    }

    for year in range(start_year, end_year + 1):
        for quarter in range(1, 5):
            found_for_qtr = False
            date_variants = quarter_end_dates[quarter]

            for date_str in date_variants:
                if found_for_qtr:
                    break

                # Primary pattern: ACS-UP-{YEAR}-Q{Q}_{MM-DD-YYYY}.pdf
                url = f"{OLD_ARCHIVE_BASE}/{year}/Q{quarter}/ACS-UP-{year}-Q{quarter}_{date_str}-{year}.pdf"
                if head_url(url):
                    urls.add(url)
                    log(f"  Found: {os.path.basename(url)}")
                    found_for_qtr = True
                    continue

                # Variant: next year for Q4 (e.g., 01-02-2010 for 2009 Q4)
                if quarter == 4:
                    next_year = year + 1
                    url2 = f"{OLD_ARCHIVE_BASE}/{year}/Q{quarter}/ACS-UP-{year}-Q{quarter}_{date_str}-{next_year}.pdf"
                    if head_url(url2):
                        urls.add(url2)
                        log(f"  Found: {os.path.basename(url2)}")
                        found_for_qtr = True
                        continue

            if not found_for_qtr:
                log(f"  No PDF found for {year} Q{quarter}")

    log(f"  Old archive probe found {len(urls)} PDFs")
    return sorted(urls)


def probe_transition_era(start_year=2020, end_year=2022):
    """
    Probe the transition-era patterns (2020-2022).
    Various naming conventions used during this period.
    """
    log(f"Probing transition-era patterns ({start_year}-{end_year})...")
    urls = set()

    quarter_end_dates = {
        1: ["03-31", "03-30", "03-29", "04-01", "04-02"],
        2: ["06-30", "06-29", "06-28", "07-01", "07-02"],
        3: ["09-30", "09-29", "09-28", "10-01", "10-02"],
        4: ["12-31", "12-30", "12-29", "11-29", "11-30", "12-01",
            "01-01", "01-02", "01-03"],
    }

    for year in range(start_year, end_year + 1):
        for quarter in range(1, 5):
            found = False
            date_variants = quarter_end_dates[quarter]

            for date_str in date_variants:
                if found:
                    break

                # Pattern 1: ACS-UP-{Q}Q-{MM-DD-YYYY}.pdf
                url1 = f"{UPLOADS_BASE}/ACS-UP-{quarter}Q-{date_str}-{year}.pdf"
                if head_url(url1):
                    urls.add(url1)
                    log(f"  Found: {os.path.basename(url1)}")
                    found = True
                    continue

                # Pattern 2: ACS-UP-{YYYY}-{Q}Q-{MM-DD-YYYY}.pdf
                url2 = f"{UPLOADS_BASE}/ACS-UP-{year}-{quarter}Q-{date_str}-{year}.pdf"
                if head_url(url2):
                    urls.add(url2)
                    log(f"  Found: {os.path.basename(url2)}")
                    found = True
                    continue

                # Pattern 3: ACS-UP-{Q}Q_{MM-DD-YYYY}.pdf
                url3 = f"{UPLOADS_BASE}/ACS-UP-{quarter}Q_{date_str}-{year}.pdf"
                if head_url(url3):
                    urls.add(url3)
                    log(f"  Found: {os.path.basename(url3)}")
                    found = True
                    continue

                # Q4 with next year date
                if quarter == 4:
                    next_year = year + 1
                    url4 = f"{UPLOADS_BASE}/ACS-UP-{quarter}Q-{date_str}-{next_year}.pdf"
                    if head_url(url4):
                        urls.add(url4)
                        log(f"  Found: {os.path.basename(url4)}")
                        found = True
                        continue

            if not found:
                log(f"  No transition PDF found for {year} Q{quarter}")

    log(f"  Transition probe found {len(urls)} PDFs")
    return sorted(urls)


def probe_current_era(start_year=2023, end_year=2026):
    """
    Probe the current-era weekly pattern (2023-2026).
    Pattern: UP-Contract-Summary-{M}-{D}-{YYYY}.pdf
    These are weekly, so iterate through every week.
    """
    log(f"Probing current-era weekly patterns ({start_year}-{end_year})...")
    urls = set()

    start_date = datetime(start_year, 1, 1)
    end_date = min(datetime(end_year, 12, 31), datetime.now())
    current = start_date

    while current <= end_date:
        m = current.month
        d = current.day
        y = current.year

        # Pattern: UP-Contract-Summary-{M}-{D}-{YYYY}.pdf (no leading zeros)
        url1 = f"{UPLOADS_BASE}/UP-Contract-Summary-{m}-{d}-{y}.pdf"
        if head_url(url1):
            urls.add(url1)
            log(f"  Found: {os.path.basename(url1)}")
            # Skip ahead ~5 days after a hit (weekly filings)
            current += timedelta(days=5)
            continue

        # Pattern with leading zeros: UP-Contract-Summary-{MM}-{DD}-{YYYY}.pdf
        url2 = f"{UPLOADS_BASE}/UP-Contract-Summary-{m:02d}-{d:02d}-{y}.pdf"
        if url2 != url1 and head_url(url2):
            urls.add(url2)
            log(f"  Found: {os.path.basename(url2)}")
            current += timedelta(days=5)
            continue

        current += timedelta(days=1)

    log(f"  Current-era probe found {len(urls)} PDFs")
    return sorted(urls)


def run_discovery():
    """Run all discovery phases and save results."""
    all_urls = set()

    # Phase 1a: Scrape the STB ACS page
    page_urls = discover_from_stb_page()
    all_urls.update(page_urls)

    # Phase 1b: Probe old archive (2008-2019)
    old_urls = probe_old_archive(2008, 2019)
    all_urls.update(old_urls)

    # Phase 1c: Probe transition era (2020-2022)
    trans_urls = probe_transition_era(2020, 2022)
    all_urls.update(trans_urls)

    # Phase 1d: Probe current era (2023-2026)
    # Only probe dates NOT already found on the ACS page
    current_urls = probe_current_era(2023, 2026)
    all_urls.update(current_urls)

    # Deduplicate and sort
    all_urls = sorted(all_urls)

    # Save discovered URLs
    result = {
        "discovered_at": datetime.now().isoformat(),
        "total_urls": len(all_urls),
        "sources": {
            "stb_page": len(page_urls),
            "old_archive": len(old_urls),
            "transition_era": len(trans_urls),
            "current_era": len(current_urls),
        },
        "urls": all_urls,
    }

    DISCOVERED_URLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DISCOVERED_URLS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    log(f"\nDiscovery complete: {len(all_urls)} total URLs")
    log(f"  STB page: {len(page_urls)}")
    log(f"  Old archive: {len(old_urls)}")
    log(f"  Transition: {len(trans_urls)}")
    log(f"  Current era: {len(current_urls)}")
    log(f"Saved to: {DISCOVERED_URLS_PATH}")

    return all_urls


# ---------------------------------------------------------------------------
# Phase 2: Download
# ---------------------------------------------------------------------------
def load_manifest():
    """Load the download manifest."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"downloads": {}}


def save_manifest(manifest):
    """Save the download manifest."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def download_pdf(url, dest_path, retries=3):
    """Download a single PDF with retry logic. Returns (success, file_size)."""
    for attempt in range(1, retries + 1):
        resp = fetch_url(url, stream=True)
        if not resp or resp.status_code != 200:
            if attempt < retries:
                log(f"  Retry {attempt}/{retries} (bad response)...")
                time.sleep(2 * attempt)
                continue
            return False, 0

        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type and "octet-stream" not in content_type:
            log(f"  Warning: unexpected content type '{content_type}' for {url}")

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        total_size = 0
        try:
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_size += len(chunk)
            return True, total_size
        except (requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                ConnectionResetError) as e:
            if attempt < retries:
                log(f"  Retry {attempt}/{retries} (connection error)...")
                time.sleep(2 * attempt)
                continue
            log(f"  Failed after {retries} attempts: {e}")
            # Clean up partial file
            if dest_path.exists():
                dest_path.unlink()
            return False, 0
    return False, 0


def run_download():
    """Download all discovered PDFs."""
    # Load or run discovery
    if not DISCOVERED_URLS_PATH.exists():
        log("No discovered URLs found. Running discovery first...")
        urls = run_discovery()
    else:
        with open(DISCOVERED_URLS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        urls = data["urls"]
        log(f"Loaded {len(urls)} discovered URLs")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()

    downloaded = 0
    skipped = 0
    failed = 0

    for i, url in enumerate(urls, 1):
        filename = unquote(os.path.basename(urlparse(url).path))
        dest_path = DOWNLOAD_DIR / filename

        # Skip if already downloaded successfully
        if url in manifest["downloads"]:
            entry = manifest["downloads"][url]
            if entry.get("status") == "ok" and dest_path.exists():
                skipped += 1
                continue

        log(f"[{i}/{len(urls)}] Downloading {filename}...")
        success, size = download_pdf(url, dest_path)

        if success:
            manifest["downloads"][url] = {
                "filename": filename,
                "status": "ok",
                "size_bytes": size,
                "downloaded_at": datetime.now().isoformat(),
            }
            downloaded += 1
            log(f"  OK ({size:,} bytes)")
        else:
            manifest["downloads"][url] = {
                "filename": filename,
                "status": "failed",
                "attempted_at": datetime.now().isoformat(),
            }
            failed += 1
            log(f"  FAILED")

        # Save manifest after each download (resume-friendly)
        save_manifest(manifest)

    log(f"\nDownload complete: {downloaded} new, {skipped} skipped, {failed} failed")
    return manifest


# ---------------------------------------------------------------------------
# Phase 3: Parse all downloaded PDFs into SQLite
# ---------------------------------------------------------------------------
def load_contracts_to_db(contracts, source_file, db_path):
    """
    Load parsed contracts from one PDF into the unified SQLite DB.
    Handles duplicate filings by checking source_file.
    """
    from parse_acs_pdf import generate_sql_schema

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Create schema
    for stmt in generate_sql_schema().split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt + ";")

    if not contracts:
        conn.close()
        return 0

    # Check if this filing already exists
    cur.execute("SELECT filing_id FROM acs_filing WHERE source_file = ?",
                (source_file,))
    existing = cur.fetchone()

    if existing:
        filing_id = existing[0]
        # Delete old data for this filing so we can re-insert
        cur.execute("""
            DELETE FROM acs_exhibit WHERE contract_id IN
            (SELECT contract_id FROM acs_contract WHERE filing_id = ?)
        """, (filing_id,))
        cur.execute("""
            DELETE FROM acs_destination WHERE contract_id IN
            (SELECT contract_id FROM acs_contract WHERE filing_id = ?)
        """, (filing_id,))
        cur.execute("""
            DELETE FROM acs_origin WHERE contract_id IN
            (SELECT contract_id FROM acs_contract WHERE filing_id = ?)
        """, (filing_id,))
        cur.execute("""
            DELETE FROM acs_shipper WHERE contract_id IN
            (SELECT contract_id FROM acs_contract WHERE filing_id = ?)
        """, (filing_id,))
        cur.execute("""
            DELETE FROM acs_commodity WHERE contract_id IN
            (SELECT contract_id FROM acs_contract WHERE filing_id = ?)
        """, (filing_id,))
        cur.execute("""
            DELETE FROM acs_carrier WHERE contract_id IN
            (SELECT contract_id FROM acs_contract WHERE filing_id = ?)
        """, (filing_id,))
        cur.execute("DELETE FROM acs_contract WHERE filing_id = ?",
                     (filing_id,))
        cur.execute("DELETE FROM acs_filing WHERE filing_id = ?",
                     (filing_id,))

    # Insert filing
    c0 = contracts[0]
    cur.execute(
        "INSERT INTO acs_filing (source_file, filing_received_date, railroad) "
        "VALUES (?, ?, ?)",
        (source_file, c0.filing_received_date, c0.railroad or "UNION PACIFIC RAILROAD"),
    )
    filing_id = cur.lastrowid

    inserted = 0
    for c in contracts:
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

        for ca in c.participating_carriers:
            cur.execute(
                "INSERT INTO acs_carrier (contract_id, carrier_name, carrier_address, amendment_action) VALUES (?,?,?,?)",
                (c.contract_id, ca["name"], ca.get("address", ""), ca.get("amendment_action")),
            )
        for co in c.commodities:
            cur.execute(
                "INSERT INTO acs_commodity (contract_id, description, amendment_action) VALUES (?,?,?)",
                (c.contract_id, co["description"], co.get("amendment_action")),
            )
        for sh in c.shippers:
            cur.execute(
                "INSERT INTO acs_shipper (contract_id, shipper_name) VALUES (?,?)",
                (c.contract_id, sh),
            )
        for o in c.origins:
            cur.execute(
                "INSERT INTO acs_origin (contract_id, location, city, state, amendment_action, is_ags_reference) VALUES (?,?,?,?,?,?)",
                (c.contract_id, o["location"], o["city"], o["state"],
                 o.get("amendment_action"), 1 if o.get("is_ags_reference") else 0),
            )
        for d in c.destinations:
            cur.execute(
                "INSERT INTO acs_destination (contract_id, location, city, state, amendment_action, is_ags_reference) VALUES (?,?,?,?,?,?)",
                (c.contract_id, d["location"], d["city"], d["state"],
                 d.get("amendment_action"), 1 if d.get("is_ags_reference") else 0),
            )
        for exhibit_name, stations in c.exhibit_definitions.items():
            for station in stations:
                cur.execute(
                    "INSERT INTO acs_exhibit (contract_id, exhibit_name, station_name) VALUES (?,?,?)",
                    (c.contract_id, exhibit_name, station),
                )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


PDF_PARSE_TIMEOUT = 120  # max seconds per PDF


def _parse_one_pdf(pdf_path_str):
    """Worker function to parse a single PDF (runs in subprocess for timeout)."""
    sys.path.insert(0, str(SCRIPT_DIR))
    from parse_acs_pdf import parse_acs_pdf
    return parse_acs_pdf(pdf_path_str)


def parse_pdf_with_timeout(pdf_path_str, timeout=PDF_PARSE_TIMEOUT):
    """Parse a PDF with a timeout. Returns contracts list or raises."""
    with multiprocessing.Pool(1) as pool:
        result = pool.apply_async(_parse_one_pdf, (pdf_path_str,))
        return result.get(timeout=timeout)


def run_parse():
    """Parse all downloaded PDFs into the unified SQLite database.

    Builds the DB in a local temp directory to avoid Google Drive sync
    corruption, then copies the finished DB to the final location.
    Tracks parsed files so it can resume if interrupted.
    """
    if not DOWNLOAD_DIR.exists():
        log("No downloads directory found. Run 'download' first.")
        return

    pdf_files = sorted(DOWNLOAD_DIR.glob("*.pdf"))
    if not pdf_files:
        log("No PDF files found in downloads directory.")
        return

    log(f"Found {len(pdf_files)} PDFs to parse")

    # Use a persistent local temp DB so we can resume
    tmp_dir = Path(tempfile.gettempdir()) / "stb_parse_resume"
    tmp_dir.mkdir(exist_ok=True)
    tmp_db = tmp_dir / "stb_contracts.db"
    parsed_tracker = tmp_dir / "parsed_files.json"

    # Load set of already-parsed files
    already_parsed = set()
    if parsed_tracker.exists():
        already_parsed = set(json.loads(parsed_tracker.read_text()))
        log(f"Resuming: {len(already_parsed)} files already parsed")

    log(f"Building DB in local temp: {tmp_db}")

    total_contracts = 0
    successful = 0
    failed = 0
    skipped = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        if pdf_path.name in already_parsed:
            skipped += 1
            continue

        log(f"[{i}/{len(pdf_files)}] Parsing {pdf_path.name}...")
        try:
            contracts = parse_pdf_with_timeout(str(pdf_path))
            if contracts:
                n = load_contracts_to_db(contracts, pdf_path.name, tmp_db)
                total_contracts += n
                successful += 1
                log(f"  OK: {n} contracts")
            else:
                log(f"  Warning: no contracts found in {pdf_path.name}")
                successful += 1
            # Track as parsed
            already_parsed.add(pdf_path.name)
            parsed_tracker.write_text(json.dumps(sorted(already_parsed)))
        except multiprocessing.TimeoutError:
            failed += 1
            log(f"  TIMEOUT after {PDF_PARSE_TIMEOUT}s - skipping")
            already_parsed.add(pdf_path.name)  # don't retry on resume
            parsed_tracker.write_text(json.dumps(sorted(already_parsed)))
        except Exception as e:
            failed += 1
            log(f"  ERROR: {e}")

    log(f"\nParsing complete:")
    log(f"  PDFs processed: {successful} ok, {failed} failed, {skipped} skipped (already parsed)")
    log(f"  Total contracts loaded: {total_contracts}")

    # Copy finished DB to final location on Google Drive
    log(f"Copying DB to {DB_PATH}...")
    if DB_PATH.exists():
        DB_PATH.unlink()
    shutil.copy2(str(tmp_db), str(DB_PATH))
    log(f"  Database: {DB_PATH}")

    # Clean up tracker (keep temp DB for safety)
    if parsed_tracker.exists():
        parsed_tracker.unlink()

    # Print DB stats
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        for table in ["acs_filing", "acs_contract", "acs_carrier",
                       "acs_commodity", "acs_shipper", "acs_origin",
                       "acs_destination", "acs_exhibit"]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                log(f"  {table}: {count:,} rows")
            except sqlite3.OperationalError:
                pass
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "discover":
        run_discovery()
    elif command == "download":
        # Skip re-discovery if we already have saved URLs
        if not DISCOVERED_URLS_PATH.exists():
            run_discovery()
        else:
            log(f"Using existing discovery: {DISCOVERED_URLS_PATH}")
        run_download()
    elif command == "parse":
        run_parse()
    elif command == "all":
        run_discovery()
        run_download()
        run_parse()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: discover, download, parse, all")
        sys.exit(1)


if __name__ == "__main__":
    main()
