#!/usr/bin/env python3
"""
download_coal_data.py
Coal Module — Master Data Downloader

Downloads all Priority 1-14 coal data sources to data/raw/ subdirectories.
Run from 03_COMMODITY_MODULES/coal/ directory.

Usage:
    python src/download_coal_data.py --priority 1     # MSHA mines only
    python src/download_coal_data.py --priority 1-4   # P1 through P4
    python src/download_coal_data.py --source eia_923 # Single source by ID
    python src/download_coal_data.py --all            # All sources
    python src/download_coal_data.py --list           # List all sources and exit

Requires:
    pip install requests tqdm click

EIA API key: Set as environment variable EIA_API_KEY
Census API key: Set as environment variable CENSUS_API_KEY
"""

import os
import sys
import json
import time
import zipfile
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import click
    from tqdm import tqdm
except ImportError:
    print("Install dependencies: pip install requests tqdm click")
    sys.exit(1)

# ─── Paths ───────────────────────────────────────────────────────────────────
MODULE_DIR = Path(__file__).parent.parent
DATA_RAW = MODULE_DIR / "data" / "raw"
LOG_DIR = MODULE_DIR / "data"

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "download_log.txt"),
    ],
)
log = logging.getLogger(__name__)

# ─── API Keys (from environment) ─────────────────────────────────────────────
EIA_API_KEY = os.environ.get("EIA_API_KEY", "")
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")
COMTRADE_KEY = os.environ.get("COMTRADE_API_KEY", "")


# ─── Source Catalog ──────────────────────────────────────────────────────────

