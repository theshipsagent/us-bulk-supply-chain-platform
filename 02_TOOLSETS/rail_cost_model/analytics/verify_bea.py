"""Verify BEA names are resolving"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import query

print('=== TOP CEMENT ROUTES (with resolved BEA names) ===\n')
result = query("""
    SELECT
        COALESCE(o.bea_name, 'Unknown') as origin,
        COALESCE(d.bea_name, 'Unknown') as destination,
        CAST(SUM(w.exp_carloads) AS BIGINT) as carloads,
        ROUND(SUM(w.exp_freight_rev) / SUM(w.exp_tons), 2) as rev_per_ton
    FROM fact_waybill w
    LEFT JOIN dim_bea o ON w.origin_bea = o.bea_code
    LEFT JOIN dim_bea d ON w.term_bea = d.bea_code
    WHERE w.stcc = '32411'
      AND w.origin_bea != '000' AND w.term_bea != '000'
    GROUP BY 1, 2
    ORDER BY carloads DESC
    LIMIT 15
""")
print(result.to_string(index=False))
