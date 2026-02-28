"""
DuckDB queries for Mississippi River dry barge fleet analysis.

VTCC Reclassification (2022):
  Pre-2022: 4A40 (Open Hopper), 4A41 (Covered Hopper)
  Post-2022: 4A47 (Open Dry Cargo), 4A48 (Covered Dry Cargo)
  Combine: Covered = 4A41 + 4A48, Open = 4A40 + 4A47

Mississippi filter: region_code = 4
Missing year: 2019 not available in dataset

Operator name resolution:
  1. Use COALESCE(op.operator_name_std, op.operator_name) for known operators
  2. Fill orphaned ts_oper (no operator table match) using vessel name prefix mapping
  3. Consolidate variants (Murray American, GE Capital, etc.)
  4. Title-case ALL CAPS names
"""
import re
import pandas as pd
from usace_db.database.connection import DatabaseConnection


# VTCC codes for dry hopper barges
COVERED_CODES = ('4A41', '4A48')
OPEN_CODES = ('4A40', '4A47')
ALL_DRY_CODES = ('4A40', '4A41', '4A47', '4A48')

# Base WHERE clause for all Mississippi dry barge queries
BASE_WHERE = """
    v.region_code = 4
    AND v.vtcc_code IN ('4A40', '4A41', '4A47', '4A48')
"""

# ──────────────────────────────────────────────────────────
# ORPHAN TS_OPER MAPPING
# These ts_oper values have no entry in the operators table.
# Identified by vessel name prefixes cross-referenced against
# known operator fleets in other years.
# Only high-confidence matches (>10 barges, clear prefix match).
# ──────────────────────────────────────────────────────────
ORPHAN_MAP = {
    1899346: 'Marquette Transportation Company',   # MTC prefix (696 barges)
    2199348: 'ACBL',                                # AEP prefix — AEP River Ops merged into ACBL (466)
    2910108: 'Heartland Barge Management',          # HBM prefix (321)
    3251520: 'M/G Transport',                       # M/G, MG, MGX prefixes (233)
    310676:  'Cargo Carriers',                      # CC prefix (94)
    3209997: 'Florida Marine Transporters',         # FMTA prefix (44)
    309929:  'ACBL',                                # ACL/AEP prefix — legacy American Commercial Lines (43)
    2710125: 'M/G Transport',                       # M/GLX, M/GX prefixes (38)
    1899215: 'Canal Barge Company',                 # CB prefix (31)
    1806151: 'Campbell Transportation Company',     # CMR prefix (29)
    3209964: 'Ingram Barge Company',                # ING prefix (17)
    3210007: 'SCF Marine',                          # SCF prefix (16)
    3210052: 'Weeks Marine',                        # WEEKS prefix (13)
}

# ──────────────────────────────────────────────────────────
# OPERATOR NAME CONSOLIDATION
# Maps variant names to a single canonical name.
# Key = raw name (after COALESCE), Value = canonical name.
# ──────────────────────────────────────────────────────────
ROLLUP_MAP = {
    # Murray American — two legal names, same operator
    'MURRAY AMERICAN RIVER TOWING':            'Murray American Transportation',
    'MURRAY AMERICAN TRANSPORTATION, INC.':    'Murray American Transportation',
    # GE Capital — multiple legacy entities
    'GENERAL ELECTRIC CAPITAL CORPORATION':    'GE Capital',
    'GENERAL ELECTRIC CAPITAL CORP.':          'GE Capital',
    'GENERAL ELECTRIC CREDIT CORP. OF TENNESSEE': 'GE Capital',
    # SCF entities
    'S C F MARINE, INC.':                      'SCF Marine',
    'SCF BARGE LINE, LLC':                     'SCF Marine',
    'SCF LEWIS AND CLARK FLEETING, LLC':       'SCF Lewis & Clark Fleeting',
    'SCF WAXLER BARGE LINE, LLC':              'SCF Waxler Barge Line',
    'SCFM TOWING, LLC':                        'SCFM Towing',
    'SCF FLEETING, LLC':                       'SCF Fleeting',
    'SCF/JAR INVESTMENTS, LLC':                'SCF/JAR Investments',
    # CGB
    'C G B ENTERPRISES, INC.':                 'CGB Enterprises',
    'CGB TRUST 2009':                          'CGB Trust 2009',
    # Orion — same company, different punctuation
    'ORION MARINE CONSTRUCTION INC.':          'Orion Marine Construction',
    'ORION MARINE CONSTRUCTION, INC.':         'Orion Marine Construction',
    'ORION CONSTRUCTION, LP':                  'Orion Marine Construction',
    # Florida Marine — DB name vs orphan name
    'FLORIDA MARINE TRANSPORTERS, LLC.':       'Florida Marine Transporters',
    # Heartland — DB name (with LLC) vs orphan name (without)
    'HEARTLAND BARGE MANAGEMENT LLC':          'Heartland Barge Management',
    # Weeks Marine
    'WEEKS MARINE, INC.':                      'Weeks Marine',
    # Lone Star — fix St. Louis capitalization
    'LONE STAR INDUSTRIES (ST. LOUIS DIVISION)': 'Lone Star Industries (St. Louis Division)',
}

