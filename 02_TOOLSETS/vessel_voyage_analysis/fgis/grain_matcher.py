"""
FGIS Grain ↔ MRTIS Vessel Matching

Enriches MRTIS voyage segment data with FGIS grain cargo details by matching
vessel visits to grain elevators on the Mississippi River. The FGIS cert_date
is matched to the vessel's departure from a grain elevator within a ±5 calendar
day window (120 hours ≈ 5 days; cert_date is date-only).

Standalone post-pipeline script — does NOT modify voyage_analyzer.py.

Usage:
    python fgis/grain_matcher.py \\
        --segments results_2025_review/voyage_segments.csv \\
        --output results_2025_review/
"""

import sys
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.vessel_name_normalizer import normalize_vessel_name, build_name_key

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "fgis_export_grain.duckdb"
TERMINAL_ZONE_CSV = PROJECT_ROOT / "terminal_zone_dictionary.csv"

# Stowage factor constants (same as build_grain_report.py)
SF_CONSTANT = 2788.08
UNTRIMMED_CORRECTION = 1.06

DEFAULT_TW = {
    'WHEAT': 61.00, 'CORN': 57.32, 'SOYBEANS': 56.00, 'SORGHUM': 58.26,
    'BARLEY': 49.85, 'SUNFLOWER': 29.01, 'FLAXSEED': 50.10, 'CANOLA': 49.62,
    'RYE': 58.58, 'OATS': 43.37, 'MIXED': 60.14,
}

DEFAULT_TW_SQL = "CASE\n" + "".join(
    f"        WHEN Grain = '{grain}' THEN {tw}\n"
    for grain, tw in DEFAULT_TW.items()
) + "        ELSE 56.00\n    END"

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


