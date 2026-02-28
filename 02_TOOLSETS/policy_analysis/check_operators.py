"""Quick check of operator consolidation results."""
import sys
sys.path.insert(0, 'G:/My Drive/LLM/project_us_flag')

from src.usace_db.database.database import Database

db = Database()

# Check operator statistics
query = """
SELECT
    COUNT(DISTINCT ts_oper) as unique_operators,
    COUNT(DISTINCT operator_name) as original_names,
    COUNT(DISTINCT operator_name_std) as standardized_names,
    COUNT(DISTINCT CASE WHEN operator_name_std IS NOT NULL THEN operator_name_std END) as mapped_names
FROM operators
"""

result = db.conn.execute(query).fetchone()

print("=" * 70)
print("OPERATOR CONSOLIDATION RESULTS")
print("=" * 70)
print(f"Unique operators (ts_oper): {result[0]}")
print(f"Original distinct names: {result[1]}")
print(f"Standardized distinct names: {result[2]}")
print(f"Operators with mapping applied: {result[3]}")
print(f"Variants consolidated: {result[1] - result[2]}")
print("=" * 70)

# Show some examples of consolidated operators
examples_query = """
SELECT
    operator_name_std,
    COUNT(*) as variant_count,
    GROUP_CONCAT(DISTINCT operator_name, ', ') as variants
FROM operators
WHERE operator_name_std IS NOT NULL
  AND operator_name_std != operator_name
GROUP BY operator_name_std
ORDER BY variant_count DESC
LIMIT 10
"""

print("\nTop 10 Consolidated Operators:")
print("-" * 70)
examples = db.conn.execute(examples_query).fetchall()
for std_name, count, variants in examples:
    print(f"\n{std_name} ({count} variants):")
    variant_list = variants.split(', ')
    for v in variant_list[:5]:  # Show first 5 variants
        print(f"  - {v}")
    if count > 5:
        print(f"  ... and {count - 5} more")

print("\n" + "=" * 70)