# Post-cleanup rollup: applied AFTER title case to catch mixed-case DB entries
# that don't hit the ALL CAPS rollup above.
_POST_ROLLUP = {
    'Flowers J Russell Inc':                   'Flowers J. Russell Inc.',
    'Florida Marine Transporters, LLC.':       'Florida Marine Transporters',
    'Heartland Barge Management LLC':          'Heartland Barge Management',
    'Weeks Marine, Inc.':                      'Weeks Marine',
}

# Acronyms that stay ALL CAPS
_KEEP_UPPER = {
    'ACBL', 'ARTCO', 'CGB', 'SCF', 'GE', 'ADM', 'CMNA',
    'SCFM', 'PML', 'LLC', 'LP', 'LLP',
    'II', 'III', 'IV', 'USA', 'US',
}

# Words that get standard capitalization (not all-caps)
_STANDARD_CAP = {
    'INC': 'Inc.', 'INC.': 'Inc.', 'CO': 'Co.', 'CO.': 'Co.',
    'CORP': 'Corp.', 'CORP.': 'Corp.', 'LTD': 'Ltd.', 'LTD.': 'Ltd.',
    'LLC.': 'LLC', 'LLC,': 'LLC,',
}

# Words that should stay lowercase (mid-name only)
_KEEP_LOWER = {'of', 'the', 'and', 'for', 'in', 'at', 'by', 'to', 'a', 'an'}

# Special full-name overrides for tricky cases
_NAME_OVERRIDES = {
    'JPMORGAN CHASE BANK, N.A.': 'JPMorgan Chase Bank, N.A.',
    'P M L, INC.': 'PML, Inc.',
    'CARGILL, INC. CMNA': 'Cargill, Inc. CMNA',
    'M K J, INC.': 'MKJ, Inc.',
    'FLOWERS J RUSSELL INC': 'Flowers J. Russell Inc.',
    'U. S. BANCORP EQUIPMENT FINANCE, INC.': 'U.S. Bancorp Equipment Finance, Inc.',
    'MOTHERSHEAD, RUSS ALLEN, TRUSTEE OF THE RUSS ALLEN MOTHERSHEAD REVOCABLE LIVING TRUST DTD 12/5/94':
        'Mothershead, Russ A. (Revocable Trust)',
    'DUROCHER MARINE, A DIVISION OF KOKOSING CONSTRUCTION CO., INC.':
        'Durocher Marine (Kokosing Construction)',
}


def _title_case_word(word: str) -> str:
    """Title-case a single word, preserving known abbreviations."""
    stripped = word.strip('.,;:()')
    upper = stripped.upper()

    # Check all-caps acronyms
    if upper in _KEEP_UPPER:
        # Preserve trailing punctuation
        suffix = word[len(stripped):]
        return upper + suffix

    # Check standard capitalization overrides
    if upper in _STANDARD_CAP:
        return _STANDARD_CAP[upper]
    # With trailing punctuation
    if stripped.upper() + '.' in _STANDARD_CAP:
        return _STANDARD_CAP[stripped.upper() + '.']

    if upper in {w.upper() for w in _KEEP_LOWER}:
        return word.lower()

    # Handle L.P., L.L.C., N.A., etc.
    if re.match(r'^[A-Za-z]\.([A-Za-z]\.)*$', stripped):
        return word.upper()

    return word.capitalize()