SOURCES = [
    # ── Priority 1 — Foundation ──────────────────────────────────────────────
    {
        "id": "msha_mines",
        "priority": 1,
        "name": "MSHA Master Mine List",
        "url": "https://arlweb.msha.gov/OpenGovernmentData/DataSets/Mines.zip",
        "dest_dir": DATA_RAW / "msha",
        "filename": "Mines.zip",
        "unzip": True,
        "notes": "Filter COAL_METAL_IND='C' for coal mines. Contains lat/lon coordinates.",
    },
    {
        "id": "msha_production_quarterly",
        "priority": 1,
        "name": "MSHA Mine Production (Quarterly)",
        "url": "https://arlweb.msha.gov/OpenGovernmentData/DataSets/MinesProdQuarterly.zip",
        "dest_dir": DATA_RAW / "msha",
        "filename": "MinesProdQuarterly.zip",
        "unzip": True,
        "notes": "Quarterly short tons and employment by MINE_ID.",
    },
    {
        "id": "msha_data_dictionary",
        "priority": 1,
        "name": "MSHA Data Dictionary",
        "url": "https://arlweb.msha.gov/OpenGovernmentData/DataSets/DataDictionary.xls",
        "dest_dir": DATA_RAW / "msha",
        "filename": "DataDictionary.xls",
        "unzip": False,
    },
    {
        "id": "usgs_coal_fields_gis",
        "priority": 1,
        "name": "USGS US Coal Fields Map (GIS)",
        "url": "https://www.usgs.gov/maps/us-coal-fields-2012",
        "dest_dir": DATA_RAW / "usgs" / "gis",
        "filename": None,  # Manual download — shapefile linked from page
        "method": "manual",
        "notes": "Download shapefile from USGS map page. Alternatively use CERTMAPPER: "
                 "https://certmapper.cr.usgs.gov/data/coal/national/spatial/shp/",
    },
    {
        "id": "bts_ntad_ports",
        "priority": 1,
        "name": "BTS NTAD US Ports (Shapefile)",
        "url": "https://geodata.bts.gov/datasets/usdot::ports/about",
        "dest_dir": DATA_RAW / "geospatial",
        "filename": None,
        "method": "manual",
        "notes": "Download Shapefile from BTS ArcGIS Hub. Includes Schedule D port codes.",
    },
    # ── Priority 2 — EIA Bulk Downloads ──────────────────────────────────────
    {
        "id": "eia_acr_tables",
        "priority": 2,
        "name": "EIA Annual Coal Report — All Tables",
        "url": None,  # Multi-file download (see download function)
        "dest_dir": DATA_RAW / "eia" / "annual_coal_report",
        "filename": "acr_table_{NN}.xlsx",
        "method": "multi_file",
        "file_range": range(1, 21),
        "url_pattern": "https://www.eia.gov/coal/annual/xls/acr_table{:02d}.xlsx",
        "notes": "Tables 1-20: production, exports, reserves, prices, transportation modes.",
    },
    {
        "id": "eia_923_latest",
        "priority": 2,
        "name": "EIA Form EIA-923 (Latest Year ZIP)",
        "url": "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_2023.zip",
        "dest_dir": DATA_RAW / "eia" / "eia923",
        "filename": "f923_2023.zip",
        "unzip": True,
        "notes": "Extract Schedule 2 (coal receipts) and Schedule 3 (boiler fuel). "
                 "Contains mine-to-plant records with MSHA Mine ID as join key.",
    },
    {
        "id": "eia_steo",
        "priority": 2,
        "name": "EIA Short-Term Energy Outlook (Full Excel)",
        "url": "https://www.eia.gov/steo/xls/steo_full.xlsx",
        "dest_dir": DATA_RAW / "eia" / "steo",
        "filename": f"steo_full_{datetime.now().strftime('%Y%m')}.xlsx",
        "unzip": False,
        "notes": "Table 7: Coal supply and consumption forecast.",
    },
    {
        "id": "eia_mer_coal",
        "priority": 2,
        "name": "EIA Monthly Energy Review — Coal Tables (6.1-6.6)",
        "url": None,
        "dest_dir": DATA_RAW / "eia" / "mer",
        "method": "multi_file",
        "url_template": "https://www.eia.gov/totalenergy/data/browser/xls.php?tbl=T06.0{n}",
        "table_nums": [1, 2, 3, 4, 5, 6],
        "notes": "Tables 6.1-6.6: Coal overview, production by region, consumption, imports/exports.",
    },
    {
        "id": "usgs_minerals_yearbook",
        "priority": 2,
        "name": "USGS Minerals Yearbook — Coal Chapter (2022)",
        "url": "https://pubs.usgs.gov/myb/vol1/2022/myb1-2022-coal.xlsx",
        "dest_dir": DATA_RAW / "usgs",
        "filename": "usgs_myb_2022_coal.xlsx",
        "unzip": False,
        "notes": "Global and US coal production/trade statistics.",
    },
    {
        "id": "usgs_mcs_coal",
        "priority": 2,
        "name": "USGS Mineral Commodity Summary — Coal (2024)",
        "url": "https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-coal.pdf",
        "dest_dir": DATA_RAW / "usgs",
        "filename": "usgs_mcs2024_coal.pdf",
        "unzip": False,
    },
    {
        "id": "world_bank_pink_sheet",
        "priority": 2,
        "name": "World Bank Commodity Price Pink Sheet",
        "url": "https://www.worldbank.org/en/research/commodity-markets",
        "dest_dir": DATA_RAW / "pricing",
        "filename": None,
        "method": "manual",
        "notes": "Download latest Pink Sheet Excel from World Bank page. "
                 "Extracts: COAL_AUS, COAL_US, COAL_SAFS series.",
    },
    {
        "id": "energy_institute_stat_review",
        "priority": 2,
        "name": "Energy Institute Statistical Review — Excel Workbook",
        "url": "https://www.energyinst.org/statistical-review/resources-and-data/downloads",
        "dest_dir": DATA_RAW / "global",
        "filename": None,
        "method": "manual",
        "notes": "Download 'Statistical Review of World Energy Data.xlsx'. "
                 "Coal tabs: Production, Consumption, Trade Movements, Prices.",
    },
    # ── Priority 3 — Geospatial ───────────────────────────────────────────────
    {
        "id": "bts_ntad_rail",
        "priority": 3,
        "name": "BTS NTAD North American Rail Lines (Shapefile)",
        "url": "https://geodata.bts.gov/datasets/usdot::north-american-rail-lines/about",
        "dest_dir": DATA_RAW / "geospatial",
        "filename": None,
        "method": "manual",
        "notes": "Download Shapefile from BTS ArcGIS Hub. All Class I + regional rail with operator attributes.",
    },
    {
        "id": "bts_ntad_waterway",
        "priority": 3,
        "name": "BTS NTAD National Waterway Network",
        "url": "https://www.bts.gov/ntad/national-waterway-network",
        "dest_dir": DATA_RAW / "geospatial",
        "filename": None,
        "method": "manual",
        "notes": "Download Shapefile. Navigable waterway network with terminal nodes.",
    },
    # ── Priority 4 — EIA API (requires key) ──────────────────────────────────
    {
        "id": "eia_api_production",
        "priority": 4,
        "name": "EIA API — Coal Production (Annual, by State)",
        "url": "https://api.eia.gov/v2/coal/production/data/",
        "dest_dir": DATA_RAW / "eia" / "api",
        "filename": "eia_coal_production_by_state.json",
        "method": "eia_api",
        "params": {
            "frequency": "annual",
            "data[0]": "production",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 5000,
        },
        "requires_key": "EIA_API_KEY",
    },
    {
        "id": "eia_api_prices_weekly",
        "priority": 4,
        "name": "EIA API — Coal Spot Prices (Weekly, all regions)",
        "url": "https://api.eia.gov/v2/coal/price/data/",
        "dest_dir": DATA_RAW / "eia" / "api",
        "filename": "eia_coal_prices_weekly.json",
        "method": "eia_api",
        "params": {
            "frequency": "weekly",
            "data[0]": "price",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 5000,
        },
        "requires_key": "EIA_API_KEY",
    },
    {
        "id": "eia_api_exports",
        "priority": 4,
        "name": "EIA API — Coal Exports (Annual, by Country)",
        "url": "https://api.eia.gov/v2/coal/exports/data/",
        "dest_dir": DATA_RAW / "eia" / "api",
        "filename": "eia_coal_exports_annual.json",
        "method": "eia_api",
        "params": {
            "frequency": "annual",
            "data[0]": "quantity",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 5000,
        },
        "requires_key": "EIA_API_KEY",
    },
    # ── Priority 5 — Trade Data (requires registration) ──────────────────────
    {
        "id": "usitc_dataweb",
        "priority": 5,
        "name": "USITC DataWeb — Coal HTS 2701 (Export/Import)",
        "url": "https://dataweb.usitc.gov/",
        "dest_dir": DATA_RAW / "census_trade",
        "filename": None,
        "method": "manual",
        "notes": "Query HTS 2701 at dataweb.usitc.gov. Download CSV. No registration required.",
    },
    {
        "id": "msha_accidents",
        "priority": 5,
        "name": "MSHA Accidents and Injuries",
        "url": "https://arlweb.msha.gov/OpenGovernmentData/DataSets/Accidents.zip",
        "dest_dir": DATA_RAW / "msha",
        "filename": "Accidents.zip",
        "unzip": True,
    },
]


