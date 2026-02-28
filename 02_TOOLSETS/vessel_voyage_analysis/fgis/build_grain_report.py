"""
FGIS Grain Report Builder

Builds the processed grain report from the FGIS DuckDB database.
Applies filters (Ship + Bulk only), region roll-ups, column transformations,
and stowage factor calculations.

Stowage Factor:
    SF (ft³/LT) = 2788.08 / TW
    SF_untrimmed = SF × 1.06  (correction for untrimmed ends, F-UT cargo centroid)

    Where: 2788.08 = 2240 lbs/LT × 1.2445 ft³/bushel
    Ref: GRAIN STOWAGE FACTOR & STABILITY CALCULATION RULES

Usage:
    python fgis/build_grain_report.py
    python fgis/build_grain_report.py --output fgis/custom_output.csv
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "fgis_export_grain.duckdb"
DEFAULT_OUTPUT = Path(__file__).parent / "grain_report.csv"

# Stowage factor constants
SF_CONSTANT = 2788.08          # 2240 lbs/LT × 1.2445 ft³/bushel
UNTRIMMED_CORRECTION = 1.06    # F-UT cargo centroid correction factor

# Default TW by grain (median from dataset, used when TW missing or invalid)
DEFAULT_TW = {
    'WHEAT':     61.00,
    'CORN':      57.32,
    'SOYBEANS':  56.00,
    'SORGHUM':   58.26,
    'BARLEY':    49.85,
    'SUNFLOWER': 29.01,
    'FLAXSEED':  50.10,
    'CANOLA':    49.62,
    'RYE':       58.58,
    'OATS':      43.37,
    'MIXED':     60.14,
}

# Build SQL CASE for default TW fallback
DEFAULT_TW_SQL = "CASE\n" + "".join(
    f"        WHEN Grain = '{grain}' THEN {tw}\n"
    for grain, tw in DEFAULT_TW.items()
) + "        ELSE 56.00\n    END"

# Region roll-up: Field Office -> Region, with Port used to split shared offices
REGION_SQL = """
    CASE
        -- Mississippi River (East Gulf LA offices)
        WHEN "Field Office" IN ('NEW ORLEANS', 'LUTCHER', 'DESTREHAN', 'BELLE CHASSE')
            THEN 'Mississippi River'

        -- Houston (N. Texas offices, excl Lake Charles & Beaumont)
        WHEN "Field Office" IN ('LEAGUE CITY', 'PASADENA', 'GALVESTON')
            THEN 'Houston'

        -- Columbia River vs Puget Sound: shared offices split by Port
        WHEN "Field Office" IN ('OLYMPIA', 'PORTLAND', 'PACIFICNW', 'FMMS')
             AND Port = 'COLUMBIA R.'
            THEN 'Columbia River'
        WHEN "Field Office" IN ('OLYMPIA', 'PORTLAND', 'PACIFICNW', 'SEATTLE')
             AND Port = 'PUGET SOUND'
            THEN 'Puget Sound (Seattle-Tacoma)'

        -- Corpus Christi
        WHEN "Field Office" = 'CORPUS CHRIS'
            THEN 'Corpus Christi'

        -- Mobile
        WHEN "Field Office" = 'MOBILE'
            THEN 'Mobile'

        -- Lake Charles
        WHEN "Field Office" = 'LAKE CHARLES'
            THEN 'Lake Charles'

        -- Beaumont
        WHEN "Field Office" = 'BEAUMONT'
            THEN 'Beaumont'

        -- Great Lakes (all lake ports consolidated)
        WHEN "Field Office" IN ('TOLEDO', 'DULUTH', 'MINNEAPOLIS', 'CHICAGO', 'SAGINAW', 'PEORIA')
            THEN 'Great Lakes'

        -- South Atlantic
        WHEN "Field Office" = 'BALTIMORE'
            THEN 'South Atlantic'

        ELSE NULL
    END
