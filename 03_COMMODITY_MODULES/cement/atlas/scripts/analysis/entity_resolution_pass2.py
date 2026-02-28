#!/usr/bin/env python3
"""Second-pass entity resolution for EPA cement consumers."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import duckdb

DB_PATH = 'atlas/data/atlas.duckdb'
con = duckdb.connect(DB_PATH)

print("=" * 70)
print("SECOND-PASS ENTITY RESOLUTION")
print("=" * 70)

before = con.execute("""
    SELECT COUNT(*) FROM epa_cement_consumers
    WHERE corporate_parent IS NULL OR corporate_parent = ''
""").fetchone()[0]
print(f"\nUnresolved before: {before:,}")

resolved_count = 0

# ===== PART 1: Decode truncated parent_company values =====
parent_mappings = [
    # Truncated EPA parents -> known corporate groups
    ("STAKER &", "CRH plc", "INTEGRATED_PRODUCER"),
    ("JACK B", "CRH plc", "INTEGRATED_PRODUCER"),
    ("OLD CASTLE", "CRH plc", "INTEGRATED_PRODUCER"),
    ("PENNSY SUPPLY", "CRH plc", "INTEGRATED_PRODUCER"),
    ("INTERSTATE &", "Knife River (MDU)", "MAJOR_READYMIX"),
    ("INTERSTATE ASPHALT", "Knife River (MDU)", "MAJOR_READYMIX"),
    ("MMC", "MMC Materials", "MAJOR_READYMIX"),
    ("MMC GULF", "MMC Materials", "MAJOR_READYMIX"),
    ("S T", "S.T. Wooten Corp", "REGIONAL_READYMIX"),
    ("S B", "S.B. Cox Ready Mix", "REGIONAL_READYMIX"),
    ("B B", "B&B Concrete Co", "REGIONAL_READYMIX"),
    ("FEDERAL", "Federal Materials", "REGIONAL_READYMIX"),
    ("OBRIEN ROCK", "OBrien Rock Co", "REGIONAL_READYMIX"),
    ("SUMMERS TAYLOR", "Summers-Taylor", "REGIONAL_READYMIX"),
    ("CAMPBELL RMC", "Campbell RMC", "REGIONAL_READYMIX"),
    ("MASCHMEYER", "Maschmeyer Concrete", "REGIONAL_READYMIX"),
    ("SEQUATCHIE SERVICE", "Sequatchie Concrete Svc", "REGIONAL_READYMIX"),
    ("NARVICK BROTHERS", "Narvick Brothers", "REGIONAL_READYMIX"),
    ("BAJA CONTRACTORS", "Baja Contractors", "REGIONAL_READYMIX"),
    ("WELSCH", "Welsch Ready Mix", "REGIONAL_READYMIX"),
    ("MILBURN BROTHERS", "Milburn Brothers", "REGIONAL_READYMIX"),
    ("SJOSTROM &", "Sjostrom & Sons", "REGIONAL_READYMIX"),
    ("RALPH CLAYTON", "Ralph Clayton & Sons", "REGIONAL_READYMIX"),
    ("KRM MIDLANDS", "KRM Midlands", "REGIONAL_READYMIX"),
    ("BLUEDOT READI", "BlueDot Readi-Mix", "REGIONAL_READYMIX"),
    ("BEELMAN", "Beelman Ready Mix", "REGIONAL_READYMIX"),
    ("CORNEJO &", "Cornejo & Sons", "REGIONAL_READYMIX"),
    ("PETE LIEN", "Pete Lien & Sons", "REGIONAL_READYMIX"),
    ("BURNCO COLORADO", "BURNCO", "REGIONAL_READYMIX"),
    ("SIMON CONTRACTORS", "Simon Contractors", "REGIONAL_READYMIX"),
    ("BUILDERS SUPPLY", "Builders Supply Co", "REGIONAL_READYMIX"),
    ("P W", "P.W. Feenstra Const", "REGIONAL_READYMIX"),
    ("BAMA BIRMINGHAM", "Bama Concrete", "REGIONAL_READYMIX"),
    ("SOUTHERN EQUIPMENT", "Southern Equipment", "REGIONAL_READYMIX"),
    ("DOBSON BROTHERS", "Dobson Brothers", "REGIONAL_READYMIX"),
    ("GATE", "Gate Precast", "PRECAST_NATIONAL"),
    ("CORESLAB STRUCTURES", "Coreslab Structures", "PRECAST_NATIONAL"),
    ("PRESTRESS SERVICES", "Prestress Services Ind", "PRECAST_NATIONAL"),
    ("NORTHFIELD BLOCK", "Northfield Block Co", "BLOCK_MASONRY"),
    ("ANGELUS BLOCK", "Angelus Block Co", "BLOCK_MASONRY"),
    ("SUPERLITE BLOCK", "Superlite Block", "BLOCK_MASONRY"),
    ("MASONRY SUPPLY", "Georgia Masonry Supply", "BLOCK_MASONRY"),
    ("CUSTOM BUILDING", "Custom Building Products", "BLOCK_MASONRY"),
    ("GRANITE CONSTRUCTION", "Granite Construction", "MAJOR_READYMIX"),
    ("GRANITE ROCK", "Graniterock Co", "REGIONAL_READYMIX"),
    ("CASTLE ROCK", "Castle Rock Construction", "REGIONAL_READYMIX"),
    ("VALCO", "Valco Industries", "REGIONAL_READYMIX"),
    ("DELTA", "Delta Concrete", "REGIONAL_READYMIX"),
]

print("\nPart 1: Matching by parent_company field...")
for pattern, corp_parent, ptype in parent_mappings:
    safe_parent = corp_parent.replace("'", "''")
    safe_pattern = pattern.replace("'", "''")
    cnt_before = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE (corporate_parent IS NULL OR corporate_parent = '')
        AND parent_company = '{safe_pattern}'
    """).fetchone()[0]
    if cnt_before > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET corporate_parent = '{safe_parent}', parent_type = '{ptype}'
            WHERE (corporate_parent IS NULL OR corporate_parent = '')
            AND parent_company = '{safe_pattern}'
        """)
        resolved_count += cnt_before
        print(f"  {pattern:<30} -> {corp_parent:<30} ({cnt_before} fac)")

# ===== PART 2: Match by fac_name patterns =====
name_patterns = [
    ("READY MIX USA", "Ready Mix USA", "MAJOR_READYMIX"),
    ("MMC MATERIALS", "MMC Materials", "MAJOR_READYMIX"),
    ("CONCRETE SUPPLY CO", "Concrete Supply Co", "REGIONAL_READYMIX"),
    ("IDEAL READY MIX", "Ideal Ready Mix", "REGIONAL_READYMIX"),
    ("AMERICAN CONCRETE PRODUCTS", "American Concrete Products", "REGIONAL_READYMIX"),
    ("MANATT", "Manatts Inc", "REGIONAL_READYMIX"),
    ("PAULSEN", "Paulsen Inc", "REGIONAL_READYMIX"),
    ("CEMSTONE", "Cemstone Products", "REGIONAL_READYMIX"),
    ("SOUTHERN CONCRETE MATERIAL", "Southern Concrete Materials", "REGIONAL_READYMIX"),
    ("LATTIMORE MATERIAL", "Lattimore Materials", "REGIONAL_READYMIX"),
    ("MIDWEST CONCRETE MATERIAL", "Midwest Concrete Materials", "REGIONAL_READYMIX"),
    ("SCHUSTER CONCRETE", "Schuster Concrete", "REGIONAL_READYMIX"),
    ("BAYOU CONCRETE", "Bayou Concrete", "REGIONAL_READYMIX"),
    ("FOLEY PRODUCTS", "Foley Products", "PIPE_PRODUCTS"),
    ("DELTA INDUSTRIES", "Delta Industries", "REGIONAL_READYMIX"),
    ("SHERMAN INDUSTRIES", "Sherman Industries", "REGIONAL_READYMIX"),
    ("CHANDLER CONCRETE", "Chandler Concrete", "REGIONAL_READYMIX"),
    ("S. T. WOOTEN", "S.T. Wooten Corp", "REGIONAL_READYMIX"),
    ("S T WOOTEN", "S.T. Wooten Corp", "REGIONAL_READYMIX"),
    ("S B COX", "S.B. Cox Ready Mix", "REGIONAL_READYMIX"),
    ("ESSEX CONCRETE", "Essex Concrete", "REGIONAL_READYMIX"),
    ("CATALINA PACIFIC", "Catalina Pacific Concrete", "REGIONAL_READYMIX"),
    ("OZARK READY MIX", "Ozark Ready Mix", "REGIONAL_READYMIX"),
    ("GARROTT BROTHERS", "Garrott Brothers", "REGIONAL_READYMIX"),
    ("BRECKENRIDGE MATERIAL", "Breckenridge Materials", "REGIONAL_READYMIX"),
    ("CENTURY CONCRETE", "Century Concrete", "REGIONAL_READYMIX"),
    ("SOUTHERN CONCRETE PRODUCTS", "Southern Concrete Products", "REGIONAL_READYMIX"),
    ("CONCRETE INDUSTRIES", "Concrete Industries", "REGIONAL_READYMIX"),
    ("TREMRON", "Tremron", "BLOCK_MASONRY"),
    ("SUNROCK", "Sunrock Industries", "REGIONAL_READYMIX"),
    ("BARD MATERIAL", "Bard Materials", "REGIONAL_READYMIX"),
    ("IDAHO CONCRETE", "Idaho Concrete", "REGIONAL_READYMIX"),
    ("SHELBY CONCRETE", "Shelby Concrete", "REGIONAL_READYMIX"),
    ("SEMO READY MIX", "SEMO Ready Mix", "REGIONAL_READYMIX"),
    ("BESTWAY CONCRETE", "Bestway Concrete", "REGIONAL_READYMIX"),
    ("EASTERN CONCRETE", "Eastern Concrete Materials", "REGIONAL_READYMIX"),
    ("WALTERS READY MIX", "Walters Ready Mix", "REGIONAL_READYMIX"),
    ("SOUTH VALLEY MATERIAL", "South Valley Materials", "REGIONAL_READYMIX"),
    ("ALLIANCE READY MIX", "Alliance Ready Mix", "REGIONAL_READYMIX"),
    ("HMSS PLANT", "HMSS", "REGIONAL_READYMIX"),
    ("SUPERIOR CONCRETE", "Superior Concrete", "REGIONAL_READYMIX"),
    ("CONSOLIDATED CONCRETE", "Consolidated Concrete", "REGIONAL_READYMIX"),
    ("ADONEL CONCRETE", "Adonel Concrete", "REGIONAL_READYMIX"),
    ("ARPS RED", "Arps Redi-Mix", "REGIONAL_READYMIX"),
    ("ERNST ENTERPRISES", "Ernst Enterprises", "REGIONAL_READYMIX"),
    ("MILES SAND", "Miles Sand & Gravel", "REGIONAL_READYMIX"),
    ("STAKER", "CRH plc", "INTEGRATED_PRODUCER"),
    ("JACK B. PARSON", "CRH plc", "INTEGRATED_PRODUCER"),
    ("JACK B PARSON", "CRH plc", "INTEGRATED_PRODUCER"),
    ("INTERSTATE CONCRETE", "Knife River (MDU)", "MAJOR_READYMIX"),
    ("7/11 MATERIAL", "7/11 Materials", "REGIONAL_READYMIX"),
    ("ORCO BLOCK", "Orco Block Co", "BLOCK_MASONRY"),
    ("B AND B CONCRETE", "B&B Concrete Co", "REGIONAL_READYMIX"),
    ("MEDINA SUPPLY", "Medina Supply Co", "REGIONAL_READYMIX"),
    ("METRO READY MIX", "Metro Ready Mix", "REGIONAL_READYMIX"),
    ("CARROLL CONCRETE", "Carroll Concrete", "REGIONAL_READYMIX"),
    ("MID-ILLINOIS", "Mid-Illinois Concrete", "REGIONAL_READYMIX"),
    ("ROWE CONSTRUCTION", "Rowe Construction", "REGIONAL_READYMIX"),
    ("ROGERS REDI", "Rogers Redi-Mix", "REGIONAL_READYMIX"),
    ("SEQUATCHIE CONCRETE", "Sequatchie Concrete Svc", "REGIONAL_READYMIX"),
    ("QUALITY READY MIX", "Quality Ready Mix", "REGIONAL_READYMIX"),
    ("S & W READY MIX", "S&W Ready Mix", "REGIONAL_READYMIX"),
    ("CENTRAL READY MIX", "Central Ready Mix", "REGIONAL_READYMIX"),
    ("PENNY", "Pennys Concrete", "REGIONAL_READYMIX"),
    ("MAD DOG CONCRETE", "Mad Dog Concrete", "REGIONAL_READYMIX"),
    ("LYCON", "Lycon Inc", "REGIONAL_READYMIX"),
    ("HI GRADE", "Hi-Grade Materials", "REGIONAL_READYMIX"),
    ("CONCRETE ENTERPRISE", "Concrete Enterprises", "REGIONAL_READYMIX"),
    ("CONCRETE SERVICE COMPANY", "Concrete Service Co", "REGIONAL_READYMIX"),
    ("TCS MATERIAL", "TCS Materials", "REGIONAL_READYMIX"),
    ("HORMIG MAYAGUEZANA", "Hormigonera Mayaguezana", "REGIONAL_READYMIX"),
    ("QUAD COUNTY", "Quad County Ready Mix", "REGIONAL_READYMIX"),
    ("CENTRAL IOWA", "Central Iowa Ready Mix", "REGIONAL_READYMIX"),
    ("PLOTE CONSTRUCTION", "Plote Construction", "REGIONAL_READYMIX"),
    ("DRAGON PRODUCTS", "Dragon Products", "REGIONAL_READYMIX"),
    ("KENDALL COUNTY CONCRETE", "Kendall County Concrete", "REGIONAL_READYMIX"),
    ("RIVER REDI", "River Redi-Mix", "REGIONAL_READYMIX"),
    ("CONTRACTORS CONCRETE", "Contractors Concrete", "REGIONAL_READYMIX"),
    ("RED E MIX", "Red-E-Mix", "REGIONAL_READYMIX"),
    ("NARVICK BROTHERS", "Narvick Brothers", "REGIONAL_READYMIX"),
    ("MASCHMEYER CONCRETE", "Maschmeyer Concrete", "REGIONAL_READYMIX"),
    ("HUEY P", "Huey P Long Industries", "REGIONAL_READYMIX"),
    ("AMERICAN ROCK", "American Rock Products", "REGIONAL_READYMIX"),
    ("ROCKY MOUNTAIN PRESTRESS", "Rocky Mountain Prestress", "PRECAST_NATIONAL"),
    ("CALMAT", "CalMat (Vulcan)", "MAJOR_READYMIX"),
    ("VAN SMITH", "Van Smith Concrete", "REGIONAL_READYMIX"),
    ("SUPER MIX", "Super Mix Inc", "REGIONAL_READYMIX"),
]

print("\nPart 2: Matching by fac_name patterns...")
for pattern, corp_parent, ptype in name_patterns:
    safe_parent = corp_parent.replace("'", "''")
    cnt_before = con.execute(f"""
        SELECT COUNT(*) FROM epa_cement_consumers
        WHERE (corporate_parent IS NULL OR corporate_parent = '')
        AND UPPER(fac_name) LIKE '%{pattern}%'
    """).fetchone()[0]
    if cnt_before > 0:
        con.execute(f"""
            UPDATE epa_cement_consumers
            SET corporate_parent = '{safe_parent}', parent_type = '{ptype}'
            WHERE (corporate_parent IS NULL OR corporate_parent = '')
            AND UPPER(fac_name) LIKE '%{pattern}%'
        """)
        resolved_count += cnt_before
        print(f"  {pattern:<35} -> {corp_parent:<30} ({cnt_before} by name)")

# ===== RESULTS =====
after = con.execute("""
    SELECT COUNT(*) FROM epa_cement_consumers
    WHERE corporate_parent IS NULL OR corporate_parent = ''
