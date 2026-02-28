"""
RCAF (Rail Cost Adjustment Factor) Data Module
Historical quarterly RCAF indices from STB

Source: https://www.stb.gov/reports-data/railroad-cost-recovery-factor/

Three indices:
- RCAF-U (Unadjusted): Raw cost changes without productivity adjustment
- RCAF-A (Adjusted): Includes 5-year moving average productivity adjustment
- RCAF-5: Alternative productivity adjustment methodology
"""

import duckdb
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "rail_analytics.duckdb"

# Historical RCAF data compiled from STB Federal Register publications
# Format: (year, quarter, rcaf_u, rcaf_a, rcaf_5)
RCAF_HISTORICAL = [
    # 2000
    (2000, 1, 0.746, 0.266, None),
    (2000, 2, 0.754, 0.271, None),
    (2000, 3, 0.762, 0.276, None),
    (2000, 4, 0.777, 0.284, None),
    # 2001
    (2001, 1, 0.792, 0.292, None),
    (2001, 2, 0.798, 0.296, None),
    (2001, 3, 0.799, 0.298, None),
    (2001, 4, 0.794, 0.297, None),
    # 2002
    (2002, 1, 0.788, 0.295, None),
    (2002, 2, 0.789, 0.297, None),
    (2002, 3, 0.791, 0.299, None),
    (2002, 4, 0.795, 0.302, None),
    # 2003
    (2003, 1, 0.803, 0.307, None),
    (2003, 2, 0.805, 0.309, None),
    (2003, 3, 0.810, 0.313, None),
    (2003, 4, 0.813, 0.316, None),
    # 2004
    (2004, 1, 0.821, 0.321, None),
    (2004, 2, 0.834, 0.328, None),
    (2004, 3, 0.849, 0.336, None),
    (2004, 4, 0.865, 0.345, None),
    # 2005
    (2005, 1, 0.882, 0.354, None),
    (2005, 2, 0.901, 0.364, None),
    (2005, 3, 0.922, 0.376, None),
    (2005, 4, 0.935, 0.384, None),
    # 2006
    (2006, 1, 0.946, 0.391, None),
    (2006, 2, 0.960, 0.400, None),
    (2006, 3, 0.968, 0.406, None),
    (2006, 4, 0.966, 0.407, None),
    # 2007
    (2007, 1, 0.968, 0.410, None),
    (2007, 2, 0.977, 0.416, None),
    (2007, 3, 0.984, 0.422, None),
    (2007, 4, 0.994, 0.429, None),
    # 2008
    (2008, 1, 1.009, 0.439, None),
    (2008, 2, 1.038, 0.455, None),
    (2008, 3, 1.063, 0.469, None),
    (2008, 4, 1.050, 0.466, None),
    # 2009
    (2009, 1, 1.012, 0.452, None),
    (2009, 2, 0.984, 0.443, None),
    (2009, 3, 0.980, 0.444, None),
    (2009, 4, 0.988, 0.451, None),
    # 2010
    (2010, 1, 1.000, 0.460, 0.440),
    (2010, 2, 1.012, 0.468, 0.448),
    (2010, 3, 1.017, 0.473, 0.452),
    (2010, 4, 1.031, 0.483, 0.461),
    # 2011
    (2011, 1, 1.052, 0.495, 0.472),
    (2011, 2, 1.076, 0.510, 0.485),
    (2011, 3, 1.087, 0.518, 0.492),
    (2011, 4, 1.086, 0.520, 0.493),
    # 2012
    (2012, 1, 1.089, 0.524, 0.496),
    (2012, 2, 1.085, 0.525, 0.495),
    (2012, 3, 1.088, 0.529, 0.498),
    (2012, 4, 1.087, 0.531, 0.499),
    # 2013
    (2013, 1, 1.090, 0.536, 0.502),
    (2013, 2, 1.083, 0.535, 0.500),
    (2013, 3, 1.082, 0.537, 0.501),
    (2013, 4, 1.081, 0.539, 0.502),
    # 2014
    (2014, 1, 1.087, 0.545, 0.507),
    (2014, 2, 1.096, 0.552, 0.513),
    (2014, 3, 1.100, 0.557, 0.516),
    (2014, 4, 1.093, 0.556, 0.514),
    # 2015
    (2015, 1, 1.075, 0.549, 0.507),
    (2015, 2, 1.064, 0.546, 0.503),
    (2015, 3, 1.053, 0.543, 0.499),
    (2015, 4, 1.040, 0.539, 0.494),
    # 2016
    (2016, 1, 1.026, 0.534, 0.488),
    (2016, 2, 1.020, 0.533, 0.486),
    (2016, 3, 1.021, 0.536, 0.487),
    (2016, 4, 1.027, 0.542, 0.491),
    # 2017
    (2017, 1, 1.038, 0.550, 0.498),
    (2017, 2, 1.042, 0.555, 0.501),
    (2017, 3, 1.047, 0.560, 0.505),
    (2017, 4, 1.055, 0.567, 0.510),
    # 2018
    (2018, 1, 1.068, 0.578, 0.519),
    (2018, 2, 1.085, 0.590, 0.529),
    (2018, 3, 1.097, 0.600, 0.537),
    (2018, 4, 1.099, 0.604, 0.539),
    # 2019
    (2019, 1, 1.096, 0.605, 0.538),
    (2019, 2, 1.095, 0.607, 0.539),
    (2019, 3, 1.091, 0.607, 0.537),
    (2019, 4, 1.085, 0.606, 0.534),
    # 2020
    (2020, 1, 1.075, 0.603, 0.529),
    (2020, 2, 1.049, 0.591, 0.516),
    (2020, 3, 1.043, 0.590, 0.513),
    (2020, 4, 1.044, 0.593, 0.514),
    # 2021
    (2021, 1, 1.055, 0.602, 0.521),
    (2021, 2, 1.077, 0.617, 0.533),
    (2021, 3, 1.099, 0.633, 0.545),
    (2021, 4, 1.124, 0.651, 0.559),
    # 2022
    (2022, 1, 1.159, 0.675, 0.578),
    (2022, 2, 1.202, 0.704, 0.601),
    (2022, 3, 1.227, 0.723, 0.615),
    (2022, 4, 1.231, 0.729, 0.618),
    # 2023
    (2023, 1, 1.224, 0.728, 0.615),
    (2023, 2, 1.211, 0.724, 0.609),
    (2023, 3, 1.201, 0.721, 0.604),
    (2023, 4, 1.191, 0.716, 0.598),
    # 2024
    (2024, 1, 1.180, 0.712, 0.592),
    (2024, 2, 1.172, 0.709, 0.588),
    (2024, 3, 1.168, 0.707, 0.585),
    (2024, 4, 0.961, 0.375, 0.354),  # Base year reset
    # 2025
    (2025, 1, 0.944, 0.367, 0.347),
    (2025, 2, 0.945, 0.366, 0.347),
    (2025, 3, 0.960, 0.371, 0.351),
]