def clean_operator_name(raw: str) -> str:
    """
    Clean an operator name:
    1. Apply full-name overrides
    2. Apply rollup mapping
    3. Convert ALL CAPS to proper title case
    4. Preserve known abbreviations
    """
    if raw is None:
        return None

    # Check full-name overrides first (exact match)
    if raw in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[raw]

    # Check rollup
    if raw in ROLLUP_MAP:
        return ROLLUP_MAP[raw]

    # If already mixed case (has lowercase letters), apply post-rollup only
    if any(c.islower() for c in raw):
        return _POST_ROLLUP.get(raw, raw)

    # ALL CAPS — convert to title case
    words = raw.split()
    result = [_title_case_word(w) for w in words]

    # First word should always be capitalized
    if result and result[0] and result[0][0].islower():
        result[0] = result[0][0].upper() + result[0][1:]

    cleaned = ' '.join(result)

    return cleaned


def _build_orphan_case_sql() -> str:
    """Build SQL CASE expression to fill in orphaned ts_oper operator names."""
    lines = []
    for ts_oper, name in ORPHAN_MAP.items():
        lines.append(f"            WHEN v.ts_oper = {ts_oper} THEN '{name}'")
    case_block = '\n'.join(lines)
    return f"""
        CASE
            WHEN op.ts_oper IS NOT NULL THEN COALESCE(op.operator_name_std, op.operator_name)
{case_block}
            ELSE NULL
        END"""


# Pre-built SQL expression for operator name resolution
OPERATOR_NAME_SQL = _build_orphan_case_sql()


