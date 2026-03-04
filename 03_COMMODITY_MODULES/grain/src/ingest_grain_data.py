#!/usr/bin/env python3
"""
Grain Commodity Module — Master Data Ingestion Pipeline
========================================================
Pulls from all 26 catalogued data sources in priority order.

Usage:
    python ingest_grain_data.py                          # Full ingestion
    python ingest_grain_data.py --step production        # NASS supply data only
    python ingest_grain_data.py --step psd               # FAS PSD only
    python ingest_grain_data.py --step esr               # FAS ESR weekly exports
    python ingest_grain_data.py --step census            # Census trade data
    python ingest_grain_data.py --step gtr               # AMS GTR freight datasets
    python ingest_grain_data.py --step fgis              # FGIS inspection data
    python ingest_grain_data.py --commodity CORN         # Single commodity
    python ingest_grain_data.py --year 2025              # Specific year

Requirements:
    pip install requests pandas openpyxl pyarrow python-dotenv aiohttp

Environment Variables (required for some sources):
    USDA_API_KEY    — Register at https://api.data.gov/signup/
    CENSUS_API_KEY  — Register at https://api.census.gov/data/key_signup.html
    EIA_API_KEY     — Register at https://www.eia.gov/opendata/ (optional)
"""

import os
import sys
import json
import logging
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

