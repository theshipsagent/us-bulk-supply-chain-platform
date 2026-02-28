"""
Corporate Entity Resolution for EPA Cement Consumer Facilities
==============================================================
Maps messy EPA parent_company and fac_name values to standardized
corporate parent groups. Creates a corporate_parents mapping table
and updates epa_cement_consumers with resolved corporate_parent.
"""

import sys
import io
import duckdb

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"G:\My Drive\LLM\project_cement_markets\atlas\data\atlas.duckdb"

# =============================================================================
# CORPORATE ENTITY MAPPING DEFINITIONS
# =============================================================================
# Each entry: (corporate_parent, parent_type, [list of keyword patterns])
# Patterns are matched against UPPER(parent_company) and UPPER(fac_name)
# Order matters: more specific patterns should come before generic ones.

ENTITY_MAPPINGS = [
    # =========================================================================
    # INTEGRATED CEMENT PRODUCERS (they make AND sell cement)
    # =========================================================================

    ("CEMEX", "INTEGRATED_PRODUCER", [
        "CEMEX",
        "RINKER",       # acquired 2007
        "SOUTHDOWN",    # acquired by CEMEX
    ]),

    ("Holcim Group", "INTEGRATED_PRODUCER", [
        "HOLCIM",
        "LAFARGEHOLCIM",
        "LAFARGE",
        "AGGREGATE IND",     # Aggregate Industries (Holcim sub)
        "CONTINENTAL BUILDING",
        "HOLNAM",            # old Holcim name in US
        "GLACIER NORTHWEST", # Holcim subsidiary
        "GLACIER NW",
    ]),

    ("CRH plc", "INTEGRATED_PRODUCER", [
        "OLDCASTLE",
        "ASH GROVE",
        "APAC ",             # space after to avoid partial matches
        "APAC-",
        "PIKE ELECTRIC",     # avoid: want Pike Industries
        "CALLANAN",
        "TILCON",
        "TRAP ROCK",
        "DUFFERIN",
        "PIKE IND",
        "PIKE LUMBER",
        # CRH itself
        "CRH ",
        "CRH,",
        # Specific APAC subsidiaries
        "APAC ATLANTIC",
        "APAC TENNESSEE",
        "APAC KANSAS",
        "APAC CAROLINA",
        "APAC SOUTHEAST",
        "APAC MISSOURI",
        "APAC PAVING",
        "APAC SHEA",
        # Lane Construction (CRH sub)
        "LANE CONSTRUCTION",
    ]),

    ("Heidelberg Materials", "INTEGRATED_PRODUCER", [
        "HEIDELBERG",
        "LEHIGH",
        "ESSROC",
        "HANSON",
        "CASTLE CEMENT",
        "HM SOUTHEAST",
        "HM TEXAS",
        "BLUE CIRCLE",       # legacy name
    ]),

    ("Buzzi Unicem", "INTEGRATED_PRODUCER", [
        "BUZZI",
        "UNICEM",
        "ALAMO CEMENT",
        "LONE STAR",
        "RC CEMENT",
    ]),

    ("Eagle Materials", "INTEGRATED_PRODUCER", [
        "EAGLE MATERIAL",
        "TEXAS LEHIGH",      # Note: joint venture Eagle/Lehigh
        "MOUNTAIN CEMENT",
        "NEVADA CEMENT",
        "CENTRAL PLAINS",
        "HEADWATERS",        # Eagle acquired Headwaters 2017
    ]),

    ("Summit Materials", "INTEGRATED_PRODUCER", [
        "SUMMIT MATERIAL",
        "CONTINENTAL CEMENT",
        "CONTINENTAL ILASCO",
    ]),

    ("Martin Marietta", "INTEGRATED_PRODUCER", [
        "MARTIN MARIETTA",
        "TXI",               # acquired 2014
        "TEXAS INDUSTRIES",
    ]),

    ("Argos USA", "INTEGRATED_PRODUCER", [
        "ARGOS",
        "CEMENTOS ARGOS",
    ]),

    ("Titan America", "INTEGRATED_PRODUCER", [
        "TITAN",
    ]),

    ("CalPortland", "INTEGRATED_PRODUCER", [
        "CALPORTLAND",
        "CAL PORTLAND",
    ]),

    ("GCC", "INTEGRATED_PRODUCER", [
        "GCC ALLIANCE",
        "GCC DACOTAH",
        "GCC RIO",
        "GCC CONSOLIDATED",
        "GCC SERGEANT",
        "GCC OF AMERICA",
    ]),

    ("National Cement", "INTEGRATED_PRODUCER", [
        "NATIONAL CEMENT",
    ]),

    ("Giant Cement", "INTEGRATED_PRODUCER", [
        "GIANT CEMENT",
    ]),

    ("St Marys Cement", "INTEGRATED_PRODUCER", [
        "ST MARYS",
        "ST. MARYS",
        "ST MARY'S",
        "VOTORANTIM",
    ]),

    ("Suwannee American Cement", "INTEGRATED_PRODUCER", [
        "SUWANNEE",
    ]),

    ("Drake Cement", "INTEGRATED_PRODUCER", [
        "DRAKE CEMENT",
        "DRAKE",
    ]),

    ("Phoenix Cement", "INTEGRATED_PRODUCER", [
        "PHOENIX CEMENT",
    ]),

    ("Boral", "INTEGRATED_PRODUCER", [
        "BORAL",
    ]),

    ("Ash Grove Cement", "INTEGRATED_PRODUCER", [
        # Ash Grove was independent before CRH acquired 2018
        # But we map to CRH above; this catches any remaining
    ]),

    ("Illinois Cement", "INTEGRATED_PRODUCER", [
        "ILLINOIS CEMENT",
    ]),

    ("Kosmos Cement", "INTEGRATED_PRODUCER", [
        "KOSMOS",
    ]),

    ("Capitol Aggregates", "INTEGRATED_PRODUCER", [
        "CAPITOL AGGREGATES",
        "CAPITOL CEMENT",
    ]),

    ("Systech / Continental Cement", "INTEGRATED_PRODUCER", [
        "SYSTECH",
    ]),

    # =========================================================================
    # MAJOR READY-MIX / CONCRETE COMPANIES (they BUY cement)
    # =========================================================================

    ("U.S. Concrete", "MAJOR_READYMIX", [
        "US CONCRETE",
        "U.S. CONCRETE",
    ]),

    ("QUIKRETE Holdings", "MAJOR_READYMIX", [
        "QUIKRETE",
        "FORTERRA",
        "SESCO",
        "AMERIMIX",
    ]),

    ("Knife River (MDU)", "MAJOR_READYMIX", [
        "KNIFE RIVER",
    ]),

    ("Irving Materials (IMI)", "MAJOR_READYMIX", [
        "IRVING",
        "IMI TENNESSEE",
        "IMI INDIANA",
        "IMI CONCRETE",
        "IMI READY",
        "IMI",           # bare "IMI" in parent_company
    ]),

    ("Ozinga", "MAJOR_READYMIX", [
        "OZINGA",
    ]),

    ("Geneva Rock", "MAJOR_READYMIX", [
        "GENEVA ROCK",
    ]),

    ("Robertson's Ready Mix", "MAJOR_READYMIX", [
        "ROBERTSON",
    ]),

    ("Chaney Enterprises", "MAJOR_READYMIX", [
        "CHANEY",
    ]),

    ("Thomas Concrete", "MAJOR_READYMIX", [
        "THOMAS CAROLINA",
        "THOMAS CONCRETE",
    ]),

    ("Preferred Materials", "MAJOR_READYMIX", [
        "PREFERRED",
    ]),

    ("Tarmac America", "MAJOR_READYMIX", [
        "TARMAC",
    ]),

    ("Vulcan Materials", "MAJOR_READYMIX", [
        "VULCAN",
        "FLORIDA ROCK",
    ]),

    ("Prairie Materials (VCNA)", "MAJOR_READYMIX", [
        "VCNA PRAIRIE",
        "PRAIRIE MATERIAL",
        "VCNA PRESTIGE",
        "VCNA",
    ]),

    ("Croell Redi-Mix", "MAJOR_READYMIX", [
        "CROELL",
    ]),

    ("Central Supply", "MAJOR_READYMIX", [
        "CENTRAL SUPPLY",
    ]),

    ("Wells Group", "MAJOR_READYMIX", [
        "WELLS",   # broad but high freq in data
    ]),

    ("Smyrna Ready Mix", "MAJOR_READYMIX", [
        "SMYRNA",
    ]),

    ("Meyer Material", "MAJOR_READYMIX", [
        "MEYER MATERIAL",
    ]),

    ("Basalite (Paccoast)", "MAJOR_READYMIX", [
        "BASALITE",
    ]),

    ("County Materials", "MAJOR_READYMIX", [
        "COUNTY MATERIAL",
    ]),

    ("Pavestone", "BLOCK_MASONRY", [
        "PAVESTONE",
    ]),

    ("James Hardie", "INDEPENDENT", [
        "JAMES HARDIE",
    ]),

    ("Best Block", "BLOCK_MASONRY", [
        "BEST BLOCK",
    ]),

    ("Dolese Bros", "MAJOR_READYMIX", [
        "DOLESE",
    ]),

    ("Holliday Rock", "MAJOR_READYMIX", [
        "HOLLIDAY ROCK",
    ]),

    ("Ready Mixed Concrete Co", "MAJOR_READYMIX", [
        "READY MIXED",
    ]),

    ("Transit Mix Concrete", "MAJOR_READYMIX", [
        "TRANSIT MIX",
    ]),

    ("Emery Sapp & Sons", "MAJOR_READYMIX", [
        "EMERY SAPP",
    ]),

    ("Rockingham Redi-Mix", "REGIONAL_READYMIX", [
        "ROCKINGHAM REDI",
    ]),

    ("Clarkson Construction", "REGIONAL_READYMIX", [
        "CLARKSON CONSTRUCTION",
        "CLARKSON CONST",
        "CLARKSON CONSTRUCTIO",
    ]),

    ("Van Eaton", "REGIONAL_READYMIX", [
        "VAN EATON",
    ]),

    ("Mark Twain Redi-Mix", "REGIONAL_READYMIX", [
        "MARK TWAIN",
    ]),

    ("McCarthy Improvement", "REGIONAL_READYMIX", [
        "MCCARTHY IMPROVEMENT",
        "MCCARTHY IMP",
    ]),

    ("Fred Weber Inc", "REGIONAL_READYMIX", [
        "FRED WEBER",
        "MILLSTONE WEBER",
    ]),

    ("Hydro Conduit", "PIPE_PRODUCTS", [
        "HYDRO CONDUIT",
    ]),

    ("Hanson Pipe & Precast", "PIPE_PRODUCTS", [
        "HANSON PIPE",
    ]),

    ("Brown Wilbert", "PRECAST_NATIONAL", [
        "BROWN WILBERT",
    ]),

    ("Plote Construction", "REGIONAL_READYMIX", [
        "PLOTE",
    ]),

    ("James Cape & Sons", "REGIONAL_READYMIX", [
        "JAMES CAPE",
    ]),

    ("Central Pre-Mix", "REGIONAL_READYMIX", [
        "CENTRAL PRE",
    ]),

    ("Central Iowa Ready Mix", "REGIONAL_READYMIX", [
        "CENTRAL IOWA",
    ]),

    ("Central Supermix", "REGIONAL_READYMIX", [
        "CENTRAL SUPERMIX",
    ]),

    ("Associated Ready Mix", "REGIONAL_READYMIX", [
        "ASSOCIATED READY",
    ]),

    ("Valley Paving", "REGIONAL_READYMIX", [
        "VALLEY PAVING",
    ]),

    ("Dragon Products", "REGIONAL_READYMIX", [
        "DRAGON",
    ]),

    ("Gerhold Concrete", "REGIONAL_READYMIX", [
        "GERHOLD",
    ]),

    ("Jensen Precast", "PRECAST_NATIONAL", [
        "JENSEN",
    ]),

    ("Quad County Ready Mix", "REGIONAL_READYMIX", [
        "QUAD COUNTY",
    ]),

    ("Kienstra Group", "REGIONAL_READYMIX", [
        "KIENSTRA",
    ]),

    ("Roanoke Cement", "REGIONAL_READYMIX", [
        "ROANOKE",
    ]),

    ("Western Mobile", "REGIONAL_READYMIX", [
        "WESTERN MOBILE",
    ]),

    ("Dawkins", "REGIONAL_READYMIX", [
        "DAWKINS",
    ]),

    ("Conrad Yelvington", "REGIONAL_READYMIX", [
        "CONRAD YELVINGTON",
    ]),

    ("Aggregate WCR", "REGIONAL_READYMIX", [
        "AGGREGATE WCR",
    ]),

    ("Tehachapi Cement", "INTEGRATED_PRODUCER", [
        "TEHACHAPI",
    ]),

    ("Lambcon", "REGIONAL_READYMIX", [
        "LAMBCON",
    ]),

    ("Service Rock", "REGIONAL_READYMIX", [
        "SERVICE ROCK",
    ]),

    ("Halliburton", "INDEPENDENT", [
        "HALLIBURTON",
    ]),

    ("Mitsubishi Cement", "INTEGRATED_PRODUCER", [
        "MITSUBISHI",
    ]),
]

