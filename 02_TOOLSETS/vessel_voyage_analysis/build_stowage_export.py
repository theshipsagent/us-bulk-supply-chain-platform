"""
Grain Stowage Factor Export Builder

Builds stowage factor reference tables and vessel-level roll-ups from
the FGIS DuckDB database (project_mrtis/fgis).

Stowage Factor:
    SF (ft³/LT) = 2788.08 / TW
    SF_untrimmed = SF × 1.06  (F-UT cargo centroid correction)

    Where: 2788.08 = 2240 lbs/LT × 1.2445 ft³/bushel
    Ref: GRAIN STOWAGE FACTOR & STABILITY CALCULATION RULES

Outputs:
    grain_stowage_factors.csv       — SF benchmarks by grain/class/grade (reference)
    vessel_stowage_factors.csv      — vessel-level roll-up (port/vessel/date/commodity/country)
    port_commodity_annual.csv       — annual tonnage & SF by port and commodity (trends)
    commodity_summary.csv           — high-level commodity overview

Usage:
    python build_stowage_export.py
    python build_stowage_export.py --db-path /custom/path/fgis_export_grain.duckdb
"""

import sys
import logging
import argparse
from pathlib import Path

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default FGIS database location (sibling project)
SCRIPT_DIR = Path(__file__).parent
DEFAULT_DB = SCRIPT_DIR.parent / "project_mrtis" / "fgis" / "fgis_export_grain.duckdb"
OUTPUT_DIR = SCRIPT_DIR

# ── Constants ────────────────────────────────────────────────────────────────
SF_CONSTANT = 2788.08          # 2240 lbs/LT × 1.2445 ft³/bushel
UNTRIMMED_CORRECTION = 1.06    # F-UT cargo centroid correction factor

# Default TW by grain (dataset median, fallback when TW missing or invalid)
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

DEFAULT_TW_SQL = "CASE\n" + "".join(
    f"        WHEN Grain = '{grain}' THEN {tw}\n"
    for grain, tw in DEFAULT_TW.items()
) + "        ELSE 56.00\n    END"

# ── Class code → human-readable name ────────────────────────────────────────
CLASS_NAMES = {
    'BAR': 'Barley',
    'K': 'Canola',
    'YC': 'Yellow Corn',
    'WHC': 'White Corn',
    'XC': 'Mixed Corn',
    'FLAX': 'Flaxseed',
    'DUWH': 'Durum Wheat',
    'HDWH': 'Hard White Wheat',
    'HRS': 'Hard Red Spring',
    'HRW': 'Hard Red Winter',
    'SRW': 'Soft Red Winter',
    'SWW': 'Soft White Wheat',
    'WW': 'Western White Wheat',
    'XWHT': 'Unclassed/Mixed Wheat',
    'S': 'Sorghum',
    'WHS': 'White Sorghum',
    'YS': 'Yellow Sorghum',
    'YSB': 'Yellow Soybeans',
}

GRADE_NAMES = {
    '1': 'US No. 1',
    '2': 'US No. 2',
    '3': 'US No. 3',
    '4': 'US No. 4',
    '5': 'US No. 5',
    '2 O/B': 'US No. 2 or Better',
    '3 O/B': 'US No. 3 or Better',
    '4 O/B': 'US No. 4 or Better',
    '5 O/B': 'US No. 5 or Better',
    'SG': 'Sample Grade',
    'SG O/B': 'Sample Grade or Better',
    'SGO/B': 'Sample Grade or Better',
    'NG': 'No Grade',
    'XGR': 'Mixed Grain',
}

# ── Region roll-up (Field Office → Region, Port for disambiguation) ─────────
REGION_SQL = """
    CASE
        WHEN "Field Office" IN ('NEW ORLEANS', 'LUTCHER', 'DESTREHAN', 'BELLE CHASSE')
            THEN 'Mississippi River'
        WHEN "Field Office" IN ('LEAGUE CITY', 'PASADENA', 'GALVESTON')
            THEN 'Houston'
        WHEN "Field Office" IN ('OLYMPIA', 'PORTLAND', 'PACIFICNW', 'FMMS')
             AND Port = 'COLUMBIA R.'
            THEN 'Columbia River'
        WHEN "Field Office" IN ('OLYMPIA', 'PORTLAND', 'PACIFICNW', 'SEATTLE')
             AND Port = 'PUGET SOUND'
            THEN 'Puget Sound (Seattle-Tacoma)'
        WHEN "Field Office" = 'CORPUS CHRIS'
            THEN 'Corpus Christi'
        WHEN "Field Office" = 'MOBILE'
            THEN 'Mobile'
        WHEN "Field Office" = 'LAKE CHARLES'
            THEN 'Lake Charles'
        WHEN "Field Office" = 'BEAUMONT'
            THEN 'Beaumont'
        WHEN "Field Office" IN ('TOLEDO', 'DULUTH', 'MINNEAPOLIS', 'CHICAGO', 'SAGINAW', 'PEORIA')
            THEN 'Great Lakes'
        WHEN "Field Office" = 'BALTIMORE'
            THEN 'South Atlantic'
        ELSE NULL
    END
"""