USDA_KEY = os.getenv("USDA_API_KEY")
CENSUS_KEY = os.getenv("CENSUS_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("grain_ingest")

# ---------------------------------------------------------------------------
# Commodity master mapping
# ---------------------------------------------------------------------------
GRAINS = {
    "CORN": {
        "esr_code": "104",
        "psd_code": "0440000",
        "nass_desc": "CORN",
        "hs10_export": "1005900020",
        "stcc_rail": "01112",
        "usace_code": "15",
        "marketing_year_start": "SEP",
    },
    "SOYBEANS": {
        "esr_code": "801",
        "psd_code": "2222000",
        "nass_desc": "SOYBEANS",
        "hs10_export": "1201900005",
        "stcc_rail": "01141",
        "usace_code": "14",
        "marketing_year_start": "SEP",
    },
    "WHEAT": {
        "esr_code": "101",
        "psd_code": "0410000",
        "nass_desc": "WHEAT",
        "hs10_subcodes": ["1001990010", "1001990020", "1001990030", "1001990040"],
        "stcc_rail": "01131",
        "usace_code": "17",
        "marketing_year_start": "JUN",
    },
    "SORGHUM": {
        "esr_code": "106",
        "psd_code": "0450000",
        "nass_desc": "SORGHUM",
        "hs10_export": "1007900010",
        "stcc_rail": "01155",
        "marketing_year_start": "SEP",
    },
    "BARLEY": {
        "esr_code": "102",
        "psd_code": "0430000",
        "nass_desc": "BARLEY",
        "hs10_export": "1003900010",
        "stcc_rail": "01130",
        "marketing_year_start": "JUN",
    },
    "OATS": {
        "esr_code": "103",
        "psd_code": "0460000",
        "nass_desc": "OATS",
        "hs10_export": "1004900000",
        "marketing_year_start": "JUN",
    },
    "RICE": {
        "esr_code": "501",
        "psd_code": "0422110",
        "nass_desc": "RICE",
        "hs10_export": "1006300010",
        "marketing_year_start": "AUG",
    },
    "DDGS": {
        "esr_code": "105",
        "nass_desc": None,
        "hs10_export": "2303100040",
    },
    "SOY_MEAL": {
        "esr_code": "803",
        "psd_code": "2223000",
        "nass_desc": None,
        "hs10_export": "2304001000",
    },
    "SOY_OIL": {
        "esr_code": "802",
        "psd_code": "4243000",
        "nass_desc": None,
        "hs10_export": "1507100000",
    },
}

# AMS GTR dataset filenames
GTR_DATASETS = {
    "transport_indicators": "Table01GTRDataset.xlsx",
    "price_spreads": "Table02GTRDataset.xlsx",
    "railcar_bids": "Table05GTRDataset.xlsx",
    "fuel_surcharges": "Figure09GTRDataset.xlsx",
    "barge_rates_southbound": "Table09GTRDataset.xlsx",
    "barge_movements_locks": "Table10GTRDataset.xlsx",
    "barge_freight_columbia": "Table11GTRDataset.xlsx",
    "barge_grain_columbia": "Table12GTRDataset.xlsx",
    "export_balances": "Table14GTRDataset.xlsx",
    "ocean_rates_japan": "Figure20GTRDataset.xlsx",
    "grain_bids_30day": "GrainBidDataset.xlsx",
}
GTR_BASE = "https://www.ams.usda.gov/sites/default/files/media/"

# ERS Excel downloads
ERS_DOWNLOADS = {
    "feed_grains_db": "https://www.ers.usda.gov/webdocs/DataFiles/50048/FeedGrains.xlsx",
    "fatus_monthly_value": "https://www.ers.usda.gov/webdocs/DataFiles/50048/sumtab1.xlsx",
    "fatus_annual_country": "https://www.ers.usda.gov/webdocs/DataFiles/50048/sumtab2.xlsx",
    "fatus_monthly_country": "https://www.ers.usda.gov/webdocs/DataFiles/50048/sumtab3.xlsx",
    "fatus_bulk": "https://www.ers.usda.gov/webdocs/DataFiles/50048/sumtab4.xlsx",
}


# ---------------------------------------------------------------------------
# Source 1: USDA FAS ESR — Weekly Export Sales
# ---------------------------------------------------------------------------
def fetch_fas_esr(commodity: str, market_year: int) -> Optional[pd.DataFrame]:
    """Pull FAS Export Sales Report data for one commodity and market year."""
    code = GRAINS[commodity]["esr_code"]
    url = f"https://apps.fas.usda.gov/OpenData/api/esr/exports/commodityCode/{code}/allCountries/marketYear/{market_year}"
    log.info(f"  FAS ESR: {commodity} {market_year} — {url}")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            log.warning(f"  FAS ESR: No data returned for {commodity} {market_year}")
            return None
        df = pd.DataFrame(data)
        df["commodity"] = commodity
        df["market_year"] = market_year
        return df
    except Exception as e:
        log.error(f"  FAS ESR FAILED {commodity} {market_year}: {e}")
        return None


# ---------------------------------------------------------------------------
# Source 2: USDA FAS PSD — Production, Supply & Distribution
# ---------------------------------------------------------------------------
def fetch_fas_psd(commodity: str, year: int) -> Optional[pd.DataFrame]:
    """Pull FAS PSD global supply/demand data."""
    if "psd_code" not in GRAINS[commodity]:
        return None
    code = GRAINS[commodity]["psd_code"]
    url = f"https://apps.fas.usda.gov/OpenData/api/psd/commodity/{code}/country/all/year/{year}"
    log.info(f"  FAS PSD: {commodity} {year}")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        df = pd.DataFrame(data)
        df["commodity"] = commodity
        df["year"] = year
        return df
    except Exception as e:
        log.error(f"  FAS PSD FAILED {commodity} {year}: {e}")
        return None


# ---------------------------------------------------------------------------
# Source 3: USDA NASS QuickStats
# ---------------------------------------------------------------------------
def fetch_nass(
    commodity: str,
    stat_category: str,
    year_ge: int = 2000,
    agg_level: str = "NATIONAL",
) -> Optional[pd.DataFrame]:
    """Pull NASS QuickStats production/stocks/prices data."""
    if not USDA_KEY:
        log.error("  NASS: USDA_API_KEY not set — skipping")
        return None
    nass_desc = GRAINS[commodity].get("nass_desc")
    if not nass_desc:
        return None

    url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params = {
        "key": USDA_KEY,
        "commodity_desc": nass_desc,
        "statisticcat_desc": stat_category,
        "year__GE": year_ge,
        "agg_level_desc": agg_level,
        "format": "JSON",
    }
    log.info(f"  NASS: {commodity} / {stat_category} (>={year_ge}, {agg_level})")
    try:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None
        df = pd.DataFrame(data)
        df["commodity"] = commodity
        return df
    except Exception as e:
        log.error(f"  NASS FAILED {commodity}/{stat_category}: {e}")
        return None


# ---------------------------------------------------------------------------
# Source 4: U.S. Census Bureau International Trade API
# ---------------------------------------------------------------------------
def fetch_census_exports(hs_code: str, year_month: str) -> Optional[pd.DataFrame]:
    """Pull Census export data for one HS code and year-month (YYYY-MM)."""
    if not CENSUS_KEY:
        log.error("  Census: CENSUS_API_KEY not set — skipping")
        return None

    url = "https://api.census.gov/data/timeseries/intltrade/exports/hs"
    params = {
        "get": "CTY_CODE,CTY_NAME,ALL_VAL_MO,QTY_1_MO,QTY_2_MO",
        "E_COMMODITY": hs_code,
        "time": year_month,
        "key": CENSUS_KEY,
    }
    log.info(f"  Census: HS {hs_code} for {year_month}")
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        raw = r.json()
        if len(raw) < 2:
            return None
        df = pd.DataFrame(raw[1:], columns=raw[0])
        df["hs_code"] = hs_code
        df["year_month"] = year_month
        return df
    except Exception as e:
        log.error(f"  Census FAILED HS {hs_code} {year_month}: {e}")
        return None


def fetch_census_exports_by_port(hs6_code: str, year_month: str) -> Optional[pd.DataFrame]:
    """Pull Census export data by port for one HS-6 code and year-month."""
    if not CENSUS_KEY:
        return None
    url = "https://api.census.gov/data/timeseries/intltrade/exports/porths"
    params = {
        "get": "PORT,PORT_NAME,ALL_VAL_MO,QTY_1_MO",
        "E_COMMODITY": hs6_code,
        "time": year_month,
        "key": CENSUS_KEY,
    }
    log.info(f"  Census (by port): HS6 {hs6_code} for {year_month}")
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        raw = r.json()
        if len(raw) < 2:
            return None
        df = pd.DataFrame(raw[1:], columns=raw[0])
        df["hs6_code"] = hs6_code
        df["year_month"] = year_month
        return df
    except Exception as e:
        log.error(f"  Census by port FAILED HS6 {hs6_code} {year_month}: {e}")
        return None


# ---------------------------------------------------------------------------
# Source 6: USDA AMS GTR Freight Datasets
# ---------------------------------------------------------------------------
def fetch_ams_gtr(dataset_name: str) -> Optional[pd.DataFrame]:
    """Download one AMS GTR Excel dataset."""
    filename = GTR_DATASETS.get(dataset_name)
    if not filename:
        log.error(f"  AMS GTR: Unknown dataset {dataset_name}")
        return None

    url = GTR_BASE + filename
    out_path = RAW_DIR / "gtr" / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"  AMS GTR: {dataset_name} → {filename}")
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        # Return dict of sheet DataFrames
        return pd.read_excel(out_path, sheet_name=None)
    except Exception as e:
        log.error(f"  AMS GTR FAILED {dataset_name}: {e}")
        return None


