#!/usr/bin/env python3
"""Query EPA FRS for cement-related facilities."""

import duckdb

con = duckdb.connect('G:/My Drive/LLM/task_epa_frs/data/frs.duckdb', read_only=True)

print('=== CEMENT-RELATED NAICS (3273xx) ===')
df = con.execute('''
    SELECT naics_code, COUNT(DISTINCT registry_id) as facilities
    FROM naics_codes
    WHERE naics_code LIKE '3273%'
    GROUP BY naics_code
    ORDER BY facilities DESC
''').fetchdf()
print(df.to_string())
print()
print('Total facilities:', df['facilities'].sum())

print()
print('=== FACILITIES BY STATE (NAICS 3273%) ===')
df = con.execute('''
    SELECT f.fac_state as state, COUNT(DISTINCT f.registry_id) as facilities
    FROM facilities f
    JOIN naics_codes n ON f.registry_id = n.registry_id
    WHERE n.naics_code LIKE '3273%'
    GROUP BY f.fac_state
    ORDER BY facilities DESC
    LIMIT 25
''').fetchdf()
print(df.to_string())

print()
print('=== BY SPECIFIC NAICS ===')
# 327310 - Cement Manufacturing
# 327320 - Ready-Mix Concrete
# 327331 - Concrete Block/Brick
# 327332 - Concrete Pipe
# 327390 - Other Concrete Products
for naics, desc in [('327310', 'Cement Manufacturing'),
                    ('327320', 'Ready-Mix Concrete'),
                    ('327331', 'Concrete Block/Brick'),
                    ('327332', 'Concrete Pipe'),
                    ('327390', 'Other Concrete Products'),
                    ('327999', 'Other Nonmetallic Mineral')]:
    cnt = con.execute(f'''
        SELECT COUNT(DISTINCT registry_id)
        FROM naics_codes
        WHERE naics_code = '{naics}'
    ''').fetchone()[0]
    print(f'{naics} - {desc}: {cnt:,} facilities')

con.close()