# ─── Download Helpers ─────────────────────────────────────────────────────────

def _get_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (compatible; CoalModuleResearch/1.0; +https://github.com/theshipsagent)",
        "Accept": "*/*",
    }


def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """Download a single file with progress bar."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=_get_headers(), stream=True, timeout=120)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest_path, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest_path.name
        ) as bar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                bar.update(len(chunk))
        log.info(f"Downloaded: {dest_path}")
        return True
    except Exception as e:
        log.error(f"Failed: {url} → {e}")
        return False


def unzip_file(zip_path: Path, dest_dir: Path) -> None:
    """Extract ZIP archive."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    log.info(f"Extracted: {zip_path.name} → {dest_dir}")


def eia_api_download(source: dict) -> bool:
    """Download from EIA API v2."""
    if not EIA_API_KEY:
        log.warning(f"EIA_API_KEY not set — skipping {source['id']}. "
                    f"Register at https://www.eia.gov/opendata/register.php")
        return False
    params = {"api_key": EIA_API_KEY, **source["params"]}
    dest_path = source["dest_dir"] / source["filename"]
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(source["url"], params=params, timeout=60)
        r.raise_for_status()
        with open(dest_path, "w") as f:
            json.dump(r.json(), f, indent=2)
        log.info(f"EIA API saved: {dest_path}")
        return True
    except Exception as e:
        log.error(f"EIA API failed ({source['id']}): {e}")
        return False