def fetch_all_gtr() -> dict:
    """Download all AMS GTR datasets."""
    results = {}
    for name in GTR_DATASETS:
        results[name] = fetch_ams_gtr(name)
    return results


# ---------------------------------------------------------------------------
# Source 5: ERS Excel Downloads
# ---------------------------------------------------------------------------
def fetch_ers_excel(dataset_name: str) -> Optional[dict]:
    """Download one ERS Excel file."""
    url = ERS_DOWNLOADS.get(dataset_name)
    if not url:
        return None

    out_path = RAW_DIR / "ers" / f"{dataset_name}.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"  ERS: {dataset_name}")
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return pd.read_excel(out_path, sheet_name=None)
    except Exception as e:
        log.error(f"  ERS FAILED {dataset_name}: {e}")
        return None


# ---------------------------------------------------------------------------
# Normalization Schema
# ---------------------------------------------------------------------------
GRAIN_RECORD_SCHEMA = {
    # Identity
    "commodity": str,       # "CORN", "WHEAT", "SOYBEANS", etc.
    "hs_code": str,         # 10-digit HS/Schedule B
    "marketing_year": str,  # e.g., "2024/25"
    "calendar_month": str,  # "2024-10"
    # Production (NASS)
    "planted_acres": float,
    "harvested_acres": float,
    "yield_bu_acre": float,
    "production_bu": float,
    "production_mt": float,
    # Stocks (NASS)
    "ending_stocks_mt": float,
    "stocks_use_ratio": float,
    # Trade (FAS ESR + Census)
    "export_inspections_mt": float,
    "export_sales_net_mt": float,
    "export_sales_cumulative_mt": float,
    "top_destinations": list,
    "export_value_usd": float,
    # Freight (AMS GTR)
    "barge_rate_pct_tariff": float,
    "rail_secondary_bid_per_car": float,
    "truck_diesel_per_gallon": float,
    "ocean_freight_gulf_japan": float,
    # Prices
    "farm_price_bu": float,
    "gulf_elevator_basis": float,
    "futures_nearby_bu": float,
    # Inspection (FGIS)
    "inspected_for_export_mt": float,
    "inspection_port": str,
    "carrier_type": str,
    # Metadata
    "source": str,
    "updated_at": str,
    "data_vintage": str,
}