class FGISGrainIndex:
    """Loads Mississippi River FGIS data from DuckDB and builds a vessel name lookup index.

    Reuses the same enriched CTE pattern from build_grain_report.py (same filters,
    SF calc, region roll-up), filtered to Mississippi River only.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.index: dict[str, list[dict]] = defaultdict(list)
        self._load()

    def _load(self):
        """Query DuckDB for Mississippi River FGIS records and build the index."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"FGIS database not found: {self.db_path}")

        con = duckdb.connect(str(self.db_path), read_only=True)

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
                  AND ({REGION_SQL}) = 'Mississippi River'
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
            )
            SELECT
                TRY_STRPTIME("Cert Date", '%Y%m%d')::DATE AS cert_date,
                "Carrier Name" AS vessel_name,
                Grain AS grain,
                Class AS class,
                Destination AS destination,
                TRY_CAST("Metric Ton" AS DOUBLE) AS metric_tons,
                effective_tw AS test_weight,
                ROUND({SF_CONSTANT} / effective_tw, 2) AS stow_factor,
                ROUND({SF_CONSTANT} / effective_tw * {UNTRIMMED_CORRECTION}, 2) AS stow_factor_untrimmed
            FROM with_tw
            ORDER BY cert_date, vessel_name
        """

        logger.info("Loading FGIS Mississippi River data from DuckDB...")
        result = con.execute(query)
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]
        con.close()

        # Build index keyed by normalized vessel name
        for row in rows:
            record = dict(zip(columns, row))
            # Convert date objects for consistent handling
            if record['cert_date'] and not isinstance(record['cert_date'], date):
                record['cert_date'] = record['cert_date'].date() if hasattr(record['cert_date'], 'date') else record['cert_date']
            key = build_name_key(record['vessel_name'])
            if key:
                self.index[key].append(record)

        # Sort each vessel's records by cert_date
        for key in self.index:
            self.index[key].sort(key=lambda r: r['cert_date'] if r['cert_date'] else date.min)

        total_records = sum(len(v) for v in self.index.values())
        logger.info(f"  Loaded {total_records:,} FGIS records for {len(self.index):,} distinct vessels")

    def find_matches(self, vessel_name: str, reference_date: date, window_days: int = 5) -> list[dict]:
        """Find FGIS certificates matching a vessel within ±window_days of reference_date.

        Args:
            vessel_name: Vessel name (any case/format)
            reference_date: Date to match against (typically departure date)
            window_days: Number of calendar days for the match window (default ±5)

        Returns:
            List of matching FGIS certificate records, sorted by cert_date
        """
        key = build_name_key(vessel_name)
        if not key or key not in self.index:
            return []

        window_start = reference_date - timedelta(days=window_days)
        window_end = reference_date + timedelta(days=window_days)

        return [
            r for r in self.index[key]
            if r['cert_date'] and window_start <= r['cert_date'] <= window_end
        ]


def _load_grain_zones(csv_path: Path) -> set[str]:
    """Load grain elevator zone names from terminal_zone_dictionary.csv.

    Returns set of Zone names where Cargoes contains 'Grain'.
    """
    zones = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cargoes = row.get('Cargoes', '')
            if 'Grain' in cargoes:
                zones.add(row['Zone'])
    return zones


def _parse_departure_date(departure_str: str) -> date | None:
    """Parse FirstTerminalDepartureTime string to date.

    Expected format: '2025-01-15 22:50:00'
    """
    if not departure_str or not departure_str.strip():
        return None
    try:
        return datetime.strptime(departure_str.strip(), '%Y-%m-%d %H:%M:%S').date()
    except ValueError:
        return None


def _aggregate_matches(matches: list[dict]) -> dict:
    """Aggregate multiple FGIS certificate matches into summary columns.

    Returns dict with the enrichment columns for one segment.
    """
    if not matches:
        return {}

    grains = []
    classes = []
    destinations = []
    total_tons = 0.0
    weighted_sf_sum = 0.0
    weighted_sf_ut_sum = 0.0
    cert_dates = []

    for m in matches:
        grain = m.get('grain', '')
        cls = m.get('class', '')
        dest = m.get('destination', '')
        tons = m.get('metric_tons') or 0.0
        sf = m.get('stow_factor') or 0.0
        sf_ut = m.get('stow_factor_untrimmed') or 0.0
        cd = m.get('cert_date')

        if grain and grain not in grains:
            grains.append(grain)
        if cls and cls not in classes:
            classes.append(cls)
        if dest and dest not in destinations:
            destinations.append(dest)

        total_tons += tons
        weighted_sf_sum += sf * tons
        weighted_sf_ut_sum += sf_ut * tons
        if cd:
            cert_dates.append(cd)

    avg_sf = round(weighted_sf_sum / total_tons, 2) if total_tons > 0 else ''
    avg_sf_ut = round(weighted_sf_ut_sum / total_tons, 2) if total_tons > 0 else ''

    return {
        'FgisMatchCount': len(matches),
        'FgisGrain': ', '.join(grains),
        'FgisClass': ', '.join(classes),
        'FgisDestination': ', '.join(destinations),
        'FgisMetricTons': round(total_tons, 2) if total_tons > 0 else '',
        'FgisStowFactor': avg_sf,
        'FgisStowFactorUntrimmed': avg_sf_ut,
        'FgisCertDate': min(cert_dates).isoformat() if cert_dates else '',
    }


class GrainMatcher:
    """Orchestrates matching MRTIS voyage segments against FGIS grain data."""

    # New columns added to the enriched output
    FGIS_COLUMNS = [
        'FgisMatchStatus', 'FgisMatchCount', 'FgisGrain', 'FgisClass',
        'FgisDestination', 'FgisMetricTons', 'FgisStowFactor',
        'FgisStowFactorUntrimmed', 'FgisCertDate', 'FgisTimeDeltaDays',
    ]

    def __init__(self, fgis_index: FGISGrainIndex, grain_zones: set[str],
                 window_days: int = 5):
        self.fgis_index = fgis_index
        self.grain_zones = grain_zones
        self.window_days = window_days

        # Stats
        self.total_segments = 0
        self.grain_visits = 0
        self.matched = 0
        self.unmatched = 0
        self.no_departure = 0
        self.not_grain = 0
        self.unmatched_vessels: dict[str, int] = defaultdict(int)
        self.time_deltas: list[float] = []
        self.tonnage_by_grain: dict[str, float] = defaultdict(float)
        self.detail_rows: list[dict] = []

    def match_segments(self, segments_path: Path) -> list[dict]:
        """Read voyage_segments.csv and match each segment.

        Returns list of enriched segment dicts (all original columns + FGIS columns).
        """
        logger.info(f"Reading segments from {segments_path}")
        with open(segments_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            original_columns = reader.fieldnames
            segments = list(reader)

        self.total_segments = len(segments)
        logger.info(f"  Total segments: {self.total_segments:,}")

        enriched = []
        for seg in segments:
            row = dict(seg)  # preserve original columns
            zone = seg.get('DischargeTerminalZone', '')

            if zone not in self.grain_zones:
                # Not a grain elevator visit
                row.update(self._empty_fgis('NOT_GRAIN_ELEVATOR'))
                self.not_grain += 1
                enriched.append(row)
                continue

            self.grain_visits += 1
            departure_str = seg.get('FirstTerminalDepartureTime', '')
            departure_date = _parse_departure_date(departure_str)

            if not departure_date:
                row.update(self._empty_fgis('NO_DEPARTURE'))
                self.no_departure += 1
                enriched.append(row)
                continue

            vessel_name = seg.get('VesselName', '')
            matches = self.fgis_index.find_matches(vessel_name, departure_date, self.window_days)

            if matches:
                agg = _aggregate_matches(matches)
                # Calculate time delta to nearest cert_date
                nearest_cert = min(matches, key=lambda m: abs((m['cert_date'] - departure_date).days))
                delta_days = (nearest_cert['cert_date'] - departure_date).days

                row['FgisMatchStatus'] = 'MATCHED'
                row['FgisMatchCount'] = agg['FgisMatchCount']
                row['FgisGrain'] = agg['FgisGrain']
                row['FgisClass'] = agg['FgisClass']
                row['FgisDestination'] = agg['FgisDestination']
                row['FgisMetricTons'] = agg['FgisMetricTons']
                row['FgisStowFactor'] = agg['FgisStowFactor']
                row['FgisStowFactorUntrimmed'] = agg['FgisStowFactorUntrimmed']
                row['FgisCertDate'] = agg['FgisCertDate']
                row['FgisTimeDeltaDays'] = delta_days

                self.matched += 1
                self.time_deltas.append(delta_days)

                # Track tonnage by grain
                for m in matches:
                    grain = m.get('grain', 'UNKNOWN')
                    tons = m.get('metric_tons') or 0.0
                    self.tonnage_by_grain[grain] += tons

                # Build detail rows
                for m in matches:
                    self.detail_rows.append({
                        'VoyageID': seg.get('VoyageID', ''),
                        'VesselName': vessel_name,
                        'VesselNameFGIS': m.get('vessel_name', ''),
                        'DischargeTerminalZone': zone,
                        'FirstTerminalDepartureTime': departure_str,
                        'cert_date': m['cert_date'].isoformat() if m['cert_date'] else '',
                        'grain': m.get('grain', ''),
                        'class': m.get('class', ''),
                        'destination': m.get('destination', ''),
                        'metric_tons': m.get('metric_tons', ''),
                        'stow_factor': m.get('stow_factor', ''),
                        'stow_factor_untrimmed': m.get('stow_factor_untrimmed', ''),
                        'time_delta_days': (m['cert_date'] - departure_date).days if m['cert_date'] else '',
                    })
            else:
                row.update(self._empty_fgis('UNMATCHED'))
                self.unmatched += 1
                self.unmatched_vessels[vessel_name] += 1

            enriched.append(row)

        logger.info(f"  Grain elevator visits: {self.grain_visits:,}")
        logger.info(f"  Matched: {self.matched:,}")
        logger.info(f"  Unmatched: {self.unmatched:,}")
        logger.info(f"  No departure time: {self.no_departure:,}")

        return enriched, original_columns

    def _empty_fgis(self, status: str) -> dict:
        """Return empty FGIS columns with given status."""
        return {
            'FgisMatchStatus': status,
            'FgisMatchCount': '',
            'FgisGrain': '',
            'FgisClass': '',
            'FgisDestination': '',
            'FgisMetricTons': '',
            'FgisStowFactor': '',
            'FgisStowFactorUntrimmed': '',
            'FgisCertDate': '',
            'FgisTimeDeltaDays': '',
        }

    def write_enriched_csv(self, enriched: list[dict], original_columns: list[str],
                           output_path: Path):
        """Write voyage_segments_enriched.csv with all original + FGIS columns."""
        all_columns = list(original_columns) + self.FGIS_COLUMNS
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(enriched)

        logger.info(f"Wrote enriched segments: {output_path} ({len(enriched):,} rows)")

    def write_detail_csv(self, output_path: Path):
        """Write grain_match_detail.csv — one row per FGIS certificate match."""
        detail_columns = [
            'VoyageID', 'VesselName', 'VesselNameFGIS', 'DischargeTerminalZone',
            'FirstTerminalDepartureTime', 'cert_date', 'grain', 'class',
            'destination', 'metric_tons', 'stow_factor', 'stow_factor_untrimmed',
            'time_delta_days',
        ]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=detail_columns)
            writer.writeheader()
            writer.writerows(self.detail_rows)

        logger.info(f"Wrote match detail: {output_path} ({len(self.detail_rows):,} rows)")

    def write_report(self, output_path: Path):
        """Write grain_match_report.txt with summary statistics."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []

        lines.append("=" * 70)
        lines.append("FGIS Grain ↔ MRTIS Vessel Matching Report")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)

        # Overview
        lines.append("")
        lines.append("SEGMENT OVERVIEW")
        lines.append("-" * 40)
        lines.append(f"  Total segments:           {self.total_segments:>8,}")
        lines.append(f"  Not grain elevator:       {self.not_grain:>8,}")
        lines.append(f"  Grain elevator visits:    {self.grain_visits:>8,}")
        lines.append(f"    Matched:                {self.matched:>8,}")
        lines.append(f"    Unmatched:              {self.unmatched:>8,}")
        lines.append(f"    No departure time:      {self.no_departure:>8,}")

        if self.grain_visits > 0:
            match_rate = self.matched / self.grain_visits * 100
            lines.append(f"  Match rate:               {match_rate:>7.1f}%")

        # Time delta distribution
        if self.time_deltas:
            lines.append("")
            lines.append("TIME DELTA DISTRIBUTION (days, departure → cert_date)")
            lines.append("-" * 40)
            buckets = defaultdict(int)
            for d in self.time_deltas:
                buckets[d] += 1
            for delta in sorted(buckets.keys()):
                bar = '#' * buckets[delta]
                lines.append(f"  {delta:>+3d} days: {buckets[delta]:>4d}  {bar}")
            avg_delta = sum(self.time_deltas) / len(self.time_deltas)
            abs_deltas = [abs(d) for d in self.time_deltas]
            lines.append(f"  Mean delta:    {avg_delta:>+.1f} days")
            lines.append(f"  Mean |delta|:  {sum(abs_deltas)/len(abs_deltas):.1f} days")
            lines.append(f"  Same day (0):  {buckets.get(0, 0):>4d}")

        # Tonnage by grain
        if self.tonnage_by_grain:
            lines.append("")
            lines.append("TONNAGE BY GRAIN TYPE (metric tons)")
            lines.append("-" * 40)
            total_tons = sum(self.tonnage_by_grain.values())
            for grain, tons in sorted(self.tonnage_by_grain.items(),
                                      key=lambda x: -x[1]):
                pct = tons / total_tons * 100 if total_tons > 0 else 0
                lines.append(f"  {grain:<20s}: {tons:>12,.0f} MT ({pct:>5.1f}%)")
            lines.append(f"  {'TOTAL':<20s}: {total_tons:>12,.0f} MT")

        # Unmatched vessels
        if self.unmatched_vessels:
            lines.append("")
            lines.append("UNMATCHED VESSEL NAMES (MRTIS name → count)")
            lines.append("-" * 40)
            for name, count in sorted(self.unmatched_vessels.items(),
                                      key=lambda x: -x[1]):
                key = build_name_key(name)
                lines.append(f"  {name:<35s} (key: {key}) × {count}")

        lines.append("")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        logger.info(f"Wrote match report: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Match MRTIS voyage segments to FGIS grain certificates")
    parser.add_argument('--segments', type=str, required=True,
                        help='Path to voyage_segments.csv')
    parser.add_argument('--output', type=str, required=True,
                        help='Output directory for results')
    parser.add_argument('--db-path', type=str, default=None,
                        help='Custom FGIS DuckDB database path')
    parser.add_argument('--window-days', type=int, default=5,
                        help='Match window in calendar days (default: 5)')
    parser.add_argument('--zones-csv', type=str, default=None,
                        help='Custom terminal_zone_dictionary.csv path')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("FGIS Grain ↔ MRTIS Vessel Matching")
    logger.info("=" * 60)

    # Load FGIS index
    db_path = Path(args.db_path) if args.db_path else DB_PATH
    fgis_index = FGISGrainIndex(db_path)

    # Load grain elevator zones
    zones_csv = Path(args.zones_csv) if args.zones_csv else TERMINAL_ZONE_CSV
    grain_zones = _load_grain_zones(zones_csv)
    logger.info(f"Grain elevator zones: {len(grain_zones)} ({', '.join(sorted(grain_zones))})")

    # Run matching
    matcher = GrainMatcher(fgis_index, grain_zones, args.window_days)
    segments_path = Path(args.segments)
    enriched, original_columns = matcher.match_segments(segments_path)

    # Write outputs
    output_dir = Path(args.output)
    matcher.write_enriched_csv(enriched, original_columns,
                               output_dir / "voyage_segments_enriched.csv")
    matcher.write_detail_csv(output_dir / "grain_match_detail.csv")
    matcher.write_report(output_dir / "grain_match_report.txt")

    logger.info("=" * 60)
    logger.info("Done.")


if __name__ == "__main__":
    main()