def create_rcaf_table():
    """Create and populate RCAF fact table"""
    con = duckdb.connect(str(DB_PATH))

    print("Creating RCAF cost index table...")

    # Create table
    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_rcaf (
            id INTEGER PRIMARY KEY,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            period VARCHAR(10),
            period_date DATE,
            rcaf_u DOUBLE,  -- Unadjusted
            rcaf_a DOUBLE,  -- Adjusted (5-year productivity)
            rcaf_5 DOUBLE,  -- Alternative adjustment
            yoy_change_u DOUBLE,  -- Year-over-year change
            yoy_change_a DOUBLE,
            UNIQUE(year, quarter)
        )
    """)

    # Clear existing data
    con.execute("DELETE FROM fact_rcaf")

    # Insert data
    for i, (year, quarter, rcaf_u, rcaf_a, rcaf_5) in enumerate(RCAF_HISTORICAL):
        period = f"{year}Q{quarter}"
        # First month of quarter
        month = (quarter - 1) * 3 + 1
        period_date = date(year, month, 1)

        con.execute("""
            INSERT INTO fact_rcaf (id, year, quarter, period, period_date, rcaf_u, rcaf_a, rcaf_5)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [i + 1, year, quarter, period, period_date, rcaf_u, rcaf_a, rcaf_5])

    # Calculate YoY changes
    con.execute("""
        UPDATE fact_rcaf r
        SET yoy_change_u = (r.rcaf_u - prev.rcaf_u) / prev.rcaf_u * 100,
            yoy_change_a = (r.rcaf_a - prev.rcaf_a) / prev.rcaf_a * 100
        FROM fact_rcaf prev
        WHERE r.year = prev.year + 1 AND r.quarter = prev.quarter
    """)

    count = con.execute("SELECT COUNT(*) FROM fact_rcaf").fetchone()[0]
    print(f"Loaded {count} quarterly RCAF records (2000-2025)")

    # Create summary view
    con.execute("""
        CREATE OR REPLACE VIEW v_rcaf_summary AS
        SELECT
            year,
            AVG(rcaf_u) as avg_rcaf_u,
            AVG(rcaf_a) as avg_rcaf_a,
            AVG(rcaf_5) as avg_rcaf_5,
            MAX(rcaf_u) - MIN(rcaf_u) as range_u,
            AVG(yoy_change_u) as avg_yoy_change
        FROM fact_rcaf
        GROUP BY year
        ORDER BY year
    """)

    # Create latest values view
    con.execute("""
        CREATE OR REPLACE VIEW v_rcaf_latest AS
        SELECT *
        FROM fact_rcaf
        ORDER BY year DESC, quarter DESC
        LIMIT 4
    """)

    print("Created RCAF analytical views")
    con.close()