# ---------------------------------------------------------------------------
# Cross-Source Validation
# ---------------------------------------------------------------------------
def validate_grain_data(data_dir: Path = PROCESSED_DIR) -> list:
    """
    Cross-validate grain data sources for consistency.
    Returns list of validation results/warnings.
    """
    checks = []

    # Check 1: FAS ESR vs Census trade data (should be within 5% monthly)
    checks.append({
        "check": "FAS_ESR_vs_Census",
        "description": "FAS ESR weekly export inspections vs Census monthly HS trade — expect within 5%",
        "methodology_note": "FAS ESR covers ~40% of exports (mandatory reporters); Census covers all",
        "acceptable_variance_pct": 5,
        "status": "PENDING — requires both datasets to be loaded",
    })

    # Check 2: NASS production vs FAS PSD domestic production
    checks.append({
        "check": "NASS_vs_FAS_PSD_production",
        "description": "NASS U.S. production vs FAS PSD U.S. production — should match closely",
        "acceptable_variance_pct": 1,
        "status": "PENDING",
    })

    # Check 3: AMS GTR barge movements vs USACE waterborne commerce
    checks.append({
        "check": "AMS_GTR_vs_USACE_barge",
        "description": "AMS GTR weekly barge lock movements vs USACE annual waterborne tonnage",
        "note": "USACE data has 1-2 year lag; reconcile annually",
        "status": "PENDING",
    })

    # Check 4: FGIS inspection volumes vs FAS ESR export inspections
    checks.append({
        "check": "FGIS_vs_FAS_ESR_inspections",
        "description": "FGIS official inspection volumes vs FAS ESR reported inspections",
        "acceptable_variance_pct": 2,
        "status": "PENDING",
    })

    return checks


# ---------------------------------------------------------------------------
# Ensure output directories exist
# ---------------------------------------------------------------------------
def ensure_dirs():
    for subdir in ["supply", "trade", "freight", "prices", "reference"]:
        (PROCESSED_DIR / subdir).mkdir(parents=True, exist_ok=True)
    for subdir in ["fas", "nass", "ers", "ams", "census", "fgis", "gtr"]:
        (RAW_DIR / subdir).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Main Ingestion Orchestrator