class BargeQueries:
    """All DuckDB queries for the barge fleet acquisition report."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    @staticmethod
    def _clean_operator_col(df: pd.DataFrame, col: str = 'operator') -> pd.DataFrame:
        """Apply name cleanup to operator column in a DataFrame."""
        if col in df.columns:
            df[col] = df[col].apply(lambda x: clean_operator_name(x) if x else x)
            # After cleanup, re-aggregate if rollups merged rows
            # (only for grouped queries — caller handles if needed)
        return df

    @staticmethod
    def _reaggregate(df: pd.DataFrame) -> pd.DataFrame:
        """Re-aggregate after name cleanup merges operators."""
        if 'operator' not in df.columns or df.empty:
            return df

        # Identify numeric columns to sum vs average
        sum_cols = [c for c in ['total', 'covered', 'open'] if c in df.columns]
        avg_cols = [c for c in ['avg_age'] if c in df.columns]
        min_cols = [c for c in ['oldest_build'] if c in df.columns]
        max_cols = [c for c in ['newest_build'] if c in df.columns]

        agg_dict = {}
        for c in sum_cols:
            agg_dict[c] = 'sum'
        for c in avg_cols:
            # Weighted average by total count
            agg_dict[c] = 'mean'
        for c in min_cols:
            agg_dict[c] = 'min'
        for c in max_cols:
            agg_dict[c] = 'max'

        if not agg_dict:
            return df

        result = df.groupby('operator', as_index=False).agg(agg_dict)

        # Recalculate market_share if present
        if 'market_share' in df.columns and 'total' in result.columns:
            fleet_total = result['total'].sum()
            result['market_share'] = (result['total'] / fleet_total * 100).round(1)

        # Re-round avg_age
        if 'avg_age' in result.columns:
            result['avg_age'] = result['avg_age'].round(1)

        return result.sort_values('total', ascending=False).reset_index(drop=True)

    def fleet_by_year(self) -> pd.DataFrame:
        """Total fleet size by year with covered/open breakdown."""
        sql = f"""
            SELECT
                v.fleet_year AS year,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A41', '4A48')) AS covered,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A40', '4A47')) AS open
            FROM vessels v
            WHERE {BASE_WHERE}
            GROUP BY v.fleet_year
            ORDER BY v.fleet_year
        """
        return self.db.query_df(sql)

    def fleet_summary_latest(self) -> dict:
        """Key metrics for the most recent fleet year."""
        sql = f"""
            SELECT
                COUNT(*) AS total_barges,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A41', '4A48')) AS covered,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A40', '4A47')) AS open,
                COUNT(DISTINCT v.ts_oper) AS unique_operators,
                AVG(2023 - v.year_built) AS avg_age,
                MEDIAN(2023 - v.year_built) AS median_age,
                MIN(v.year_built) AS oldest_build,
                MAX(v.year_built) AS newest_build,
                SUM(v.nrt) AS total_nrt,
                AVG(v.nrt) AS avg_nrt,
                SUM(v.cap_tons) AS total_cap_tons,
                AVG(v.cap_tons) AS avg_cap_tons,
                AVG(v.over_length) AS avg_length,
                AVG(v.over_breadth) AS avg_breadth
            FROM vessels v
            WHERE {BASE_WHERE}
              AND v.fleet_year = 2023
        """
        row = self.db.query(sql)[0]
        return {
            'total_barges': row[0],
            'covered': row[1],
            'open': row[2],
            'unique_operators': row[3],
            'avg_age': round(row[4], 1) if row[4] else None,
            'median_age': round(row[5], 1) if row[5] else None,
            'oldest_build': row[6],
            'newest_build': row[7],
            'total_nrt': round(row[8], 0) if row[8] else None,
            'avg_nrt': round(row[9], 1) if row[9] else None,
            'total_cap_tons': round(row[10], 0) if row[10] else None,
            'avg_cap_tons': round(row[11], 1) if row[11] else None,
            'avg_length': round(row[12], 1) if row[12] else None,
            'avg_breadth': round(row[13], 1) if row[13] else None,
        }

    def age_distribution(self, fleet_year: int = 2023) -> pd.DataFrame:
        """Age distribution in 5-year buckets for given fleet year."""
        sql = f"""
            SELECT
                CASE
                    WHEN ({fleet_year} - v.year_built) < 5 THEN '0-4'
                    WHEN ({fleet_year} - v.year_built) < 10 THEN '5-9'
                    WHEN ({fleet_year} - v.year_built) < 15 THEN '10-14'
                    WHEN ({fleet_year} - v.year_built) < 20 THEN '15-19'
                    WHEN ({fleet_year} - v.year_built) < 25 THEN '20-24'
                    WHEN ({fleet_year} - v.year_built) < 30 THEN '25-29'
                    WHEN ({fleet_year} - v.year_built) < 35 THEN '30-34'
                    WHEN ({fleet_year} - v.year_built) < 40 THEN '35-39'
                    ELSE '40+'
                END AS age_bucket,
                COUNT(*) AS count,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A41', '4A48')) AS covered,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A40', '4A47')) AS open,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
            FROM vessels v
            WHERE {BASE_WHERE}
              AND v.fleet_year = {fleet_year}
              AND v.year_built IS NOT NULL
            GROUP BY age_bucket
            ORDER BY
                CASE age_bucket
                    WHEN '0-4' THEN 1
                    WHEN '5-9' THEN 2
                    WHEN '10-14' THEN 3
                    WHEN '15-19' THEN 4
                    WHEN '20-24' THEN 5
                    WHEN '25-29' THEN 6
                    WHEN '30-34' THEN 7
                    WHEN '35-39' THEN 8
                    WHEN '40+' THEN 9
                END
        """
        return self.db.query_df(sql)

    def build_decade_cohorts(self, fleet_year: int = 2023) -> pd.DataFrame:
        """Fleet by build decade with retirement status estimates."""
        sql = f"""
            SELECT
                (v.year_built // 10) * 10 AS decade,
                COUNT(*) AS count,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A41', '4A48')) AS covered,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A40', '4A47')) AS open,
                AVG({fleet_year} - v.year_built) AS avg_age,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
            FROM vessels v
            WHERE {BASE_WHERE}
              AND v.fleet_year = {fleet_year}
              AND v.year_built IS NOT NULL
            GROUP BY decade
            ORDER BY decade
        """
        return self.db.query_df(sql)

    def new_builds_by_year(self) -> pd.DataFrame:
        """Count of new builds per construction year (from 2023 snapshot)."""
        sql = f"""
            SELECT
                v.year_built,
                COUNT(*) AS builds,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A41', '4A48')) AS covered,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A40', '4A47')) AS open
            FROM vessels v
            WHERE {BASE_WHERE}
              AND v.fleet_year = 2023
              AND v.year_built IS NOT NULL
              AND v.year_built >= 2000
            GROUP BY v.year_built
            ORDER BY v.year_built
        """
        return self.db.query_df(sql)

    def top_operators(self, fleet_year: int = 2023, limit: int = 15) -> pd.DataFrame:
        """Top operators by fleet size with covered/open breakdown."""
        sql = f"""
            SELECT
                {OPERATOR_NAME_SQL} AS operator,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A41', '4A48')) AS covered,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A40', '4A47')) AS open,
                ROUND(AVG({fleet_year} - v.year_built), 1) AS avg_age,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS market_share
            FROM vessels v
            LEFT JOIN operators op ON v.ts_oper = op.ts_oper
            WHERE {BASE_WHERE}
              AND v.fleet_year = {fleet_year}
            GROUP BY operator
            ORDER BY total DESC
            LIMIT {limit * 3}
        """
        df = self.db.query_df(sql)
        df = self._clean_operator_col(df)
        df = self._reaggregate(df)
        # Recalculate market share against full fleet (not just fetched rows)
        full_total_sql = f"""
            SELECT COUNT(*) FROM vessels v
            WHERE {BASE_WHERE} AND v.fleet_year = {fleet_year}
        """
        fleet_total = self.db.query(full_total_sql)[0][0]
        df['market_share'] = (df['total'] / fleet_total * 100).round(1)
        return df.head(limit)

    def all_operators(self, fleet_year: int = 2023) -> pd.DataFrame:
        """All operators with fleet counts for the appendix."""
        sql = f"""
            SELECT
                {OPERATOR_NAME_SQL} AS operator,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A41', '4A48')) AS covered,
                COUNT(*) FILTER (WHERE v.vtcc_code IN ('4A40', '4A47')) AS open,
                ROUND(AVG({fleet_year} - v.year_built), 1) AS avg_age,
                MIN(v.year_built) AS oldest_build,
                MAX(v.year_built) AS newest_build
            FROM vessels v
            LEFT JOIN operators op ON v.ts_oper = op.ts_oper
            WHERE {BASE_WHERE}
              AND v.fleet_year = {fleet_year}
            GROUP BY operator
            ORDER BY total DESC
        """
        df = self.db.query_df(sql)
        df = self._clean_operator_col(df)
        df = self._reaggregate(df)
        return df

    def concentration_metrics(self, fleet_year: int = 2023) -> dict:
        """Market concentration: HHI, top-3 share, top-5 share."""
        sql = f"""
            WITH operator_counts AS (
                SELECT
                    {OPERATOR_NAME_SQL} AS operator,
                    COUNT(*) AS cnt
                FROM vessels v
                LEFT JOIN operators op ON v.ts_oper = op.ts_oper
                WHERE {BASE_WHERE}
                  AND v.fleet_year = {fleet_year}
                GROUP BY operator
            ),
            total AS (
                SELECT SUM(cnt) AS fleet_total FROM operator_counts
            ),
            shares AS (
                SELECT
                    operator,
                    cnt,
                    cnt * 100.0 / fleet_total AS share,
                    ROW_NUMBER() OVER (ORDER BY cnt DESC) AS rank
                FROM operator_counts, total
            )
            SELECT
                SUM(CASE WHEN rank <= 3 THEN share ELSE 0 END) AS top3_share,
                SUM(CASE WHEN rank <= 5 THEN share ELSE 0 END) AS top5_share,
                SUM(CASE WHEN rank <= 10 THEN share ELSE 0 END) AS top10_share,
                SUM(share * share) AS hhi,
                COUNT(*) AS total_operators
            FROM shares
        """
        # Run the SQL, then apply rollups in Python for accurate concentration
        raw_df = self.db.query_df(f"""
            SELECT
                {OPERATOR_NAME_SQL} AS operator,
                COUNT(*) AS cnt
            FROM vessels v
            LEFT JOIN operators op ON v.ts_oper = op.ts_oper
            WHERE {BASE_WHERE}
              AND v.fleet_year = {fleet_year}
            GROUP BY operator
        """)
        raw_df['operator'] = raw_df['operator'].apply(
            lambda x: clean_operator_name(x) if x else x)
        merged = raw_df.groupby('operator', as_index=False)['cnt'].sum()
        merged = merged.sort_values('cnt', ascending=False).reset_index(drop=True)

        fleet_total = merged['cnt'].sum()
        merged['share'] = merged['cnt'] / fleet_total * 100

        top3 = merged.head(3)['share'].sum()
        top5 = merged.head(5)['share'].sum()
        top10 = merged.head(10)['share'].sum()
        hhi = (merged['share'] ** 2).sum()

        return {
            'top3_share': round(top3, 1),
            'top5_share': round(top5, 1),
            'top10_share': round(top10, 1),
            'hhi': round(hhi, 0),
            'total_operators': len(merged),
        }

    def capacity_trend(self) -> pd.DataFrame:
        """Total NRT and cap_tons by fleet year."""
        sql = f"""
            SELECT
                v.fleet_year AS year,
                SUM(v.nrt) AS total_nrt,
                SUM(v.cap_tons) AS total_cap_tons,
                AVG(v.nrt) AS avg_nrt,
                AVG(v.cap_tons) AS avg_cap_tons
            FROM vessels v
            WHERE {BASE_WHERE}
            GROUP BY v.fleet_year
            ORDER BY v.fleet_year
        """
        return self.db.query_df(sql)

    def operator_growth_trend(self, top_n: int = 5) -> pd.DataFrame:
        """Fleet count per year for top N operators (by 2023 fleet size)."""
        sql = f"""
            WITH top_ops AS (
                SELECT {OPERATOR_NAME_SQL} AS operator
                FROM vessels v
                LEFT JOIN operators op ON v.ts_oper = op.ts_oper
                WHERE {BASE_WHERE}
                  AND v.fleet_year = 2023
                GROUP BY operator
                ORDER BY COUNT(*) DESC
                LIMIT {top_n}
            )
            SELECT
                v.fleet_year AS year,
                {OPERATOR_NAME_SQL} AS operator,
                COUNT(*) AS count
            FROM vessels v
            LEFT JOIN operators op ON v.ts_oper = op.ts_oper
            WHERE {BASE_WHERE}
              AND {OPERATOR_NAME_SQL} IN (SELECT operator FROM top_ops)
            GROUP BY v.fleet_year, operator
            ORDER BY v.fleet_year, count DESC
        """
        df = self.db.query_df(sql)
        return self._clean_operator_col(df)

    def age_trend_by_year(self) -> pd.DataFrame:
        """Average fleet age over time."""
        sql = f"""
            SELECT
                v.fleet_year AS year,
                ROUND(AVG(v.fleet_year - v.year_built), 1) AS avg_age,
                ROUND(MEDIAN(v.fleet_year - v.year_built), 1) AS median_age,
                COUNT(*) FILTER (WHERE (v.fleet_year - v.year_built) >= 30) AS over_30,
                COUNT(*) FILTER (WHERE (v.fleet_year - v.year_built) < 5) AS under_5
            FROM vessels v
            WHERE {BASE_WHERE}
              AND v.year_built IS NOT NULL
            GROUP BY v.fleet_year
            ORDER BY v.fleet_year
        """
        return self.db.query_df(sql)

    def physical_specs(self, fleet_year: int = 2023) -> pd.DataFrame:
        """Physical characteristics summary by barge type."""
        sql = f"""
            SELECT
                CASE
                    WHEN v.vtcc_code IN ('4A41', '4A48') THEN 'Covered'
                    ELSE 'Open'
                END AS barge_type,
                COUNT(*) AS count,
                ROUND(AVG(v.over_length), 1) AS avg_length,
                ROUND(AVG(v.over_breadth), 1) AS avg_breadth,
                ROUND(AVG(v.nrt), 1) AS avg_nrt,
                ROUND(AVG(v.cap_tons), 1) AS avg_cap_tons,
                ROUND(AVG(v.load_draft), 1) AS avg_draft
            FROM vessels v
            WHERE {BASE_WHERE}
              AND v.fleet_year = {fleet_year}
            GROUP BY barge_type
            ORDER BY barge_type
        """
        return self.db.query_df(sql)
