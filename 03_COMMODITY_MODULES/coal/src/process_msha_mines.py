#!/usr/bin/env python3
"""
process_msha_mines.py
Coal Module — MSHA Mine Data Processor

Loads MSHA Mines.csv (downloaded by download_coal_data.py) into the
site_master_registry DuckDB database as coal mining facilities.

Usage:
    python src/process_msha_mines.py --dry-run     # Preview, don't write
    python src/process_msha_mines.py --load         # Load to site_master_registry
    python src/process_msha_mines.py --export-csv   # Export cleaned coal mines CSV

Output:
    data/processed/coal_mines_master.csv
    (optionally) loaded into site_master_registry/data/site_master.duckdb
"""

import sys
from pathlib import Path

try:
    import pandas as pd
    import duckdb
    import click
except ImportError:
    print("Install: pip install pandas duckdb click")
    sys.exit(1)

# ─── Paths ───────────────────────────────────────────────────────────────────
MODULE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = MODULE_DIR.parent.parent  # project_master_reporting/
MSHA_ZIP_DIR = MODULE_DIR / "data" / "raw" / "msha"
MINES_CSV = MSHA_ZIP_DIR / "Mines.csv"
OUTPUT_CSV = MODULE_DIR / "data" / "processed" / "coal_mines_master.csv"
SITE_REGISTRY_DB = PROJECT_ROOT / "02_TOOLSETS" / "site_master_registry" / "data" / "site_master.duckdb"

# ─── MSHA → Platform field mapping ───────────────────────────────────────────
FIELD_MAP = {
    # MSHA field (actual .txt schema)  → platform field
    "MINE_ID":                  "source_id",
    "CURRENT_MINE_NAME":        "site_name",
    "STATE":                    "state",        # actual col name in Mines.txt
    "FIPS_CNTY_CD":             "fips_county",
    "FIPS_CNTY_NM":             "county_name",
    "LATITUDE":                 "latitude",
    "LONGITUDE":                "longitude",
    "CURRENT_MINE_TYPE":        "mine_type",    # actual col name
    "CURRENT_MINE_STATUS":      "operational_status",  # actual col name
    "CURRENT_OPERATOR_NAME":    "operator_name",
    "CURRENT_CONTROLLER_NAME":  "parent_company",
    "DISTRICT":                 "msha_district",
    "COAL_METAL_IND":           "_coal_metal_ind",  # internal filter column
    "NO_EMPLOYEES":             "employee_count",
    "PRIMARY_SIC_CD":           "sic_code",
}

# Mine type → NAICS mapping
MINE_TYPE_NAICS = {
    "Surface": "212111",
    "Strip": "212111",
    "Auger": "212111",
    "Culm Bank": "212111",
    "Refuse Pile": "212111",
    "Underground": "212112",
    "Underground and Surface": "212112",
}


def load_msha_mines(mines_csv: Path) -> pd.DataFrame:
    """Load and filter MSHA mines to coal only."""
    if not mines_csv.exists():
        raise FileNotFoundError(
            f"Mines.csv not found at {mines_csv}\n"
            "Run: python src/download_coal_data.py --priority 1"
        )

    # Mines.txt is pipe-delimited (not CSV)
    df = pd.read_csv(mines_csv, sep="|", encoding="latin-1", low_memory=False)
    print(f"MSHA mines loaded: {len(df):,} total records")

    # Filter: coal only
    coal = df[df["COAL_METAL_IND"] == "C"].copy()
    print(f"Coal mines after filter: {len(coal):,}")

    print(f"All statuses: {coal['CURRENT_MINE_STATUS'].value_counts().to_dict()}")

    return coal