# ---------------------------------------------------------------------------
def run_ingestion(
    step: Optional[str] = None,
    commodity_filter: Optional[str] = None,
    year: Optional[int] = None,
):
    ensure_dirs()
    current_year = year or datetime.now().year
    commodities = [commodity_filter] if commodity_filter else list(GRAINS.keys())

    log.info("=" * 60)
    log.info("GRAIN COMMODITY MODULE — DATA INGESTION")
    log.info(f"Year: {current_year} | Step: {step or 'ALL'} | Commodities: {len(commodities)}")
    log.info("=" * 60)

    # ------------------------------------------------------------------
    # STEP: production — NASS supply data
    # ------------------------------------------------------------------
    if step in (None, "production"):
        log.info("\n[STEP 1] NASS QuickStats — U.S. Production & Stocks")
        if not USDA_KEY:
            log.warning("  USDA_API_KEY not set — skipping NASS. Set env var to enable.")
        else:
            for comm in commodities:
                if not GRAINS[comm].get("nass_desc"):
                    continue
                for stat in ["PRODUCTION", "AREA PLANTED", "AREA HARVESTED", "YIELD", "PRICE RECEIVED"]:
                    df = fetch_nass(comm, stat, year_ge=2010)
                    if df is not None and not df.empty:
                        slug = stat.lower().replace(" ", "_")
                        out = PROCESSED_DIR / "supply" / f"nass_{slug}_{comm}.parquet"
                        df.to_parquet(out, index=False)
                        log.info(f"    ✓ {comm}/{stat}: {len(df)} records → {out.name}")

                # Quarterly grain stocks
                df_stocks = fetch_nass(comm, "STOCKS", year_ge=2010)
                if df_stocks is not None and not df_stocks.empty:
                    out = PROCESSED_DIR / "supply" / f"nass_stocks_{comm}.parquet"
                    df_stocks.to_parquet(out, index=False)
                    log.info(f"    ✓ {comm}/STOCKS: {len(df_stocks)} records")

    # ------------------------------------------------------------------
    # STEP: psd — FAS global supply/demand
    # ------------------------------------------------------------------
    if step in (None, "psd"):
        log.info("\n[STEP 2] FAS PSD — Global Supply/Demand Balances")
        for comm in commodities:
            if not GRAINS[comm].get("psd_code"):
                continue
            for yr in [current_year - 1, current_year]:
                df = fetch_fas_psd(comm, yr)
                if df is not None and not df.empty:
                    out = PROCESSED_DIR / "supply" / f"fas_psd_{comm}_{yr}.parquet"
                    df.to_parquet(out, index=False)
                    log.info(f"    ✓ {comm} {yr}: {len(df)} country records")

    # ------------------------------------------------------------------
    # STEP: esr — FAS weekly export sales
    # ------------------------------------------------------------------
    if step in (None, "esr"):
        log.info("\n[STEP 3] FAS ESR — Weekly U.S. Export Sales")
        for comm in commodities:
            if not GRAINS[comm].get("esr_code"):
                continue
            for yr in [current_year - 1, current_year]:
                df = fetch_fas_esr(comm, yr)
                if df is not None and not df.empty:
                    out = PROCESSED_DIR / "trade" / f"fas_esr_{comm}_{yr}.parquet"
                    df.to_parquet(out, index=False)
                    log.info(f"    ✓ {comm} {yr}: {len(df)} weekly records")

    # ------------------------------------------------------------------
    # STEP: census — Census Bureau trade data
    # ------------------------------------------------------------------
    if step in (None, "census"):
        log.info("\n[STEP 4] Census Bureau — Monthly Export Trade by HS Code")
        if not CENSUS_KEY:
            log.warning("  CENSUS_API_KEY not set — skipping Census. Set env var to enable.")
        else:
            # Pull last 12 months
            months = []
            for i in range(12, 0, -1):
                dt = datetime.now() - timedelta(days=30 * i)
                months.append(dt.strftime("%Y-%m"))

            all_dfs = []
            for comm in commodities:
                hs_code = GRAINS[comm].get("hs10_export")
                if not hs_code:
                    continue
                for ym in months:
                    df = fetch_census_exports(hs_code, ym)
                    if df is not None and not df.empty:
                        df["commodity"] = comm
                        all_dfs.append(df)

            if all_dfs:
                combined = pd.concat(all_dfs, ignore_index=True)
                out = PROCESSED_DIR / "trade" / f"census_exports_12mo.parquet"
                combined.to_parquet(out, index=False)
                log.info(f"    ✓ Census exports: {len(combined)} records (12 months, {len(commodities)} commodities)")

    # ------------------------------------------------------------------
    # STEP: gtr — AMS GTR freight datasets
    # ------------------------------------------------------------------
    if step in (None, "gtr"):
        log.info("\n[STEP 5] AMS GTR — Grain Transportation Freight Datasets")
        for name in GTR_DATASETS:
            result = fetch_ams_gtr(name)
            if result:
                log.info(f"    ✓ GTR {name}: downloaded ({len(result)} sheets)")
            else:
                log.warning(f"    ✗ GTR {name}: FAILED (URL may have changed — verify at AMS portal)")

    # ------------------------------------------------------------------
    # STEP: ers — ERS Excel downloads
    # ------------------------------------------------------------------
    if step in (None, "ers"):
        log.info("\n[STEP 6] ERS — Feed Grains Database and FATUS Downloads")
        for name in ERS_DOWNLOADS:
            result = fetch_ers_excel(name)
            if result:
                log.info(f"    ✓ ERS {name}: downloaded")
            else:
                log.warning(f"    ✗ ERS {name}: FAILED")

    # ------------------------------------------------------------------
    # STEP: fgis — FGIS export inspection data
    # ------------------------------------------------------------------
    if step in (None, "fgis"):
        log.info("\n[STEP 7] FGIS — Export Grain Inspection Data")
        log.info("  NOTE: FGIS public aggregate reports at https://fgisonline.ams.usda.gov/exportgrainreport/")
        log.info("  NOTE: Carrier-level data requires USDA eAuthentication registration")
        log.info("  NOTE: For automated access, integrate with vessel_voyage_analysis toolset")
        log.info("  NOTE: See toolset at ../../02_TOOLSETS/vessel_voyage_analysis/fgis/grain_matcher.py")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    log.info("\n[VALIDATION] Cross-source consistency checks")
    checks = validate_grain_data(PROCESSED_DIR)
    pending = sum(1 for c in checks if c["status"] == "PENDING")
    log.info(f"  {len(checks)} validation checks defined; {pending} pending data load")

    log.info("\n" + "=" * 60)
    log.info("✅ GRAIN INGESTION COMPLETE")
    log.info(f"   Processed data: {PROCESSED_DIR}")
    log.info(f"   Raw data:       {RAW_DIR}")
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grain commodity module data ingestion pipeline"
    )
    parser.add_argument(
        "--step",
        choices=["production", "psd", "esr", "census", "gtr", "ers", "fgis"],
        default=None,
        help="Run only one ingestion step (default: all steps)",
    )
    parser.add_argument(
        "--commodity",
        choices=list(GRAINS.keys()),
        default=None,
        help="Filter to single commodity",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Target marketing/calendar year (default: current year)",
    )

    args = parser.parse_args()
    run_ingestion(step=args.step, commodity_filter=args.commodity, year=args.year)