# Patterns that should be EXCLUDED from certain generic matches
# to avoid false positives
EXCLUSION_RULES = {
    # "WELLS" is generic - only match parent_company, not fac_name
    "WELLS": "parent_only",
    # "TITAN" could match non-cement Titan companies
    "TITAN": "parent_only",
    # "PREFERRED" is vague
    "PREFERRED": "parent_only",
    # "DRAGON" - could be Dragon Products (cement/lime) or others
    "DRAGON": "parent_only",
    # "CONTINENTAL" conflicts with many non-cement companies
    "CONTINENTAL CEMENT": "both",
    "CONTINENTAL ILASCO": "both",
    # Avoid matching EAGLE broadly - only EAGLE MATERIAL
    # "JENSEN" - could match non-precast Jensen
    "JENSEN": "parent_only",
    # IRVING / IMI - only on parent
    "IRVING": "parent_only",
    "IMI": "parent_only",
    # DRAKE could be non-cement in fac_name
    "DRAKE": "parent_only",
}


def build_pattern_match_sql():
    """
    Build a giant CASE WHEN statement that checks parent_company and fac_name
    against all known patterns. Returns (case_sql_corporate_parent, case_sql_parent_type).
    """
    case_lines_corp = []
    case_lines_type = []

    for corp_parent, ptype, patterns in ENTITY_MAPPINGS:
        if not patterns:
            continue
        conditions = []
        for pat in patterns:
            pat_upper = pat.upper().replace("'", "''")
            rule = EXCLUSION_RULES.get(pat, "both")

            if rule == "parent_only":
                # Only match against parent_company
                conditions.append(
                    f"UPPER(e.parent_company) LIKE '%{pat_upper}%'"
                )
            elif rule == "fac_only":
                conditions.append(
                    f"UPPER(e.fac_name) LIKE '%{pat_upper}%'"
                )
            else:
                # Match against both parent_company and fac_name
                conditions.append(
                    f"(UPPER(e.parent_company) LIKE '%{pat_upper}%' OR UPPER(e.fac_name) LIKE '%{pat_upper}%')"
                )

        if conditions:
            or_clause = " OR ".join(conditions)
            safe_corp = corp_parent.replace("'", "''")
            safe_type = ptype.replace("'", "''")
            case_lines_corp.append(f"    WHEN {or_clause} THEN '{safe_corp}'")
            case_lines_type.append(f"    WHEN {or_clause} THEN '{safe_type}'")

    case_corp = "CASE\n" + "\n".join(case_lines_corp) + "\n    ELSE NULL\n  END"
    case_type = "CASE\n" + "\n".join(case_lines_type) + "\n    ELSE 'UNKNOWN'\n  END"

    return case_corp, case_type