"""


def build_report(db_path: Path = DB_PATH, output_path: Path = DEFAULT_OUTPUT):
    """Build the processed grain report CSV."""
    logger.info("=" * 60)
    logger.info("FGIS Grain Report Builder")
    logger.info("=" * 60)

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.info("Run build_database.py --build first")
        return

    con = duckdb.connect(str(db_path), read_only=True)

    query = f"""
        WITH base AS (
            SELECT
                *,
                TRY_CAST(TW AS DOUBLE) AS tw_numeric,
                {DEFAULT_TW_SQL} AS default_tw
            FROM export_grain
            WHERE "Type Carrier" = '1'
              AND "Type Shipm" = 'BU'
              AND Port <> 'INTERIOR'
              AND "Field Office" NOT IN ('PHILADELPHIA', 'SACRAMENTO', 'MONTREAL')
              AND ({REGION_SQL}) IS NOT NULL
        ),
        with_tw AS (
            SELECT
                *,
                -- Use actual TW if valid (> 0 and < 100), otherwise default
                CASE
                    WHEN tw_numeric > 0 AND tw_numeric < 100 THEN tw_numeric
                    ELSE default_tw
                END AS effective_tw,
                CASE
                    WHEN tw_numeric > 0 AND tw_numeric < 100 THEN 'actual'
                    ELSE 'default'
                END AS tw_source
            FROM base
        )
        SELECT
            -- Date: format YYYYMMDD -> proper date for time-series
            TRY_STRPTIME("Cert Date", '%Y%m%d')::DATE AS cert_date,

            -- Region roll-up
            {REGION_SQL} AS region,

            -- Carrier
            "Carrier Name" AS vessel_name,

            -- Grain identity
            Grain AS grain,
            Class AS class,
            SubClass AS subclass,
            Grade AS grade,
            "Spec Gr 1" AS spec_grade_1,
            "Spec Gr 2" AS spec_grade_2,

            -- Destination
            Destination AS destination,

            -- Volume / Weight (cast to numeric)
            TRY_CAST(Pounds AS BIGINT) AS pounds,
            TRY_CAST("1000 Bushels" AS DOUBLE) AS thousand_bushels,
            TRY_CAST("Metric Ton" AS DOUBLE) AS metric_tons,

            -- Test weight & stowage factor
            effective_tw AS test_weight,
            tw_source,
            ROUND({SF_CONSTANT} / effective_tw, 2) AS stow_factor,
            ROUND({SF_CONSTANT} / effective_tw * {UNTRIMMED_CORRECTION}, 2) AS stow_factor_untrimmed,

            -- Quality
            Fumigant AS fumigant,

            -- Carrier detail
            TRY_CAST("Subl/Carrs" AS INTEGER) AS sublots_carriers,

            -- Geography (raw for drill-down)
            "Field Office" AS field_office,
            Port AS port,
            "AMS Reg" AS ams_region,
            "FGIS Reg" AS fgis_region,
            State AS state,

            -- Source tracking
            source_year

        FROM with_tw
        ORDER BY cert_date, region, vessel_name
    """

    logger.info("Running query (Ship + Bulk, 10 regions) ...")
    result = con.execute(query)

    # Get row count
    df = result.fetchdf()
    total_rows = len(df)
    logger.info(f"Query returned {total_rows:,} rows")

    # Region summary
    logger.info("\nRecords by region:")
    region_counts = df['region'].value_counts().sort_values(ascending=False)
    for region, count in region_counts.items():
        logger.info(f"  {region:<35s}: {count:>8,}")

    # Grain summary
    logger.info("\nRecords by grain:")
    grain_counts = df['grain'].value_counts().sort_values(ascending=False)
    for grain, count in grain_counts.items():
        logger.info(f"  {grain:<20s}: {count:>8,}")

    # Year range
    logger.info(f"\nDate range: {df['cert_date'].min()} to {df['cert_date'].max()}")

    # Stowage factor stats
    tw_actual = (df['tw_source'] == 'actual').sum()
    tw_default = (df['tw_source'] == 'default').sum()
    logger.info(f"\nStowage factor coverage:")
    logger.info(f"  Actual TW:  {tw_actual:>8,} ({tw_actual*100/total_rows:.1f}%)")
    logger.info(f"  Default TW: {tw_default:>8,} ({tw_default*100/total_rows:.1f}%)")
    logger.info(f"  SF range:   {df['stow_factor'].min():.2f} - {df['stow_factor'].max():.2f} ft³/LT")
    logger.info(f"  SF untrimmed range: {df['stow_factor_untrimmed'].min():.2f} - {df['stow_factor_untrimmed'].max():.2f} ft³/LT")
    logger.info(f"  Untrimmed correction: {UNTRIMMED_CORRECTION}")

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(str(output_path), index=False)

    file_size = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"\nOutput: {output_path}")
    logger.info(f"Rows: {total_rows:,}")
    logger.info(f"Columns: {len(df.columns)}")
    logger.info(f"File size: {file_size:.1f} MB")

    con.close()
    return df


def main():
    parser = argparse.ArgumentParser(description="FGIS Grain Report Builder")
    parser.add_argument('--output', type=str, default=None,
                       help='Output CSV path')
    parser.add_argument('--db-path', type=str, default=None,
                       help='Custom database path')

    args = parser.parse_args()

    db = Path(args.db_path) if args.db_path else DB_PATH
    out = Path(args.output) if args.output else DEFAULT_OUTPUT

    build_report(db, out)


if __name__ == "__main__":
    main()