def clean_mines(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize and enrich the coal mine dataset."""
    # Rename to platform schema
    rename_cols = {k: v for k, v in FIELD_MAP.items() if k in df.columns and not v.startswith("_")}
    df = df.rename(columns=rename_cols)

    # Add commodity_sector
    df["commodity_sector"] = "coal_mining"

    # Add NAICS code based on mine type
    df["naics_code"] = df["mine_type"].map(MINE_TYPE_NAICS).fillna("212112")

    # Add source identifier
    df["source"] = "msha_mines"
    df["source_dataset"] = "MSHA Open Data - Mines.zip"

    # Normalize coordinates
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Flag records with valid coordinates
    df["has_coordinates"] = df["latitude"].notna() & df["longitude"].notna()
    coord_pct = df["has_coordinates"].mean() * 100
    print(f"Records with coordinates: {coord_pct:.1f}%")

    # Basin assignment based on state
    basin_map = {
        "WV": "Central/Northern Appalachian",
        "VA": "Central Appalachian",
        "KY": "Central/Northern Appalachian",
        "PA": "Northern Appalachian",
        "OH": "Northern Appalachian",
        "IL": "Illinois Basin",
        "IN": "Illinois Basin",
        "WY": "Powder River Basin",
        "MT": "Powder River Basin",
        "AL": "Warrior Basin",
        "UT": "Uinta-Piceance Basin",
        "CO": "Uinta-Piceance Basin",
        "TX": "Gulf Coast Lignite",
        "ND": "Lignite (Williston Basin)",
        "MS": "Gulf Coast Lignite",
        "TN": "Central Appalachian",
        "MO": "Interior",
    }
    df["coal_basin"] = df["state"].map(basin_map).fillna("Other/Unknown")

    # Select output columns
    out_cols = [
        "source_id", "site_name", "operator_name", "parent_company",
        "state", "fips_county", "latitude", "longitude",
        "mine_type", "operational_status", "naics_code",
        "commodity_sector", "coal_basin", "msha_district",
        "commodity_detail", "source", "source_dataset", "has_coordinates",
    ]
    # Only include columns that exist
    out_cols = [c for c in out_cols if c in df.columns]
    return df[out_cols]


def export_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Save cleaned coal mine DataFrame to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path} ({len(df):,} rows)")


def load_to_registry(df: pd.DataFrame, db_path: Path, dry_run: bool = False) -> None:
    """Load coal mines into site_master_registry DuckDB."""
    if not db_path.exists():
        print(f"WARNING: site_master_registry DB not found at {db_path}")
        print("Export CSV only with --export-csv")
        return

    active = df[df["operational_status"] == "Active"]
    print(f"Active coal mines to load: {len(active):,}")

    if dry_run:
        print(f"[DRY RUN] Would insert {len(active):,} coal mine records into site_master_registry")
        print(f"Sample records:")
        print(active[["source_id", "site_name", "state", "coal_basin", "mine_type"]].head(10).to_string())
        return

    con = duckdb.connect(str(db_path))
    # Check for existing coal mines from MSHA source
    try:
        existing = con.execute(
            "SELECT COUNT(*) FROM sites WHERE source = 'msha_mines'"
        ).fetchone()[0]
        if existing > 0:
            print(f"Found {existing:,} existing MSHA coal mine records in registry.")
            resp = input("Replace existing records? [y/N]: ")
            if resp.lower() != "y":
                print("Skipped. Use --export-csv to save CSV only.")
                con.close()
                return
            con.execute("DELETE FROM sites WHERE source = 'msha_mines'")
            print("Cleared existing MSHA coal mine records.")

        con.register("coal_df", active)
        con.execute("INSERT INTO sites SELECT * FROM coal_df")
        count = con.execute(
            "SELECT COUNT(*) FROM sites WHERE source = 'msha_mines'"
        ).fetchone()[0]
        print(f"Loaded {count:,} coal mine records to site_master_registry")
    except Exception as e:
        print(f"Error loading to registry: {e}")
        print("Check that site_master_registry schema matches output columns.")
    finally:
        con.close()


@click.command()
@click.option("--dry-run", is_flag=True, help="Preview without writing")
@click.option("--load", "do_load", is_flag=True, help="Load to site_master_registry DuckDB")
@click.option("--export-csv", "do_export", is_flag=True, default=True,
              help="Export cleaned CSV (default: True)")
@click.option("--status-filter", default=None,
              help="Filter by mine status (Active, Inactive, Abandoned, etc.)")
def main(dry_run: bool, do_load: bool, do_export: bool, status_filter: str):
    """Process MSHA coal mine data for the coal module."""
    print("\nMSHA Coal Mine Processor")
    print(f"Source: {MINES_CSV}")

    df_raw = load_msha_mines(MINES_CSV)
    df = clean_mines(df_raw)

    if status_filter:
        df = df[df.get("operational_status", pd.Series()) == status_filter]
        print(f"Filtered to {status_filter}: {len(df):,} mines")

    # Summary stats
    print(f"\n{'='*50}")
    print(f"Coal mines total:   {len(df):,}")
    print(f"Active mines:       {(df['operational_status'] == 'Active').sum():,}")
    print(f"With coordinates:   {df['has_coordinates'].sum():,}")
    print(f"\nTop states:")
    print(df["state"].value_counts().head(10).to_string())
    print(f"\nBy basin:")
    print(df["coal_basin"].value_counts().to_string())
    print(f"\nBy mine type:")
    print(df["mine_type"].value_counts().to_string())
    print(f"{'='*50}\n")

    if do_export or not do_load:
        export_csv(df, OUTPUT_CSV)

    if do_load:
        load_to_registry(df, SITE_REGISTRY_DB, dry_run=dry_run)


if __name__ == "__main__":
    main()