""").fetchone()[0]

print(f"\n{'=' * 70}")
print(f"SECOND PASS RESULTS")
print(f"{'=' * 70}")
print(f"Resolved this pass:  {resolved_count:,}")
print(f"Unresolved before:   {before:,}")
print(f"Unresolved after:    {after:,}")
print(f"Total resolved:      {15782 - after:,} of 15,782 ({(15782-after)*100/15782:.1f}%)")

print(f"\n=== PARENT_TYPE DISTRIBUTION (updated) ===")
r = con.execute("""
    SELECT parent_type, COUNT(*) c FROM epa_cement_consumers
    GROUP BY parent_type ORDER BY c DESC
""").fetchdf()
for _, row in r.iterrows():
    print(f"  {row['parent_type']:<25} {row['c']:>7,}")

print(f"\n=== TOP 40 CORPORATE PARENTS (updated) ===")
r2 = con.execute("""
    SELECT corporate_parent, parent_type, COUNT(*) c
    FROM epa_cement_consumers
    WHERE corporate_parent IS NOT NULL AND corporate_parent != ''
    GROUP BY corporate_parent, parent_type ORDER BY c DESC LIMIT 40
""").fetchdf()
print(f"{'Corporate Parent':<37} {'Type':<22} {'Fac':>5}")
print("-" * 67)
for _, row in r2.iterrows():
    print(f"  {str(row['corporate_parent'])[:35]:<35} {str(row['parent_type'])[:20]:<22} {row['c']:>5}")

# NC market updated
print(f"\n=== NORTH CAROLINA MARKET (updated) ===")
r3 = con.execute("""
    SELECT
        COALESCE(NULLIF(corporate_parent, ''), '(Independent)') as company,
        parent_type,
        COUNT(*) as fac_count
    FROM epa_cement_consumers
    WHERE fac_state = 'NC'
    GROUP BY company, parent_type
    ORDER BY fac_count DESC
    LIMIT 25
""").fetchdf()
for _, row in r3.iterrows():
    print(f"  {str(row['company'])[:38]:<40} {str(row['parent_type'])[:18]:<20} {row['fac_count']:>4}")

con.close()
print("\nDone.")
