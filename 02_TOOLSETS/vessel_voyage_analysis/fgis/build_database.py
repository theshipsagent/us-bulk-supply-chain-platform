"""
FGIS Export Grain Database Builder (DuckDB)

Downloads and consolidates FGIS (Federal Grain Inspection Service) export grain
inspection data from https://fgisonline.ams.usda.gov/ExportGrainReport/

Uses DuckDB for fast analytical queries and Google Drive compatibility.

Usage:
    # Build full database from already-downloaded raw CSVs
    python fgis/build_database.py --build

    # Download current year CSV and rebuild (weekly refresh)
    python fgis/build_database.py --refresh

    # Download ALL years and build from scratch
    python fgis/build_database.py --download-all --build

    # Show database stats
    python fgis/build_database.py --stats
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime, date
from typing import Optional

import duckdb

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FGIS_BASE_URL = "https://fgisonline.ams.usda.gov/ExportGrainReport"
FIRST_YEAR = 1983
RAW_DATA_DIR = Path(__file__).parent / "raw_data"
DB_PATH = Path(__file__).parent / "fgis_export_grain.duckdb"


class FGISDatabase:
    """Manages the FGIS export grain DuckDB database."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.raw_data_dir = RAW_DATA_DIR

    def _connect(self):
        """Open a DuckDB connection."""
        return duckdb.connect(str(self.db_path))

    # ------------------------------------------------------------------
    # Downloading
    # ------------------------------------------------------------------

    def download_file(self, year: int) -> Path:
        """Download a single year's CSV from FGIS."""
        import urllib.request
        url = f"{FGIS_BASE_URL}/CY{year}.csv"
        dest = self.raw_data_dir / f"CY{year}.csv"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {url} ...")
        urllib.request.urlretrieve(url, str(dest))
        logger.info(f"  Saved to {dest} ({dest.stat().st_size / 1024:.0f} KB)")
        return dest

    def download_all(self):
        """Download all years from FGIS (1983 to current year)."""
        current_year = date.today().year
        for year in range(FIRST_YEAR, current_year + 1):
            self.download_file(year)
        logger.info(f"Downloaded {current_year - FIRST_YEAR + 1} files")

    def refresh_current_year(self):
        """Re-download current year CSV and replace its rows in the DB."""
        current_year = date.today().year
        self.download_file(current_year)
        self._rebuild_year(current_year)
        logger.info(f"Refreshed CY{current_year} in database")

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def build(self):
        """Build the full DuckDB database from all raw CSV files."""
        logger.info("=" * 60)
        logger.info("FGIS Database Builder  (DuckDB)")
        logger.info("=" * 60)

        csv_files = sorted(self.raw_data_dir.glob("CY*.csv"))
        if not csv_files:
            logger.error(f"No CSV files found in {self.raw_data_dir}")
            logger.info("Run with --download-all first")
            return

        logger.info(f"Found {len(csv_files)} CSV files in {self.raw_data_dir}")

        # Remove old DB file so we start fresh
        if self.db_path.exists():
            self.db_path.unlink()

        con = self._connect()

        # DuckDB can read CSVs directly — load all files in one pass
        # Using read_csv with union by name handles any minor column drift
        raw_dir_posix = self.raw_data_dir.as_posix()
        glob_pattern = f"{raw_dir_posix}/CY*.csv"

        logger.info("Loading all CSV files into DuckDB ...")
        con.execute(f"""
            CREATE TABLE export_grain AS
            SELECT
                CAST(regexp_extract(filename, 'CY(\\d+)', 1) AS INTEGER) AS source_year,
                *
            FROM read_csv(
                '{glob_pattern}',
                header = true,
                all_varchar = true,
                filename = true,
                ignore_errors = true,
                null_padding = true
            )
        """)

        # Drop the filename column DuckDB added
        con.execute("ALTER TABLE export_grain DROP COLUMN filename")

        total_rows = con.execute("SELECT COUNT(*) FROM export_grain").fetchone()[0]
        logger.info(f"Loaded {total_rows:,} total rows")

        # Create indexes for common query patterns
        logger.info("Creating indexes ...")
        con.execute("CREATE INDEX idx_source_year ON export_grain (source_year)")
        con.execute("CREATE INDEX idx_grain ON export_grain (Grain)")
        con.execute("CREATE INDEX idx_port ON export_grain (Port)")
        con.execute("CREATE INDEX idx_dest ON export_grain (Destination)")
        con.execute('CREATE INDEX idx_cert_date ON export_grain ("Cert Date")')
        con.execute('CREATE INDEX idx_ams_reg ON export_grain ("AMS Reg")')
        con.execute('CREATE INDEX idx_carrier_type ON export_grain ("Type Carrier")')

        # Metadata table
        con.execute("DROP TABLE IF EXISTS metadata")
        con.execute("""
            CREATE TABLE metadata (
                key VARCHAR PRIMARY KEY,
                value VARCHAR
            )
        """)
        con.execute("INSERT INTO metadata VALUES ('build_date', ?)", [datetime.now().isoformat()])
        con.execute("INSERT INTO metadata VALUES ('total_rows', ?)", [str(total_rows)])
        con.execute("INSERT INTO metadata VALUES ('file_count', ?)", [str(len(csv_files))])
        year_min = csv_files[0].stem.replace('CY', '')
        year_max = csv_files[-1].stem.replace('CY', '')
        con.execute("INSERT INTO metadata VALUES ('year_range', ?)", [f"{year_min}-{year_max}"])

        con.close()

        db_size = self.db_path.stat().st_size / (1024 * 1024)
        logger.info(f"\nDatabase built: {self.db_path}")
        logger.info(f"Total rows: {total_rows:,}")
        logger.info(f"Database size: {db_size:.1f} MB")

    def _rebuild_year(self, year: int):
        """Delete and reload a single year in the database."""
        con = self._connect()

        con.execute("DELETE FROM export_grain WHERE source_year = ?", [year])
        logger.info(f"Cleared existing CY{year} rows")

        csv_path = self.raw_data_dir / f"CY{year}.csv"
        if csv_path.exists():
            csv_posix = csv_path.as_posix()
            con.execute(f"""
                INSERT INTO export_grain
                SELECT
                    {year} AS source_year,
                    *
                FROM read_csv(
                    '{csv_posix}',
                    header = true,
                    all_varchar = true,
                    ignore_errors = true,
                    null_padding = true
                )
            """)
            rows = con.execute(
                "SELECT COUNT(*) FROM export_grain WHERE source_year = ?", [year]
            ).fetchone()[0]
            logger.info(f"Loaded {rows:,} rows for CY{year}")

        con.execute(
            "UPDATE metadata SET value = ? WHERE key = 'build_date'",
            [datetime.now().isoformat()]
        )
        con.close()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self):
        """Print database statistics."""
        if not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            return

        con = self._connect()

        print("\n" + "=" * 60)
        print("FGIS Export Grain Database Statistics  (DuckDB)")
        print("=" * 60)

        # Metadata
        for row in con.execute("SELECT key, value FROM metadata").fetchall():
            print(f"  {row[0]}: {row[1]}")
        db_size = self.db_path.stat().st_size / (1024 * 1024)
        print(f"  db_size: {db_size:.1f} MB")

        # Column count
        col_count = len(con.execute("DESCRIBE export_grain").fetchall())
        print(f"  columns: {col_count}")

        # Rows by year
        print("\nRows by year:")
        for year, cnt in con.execute("""
            SELECT source_year, COUNT(*) AS cnt
            FROM export_grain GROUP BY source_year ORDER BY source_year
        """).fetchall():
            print(f"  CY{year}: {cnt:>8,}")

        # Top grains
        print("\nTop grains:")
        for grain, cnt in con.execute("""
            SELECT Grain, COUNT(*) AS cnt
            FROM export_grain GROUP BY Grain ORDER BY cnt DESC LIMIT 10
        """).fetchall():
            print(f"  {str(grain):<20s}: {cnt:>8,}")

        # Top ports
        print("\nTop ports:")
        for port, cnt in con.execute("""
            SELECT Port, COUNT(*) AS cnt
            FROM export_grain GROUP BY Port ORDER BY cnt DESC LIMIT 10
        """).fetchall():
            print(f"  {str(port):<30s}: {cnt:>8,}")

        # AMS regions
        print("\nAMS Regions:")
        for reg, cnt in con.execute("""
            SELECT "AMS Reg", COUNT(*) AS cnt
            FROM export_grain GROUP BY "AMS Reg" ORDER BY cnt DESC
        """).fetchall():
            print(f"  {str(reg):<20s}: {cnt:>8,}")

        con.close()


def main():
    parser = argparse.ArgumentParser(description="FGIS Export Grain Database Builder (DuckDB)")
    parser.add_argument('--download-all', action='store_true',
                       help='Download all yearly CSVs from FGIS (1983-current)')
    parser.add_argument('--build', action='store_true',
                       help='Build DuckDB database from downloaded CSVs')
    parser.add_argument('--refresh', action='store_true',
                       help='Re-download current year CSV and update database')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--db-path', type=str, default=None,
                       help='Custom database path')

    args = parser.parse_args()

    db = FGISDatabase(db_path=Path(args.db_path) if args.db_path else None)

    if args.download_all:
        db.download_all()

    if args.build:
        db.build()

    if args.refresh:
        db.refresh_current_year()

    if args.stats:
        db.stats()

    if not any([args.download_all, args.build, args.refresh, args.stats]):
        parser.print_help()


if __name__ == "__main__":
    main()