def download_source(source: dict, dry_run: bool = False) -> bool:
    """Route a source dict to the correct download method."""
    method = source.get("method", "direct")

    if method == "manual":
        log.info(f"[MANUAL] {source['name']}")
        log.info(f"  → URL: {source['url']}")
        if source.get("notes"):
            log.info(f"  → Notes: {source['notes']}")
        return True  # Mark as handled

    if dry_run:
        log.info(f"[DRY RUN] Would download: {source['name']}")
        return True

    dest_dir: Path = source["dest_dir"]
    dest_dir.mkdir(parents=True, exist_ok=True)

    if method == "direct":
        dest_path = dest_dir / source["filename"]
        ok = download_file(source["url"], dest_path)
        if ok and source.get("unzip") and dest_path.suffix == ".zip":
            unzip_file(dest_path, dest_dir)
        return ok

    elif method == "multi_file":
        # EIA ACR tables
        if "url_pattern" in source:
            ok_all = True
            for n in source["file_range"]:
                url = source["url_pattern"].format(n)
                fname = source["dest_dir"] / f"acr_table{n:02d}.xlsx"
                ok = download_file(url, fname)
                ok_all = ok_all and ok
                time.sleep(0.5)  # Be polite to EIA servers
            return ok_all
        # EIA MER tables
        if "url_template" in source:
            ok_all = True
            for n in source["table_nums"]:
                url = source["url_template"].format(n=n)
                fname = dest_dir / f"mer_table_6{n}.xlsx"
                ok = download_file(url, fname)
                ok_all = ok_all and ok
                time.sleep(0.5)
            return ok_all

    elif method == "eia_api":
        return eia_api_download(source)

    log.warning(f"Unknown method '{method}' for source {source['id']}")
    return False


# ─── CLI ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--priority", default=None, help="Priority level (e.g. 1, 2, 1-3)")
@click.option("--source", default=None, help="Download specific source by ID")
@click.option("--all", "download_all", is_flag=True, help="Download all sources")
@click.option("--list", "list_sources", is_flag=True, help="List all sources")
@click.option("--dry-run", is_flag=True, help="Show what would be downloaded without downloading")
def main(priority: Optional[str], source: Optional[str], download_all: bool,
         list_sources: bool, dry_run: bool):
    """Coal Module — Master Data Downloader"""

    if list_sources:
        click.echo("\nCoal Module Data Sources:\n")
        click.echo(f"{'P':>2}  {'ID':<35} {'Name'}")
        click.echo("-" * 80)
        for s in sorted(SOURCES, key=lambda x: x["priority"]):
            click.echo(f"{s['priority']:>2}  {s['id']:<35} {s['name']}")
        return

    # Determine which sources to download
    targets = []
    if download_all:
        targets = SOURCES
    elif priority:
        if "-" in priority:
            lo, hi = priority.split("-")
            targets = [s for s in SOURCES if int(lo) <= s["priority"] <= int(hi)]
        else:
            targets = [s for s in SOURCES if s["priority"] == int(priority)]
    elif source:
        targets = [s for s in SOURCES if s["id"] == source]
        if not targets:
            click.echo(f"Source '{source}' not found. Use --list to see available sources.")
            sys.exit(1)
    else:
        click.echo("Specify --priority N, --source ID, --all, or --list")
        sys.exit(1)

    click.echo(f"\nCoal Module Data Downloader")
    click.echo(f"Download directory: {DATA_RAW}")
    click.echo(f"Sources to download: {len(targets)}")
    if dry_run:
        click.echo("[DRY RUN MODE]\n")

    results = {"success": 0, "failed": 0, "manual": 0}

    for s in targets:
        click.echo(f"\n[P{s['priority']}] {s['name']}")
        method = s.get("method", "direct")
        if method == "manual":
            results["manual"] += 1
        ok = download_source(s, dry_run=dry_run)
        if ok:
            results["success"] += 1
        else:
            results["failed"] += 1

    click.echo(f"\n{'='*60}")
    click.echo(f"Results: {results['success']} success | {results['failed']} failed | {results['manual']} manual")
    if results["manual"] > 0:
        click.echo("Manual sources require browser download — see log for URLs.")
    if results["failed"] > 0:
        click.echo("Check download_log.txt for error details.")


if __name__ == "__main__":
    main()