def main():
    conn = duckdb.connect(DB_PATH)

    print("=" * 80)
    print("CORPORATE ENTITY RESOLUTION - EPA Cement Consumers")
    print("=" * 80)
    print()

    # -------------------------------------------------------------------------
    # Step 0: Baseline stats
    # -------------------------------------------------------------------------
    total = conn.execute("SELECT COUNT(*) FROM epa_cement_consumers").fetchone()[0]
    distinct_parents = conn.execute(
        "SELECT COUNT(DISTINCT parent_company) FROM epa_cement_consumers"
    ).fetchone()[0]
    print(f"Total facilities:           {total:,}")
    print(f"Distinct parent_company:    {distinct_parents:,}")
    print()

    # -------------------------------------------------------------------------
    # Step 1: Create the corporate_parents mapping table
    # -------------------------------------------------------------------------
    print("Creating corporate_parents mapping table...")

    conn.execute("DROP TABLE IF EXISTS corporate_parents")
    conn.execute("""
        CREATE TABLE corporate_parents (
            parent_pattern VARCHAR,
            corporate_parent VARCHAR,
            parent_type VARCHAR
        )
    """)

    # Insert all mapping rows
    insert_sql = "INSERT INTO corporate_parents VALUES (?, ?, ?)"
    row_count = 0
    for corp_parent, ptype, patterns in ENTITY_MAPPINGS:
        for pat in patterns:
            if pat.strip():
                conn.execute(insert_sql, [pat.upper(), corp_parent, ptype])
                row_count += 1

    print(f"  Inserted {row_count} pattern rows into corporate_parents")
    print()

    # -------------------------------------------------------------------------
    # Step 2: Add corporate_parent and parent_type columns if not exist
    # -------------------------------------------------------------------------
    cols = [r[0] for r in conn.execute("DESCRIBE epa_cement_consumers").fetchall()]

    if "corporate_parent" not in cols:
        print("Adding corporate_parent column to epa_cement_consumers...")
        conn.execute("ALTER TABLE epa_cement_consumers ADD COLUMN corporate_parent VARCHAR")
    else:
        print("corporate_parent column already exists, resetting...")
        conn.execute("UPDATE epa_cement_consumers SET corporate_parent = NULL")

    if "parent_type" not in cols:
        print("Adding parent_type column to epa_cement_consumers...")
        conn.execute("ALTER TABLE epa_cement_consumers ADD COLUMN parent_type VARCHAR")
    else:
        print("parent_type column already exists, resetting...")
        conn.execute("UPDATE epa_cement_consumers SET parent_type = NULL")

    print()

    # -------------------------------------------------------------------------
    # Step 3: Build and execute the UPDATE with CASE WHEN matching
    # -------------------------------------------------------------------------
    print("Running entity resolution UPDATE...")

    case_corp, case_type = build_pattern_match_sql()

    # We need to use a temp table approach because DuckDB UPDATE with complex
    # CASE is more reliable via CREATE-then-join.

    # First, compute the resolution into a temp table
    conn.execute(f"""
        CREATE OR REPLACE TEMP TABLE resolved AS
        SELECT
            e.registry_id,
            {case_corp} AS corporate_parent,
            {case_type} AS parent_type
        FROM epa_cement_consumers e
    """)

    # Check how many were resolved
    resolved_count = conn.execute(
        "SELECT COUNT(*) FROM resolved WHERE corporate_parent IS NOT NULL"
    ).fetchone()[0]
    print(f"  Resolved {resolved_count:,} of {total:,} facilities ({100*resolved_count/total:.1f}%)")
    print()

    # Update the main table
    print("Updating epa_cement_consumers with resolved entities...")
    conn.execute("""
        UPDATE epa_cement_consumers AS e
        SET corporate_parent = r.corporate_parent,
            parent_type = r.parent_type
        FROM resolved r
        WHERE e.registry_id = r.registry_id
          AND r.corporate_parent IS NOT NULL
    """)

    # For unresolved, set parent_type = UNKNOWN
    conn.execute("""
        UPDATE epa_cement_consumers
        SET parent_type = 'UNKNOWN'
        WHERE corporate_parent IS NULL
    """)

    # For facilities where segment=CEMENT_MANUFACTURER and still unresolved,
    # try to use parent_company directly
    conn.execute("""
        UPDATE epa_cement_consumers
        SET corporate_parent = parent_company,
            parent_type = 'INTEGRATED_PRODUCER'
        WHERE corporate_parent IS NULL
          AND segment = 'CEMENT_MANUFACTURER'
          AND parent_company IS NOT NULL
          AND LENGTH(parent_company) > 2
    """)

    conn.execute("DROP TABLE IF EXISTS resolved")

    print("  Update complete.")
    print()

    # -------------------------------------------------------------------------
    # Step 4: Summary Reports
    # -------------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY: Record counts by corporate_parent (Top 50)")
    print("=" * 80)
    rows = conn.execute("""
        SELECT
            COALESCE(corporate_parent, '(UNRESOLVED)') AS corp,
            parent_type,
            COUNT(*) AS cnt
        FROM epa_cement_consumers
        GROUP BY corporate_parent, parent_type
        ORDER BY cnt DESC
        LIMIT 50
    """).fetchall()

    print(f"{'Corporate Parent':<40} {'Type':<25} {'Count':>7}")
    print("-" * 75)
    for r in rows:
        print(f"{r[0]:<40} {r[1]:<25} {r[2]:>7,}")
    print()

    # -------------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY: Record counts by parent_type")
    print("=" * 80)
    rows = conn.execute("""
        SELECT
            parent_type,
            COUNT(*) AS cnt,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM epa_cement_consumers
        GROUP BY parent_type
        ORDER BY cnt DESC
    """).fetchall()

    print(f"{'Parent Type':<30} {'Count':>7} {'Pct':>7}")
    print("-" * 47)
    for r in rows:
        print(f"{r[0]:<30} {r[1]:>7,} {r[2]:>6.1f}%")
    print()

    # -------------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY: Resolved vs Unresolved")
    print("=" * 80)
    resolved = conn.execute(
        "SELECT COUNT(*) FROM epa_cement_consumers WHERE corporate_parent IS NOT NULL"
    ).fetchone()[0]
    unresolved = conn.execute(
        "SELECT COUNT(*) FROM epa_cement_consumers WHERE corporate_parent IS NULL"
    ).fetchone()[0]
    print(f"  Resolved:    {resolved:>7,}  ({100*resolved/total:.1f}%)")
    print(f"  Unresolved:  {unresolved:>7,}  ({100*unresolved/total:.1f}%)")
    print(f"  Total:       {total:>7,}")
    print()

    # Distinct corporate parents resolved
    distinct_corp = conn.execute(
        "SELECT COUNT(DISTINCT corporate_parent) FROM epa_cement_consumers WHERE corporate_parent IS NOT NULL"
    ).fetchone()[0]
    print(f"  Distinct corporate parents resolved: {distinct_corp}")
    print()

    # -------------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY: Resolution rate by segment")
    print("=" * 80)
    rows = conn.execute("""
        SELECT
            segment,
            COUNT(*) AS total,
            SUM(CASE WHEN corporate_parent IS NOT NULL THEN 1 ELSE 0 END) AS resolved,
            ROUND(100.0 * SUM(CASE WHEN corporate_parent IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_resolved
        FROM epa_cement_consumers
        GROUP BY segment
        ORDER BY total DESC
    """).fetchall()

    print(f"{'Segment':<30} {'Total':>7} {'Resolved':>9} {'% Resolved':>11}")
    print("-" * 60)
    for r in rows:
        print(f"{r[0]:<30} {r[1]:>7,} {r[2]:>9,} {r[3]:>10.1f}%")
    print()

    # -------------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY: Top corporate parents among CEMENT_MANUFACTURER segment")
    print("=" * 80)
    rows = conn.execute("""
        SELECT
            COALESCE(corporate_parent, '(UNRESOLVED)') AS corp,
            COUNT(*) AS cnt
        FROM epa_cement_consumers
        WHERE segment = 'CEMENT_MANUFACTURER'
        GROUP BY corporate_parent
        ORDER BY cnt DESC
        LIMIT 25
    """).fetchall()

    print(f"{'Corporate Parent':<45} {'Count':>7}")
    print("-" * 55)
    for r in rows:
        print(f"{r[0]:<45} {r[1]:>7,}")
    print()

    # -------------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY: Top unresolved parent_company values (by facility count)")
    print("=" * 80)
    rows = conn.execute("""
        SELECT
            parent_company,
            COUNT(*) AS cnt,
            segment
        FROM epa_cement_consumers
        WHERE corporate_parent IS NULL
        GROUP BY parent_company, segment
        ORDER BY cnt DESC
        LIMIT 40
    """).fetchall()

    print(f"{'Parent Company (raw)':<40} {'Segment':<28} {'Count':>7}")
    print("-" * 78)
    for r in rows:
        print(f"{r[0]:<40} {r[2]:<28} {r[1]:>7,}")
    print()

    # -------------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY: Integrated Producers - facility breakdown")
    print("=" * 80)
    rows = conn.execute("""
        SELECT
            corporate_parent,
            COUNT(*) AS total,
            SUM(CASE WHEN segment = 'CEMENT_MANUFACTURER' THEN 1 ELSE 0 END) AS cement_plants,
            SUM(CASE WHEN segment = 'READY_MIX' THEN 1 ELSE 0 END) AS readymix,
            SUM(CASE WHEN segment NOT IN ('CEMENT_MANUFACTURER', 'READY_MIX') THEN 1 ELSE 0 END) AS other
        FROM epa_cement_consumers
        WHERE parent_type = 'INTEGRATED_PRODUCER'
        GROUP BY corporate_parent
        ORDER BY total DESC
    """).fetchall()

    print(f"{'Corporate Parent':<35} {'Total':>6} {'Cement':>7} {'RMX':>6} {'Other':>6}")
    print("-" * 63)
    for r in rows:
        print(f"{r[0]:<35} {r[1]:>6,} {r[2]:>7,} {r[3]:>6,} {r[4]:>6,}")
    print()

    # -------------------------------------------------------------------------
    # Verify the mapping table
    # -------------------------------------------------------------------------
    print("=" * 80)
    print("MAPPING TABLE: corporate_parents (sample)")
    print("=" * 80)
    rows = conn.execute("""
        SELECT parent_pattern, corporate_parent, parent_type
        FROM corporate_parents
        ORDER BY corporate_parent, parent_pattern
        LIMIT 30
    """).fetchall()
    print(f"{'Pattern':<30} {'Corporate Parent':<35} {'Type':<25}")
    print("-" * 90)
    for r in rows:
        print(f"{r[0]:<30} {r[1]:<35} {r[2]:<25}")
    print(f"  ... ({row_count} total pattern rows)")
    print()

    conn.close()
    print("Done. Database updated successfully.")


if __name__ == "__main__":
    main()