# ── Base CTE: filtered source with effective TW & SF ────────────────────────
BASE_CTE = f"""
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
            CASE
                WHEN tw_numeric > 0 AND tw_numeric < 100 THEN tw_numeric
                ELSE default_tw
            END AS effective_tw,
            CASE
                WHEN tw_numeric > 0 AND tw_numeric < 100 THEN 'actual'
                ELSE 'default'
            END AS tw_source
        FROM base
    ),
    enriched AS (
        SELECT
            TRY_STRPTIME("Cert Date", '%Y%m%d')::DATE AS cert_date,
            {REGION_SQL} AS region,
            "Carrier Name" AS vessel_name,
            Grain AS grain,
            Class AS class,
            Grade AS grade,
            Destination AS destination,
            TRY_CAST(Pounds AS BIGINT) AS pounds,
            TRY_CAST("1000 Bushels" AS DOUBLE) AS thousand_bushels,
            TRY_CAST("Metric Ton" AS DOUBLE) AS metric_tons,
            effective_tw AS test_weight,
            tw_source,
            ROUND({SF_CONSTANT} / effective_tw, 2) AS stow_factor,
            ROUND({SF_CONSTANT} / effective_tw * {UNTRIMMED_CORRECTION}, 2) AS stow_factor_untrimmed,
            source_year
        FROM with_tw
    )
"""


def write_csv(df, name, output_dir):
    """Write a DataFrame to CSV and log stats."""
    path = output_dir / name
    df.to_csv(str(path), index=False)
    size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(f"  {name:<40s} {len(df):>10,} rows  {size_mb:>6.1f} MB")
    return path


def build_grain_reference(con, output_dir):
    """Export 1: SF benchmarks by grain/class/grade."""
    df = con.execute(f"""
        {BASE_CTE}
        SELECT
            grain,
            class,
            grade,
            COUNT(*) AS records,
            ROUND(AVG(test_weight), 2) AS avg_tw,
            ROUND(MIN(test_weight), 2) AS min_tw,
            ROUND(MAX(test_weight), 2) AS max_tw,
            ROUND(MEDIAN(test_weight), 2) AS median_tw,
            ROUND(AVG(stow_factor), 2) AS avg_sf,
            ROUND(MEDIAN(stow_factor), 2) AS median_sf,
            ROUND(AVG(stow_factor_untrimmed), 2) AS avg_sf_untrimmed,
            ROUND(MEDIAN(stow_factor_untrimmed), 2) AS median_sf_untrimmed
        FROM enriched
        WHERE metric_tons > 0
        GROUP BY grain, class, grade
        ORDER BY grain, class, records DESC
    """).fetchdf()

    # Add human-readable names
    df.insert(2, 'class_name', df['class'].apply(
        lambda c: CLASS_NAMES.get(str(c).strip(), str(c).strip() if c else '')
    ))
    df.insert(4, 'grade_name', df['grade'].apply(
        lambda g: GRADE_NAMES.get(str(g).strip(), str(g).strip() if g else 'Ungraded')
    ))

    # Fix empty class_name: fall back to commodity name
    mask = df['class_name'] == ''
    df.loc[mask, 'class_name'] = df.loc[mask, 'grain']

    # Rename for clean output
    df.columns = [
        'commodity', 'class_code', 'class_name', 'grade_code', 'grade_name',
        'records', 'avg_test_weight', 'min_test_weight', 'max_test_weight',
        'median_test_weight', 'avg_sf_ft3_per_lt', 'median_sf_ft3_per_lt',
        'avg_sf_untrimmed_ft3_per_lt', 'median_sf_untrimmed_ft3_per_lt'
    ]

    return write_csv(df, 'grain_stowage_factors.csv', output_dir)


def build_vessel_rollup(con, output_dir):
    """Export 2: vessel-level roll-up with weighted-average SF."""
    df = con.execute(f"""
        {BASE_CTE}
        SELECT
            cert_date,
            region AS port,
            vessel_name AS vessel,
            grain AS commodity,
            class AS commodity_class,
            destination AS country,

            COUNT(*) AS certificates,
            SUM(metric_tons) AS metric_tons,
            SUM(pounds) AS pounds,
            SUM(thousand_bushels) AS thousand_bushels,

            ROUND(
                SUM(stow_factor * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS stow_factor_ft3_per_lt,

            ROUND(
                SUM(stow_factor_untrimmed * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS stow_factor_untrimmed_ft3_per_lt,

            ROUND(
                SUM(test_weight * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS avg_test_weight,

            MIN(stow_factor) AS min_sf,
            MAX(stow_factor) AS max_sf

        FROM enriched
        WHERE metric_tons > 0
        GROUP BY cert_date, region, vessel_name, grain, class, destination
        ORDER BY cert_date, region, vessel_name, grain
    """).fetchdf()

    return write_csv(df, 'vessel_stowage_factors.csv', output_dir)