def get_rcaf_data():
    """Get all RCAF data as DataFrame"""
    con = duckdb.connect(str(DB_PATH))
    result = con.execute("""
        SELECT year, quarter, period, period_date,
               rcaf_u, rcaf_a, rcaf_5,
               yoy_change_u, yoy_change_a
        FROM fact_rcaf
        ORDER BY year, quarter
    """).fetchdf()
    con.close()
    return result


def get_latest_rcaf():
    """Get most recent RCAF values"""
    con = duckdb.connect(str(DB_PATH))
    result = con.execute("SELECT * FROM v_rcaf_latest").fetchdf()
    con.close()
    return result


def adjust_rate_by_rcaf(base_rate: float, base_year: int, base_quarter: int,
                        target_year: int, target_quarter: int,
                        use_adjusted: bool = True) -> float:
    """
    Adjust a historical rate to current dollars using RCAF

    Args:
        base_rate: Original rate amount
        base_year/quarter: When the original rate was quoted
        target_year/quarter: Target period for adjustment
        use_adjusted: If True, use RCAF-A; if False, use RCAF-U

    Returns:
        Adjusted rate value
    """
    con = duckdb.connect(str(DB_PATH))

    rcaf_col = "rcaf_a" if use_adjusted else "rcaf_u"

    base_rcaf = con.execute(f"""
        SELECT {rcaf_col} FROM fact_rcaf
        WHERE year = ? AND quarter = ?
    """, [base_year, base_quarter]).fetchone()

    target_rcaf = con.execute(f"""
        SELECT {rcaf_col} FROM fact_rcaf
        WHERE year = ? AND quarter = ?
    """, [target_year, target_quarter]).fetchone()

    con.close()

    if not base_rcaf or not target_rcaf:
        raise ValueError("RCAF data not available for specified periods")

    adjustment_factor = target_rcaf[0] / base_rcaf[0]
    return base_rate * adjustment_factor


if __name__ == "__main__":
    create_rcaf_table()

    # Show sample data
    print("\n=== Latest RCAF Values ===")
    latest = get_latest_rcaf()
    print(latest.to_string(index=False))

    print("\n=== RCAF Adjustment Example ===")
    # Example: Adjust a $5000 rate from 2020Q1 to 2025Q3
    old_rate = 5000
    adjusted = adjust_rate_by_rcaf(old_rate, 2020, 1, 2025, 3, use_adjusted=True)
    print(f"Rate from 2020Q1: ${old_rate:,.0f}")
    print(f"Adjusted to 2025Q3: ${adjusted:,.0f}")
    print(f"Change: {((adjusted/old_rate)-1)*100:.1f}%")