def build_port_commodity_annual(con, output_dir):
    """Export 3: annual tonnage & SF by port and commodity (trend analysis)."""
    df = con.execute(f"""
        {BASE_CTE}
        SELECT
            EXTRACT(YEAR FROM cert_date) AS year,
            region AS port,
            grain AS commodity,

            COUNT(DISTINCT vessel_name) AS vessels,
            COUNT(*) AS certificates,
            ROUND(SUM(metric_tons), 0) AS metric_tons,
            ROUND(SUM(pounds) / 2240.0, 0) AS long_tons,

            ROUND(
                SUM(stow_factor * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS wtd_avg_sf,

            ROUND(
                SUM(stow_factor_untrimmed * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS wtd_avg_sf_untrimmed,

            ROUND(
                SUM(test_weight * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS wtd_avg_test_weight,

            ROUND(MIN(stow_factor), 2) AS min_sf,
            ROUND(MAX(stow_factor), 2) AS max_sf,
            ROUND(STDDEV(stow_factor), 3) AS sf_stddev

        FROM enriched
        WHERE metric_tons > 0
        GROUP BY year, region, grain
        ORDER BY year, region, grain
    """).fetchdf()

    return write_csv(df, 'port_commodity_annual.csv', output_dir)


def build_commodity_summary(con, output_dir):
    """Export 4: high-level commodity overview."""
    df = con.execute(f"""
        {BASE_CTE}
        SELECT
            grain AS commodity,
            class AS commodity_class,

            MIN(cert_date) AS first_date,
            MAX(cert_date) AS last_date,
            COUNT(DISTINCT EXTRACT(YEAR FROM cert_date)) AS years_active,

            COUNT(DISTINCT vessel_name) AS distinct_vessels,
            COUNT(DISTINCT region) AS ports,
            COUNT(DISTINCT destination) AS countries,
            COUNT(*) AS certificates,

            ROUND(SUM(metric_tons), 0) AS total_metric_tons,
            ROUND(SUM(metric_tons) / COUNT(DISTINCT EXTRACT(YEAR FROM cert_date)), 0)
                AS avg_annual_metric_tons,

            ROUND(
                SUM(stow_factor * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS wtd_avg_sf,

            ROUND(
                SUM(stow_factor_untrimmed * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS wtd_avg_sf_untrimmed,

            ROUND(
                SUM(test_weight * metric_tons) / NULLIF(SUM(metric_tons), 0), 2
            ) AS wtd_avg_test_weight,

            ROUND(MIN(stow_factor), 2) AS min_sf,
            ROUND(MAX(stow_factor), 2) AS max_sf

        FROM enriched
        WHERE metric_tons > 0
        GROUP BY grain, class
        ORDER BY total_metric_tons DESC
    """).fetchdf()

    # Add human-readable class name
    df.insert(2, 'class_name', df['commodity_class'].apply(
        lambda c: CLASS_NAMES.get(str(c).strip(), str(c).strip() if c else '')
    ))
    mask = df['class_name'] == ''
    df.loc[mask, 'class_name'] = df.loc[mask, 'commodity']

    return write_csv(df, 'commodity_summary.csv', output_dir)


def build_all(db_path: Path = DEFAULT_DB, output_dir: Path = OUTPUT_DIR):
    """Build all stowage factor exports."""
    logger.info("=" * 60)
    logger.info("Grain Stowage Factor Export Builder")
    logger.info("=" * 60)
    logger.info(f"Source DB: {db_path}")
    logger.info(f"Output:    {output_dir}")

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.info("Run project_mrtis/fgis/build_database.py --build first")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path), read_only=True)

    logger.info("")
    logger.info("Building exports:")
    build_grain_reference(con, output_dir)
    build_vessel_rollup(con, output_dir)
    build_port_commodity_annual(con, output_dir)
    build_commodity_summary(con, output_dir)

    con.close()

    logger.info("")
    logger.info("Done.")


def main():
    parser = argparse.ArgumentParser(description="Grain Stowage Factor Export Builder")
    parser.add_argument('--db-path', type=str, default=None,
                       help='Path to FGIS DuckDB database')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory')
    args = parser.parse_args()

    db = Path(args.db_path) if args.db_path else DEFAULT_DB
    out = Path(args.output_dir) if args.output_dir else OUTPUT_DIR

    build_all(db, out)


if __name__ == "__main__":
    main()
